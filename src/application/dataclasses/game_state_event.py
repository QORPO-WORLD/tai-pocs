from pydantic import BaseModel, Field
from typing import List, Optional

class Location(BaseModel):
    x: int
    y: int
    z: int

class Weapon(BaseModel):
    name: str
    type: str

class KillInstigator(BaseModel):
    location: Location
    weapon: Weapon

class Victim(BaseModel):
    user_id: str
    character: str

class Shot(BaseModel):
    kill_instigator: KillInstigator
    victim: Victim

class Ammo(BaseModel):
    name: str
    amount: int

class Player(BaseModel):
    user_id: str
    character: str
    location: Location
    rotation: float
    hit_points: int
    shield: int
    current_state: str
    shot_list: List[Shot]
    weapons: List[str]
    ammo: List[Ammo]

class Sample(BaseModel):
    timestamp: int
    players: List[Player]

class Playground(BaseModel):
    samples: List[Sample]


def main():
    # loads playground.json

    import json
    with open('../../data/playground.json', 'r') as f:
        data = json.load(f)

    model = Playground(**data)
    print(f"Succesfully loaded {len(model.samples)} samples")


if __name__ == "__main__":
    main()