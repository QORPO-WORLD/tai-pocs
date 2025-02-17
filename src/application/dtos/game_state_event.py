from uuid import uuid4
from wsgiref.validate import validator
from application.bin.account_service.account_countainer import AccountContainer

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional


class Location(BaseModel):
    x: float = Field(..., alias="x")
    y: float = Field(..., alias="y")
    z: float = Field(..., alias="z")

    @classmethod
    def sample(cls):
        return cls(x=100, y=200, z=300)


class Rotation(BaseModel):
    pitch: float = Field(..., alias="pitch")
    yaw: float = Field(..., alias="yaw")
    roll: float = Field(..., alias="roll")

    @classmethod
    def sample(cls):
        return cls(pitch=45, yaw=90, roll=180)


class Weapon(BaseModel):
    name: str = Field(..., alias="name")
    type: str = Field(..., alias="type")

    @classmethod
    def sample(cls):
        return cls(name="Sample Weapon", type="Ranged")


class KillInstigator(BaseModel):
    location: Location = Field(..., alias="location")
    weapon: Weapon = Field(..., alias="weapon")

    @classmethod
    def sample(cls):
        return cls(location=Location.sample(), weapon=Weapon.sample())


class Victim(BaseModel):
    user_id: Optional[str] = Field(None, alias="user_id")  # Can be empty strings
    character: str = Field(..., alias="character")

    @classmethod
    def sample(cls):
        return cls(user_id="victim_123", character="Sample Victim")


class Shot(BaseModel):
    kill_instigator: KillInstigator = Field(..., alias="kill_instigator")
    victim: Victim = Field(..., alias="victim")

    @classmethod
    def sample(cls):
        return cls(kill_instigator=KillInstigator.sample(), victim=Victim.sample())


class Ammo(BaseModel):
    name: str = Field(..., alias="name")
    amount: int = Field(..., alias="amount")

    @classmethod
    def sample(cls):
        return cls(name="Sample Ammo", amount=30)


class Player(BaseModel):
    user_id: str = Field(..., alias="user_id")
    user_nickname: str = Field(default="Unknown")
    character: str = Field(..., alias="character")
    location: Location = Field(..., alias="location")
    rotation: Rotation = Field(..., alias="rotation")
    hit_points: int = Field(..., alias="hit_points")
    shield: int = Field(..., alias="shield")
    current_state: List[str] = Field(..., alias="current_states")
    shot_list: List[Shot] = Field(..., alias="shot_list")
    weapons: List[str] = Field(..., alias="weapons")
    ammo: List[Ammo] = Field(..., alias="ammo")

    @classmethod
    @field_validator("user_nickname", mode="after")
    def user_nickname_validator(cls, value):
        return user_nickname_mapper(value)

    @model_validator(mode="after")
    @classmethod
    def model_after_validator(cls, obj):
        nickname = user_nickname_mapper(obj.user_id)
        obj.user_nickname = nickname
        return obj



    @classmethod
    def sample(cls):
        return cls(
            user_id=str(uuid4()),
            character="Sample Character",
            location=Location.sample(),
            rotation=Rotation.sample(),
            hit_points=100,
            shield=50,
            current_states=["alive"],
            shot_list=[Shot.sample()],
            weapons=["Sample Weapon"],
            ammo=[Ammo.sample()],
        )


class GameState(BaseModel):
    game_state_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: float = Field(..., alias="timestamp")
    players: List[Player] = Field(..., alias="players")

    @classmethod
    def sample(cls):
        return cls(
            game_state_id=str(uuid4()),
            timestamp=1672531200,  # Example timestamp
            players=[Player.sample()],
        )


class GameStateEventData(BaseModel):
    game_id: str = Field(default_factory=lambda: str(uuid4()), alias="game_id")
    game_states: List[GameState] = Field(..., alias="samples")

    @classmethod
    def sample(cls):
        return cls(
            game_id=str(uuid4()),
            samples=[GameState.sample()],
        )


class GameStateGroupGameEvent(BaseModel):
    event_identifier: str = Field(..., alias="event_identifier")
    event_data: GameStateEventData = Field(..., alias="event_data")

    @classmethod
    def sample(cls):
        return cls(
            event_identifier="Sample Event",
            event_data=GameStateEventData.sample(),
        )


def user_nickname_mapper(user_id: str):
    if user_id == "":
        return "AI Player"
    else:
        return AccountContainer().get_nick(user_id, default="Unknown")


def main():
    # loads playground.json

    import json
    with open('../../data/playground.json', 'r') as f:
        data = json.load(f)

    model = GameStateGroupGameEvent(**data)
    print("Succesfully loaded")


if __name__ == "__main__":
    main()
