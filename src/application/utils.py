import json


def get_kill_events(csv_filename: str) -> list[dict]:
    kills = []
    with open(csv_filename) as f:
        for line in f:
            parts = line.split("\t")
            kill_str = parts[2].replace('""', '"')
            kill_str = kill_str[1:-1]
            kill_json = json.loads(kill_str)
            kills.append(kill_json)
    return kills
