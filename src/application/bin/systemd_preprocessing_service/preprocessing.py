from collections import deque
from queue import Queue

from application.bin.systemd_preprocessing_service.utils import (
    get_game_events_from_json,
)


def process_batch(events_batch: list[dict]) -> None:
    pass


async def main(event_batches_queue: Queue) -> None:
    game_events = deque(get_game_events_from_json("data/playground.json"))
    window_size_sec = 5

    game_events_list = []
    while game_events:
        event = game_events.pop()
        game_events_list.append(event)
        if event["timestamp"] - game_events_list[0]["timestamp"] < window_size_sec:
            continue
        process_batch(game_events_list)
        event_batches_queue.put(game_events_list)
        game_events_list = []
    if game_events_list:
        event_batches_queue.put(game_events_list)
