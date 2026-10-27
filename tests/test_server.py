import ipaddress
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aiohttp.test_utils import TestClient, TestServer
import pytest

from src.server import create_app, get_local_ip
from src.state import LobbyState, PLAYER_COLORS, PLAYER_SHAPES


def test_lobby_state_lifecycle():
    state = LobbyState()
    assert state.snapshot() == []

    # Default name on empty / whitespace input
    p1 = state.add_player("   ")
    assert p1.id == "p1"
    assert p1.number == 1
    assert p1.name == "Jugador 1"
    assert p1.color == PLAYER_COLORS[0]
    assert p1.shape == PLAYER_SHAPES[0]

    # Custom name and truncation to 16 chars
    p2 = state.add_player("  SuperLongPlayerName12345  ")
    assert p2.id == "p2"
    assert p2.number == 2
    assert p2.name == "SuperLongPlayerN"
    assert len(p2.name) == 16
    assert p2.color == PLAYER_COLORS[1]
    assert p2.shape == PLAYER_SHAPES[1]

    # Snapshot order
    snap = state.snapshot()
    assert [p.id for p in snap] == ["p1", "p2"]

    # Ping updates timestamp
    old_ping = p1.last_ping_at
    time.sleep(0.01)
    assert state.trigger_ping("p1") is True
    assert p1.last_ping_at > old_ping
    assert state.trigger_ping("unknown") is False

    # Remove player
    state.remove_player("p1")
    assert [p.id for p in state.snapshot()] == ["p2"]
    state.remove_player("nonexistent")
    assert [p.id for p in state.snapshot()] == ["p2"]


def test_lobby_state_color_and_shape_rotation():
    state = LobbyState()
    players = [state.add_player(f"P{i}") for i in range(10)]
    for idx, p in enumerate(players):
        assert p.color == PLAYER_COLORS[idx % len(PLAYER_COLORS)]
        assert p.shape == PLAYER_SHAPES[idx % len(PLAYER_SHAPES)]


def test_get_local_ip_returns_valid_ipv4():
    ip = get_local_ip()
    parsed = ipaddress.ip_address(ip)
    assert parsed.version == 4


def test_get_local_ip_ignores_utun_vpn_interfaces(monkeypatch):
    sample_ifconfig = """\
lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384
\tinet 127.0.0.1 netmask 0xff000000
utun4: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST> mtu 1420
\tinet 10.5.0.2 --> 10.5.0.2 netmask 0xffff0000
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
\tinet 192.168.178.137 netmask 0xffffff00 broadcast 192.168.178.255
"""
    monkeypatch.setattr(
        "src.server.subprocess.check_output",
        lambda *args, **kwargs: sample_ifconfig,
    )
    assert get_local_ip() == "192.168.178.137"


@pytest.mark.asyncio
async def test_ws_join_ping_and_disconnect_cleanup():
    state = LobbyState()
    app = create_app(state)

    async with TestClient(TestServer(app)) as client:
        # Initial HTTP state check
        resp = await client.get("/api/state")
        assert resp.status == 200
        data = await resp.json()
        assert data == {"players": []}

        # Connect first client with custom name
        ws1 = await client.ws_connect("/ws")
        await ws1.send_json({"type": "join", "name": "Alicia"})
        msg1 = await ws1.receive_json()
        assert msg1["type"] == "joined"
        assert msg1["player"]["id"] == "p1"
        assert msg1["player"]["name"] == "Alicia"

        # Connect second client with empty name
        ws2 = await client.ws_connect("/ws")
        await ws2.send_json({"type": "join", "name": ""})
        msg2 = await ws2.receive_json()
        assert msg2["type"] == "joined"
        assert msg2["player"]["id"] == "p2"
        assert msg2["player"]["name"] == "Jugador 2"

        assert len(state.snapshot()) == 2

        # Send ping from ws1
        before_ping = state.snapshot()[0].last_ping_at
        time.sleep(0.01)
        await ws1.send_json({"type": "ping"})
        pong = await ws1.receive_json()
        assert pong == {"type": "pong", "player_id": "p1"}
        assert state.snapshot()[0].last_ping_at > before_ping

        # Close ws1 and verify removal
        await ws1.close()
        # Allow server loop a brief moment to run finally block
        for _ in range(20):
            if len(state.snapshot()) == 1:
                break
            await client.get("/api/state")
        assert [p.id for p in state.snapshot()] == ["p2"]

        # Close ws2 and verify empty lobby
        await ws2.close()
        for _ in range(20):
            if len(state.snapshot()) == 0:
                break
            await client.get("/api/state")
        assert state.snapshot() == []
