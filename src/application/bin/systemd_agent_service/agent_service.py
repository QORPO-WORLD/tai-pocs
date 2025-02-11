import asyncio
import time
from collections import deque
from queue import Queue
from typing import Generator

from application.aws import AwsAPI
from application.models import ModelID
from application.utils import dump_message_to_file, trim_queue

init_prompts = [
    (
        "Imagine you're commenting the battle royale game match. You'll be getting kill events from the game like this one: "
        '[{"victim": {"username": str},"KillInstigator": {"username": str,"Distance": float,"first_kill": bool,"used_weapon": {"type": str,"name": str},"Headshot": bool,"OneShot": bool,"num_kills": int,"previous_victims": [str]},"location": str,"num_players_alive": int}]. '
        "Sometimes you will be getting more than one event in this list. "
        "You'll need to comment on the kill events, using 3 senteces max. "
        "If there are multiple events, you can decide either to comment on all of them or comment the last of them while also keeping in mind other events. "
        "Even if there are multiple events, you should still be able to say everything in 3 sentences. "
        "You're not supposed to always use each field for the comment, but you can use them if you think they're relevant. "
        "Try to also remember previous events and if you see some patterns feel free to voice them. Understood?"
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
    yield from aws.get_streamed_response(model_id, messages, time.time(), temperature)


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
