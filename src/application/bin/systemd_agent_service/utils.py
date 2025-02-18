import json

from application.db_models import GameState


def dump_str_to_file(filename: str, message: str) -> None:
    with open(filename, "a") as f:
        f.write(json.dumps(message) + "\n")


def dump_dialogue_json(filename: str, dialogue: dict) -> None:
    with open(filename, "w") as f:
        json.dump(dialogue, f)


def compose_prompt_from_events(past_events: list[GameState], future_events: list[GameState]) -> str:
    past_jsons = [json.loads(event.event_data) for event in past_events]
    future_jsons = [json.loads(event.event_data) for event in future_events]
    return json.dumps(
        {
            "already_happened": past_jsons,
            "will_happen_soon": future_jsons,
        }
    )
