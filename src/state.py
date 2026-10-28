from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Callable

VALID_DIRECTIONS = ("up", "down", "left", "right", "none")
VALID_BUTTONS = ("a", "b")

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
    is_capitan: bool = False
    last_input_at: float = 0.0
    input_state: dict = field(
        default_factory=lambda: {
            "direction": "none",
            "buttons": {"a": False, "b": False},
        }
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "color": self.color,
            "shape": self.shape,
            "connected_at": self.connected_at,
            "last_ping_at": self.last_ping_at,
            "is_capitan": self.is_capitan,
            "last_input_at": self.last_input_at,
            "input_state": {
                "direction": self.input_state["direction"],
                "buttons": dict(self.input_state["buttons"]),
            },
        }


class LobbyState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._players: dict[str, Player] = {}
        self._counter = 0
        self._input_listener: Callable[[Player, str, str | None, str | None], None] | None = None

    def _recalculate_capitan_locked(self) -> None:
        if not self._players:
            return
        oldest_id = min(self._players.values(), key=lambda p: p.connected_at).id
        for p in self._players.values():
            p.is_capitan = (p.id == oldest_id)

    def get_capitan_id(self) -> str | None:
        with self._lock:
            for p in self._players.values():
                if p.is_capitan:
                    return p.id
            return None

    def is_capitan(self, player_id: str) -> bool:
        with self._lock:
            player = self._players.get(player_id)
            return bool(player and player.is_capitan)

    def set_input_listener(
        self,
        callback: Callable[[Player, str, str | None, str | None], None] | None,
    ) -> None:
        with self._lock:
            self._input_listener = callback

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
                is_capitan=False,
                last_input_at=now,
                input_state={
                    "direction": "none",
                    "buttons": {"a": False, "b": False},
                },
            )
            self._players[player.id] = player
            self._recalculate_capitan_locked()
            return player

    def remove_player(self, player_id: str) -> None:
        with self._lock:
            self._players.pop(player_id, None)
            self._recalculate_capitan_locked()

    def trigger_ping(self, player_id: str) -> bool:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return False
            player.last_ping_at = time.time()
            return True

    def update_player_input(
        self,
        player_id: str,
        action: str,
        direction: str | None = None,
        button: str | None = None,
    ) -> bool:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return False
            now = time.time()
            updated = False
            if action == "direction_change" and direction in VALID_DIRECTIONS:
                player.input_state["direction"] = direction
                player.last_input_at = now
                updated = True
            elif action == "press" and button in VALID_BUTTONS:
                player.input_state["buttons"][button] = True
                player.last_input_at = now
                updated = True
            elif action == "release" and button in VALID_BUTTONS:
                player.input_state["buttons"][button] = False
                player.last_input_at = now
                updated = True

            if updated and self._input_listener is not None:
                try:
                    self._input_listener(player, action, direction, button)
                except Exception:
                    pass
            return updated

    def get_player_input(self, player_id: str) -> dict | None:
        with self._lock:
            player = self._players.get(player_id)
            if player is None:
                return None
            return {
                "direction": player.input_state["direction"],
                "buttons": dict(player.input_state["buttons"]),
                "last_input_at": player.last_input_at,
            }

    def snapshot(self) -> list[Player]:
        with self._lock:
            return list(self._players.values())
