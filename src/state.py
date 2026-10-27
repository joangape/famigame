from __future__ import annotations

from dataclasses import dataclass
import threading
import time

PLAYER_COLORS = [
    "#FF5964",
    "#2EC4B6",
    "#FFCA3A",
    "#38BDF8",
    "#B388EB",
    "#FF9F1C",
    "#6BF178",
    "#FF6B9D",
]
PLAYER_SHAPES = ["circle", "square", "triangle", "star", "diamond", "drop"]


@dataclass
class Player:
    id: str
    number: int
    name: str
    color: str
    shape: str
    connected_at: float
    last_ping_at: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "color": self.color,
            "shape": self.shape,
            "connected_at": self.connected_at,
            "last_ping_at": self.last_ping_at,
        }


class LobbyState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._players: dict[str, Player] = {}
        self._counter = 0

    def add_player(self, name: str = "") -> Player:
        with self._lock:
            self._counter += 1
            n = self._counter
            clean_name = (name or "").strip()[:16] or f"Jugador {n}"
            now = time.time()
            player = Player(
                id=f"p{n}",
                number=n,
                name=clean_name,
                color=PLAYER_COLORS[(n - 1) % len(PLAYER_COLORS)],
                shape=PLAYER_SHAPES[(n - 1) % len(PLAYER_SHAPES)],
                connected_at=now,
                last_ping_at=now,
            )
            self._players[player.id] = player
            return player

    def remove_player(self, player_id: str) -> None:
        with self._lock:
            self._players.pop(player_id, None)

    def trigger_ping(self, player_id: str) -> bool:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return False
            player.last_ping_at = time.time()
            return True

    def snapshot(self) -> list[Player]:
        with self._lock:
            return list(self._players.values())
