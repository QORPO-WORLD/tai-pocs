import asyncio
import signal
import sys
import threading
from queue import Queue
from pathlib import Path

from application.bin.systemd_agent_service import agent_service
from application.bin.systemd_preprocessing_service import preprocessing

shutdown_event = threading.Event()



def start_event_loop(func, args):
    asyncio.run(func(*args))


def signal_handler(signum, frame):
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)


def preprocess_test():
    from application.bin.systemd_preprocessing_service.preprocess_v2 import run_preprocess
    json_path = Path("data/playground.json")

    asyncio.run(run_preprocess(json_path=json_path))


if __name__ == "__main__":
    # events_queue: "Queue[list[dict]]" = Queue()
    #
    # preprocessor = threading.Thread(target=start_event_loop, args=(preprocessing.main, (events_queue,)))
    # preprocessor.daemon = True
    # preprocessor.start()
    #
    # agent = threading.Thread(target=start_event_loop, args=(agent_service.main, (events_queue,)))
    # agent.daemon = True
    # agent.start()
    #
    # try:
    #     shutdown_event.wait()
    # except KeyboardInterrupt:
    #     sys.exit(0)

    preprocess_test()