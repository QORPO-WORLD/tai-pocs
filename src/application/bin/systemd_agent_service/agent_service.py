import asyncio
import json
import time
from collections import deque
from queue import Queue
from typing import Generator

from application.aws import AwsAPI
from application.models import ModelID
from application.utils import dump_message_to_file, trim_queue

event_example = '[{"timestamp": 1739204298, "players": [{"user_id": "1234", "character": "Zuri", "hit_points": 78, "shield": 15, "current_state": "Alive", "shot_list": [{"kill_instigator": {"weapon": {"name": "AK-47", "type": "Rifle"}}, "victim": {"user_id": "", "character": "None"}}, {"kill_instigator": {"weapon": {"name": "AK-47", "type": "Rifle"}}, "victim": {"user_id": "d55ea7", "character": "New Order"}}], "weapons": ["AK-47", "Shotgun"], "ammo": [{"name": "ShotgunAmmo", "amount": 25}, {"name": "RifleAmmo", "amount": 50}]}, {"user_id": "a20cff", "character": "Zuri", "hit_points": 78, "shield": 15, "current_state": "Alive", "shot_list": [{"kill_instigator": {"weapon": {"name": "AK-47", "type": "Rifle"}}, "victim": {"user_id": "", "character": "None"}}, {"kill_instigator": {"weapon": {"name": "AK-47", "type": "Rifle"}}, "victim": {"user_id": "d55ea7", "character": "New Order"}}], "weapons": ["AK-47", "Shotgun"], "ammo": [{"name": "ShotgunAmmo", "amount": 25}, {"name": "RifleAmmo", "amount": 50}]}]} ]'
init_prompts = [
    (
        "Imagine you're commenting the battle royale game match. You'll be getting lists of game state events like this one: "
        f"{event_example} "
        "Try to see the changes in the game state and comment on them. "
        "Requirement 1: you need to use 3 senteces max. "
        "Requirement 2: You're not supposed to always use each field for the comment, but you can use them if you think they're relevant. "
        "Requirement 3: You will also get some events which haven't happened in the game yet, you can take them into consideration but you can't comment on them directly. "
        "Understood?"
    ),
    "Understood. I'm ready to commentate on the battle royale game events.",
]


def compose_prompt_from_events(events: list[dict]) -> str:
    return "some result"


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
    prompt = json.dumps(messages)
    yield from aws.get_streamed_response_rag(model_id, prompt, time.time(), temperature)


async def main(
    event_batches_queue: Queue,
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

    while True:
        if event_batches_queue.empty():
            await asyncio.sleep(1)
            continue
        events: list[dict] = event_batches_queue.get()
        event_batches_queue.task_done()

        prompt = compose_prompt_from_events(events)
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
