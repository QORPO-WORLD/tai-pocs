import json
import time
from collections import deque
from typing import Generator

from sqlalchemy import and_

from application.aws import AwsAPI
from application.db_models import DatabaseConnection, GameState
from application.dtos.game_state_event import GameStateGroupGameEvent
from application.models import ModelID
from application.utils import dump_message_to_file, trim_queue

event_example = GameStateGroupGameEvent.sample()
init_prompts = [
    (
        "Imagine you're commenting the battle royale game match. You'll be getting lists of game state events like this one: "
        f"{event_example.model_dump()} "
        "Try to see the changes in the game state and comment on them. "
        "Requirement 1: you need to use 3 senteces max. "
        "Requirement 2: You're not supposed to always use each field for the comment, but you can use them if you think they're relevant. "
        "Requirement 3: You will also get some events which haven't happened in the game yet, you can take them into consideration but you can't comment on them directly. "
        "Understood?"
    ),
    "Understood. I'm ready to commentate on the battle royale game events.",
]


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
    yield from aws.get_streamed_response(model_id, messages, time.time(), temperature)


def main(
    region: str = "us-east-1",
    model_id: ModelID = ModelID.NOVA_PRO,
    context_window_size: int = 20,
    temperature: float = 0.9,
) -> None:
    aws = AwsAPI(region)
    q = deque(init_prompts)

    filename = f"output/text/{int(time.time())}-{model_id.value}.txt"

    dump_message_to_file("User", q[-2], filename)
    dump_message_to_file("Assistant", q[-1], filename)

    GAME_START_TIMESTAMP = 1739395974
    current_timestamp = GAME_START_TIMESTAMP
    comment_window_sec = 5
    future_window_sec = 3
    db = DatabaseConnection()
    session = db.get_session()

    while True:
        past_events: list[GameState] = (
            session.query(GameState)
            .filter(
                and_(
                    GameState.event_created_at >= current_timestamp,
                    GameState.event_created_at < current_timestamp + comment_window_sec,
                )
            )
            .all()
        )
        future_events: list[GameState] = (
            session.query(GameState)
            .filter(
                and_(
                    GameState.event_created_at >= current_timestamp + comment_window_sec,
                    GameState.event_created_at < current_timestamp + comment_window_sec + future_window_sec,
                )
            )
            .all()
        )
        current_timestamp += comment_window_sec

        past_jsons = [json.loads(event.event_data) for event in past_events]
        future_jsons = [json.loads(event.event_data) for event in future_events]

        prompt = compose_prompt_from_events(past_jsons, future_jsons)
        trim_queue(q, context_window_size, init_prompts)

        q.append(prompt)
        dump_message_to_file("User", q[-1], filename)

        response = []
        try:
            for sentence in get_sentences(q, aws, model_id, temperature):
                response.append(sentence)
        except KeyboardInterrupt:
            break

        q.append("".join(response))
        dump_message_to_file("Assistant", q[-1], filename)
