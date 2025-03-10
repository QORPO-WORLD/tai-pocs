import copy
import heapq
import random
from collections import deque
from typing import Generator

from mnemonic.mnemonic import Mnemonic

from application.event_samples import Event, KillEvent


class Player:
    def __init__(self, username, kills=None) -> None:
        self.username = username
        self.current_num_kills = 0
        self.previous_victims: list[str] = []
        self.kills: set[str] = kills or set()


class Game:
    def __init__(self, events_data: list[dict]) -> None:
        self.players: dict[str, Player] = {}
        self._events = events_data
        self.num_players_total = len(self._events) + 1
        self.locations = ("Forest", "Bank", "City", "Desert", "Jungle")

    def start(self) -> None:
        self.events_data = copy.deepcopy(self._events)
        self.num_players_alive = self.num_players_total
        self.leaderboard: list[tuple[int, str]] = []

    def generate_username(self) -> str:
        mnemonic = Mnemonic("english")
        return "".join([word.capitalize() for word in mnemonic.generate().split()[:2]])

    def generate_location(self) -> str:
        return random.choice(self.locations)

    def create_players_tree(self) -> Player:
        players_list = [Player(self.generate_username()) for _ in range(self.num_players_total)]
        self.players = {user.username: user for user in players_list}
        root = players_list.pop()
        q = deque([root])
        while q:
            killer = q.popleft()
            kills_num = min(random.randint(0, 6), len(players_list))
            for _ in range(kills_num):
                victim = players_list.pop()
                killer.kills.add(victim.username)
                q.append(victim)
        return root

    def get_events(self, player: Player) -> Generator[Event, None, None]:
        yield from self._get_next_kill_event(player)  # TODO: event choosing logic

    def _update_leaderboard(self, kill_instigator: Player) -> None:
        for i, (_, username) in enumerate(self.leaderboard):
            if username != kill_instigator.username:
                continue
            self.leaderboard[i] = (kill_instigator.current_num_kills, kill_instigator.username)
            heapq.heapify(self.leaderboard)
            return

        if len(self.leaderboard) > 5:
            heapq.heappop(self.leaderboard)
        kills_required, _ = self.leaderboard[0] if self.leaderboard else (0, "")
        if kill_instigator.current_num_kills < kills_required:
            return
        heapq.heappush(self.leaderboard, (kill_instigator.current_num_kills, kill_instigator.username))

    def _get_next_kill_event(self, player: Player) -> Generator[KillEvent, None, None]:
        if not player:
            return
        for victim_username in player.kills:
            yield from self._get_next_kill_event(self.players[victim_username])
        for victim_username in player.kills:
            yield self._create_kill_event(self.players[victim_username], player)

    def _create_kill_event(self, victim: Player, kill_instigator: Player) -> KillEvent:
        if not self.events_data:
            raise StopIteration
        kill = self.events_data.pop()
        kill_instigator.current_num_kills += 1
        self.num_players_alive -= 1
        self._update_leaderboard(kill_instigator)
        event = {
            "victim": {
                "username": victim.username,
            },
            "KillInstigator": {
                "username": kill_instigator.username,
                "Distance": kill["KillInstigator"]["Distance"],
                "first_kill": bool(kill["KillInstigator"].get("first_kill", False)),
                "used_weapon": {
                    "type": kill["KillInstigator"]["used_weapon"]["type"],
                    "name": kill["KillInstigator"]["used_weapon"]["name"],
                },
                "Headshot": bool(kill["KillInstigator"]["Headshot"]),
                "OneShot": bool(kill["KillInstigator"]["OneShot"]),
                "num_kills": kill_instigator.current_num_kills,
                "previous_victims": kill_instigator.previous_victims,
            },
            "location": self.generate_location(),
            "num_players_alive": self.num_players_alive,
        }
        kill_instigator.previous_victims.append(victim.username)
        return event
