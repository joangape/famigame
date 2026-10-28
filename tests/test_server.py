import asyncio
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
        role1 = await ws1.receive_json()
        assert role1["type"] == "role_update"
        assert role1["is_capitan"] is True

        # Connect second client with empty name
        ws2 = await client.ws_connect("/ws")
        await ws2.send_json({"type": "join", "name": ""})
        msg2 = await ws2.receive_json()
        assert msg2["type"] == "joined"
        assert msg2["player"]["id"] == "p2"
        assert msg2["player"]["name"] == "Jugador 2"
        role2 = await ws2.receive_json()
        assert role2["type"] == "role_update"
        assert role2["is_capitan"] is False

        role1_update = await ws1.receive_json()
        assert role1_update["type"] == "role_update"
        assert role1_update["is_capitan"] is True

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
        role2_promoted = await ws2.receive_json()
        assert role2_promoted["type"] == "role_update"
        assert role2_promoted["is_capitan"] is True
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


def test_player_input_state_lifecycle_in_lobby():
    state = LobbyState()
    received_signals = []
    state.set_input_listener(lambda player, act, dir_, btn: received_signals.append((player.id, act, dir_, btn)))

    p = state.add_player("GamepadTester")
    assert p.input_state == {
        "direction": "none",
        "buttons": {"a": False, "b": False},
    }
    assert p.last_input_at > 0

    # Direction changes
    assert state.update_player_input(p.id, action="direction_change", direction="up") is True
    assert state.get_player_input(p.id)["direction"] == "up"
    assert received_signals[-1] == ("p1", "direction_change", "up", None)

    assert state.update_player_input(p.id, action="direction_change", direction="right") is True
    assert state.get_player_input(p.id)["direction"] == "right"

    assert state.update_player_input(p.id, action="direction_change", direction="none") is True
    assert state.get_player_input(p.id)["direction"] == "none"

    # Invalid direction rejected
    assert state.update_player_input(p.id, action="direction_change", direction="diagonal_invalid") is False
    assert state.get_player_input(p.id)["direction"] == "none"

    # Buttons press / release
    assert state.update_player_input(p.id, action="press", button="a") is True
    assert state.get_player_input(p.id)["buttons"]["a"] is True
    assert state.get_player_input(p.id)["buttons"]["b"] is False
    assert received_signals[-1] == ("p1", "press", None, "a")

    assert state.update_player_input(p.id, action="press", button="b") is True
    assert state.get_player_input(p.id)["buttons"]["a"] is True
    assert state.get_player_input(p.id)["buttons"]["b"] is True

    assert state.update_player_input(p.id, action="release", button="a") is True
    assert state.get_player_input(p.id)["buttons"]["a"] is False
    assert state.get_player_input(p.id)["buttons"]["b"] is True
    assert received_signals[-1] == ("p1", "release", None, "a")

    # Invalid button rejected
    assert state.update_player_input(p.id, action="press", button="x") is False

    # Unknown player
    assert state.update_player_input("unknown_id", action="press", button="a") is False
    assert state.get_player_input("unknown_id") is None


@pytest.mark.asyncio
async def test_ws_input_events_realtime():
    state = LobbyState()
    app = create_app(state)

    async with TestClient(TestServer(app)) as client:
        ws = await client.ws_connect("/ws")
        await ws.send_json({"type": "join", "name": "Speedy"})
        msg = await ws.receive_json()
        assert msg["type"] == "joined"
        player_id = msg["player"]["id"]

        # Send direction_change
        await ws.send_json({
            "type": "input",
            "action": "direction_change",
            "direction": "left",
        })
        # Allow event loop processing
        await asyncio.sleep(0.02)
        inp = state.get_player_input(player_id)
        assert inp is not None
        assert inp["direction"] == "left"

        # Send simultaneous buttons press (A then B)
        await ws.send_json({"type": "input", "action": "press", "button": "a"})
        await ws.send_json({"type": "input", "action": "press", "button": "b"})
        await asyncio.sleep(0.02)
        inp = state.get_player_input(player_id)
        assert inp["buttons"] == {"a": True, "b": True}

        # Release button B and change direction
        await ws.send_json({"type": "input", "action": "release", "button": "b"})
        await ws.send_json({
            "type": "input",
            "action": "direction_change",
            "direction": "down",
        })
        await asyncio.sleep(0.02)
        inp = state.get_player_input(player_id)
        assert inp["direction"] == "down"
        assert inp["buttons"] == {"a": True, "b": False}

        await ws.close()


