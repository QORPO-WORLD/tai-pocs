from pydantic import BaseModel, Field
from typing import List

from pydantic import BaseModel, Field
from typing import List, Optional


class Location(BaseModel):
    x: int = Field(..., alias="x")
    y: int = Field(..., alias="y")
    z: int = Field(..., alias="z")


class Rotation(BaseModel):
    pitch: int = Field(..., alias="pitch")
    yaw: int = Field(..., alias="yaw")
    roll: int = Field(..., alias="roll")


class Weapon(BaseModel):
    name: str = Field(..., alias="name")
    type: str = Field(..., alias="type")


class KillInstigator(BaseModel):
    location: Location = Field(..., alias="location")
    weapon: Weapon = Field(..., alias="weapon")


class Victim(BaseModel):
    user_id: Optional[str] = Field(None, alias="user_id")  # Can be empty strings
    character: str = Field(..., alias="character")


class Shot(BaseModel):
    kill_instigator: KillInstigator = Field(..., alias="kill_instigator")
    victim: Victim = Field(..., alias="victim")


class Ammo(BaseModel):
    name: str = Field(..., alias="name")
    amount: int = Field(..., alias="amount")


class Player(BaseModel):
    user_id: str = Field(..., alias="user_id")
    character: str = Field(..., alias="character")
    location: Location = Field(..., alias="location")
    rotation: Rotation = Field(..., alias="rotation")
    hit_points: int = Field(..., alias="hit_points")
    shield: int = Field(..., alias="shield")
    current_state: str = Field(..., alias="current_state")
    shot_list: List[Shot] = Field(..., alias="shot_list")
    weapons: List[str] = Field(..., alias="weapons")
    ammo: List[Ammo] = Field(..., alias="ammo")


class GameState(BaseModel):
    timestamp: int = Field(..., alias="timestamp")
    players: List[Player] = Field(..., alias="players")


class GameStateEventData(BaseModel):
    events: List[GameState] = Field(..., alias="samples")


class GameStateGroupGameEvent(BaseModel):
    event_identifier: str = Field(..., alias="event_identifier")
    event_data: GameStateEventData = Field(..., alias="event_data")




def main():
    # loads playground.json

    import json
    with open('../../data/playground.json', 'r') as f:
        data = json.load(f)

    model = GameStateGroupGameEvent(**data)
    print(f"Succesfully loaded {len(model.samples)} samples")


if __name__ == "__main__":
    main()