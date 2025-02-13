from uuid import uuid4
from pydantic import BaseModel, Field
from typing import List, Optional


class Location(BaseModel):
    x: int = Field(0, alias="x")
    y: int = Field(0, alias="y")
    z: int = Field(0, alias="z")


class Rotation(BaseModel):
    pitch: int = Field(0, alias="pitch")
    yaw: int = Field(0, alias="yaw")
    roll: int = Field(0, alias="roll")


class Weapon(BaseModel):
    name: str = Field("Unknown Weapon", alias="name")
    type: str = Field("Unknown Type", alias="type")


class KillInstigator(BaseModel):
    location: Location = Field(default_factory=Location, alias="location")
    weapon: Weapon = Field(default_factory=Weapon, alias="weapon")


class Victim(BaseModel):
    user_id: Optional[str] = Field(None, alias="user_id")  # Can be empty strings
    character: str = Field("Unknown Character", alias="character")


class Shot(BaseModel):
    kill_instigator: KillInstigator = Field(default_factory=KillInstigator, alias="kill_instigator")
    victim: Victim = Field(default_factory=Victim, alias="victim")


class Ammo(BaseModel):
    name: str = Field("Default Ammo", alias="name")
    amount: int = Field(0, alias="amount")


class Player(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()), alias="user_id")
    character: str = Field("Unknown Character", alias="character")
    location: Location = Field(default_factory=Location, alias="location")
    rotation: Rotation = Field(default_factory=Rotation, alias="rotation")
    hit_points: int = Field(100, alias="hit_points")
    shield: int = Field(0, alias="shield")
    current_state: str = Field("Idle", alias="current_state")
    # Default factory includes a single default Shot
    shot_list: List[Shot] = Field(default_factory=lambda: [Shot()], alias="shot_list")
    # Default factory includes a single default weapon
    weapons: List[str] = Field(default_factory=lambda: ["Default Weapon"], alias="weapons")
    # Default factory includes a single default Ammo
    ammo: List[Ammo] = Field(default_factory=lambda: [Ammo()], alias="ammo")


class GameState(BaseModel):
    game_state_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: int = Field(0, alias="timestamp")
    # Default factory includes a single default Player
    players: List[Player] = Field(default_factory=lambda: [Player()], alias="players")


class GameStateEventData(BaseModel):
    game_id: str = Field(default_factory=lambda: str(uuid4()), alias="game_id")
    # Default factory includes a single default GameState
    game_states: List[GameState] = Field(default_factory=lambda: [GameState()], alias="samples")


class GameStateGroupGameEvent(BaseModel):
    event_identifier: str = Field("Default Event", alias="event_identifier")
    # Default factory includes a single default GameStateEventData
    event_data: GameStateEventData = Field(default_factory=GameStateEventData, alias="event_data")






def main():
    # loads playground.json

    # import json
    # with open('../../data/playground.json', 'r') as f:
    #     data = json.load(f)

    model = GameStateGroupGameEvent()
    print("Succesfully loaded")

if __name__ == "__main__":
    main()