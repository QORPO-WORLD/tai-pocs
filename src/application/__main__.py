import asyncio
import threading
from pathlib import Path

from application.bin.account_service.account_countainer import AccountContainer
from application.bin.systemd_agent_service import agent_service
from application.dtos.agent_service_config import AgentServiceConfig, InitPrompts, Trait
from application.models import ModelID

shutdown_event = threading.Event()
DATA_FOLDER_PATH = "data"


def init_agent_service_configs(game_start_timestamp) -> list[AgentServiceConfig]:
    configs: list[AgentServiceConfig] = []
    traits_lists: list[list[Trait]] = [
        [
            Trait(name="toxic", value=50),
            Trait(name="honest", value=30),
        ],
        [
            Trait(name="toxic", value=100),
            Trait(name="honest", value=1),
        ],
    ]
    for model_id in ModelID.__members__.values():
        for temperature in (0.5, 0.7, 0.9):
            for past_window_size_sec in (5, 10):
                for future_window_size_sec in (3, 5):
                    for traits in traits_lists:
                        config = AgentServiceConfig(
                            init_prompts=InitPrompts(traits=traits),
                            model_id=model_id,
                            temperature=temperature,
                            past_window_size_sec=past_window_size_sec,
                            future_window_size_sec=future_window_size_sec,
                            game_start_timestamp=game_start_timestamp,
                        )
                        configs.append(config)
    return configs


def initialize_services() -> None:
    user_nicknames_path = Path(DATA_FOLDER_PATH) / "user_nicknames.json"
    account_container = AccountContainer(file_path=user_nicknames_path)


def preprocess_test() -> None:
    from application.bin.systemd_preprocessing_service.preprocess_v2 import (
        run_preprocess,
    )

    json_path = Path("data/full_game_events_1.json")

    asyncio.run(run_preprocess(json_path=json_path))


def run_agent_service(configs: list[AgentServiceConfig]) -> None:
    for config in configs:
        print(f"Starting agent service with config: {config.model_dump()}")
        agent_service.main(config)


if __name__ == "__main__":
    initialize_services()
    # preprocess_test()
    configs = init_agent_service_configs(game_start_timestamp=1739395974)
    run_agent_service(configs)
