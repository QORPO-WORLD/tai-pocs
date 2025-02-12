from __future__ import annotations
import copy
import heapq
import random
from collections import deque
from typing import Generator
from typing import List

from mnemonic.mnemonic import Mnemonic

from application.dataclasses.game_state_event import KillInstigator, Player, Playground, Sample, Location, Weapon, \
    Victim, Shot, Ammo


# Updated Game class
class Game:
    def __init__(self, events_data: List[dict]) -> None:
        self.players: dict[str, Player] = {}
        self._events = events_data
        self.num_players_total = len(self._events) + 1
        self.locations = [Location(x=random.randint(0, 100), y=random.randint(0, 100), z=random.randint(0, 100))]

    def start(self) -> None:
        self.events_data = copy.deepcopy(self._events)
        self.num_players_alive = self.num_players_total
        self.leaderboard: list[tuple[int, str]] = []

    def generate_username(self) -> str:
        # Placeholder for random username generation
        return f"Player_{random.randint(1000, 9999)}"

    def generate_location(self) -> Location:
        return random.choice(self.locations)

    def create_players_tree(self) -> Player:
        players_list = [self._create_random_player() for _ in range(self.num_players_total)]
        self.players = {player.user_id: player for player in players_list}
        root = players_list.pop()
        q = deque([root])
        while q:
            killer = q.popleft()
            kills_num = min(random.randint(0, 6), len(players_list))
            for _ in range(kills_num):
                victim = players_list.pop()
                # Simulate shots
                shot = self._create_random_shot(killer, victim)
                killer.shot_list.append(shot)
                q.append(victim)
        return root

    def _create_random_player(self) -> Player:
        return Player(
            user_id=self.generate_username(),
            character="RandomCharacter",
            location=self.generate_location(),
            rotation=random.uniform(0, 360),
            hit_points=100,
            shield=50,
            current_state="alive",
            shot_list=[],
            weapons=["Pistol", "Rifle"],
            ammo=[Ammo(name="Pistol Ammo", amount=50), Ammo(name="Rifle Ammo", amount=30)],
        )

    def _create_random_shot(self, instigator: Player, victim: Player) -> Shot:
        return Shot(
            kill_instigator=KillInstigator(
                location=instigator.location,
                weapon=Weapon(name="Pistol", type="Handgun"),
            ),
            victim=Victim(
                user_id=victim.user_id,
                character=victim.character,
            ),
        )

    def get_events(self, player: Player) -> Generator[Shot, None, None]:
        yield from self._get_next_kill_event(player)

    def _get_next_kill_event(self, player: Player) -> Generator[Shot, None, None]:
        if not player:
            return
        for shot in player.shot_list:
            yield shot
