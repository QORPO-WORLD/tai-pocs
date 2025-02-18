import json
import os
import time
from collections import deque
from datetime import datetime
from typing import Generator

from sqlalchemy import and_
from sqlalchemy.orm import Session

from application.aws import AwsAPI
from application.bin.systemd_agent_service.utils import (
    compose_prompt_from_events,
    dump_dialogue_json,
    dump_str_to_file,
)
from application.db_models import DatabaseConnection, GameState
from application.dtos.agent_service_config import AgentServiceConfig


class AgentService:
    def __init__(self, config: AgentServiceConfig) -> None:
        self.config = config
        self.aws = AwsAPI()
        self.db = DatabaseConnection()
        self.dialogue_path, self.audio_path = self.make_output_paths()

        self.base_timestamp = self.config.game_start_timestamp
        self.q = deque(self.config.init_prompts.to_list())
        self.dialogue = [
            {"role": role, "message": message, "timestamp": self.config.game_start_timestamp}
            for role, message in zip(("User", "Assistant"), (self.q[-2], self.q[-1]))
        ]
        self.dialogue_filename = f"{self.dialogue_path}/dialogue"
        self.dump_configs()

    def dump_configs(self) -> None:
        for filename in (f"{self.audio_path}/config.json", f"{self.dialogue_path}/config.json"):
            with open(filename, "w") as f:
                json.dump(self.config.model_dump(), f)

    def make_output_paths(self) -> tuple[str, str]:
        human_readable_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        audio_path = f"output/audio/{human_readable_timestamp}"
        dialogue_path = f"output/text/{human_readable_timestamp}"
        for path in (audio_path, dialogue_path):
            if not os.path.exists(path):
                os.makedirs(path)

        return dialogue_path, audio_path

    def get_sentences(self) -> Generator[str, None, None]:
        roles = ("user", "assistant")
        model = self.aws.models_mapping[self.config.model_id]

        messages = [
            {
                "role": roles[i % 2],
                "content": [model.get_content(prompt)],
            }
            for i, prompt in enumerate(self.q)
        ]
        yield from self.aws.get_streamed_response(self.config.model_id, messages, self.config.temperature)

    def generate_response(self) -> list[str]:
        current_timestamp = time.time()
        response = []

        for sentence in self.get_sentences():
            response.append(sentence)
        self.aws.models_mapping[self.config.model_id].delays.append(time.time() - current_timestamp)

        return response

    def generate_audios(self, response: list[str]) -> None:
        audio_delays = []
        for i, sentence in enumerate(response):
            current_timestamp = time.time()
            audio_filename = f"{self.audio_path}/{self.base_timestamp}-{i + 1}.mp3"
            self.aws.convert_to_voice(sentence, audio_filename)
            audio_delays.append(time.time() - current_timestamp)
        self.aws.delays = audio_delays

    def get_events_from_db(self, session: Session) -> tuple[list[GameState], list[GameState]]:
        past_events: list[GameState] = (
            session.query(GameState)
            .filter(
                and_(
                    GameState.event_created_at >= self.base_timestamp,
                    GameState.event_created_at < self.base_timestamp + self.config.past_window_size_sec,
                )
            )
            .all()
        )
        future_events: list[GameState] = (
            session.query(GameState)
            .filter(
                and_(
                    GameState.event_created_at >= self.base_timestamp + self.config.past_window_size_sec,
                    GameState.event_created_at
                    < self.base_timestamp + self.config.past_window_size_sec + self.config.future_window_size_sec,
                )
            )
            .all()
        )
        return past_events, future_events

    def print_stats(self) -> None:
        print(self.aws.models_mapping[self.config.model_id].get_model_stats())
        print(self.aws.get_polly_stats())

    def _trim_queue(self) -> None:
        init_prompts_list = self.config.init_prompts.to_list()
        if len(self.q) + 2 > self.config.context_window_size:
            for _ in range(len(init_prompts_list)):
                self.q.popleft()
            self.q.popleft()
            self.q.popleft()
            for prompt in reversed(init_prompts_list):
                self.q.appendleft(prompt)

    def main(self) -> None:
        session = self.db.get_session()
        dump_str_to_file(f"{self.dialogue_filename}.txt", self.dialogue[-1])

        while self.base_timestamp < self.config.game_end_timestamp:
            past_events, future_events = self.get_events_from_db(session)
            if not past_events:
                self.base_timestamp += self.config.query_interval_sec
                continue

            prompt = compose_prompt_from_events(past_events, future_events)
            self._trim_queue()

            self.q.append(prompt)
            self.dialogue.append({"role": "User", "message": self.q[-1], "timestamp": self.base_timestamp})
            try:
                sentences = self.generate_response()
                self.generate_audios(sentences)
                self.print_stats()
            except Exception as err:
                print(f"Timestamp {self.base_timestamp} will be retried. Error: {err}")
                continue
            except KeyboardInterrupt:
                break

            self.q.append("".join(sentences))
            self.dialogue.append({"role": "Assistant", "message": self.q[-1], "timestamp": self.base_timestamp})
            dump_str_to_file(f"{self.dialogue_filename}.txt", self.dialogue[-1])

            self.base_timestamp += self.config.query_interval_sec

        dump_dialogue_json(f"{self.dialogue_filename}.json", self.dialogue)
        self.print_stats()
