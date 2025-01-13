from typing import TypedDict


class Weapon(TypedDict):
    name: str
    type: str


class KillInstigator(TypedDict):
    username: str
    Distance: int
    first_kill: bool
    used_weapon: Weapon
    Headshot: bool
    OneShot: bool
    previous_victims: list[str]
    num_kills: int


class KillEvent(TypedDict):
    victim: dict[str, str]
    KillInstigator: KillInstigator
    location: str

