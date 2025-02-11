import json


def get_game_events_from_json(json_filename: str) -> list[dict]:
    with open(json_filename) as f:
        return json.load(f)["samples"]
