import json
from pathlib import Path

from application.db_models import DatabaseConnection
from application.db_models import GameState as DBGameState
from application.dtos.game_state_event import GameStateGroupGameEvent


async def run_preprocess(json_path: Path) -> None:
    # Step 1: Load playground.json
    print("i am here")
    if not json_path.exists():
        print(f"{json_path} file not found!")
        return

    with open(json_path, "r") as file:
        raw_data: dict = json.load(file)

    db = DatabaseConnection()
    # Step 2: Convert raw data to GameStateEvent
    for event_dict in raw_data:
        game_state_event: GameStateGroupGameEvent = GameStateGroupGameEvent(**event_dict)

        session = db.get_session()
        for event in game_state_event.event_data.game_states:
            focused_players = []
            for player in event.players:
                if player.user_id == "83248802-90e1-705c-8702-e6c497b686d4":
                    focused_players.append(player)

            if not focused_players:
                continue

            event.players = focused_players

            event_data_dict = event.model_dump()

            db_model = DBGameState(event_created_at=event.created_at, event_data=json.dumps(event_data_dict))

            session.add(db_model)

        session.commit()


# Entry point for the script
# if __name__ == "__main__":
#     asyncio.run(main(json_path=Path("data/playground.json")))
