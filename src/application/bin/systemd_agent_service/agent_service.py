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
from application.utils import dump_dialogue_to_file, trim_queue


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

    dialogue = [
        {
            "role": "User",
            "message": q[-2],
            "timestamp": config.game_start_timestamp,
        },
        {
            "role": "Assistant",
            "message": q[-1],
            "timestamp": config.game_start_timestamp,
        },
    ]

    path = (
        f"output/text/{config.model_id.value}-{config.temperature}-"
        f"{config.past_window_size_sec}-{config.future_window_size_sec}-{config.query_interval_sec}"
    )
    if not os.path.exists(path):
        os.makedirs(path)

    dialogue_filename = f"{path}/{config.init_prompts.traits}-dialogue"
    with open(f"{dialogue_filename}.txt", "a") as f:
        f.write(f"{dialogue[-1]}\n")

    base_timestamp = config.game_start_timestamp
    db = DatabaseConnection()
    session = db.get_session()

    while base_timestamp < config.game_end_timestamp:
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
        if not past_events:
            base_timestamp += config.query_interval_sec
            continue

        past_jsons = [json.loads(event.event_data) for event in past_events]
        future_jsons = [json.loads(event.event_data) for event in future_events]

        prompt = compose_prompt_from_events(past_jsons, future_jsons)
        trim_queue(q, config.context_window_size, config.init_prompts)

        q.append(prompt)
        dialogue.append({"role": "User", "message": q[-1], "timestamp": base_timestamp})

        response = []
        try:
            current_timestamp = time.time()
            try:
                for sentence in get_sentences(q, aws, config.model_id, config.temperature):
                    response.append(sentence)
                aws.models_mapping[config.model_id].delays.append(time.time() - current_timestamp)
                print(aws.models_mapping[config.model_id].get_model_stats())
            except Exception as err:
                print(f"Timestamp {base_timestamp} will be retried. Error: {err}")
                continue
            except KeyboardInterrupt:
                dump_dialogue_to_file(f"{dialogue_filename}.json", dialogue)
                break

            path = (
                f"output/audio/{config.model_id.value}-{config.temperature}-"
                f"{config.past_window_size_sec}-{config.future_window_size_sec}-{config.query_interval_sec}-{config.init_prompts.traits}"
            )
            if not os.path.exists(path):
                os.makedirs(path)

            audio_delays = []
            for i, sentence in enumerate(response):
                current_timestamp = time.time()
                audio_filename = f"{path}/{base_timestamp}-{i + 1}.mp3"
                aws.convert_to_voice(sentence, audio_filename)
                audio_delays.append(time.time() - current_timestamp)

            aws.delays = audio_delays
            print(aws.get_polly_stats())

        except KeyboardInterrupt:
            dump_dialogue_to_file(f"{dialogue_filename}.json", dialogue)
            break

        q.append("".join(response))
        dialogue.append(
            {
                "role": "Assistant",
                "message": q[-1],
                "timestamp": base_timestamp,
            }
        )
        with open(f"{dialogue_filename}.txt", "a") as f:
            f.write(f"{dialogue[-1]}\n")

        base_timestamp += config.query_interval_sec

    dump_dialogue_to_file(f"{dialogue_filename}.json", dialogue)
    print(aws.models_mapping[config.model_id].get_model_stats())
    print(aws.get_polly_stats())