@pytest.mark.asyncio
async def test_static_assets_serving_and_gamepad_dom():
    state = LobbyState()
    app = create_app(state)

    async with TestClient(TestServer(app)) as client:
        # GET /
        resp_index = await client.get("/")
        assert resp_index.status == 200
        html = await resp_index.text()
        assert 'id="controller-screen"' in html
        assert 'id="dpad"' in html
        assert 'id="btn-a"' in html
        assert 'id="btn-b"' in html
        assert 'id="ctrl-ping-btn"' in html
        assert 'id="ctrl-disconnect-btn"' in html
        assert 'id="ctrl-capitan-badge"' in html
        assert 'id="ctrl-role-banner"' in html

        # GET /app.js
        resp_js = await client.get("/app.js")
        assert resp_js.status == 200
        js = await resp_js.text()
        assert "direction_change" in js
        assert "calculateDpadDirection" in js
        assert "has-controller-active" in js
        assert "role_update" in js

        # GET /style.css
        resp_css = await client.get("/style.css")
        assert resp_css.status == 200
        css = await resp_css.text()
        assert "gamepad-surface" in css
        assert "action-cluster" in css
        assert "touch-action: none" in css
        assert "ctrl-capitan-badge" in css
        assert "ctrl-role-banner" in css


@pytest.mark.asyncio
async def test_ws_role_updates_and_transfer():
    state = LobbyState()
    app = create_app(state)

    async with TestClient(TestServer(app)) as client:
        # Connect client 1: first player is designated Capitán
        ws1 = await client.ws_connect("/ws")
        await ws1.send_json({"type": "join", "name": "Capitana"})
        msg1 = await ws1.receive_json()
        assert msg1["type"] == "joined"
        assert msg1["player"]["is_capitan"] is True

        role1 = await ws1.receive_json()
        assert role1["type"] == "role_update"
        assert role1["player_id"] == "p1"
        assert role1["is_capitan"] is True
        assert role1["capitan_id"] == "p1"
        assert role1["capitan_name"] == "Capitana"

        # Connect client 2: regular player
        ws2 = await client.ws_connect("/ws")
        await ws2.send_json({"type": "join", "name": "Segunda"})
        msg2 = await ws2.receive_json()
        assert msg2["type"] == "joined"
        assert msg2["player"]["is_capitan"] is False

        # Both receive role_update
        role_for_p1 = await ws1.receive_json()
        assert role_for_p1["type"] == "role_update"
        assert role_for_p1["player_id"] == "p1"
        assert role_for_p1["is_capitan"] is True

        role_for_p2 = await ws2.receive_json()
        assert role_for_p2["type"] == "role_update"
        assert role_for_p2["player_id"] == "p2"
        assert role_for_p2["is_capitan"] is False
        assert role_for_p2["capitan_id"] == "p1"
        assert role_for_p2["capitan_name"] == "Capitana"

        # Close client 1: client 2 receives promotion role_update
        await ws1.close()
        role_transfer = await ws2.receive_json()
        assert role_transfer["type"] == "role_update"
        assert role_transfer["player_id"] == "p2"
        assert role_transfer["is_capitan"] is True
        assert role_transfer["capitan_id"] == "p2"
        assert role_transfer["capitan_name"] == "Segunda"

        await ws2.close()


def test_capitan_assignment_first_player():
    state = LobbyState()
    assert state.get_capitan_id() is None

    p1 = state.add_player("Player 1")
    assert p1.is_capitan is True
    assert p1.to_dict()["is_capitan"] is True
    assert state.get_capitan_id() == "p1"
    assert state.is_capitan("p1") is True

    p2 = state.add_player("Player 2")
    assert p2.is_capitan is False
    assert p2.to_dict()["is_capitan"] is False
    assert state.get_capitan_id() == "p1"
    assert state.is_capitan("p1") is True
    assert state.is_capitan("p2") is False


def test_capitan_transfer_on_disconnect():
    state = LobbyState()
    p1 = state.add_player("P1")
    time.sleep(0.01)
    p2 = state.add_player("P2")
    time.sleep(0.01)
    p3 = state.add_player("P3")

    assert state.get_capitan_id() == "p1"

    # Non-capitan disconnect does not change capitan
    state.remove_player("p3")
    assert state.get_capitan_id() == "p1"
    assert p1.is_capitan is True
    assert p2.is_capitan is False

    # Capitan disconnect transfers to next oldest player (p2)
    state.remove_player("p1")
    assert state.get_capitan_id() == "p2"
    assert p2.is_capitan is True
    assert state.is_capitan("p2") is True
    assert state.is_capitan("p1") is False


def test_capitan_none_when_empty():
    state = LobbyState()
    assert state.get_capitan_id() is None
    assert state.is_capitan("p1") is False

    p1 = state.add_player("Solo")
    assert state.get_capitan_id() == "p1"

    state.remove_player("p1")
    assert state.get_capitan_id() is None
    assert state.is_capitan("p1") is False

