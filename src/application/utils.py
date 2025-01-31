import json
import random
from collections import deque


def get_game_events(csv_filename: str) -> list[dict]:
    kills = []
    with open(csv_filename) as f:
        for line in f:
            parts = line.split("\t")
            kill_str = parts[2].replace('""', '"')
            kill_str = kill_str[1:-1]
            kill_json = json.loads(kill_str)
            kills.append(kill_json)
    return kills


def trim_queue(q: deque, context_window_size: int, init_prompts: list[str]) -> None:
    if len(q) + 2 > context_window_size:
        for _ in range(len(init_prompts)):
            q.popleft()
        q.popleft()
        q.popleft()
        for prompt in reversed(init_prompts):
            q.appendleft(prompt)


def dump_message_to_file(role, message: str, filename: str) -> None:
    with open(filename, "a") as f:
        f.write(f"{role}: {message}\n")
        if role == "User":
            return
        f.write("\n")


def generate_batch_sizes(game_events_total: int) -> list[int]:
    batch_sizes: list[int] = []
    while game_events_total:
        events_num = min(random.randint(1, 4), game_events_total)
        batch_sizes.append(events_num)
        game_events_total -= events_num
    return batch_sizes
