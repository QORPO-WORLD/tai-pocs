import json
import os
import time
from collections import deque
from typing import Generator

from sqlalchemy import and_

from application.aws import AwsAPI
from application.db_models import DatabaseConnection, GameState
from application.dtos.agent_service_config import AgentServiceConfig
from application.models import ModelID
from application.utils import dump_message_to_file, trim_queue


def compose_prompt_from_events(past_events: list[dict], future_events: list[dict]) -> str:
    return json.dumps(
        {
            "already_happened": past_events,
            "will_happen_soon": future_events,
        }
    )


def get_sentences(q, aws: AwsAPI, model_id: ModelID, temperature: float) -> Generator[str, None, None]:
    roles = ("user", "assistant")
    model = aws.models_mapping[model_id]

    messages = [
        {
            "role": roles[i % 2],
            "content": [model.get_content(prompt)],
        }
        for i, prompt in enumerate(q)
    ]
    yield from aws.get_streamed_response(model_id, messages, temperature)


def main(
    config: AgentServiceConfig,
) -> None:
    aws = AwsAPI()
    q = deque(config.init_prompts.to_list())

    path = (
        f"output/text/{config.model_id.value}/temp-{config.temperature}/"
        f"past-{config.past_window_size_sec}-sec/future-{config.future_window_size_sec}-sec"
    )
    if not os.path.exists(path):
        os.makedirs(path)
    dialogue_filename = f"{path}/{config.init_prompts.traits}-dialogue.txt"

    dump_message_to_file("User", q[-2], dialogue_filename)
    dump_message_to_file("Assistant", q[-1], dialogue_filename)

    base_timestamp = config.game_start_timestamp
    db = DatabaseConnection()
    session = db.get_session()

    while True:
        past_events: list[GameState] = (
            session.query(GameState)
            .filter(
                and_(
                    GameState.event_created_at >= base_timestamp,
                    GameState.event_created_at < base_timestamp + config.past_window_size_sec,
                )
            )
            .all()
        )
        future_events: list[GameState] = (
            session.query(GameState)
            .filter(
                and_(
                    GameState.event_created_at >= base_timestamp + config.past_window_size_sec,
                    GameState.event_created_at < base_timestamp + config.past_window_size_sec + config.future_window_size_sec,
                )
            )
            .all()
        )
        base_timestamp += config.past_window_size_sec

        past_jsons = [json.loads(event.event_data) for event in past_events]
        future_jsons = [json.loads(event.event_data) for event in future_events]

        prompt = compose_prompt_from_events(past_jsons, future_jsons)
        trim_queue(q, config.context_window_size, config.init_prompts)

        q.append(prompt)
        dump_message_to_file("User", q[-1], dialogue_filename)

        response = []
        try:
            current_timestamp = time.time()
            bedrock_delays = []

            for sentence in get_sentences(q, aws, config.model_id, config.temperature):
                bedrock_delays.append(time.time() - current_timestamp)
                response.append(sentence)
                current_timestamp = time.time()
            aws.models_mapping[config.model_id].delays = bedrock_delays

            path = (
                f"output/audio/{config.model_id.value}/temp-{config.temperature}/"
                f"past-{config.past_window_size_sec}-sec/future-{config.future_window_size_sec}-sec/{config.init_prompts.traits}"
            )
            if not os.path.exists(path):
                os.makedirs(path)

            audio_delays = []
            for i, sentence in enumerate(response):
                current_timestamp = time.time()
                audio_filename = f"{path}/{i + 1}-{base_timestamp - config.past_window_size_sec}.mp3"
                aws.convert_to_voice(sentence, audio_filename)
                audio_delays.append(time.time() - current_timestamp)

            aws.delays = audio_delays

            print(aws.models_mapping[config.model_id].get_model_stats())
            print(aws.get_polly_stats())

        except KeyboardInterrupt:
            break

        q.append("".join(response))
        dump_message_to_file("Assistant", q[-1], dialogue_filename)
