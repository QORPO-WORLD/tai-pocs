import json
import asyncio
from pathlib import Path
from application.dtos.game_state_event import GameStateGroupGameEvent, GameStateEventData, GameState
from application.db_models import GameState as DBGameState, DatabaseConnection



async def run_preprocess(json_path):
    # Step 1: Load playground.json
    print("i am here")
    if not json_path.exists():
        print("playground.json file not found!")
        return

    with open(json_path, "r") as file:
        raw_data = json.load(file)

    # Step 2: Convert raw data to GameStateEvent

    game_state_event: GameStateGroupGameEvent = GameStateGroupGameEvent(**raw_data)


    db = DatabaseConnection()
    session = db.get_session()
    for event in game_state_event.event_data.game_states:
        event: GameState
        event_data_dict = event.model_dump()

        db_model = DBGameState(
            event_created_at=event.created_at,
            event_data=json.dumps(event_data_dict)
        )

        session.add(db_model)

    session.commit()

# Entry point for the script
# if __name__ == "__main__":
#     asyncio.run(main(json_path=Path("data/playground.json")))
