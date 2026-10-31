from __future__ import annotations

import asyncio
import json
from pathlib import Path
import re
import socket
import subprocess
import threading

import aiohttp
from aiohttp import WSMsgType, web

from src.state import LobbyState, Player

_IGNORED_IFACE_PREFIXES = (
    "lo",
    "utun",
    "tun",
    "tap",
    "wg",
    "ppp",
    "docker",
    "br",
    "veth",
    "vmnet",
    "vboxnet",
    "awdl",
    "llw",
)
_PREFERRED_IFACE_PREFIXES = ("en", "wlan", "eth", "wl")


def _extract_lan_candidates_from_ifconfig(output: str) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    current_iface = ""
    for line in output.splitlines():
        if line and not line[0].isspace() and ":" in line:
            # Handle both macOS `en0: flags=...` and `ip -4 -o addr` `2: eth0    inet ...`
            parts = line.split(":", 2)
            first = parts[0].strip()
            if first.isdigit() and len(parts) >= 2:
                rest = parts[1].strip().split()
                current_iface = rest[0] if rest else ""
            else:
                current_iface = first
        if not current_iface or current_iface.startswith(_IGNORED_IFACE_PREFIXES):
            continue
        if "-->" in line or " peer " in line:
            continue
        match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)", line)
        if match:
            ip = match.group(1)
            if not ip.startswith(("127.", "169.254.")):
                candidates.append((current_iface, ip))
    return candidates


def get_local_ip() -> str:
    for cmd in (["ifconfig"], ["ip", "-4", "-o", "addr"]):
        try:
            out = subprocess.check_output(
                cmd, stderr=subprocess.DEVNULL, timeout=1.0, text=True, errors="ignore"
            )
            candidates = _extract_lan_candidates_from_ifconfig(out)
            if candidates:
                candidates.sort(
                    key=lambda item: (
                        0 if item[0].startswith(_PREFERRED_IFACE_PREFIXES) else 1,
                        0 if item[1].startswith("192.168.") else 1,
                        item[0],
                    )
                )
                return candidates[0][1]
        except (OSError, subprocess.SubprocessError):
            continue

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.5)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            return ip if ip and not ip.startswith("127.") else "127.0.0.1"
    except OSError:
        return "127.0.0.1"


def create_app(state: LobbyState, web_dir: Path | None = None) -> web.Application:
    resolved_web_dir = (web_dir or (Path(__file__).resolve().parent / "web")).resolve()
    app = web.Application()

    def _serve_web_file(filename: str) -> web.StreamResponse:
        target = (resolved_web_dir / filename).resolve()
        if resolved_web_dir not in target.parents or not target.is_file():
            raise web.HTTPNotFound()
        response = web.FileResponse(target)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    async def handle_index(_request: web.Request) -> web.StreamResponse:
        index_file = resolved_web_dir / "index.html"
        if index_file.is_file():
            response = web.FileResponse(index_file)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        return web.Response(
            text="<!doctype html><html><body><h1>Famigame Lobby</h1></body></html>",
            content_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    async def handle_static(request: web.Request) -> web.StreamResponse:
        filename = request.match_info.get("filename", "")
        return _serve_web_file(filename)

    async def handle_root_asset(request: web.Request) -> web.StreamResponse:
        filename = request.path.lstrip("/")
        return _serve_web_file(filename)

    async def handle_state(_request: web.Request) -> web.Response:
        return web.json_response({"players": [p.to_dict() for p in state.snapshot()]})

    active_connections: dict[web.WebSocketResponse, Player] = {}

    async def broadcast_roles() -> None:
        cap_id = state.get_capitan_id()
        cap_name = ""
        for p in state.snapshot():
            if p.id == cap_id:
                cap_name = p.name
                break
        for ws_conn, player in list(active_connections.items()):
            if not ws_conn.closed:
                is_cap = (player.id == cap_id)
                player.is_capitan = is_cap
                try:
                    await ws_conn.send_json({
                        "type": "role_update",
                        "player_id": player.id,
                        "is_capitan": is_cap,
                        "capitan_id": cap_id,
                        "capitan_name": cap_name,
                    })
                except Exception:
                    pass

    async def handle_ws(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=15.0)
        await ws.prepare(request)
        current_player: Player | None = None

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        msg_data = json.loads(msg.data)
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(msg_data, dict):
                        continue

                    msg_type = msg_data.get("type")
                    if msg_type == "join":
                        if current_player is None:
                            raw_name = msg_data.get("name", "")
                            current_player = state.add_player(
                                raw_name if isinstance(raw_name, str) else ""
                            )
                            active_connections[ws] = current_player
                        await ws.send_json(
                            {"type": "joined", "player": current_player.to_dict()}
                        )
                        await broadcast_roles()
                    elif msg_type == "ping" and current_player is not None:
                        state.trigger_ping(current_player.id)
                        await ws.send_json(
                            {"type": "pong", "player_id": current_player.id}
                        )
                    elif msg_type == "toggle_fullscreen" and current_player is not None:
                        if state.trigger_fullscreen_toggle(current_player.id):
                            await ws.send_json(
                                {"type": "fullscreen_toggled", "status": "ok"}
                            )
                        else:
                            await ws.send_json(
                                {
                                    "type": "error",
                                    "message": "Solo el Capitán puede alternar pantalla completa",
                                }
                            )
                    elif msg_type == "input" and current_player is not None:
                        action = msg_data.get("action")
                        direction = msg_data.get("direction")
                        button = msg_data.get("button")
                        if isinstance(action, str):
                            state.update_player_input(
                                current_player.id,
                                action=action,
                                direction=direction if isinstance(direction, str) else None,
                                button=button if isinstance(button, str) else None,
                            )
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        finally:
            active_connections.pop(ws, None)
            if current_player is not None:
                state.remove_player(current_player.id)
                await broadcast_roles()

        return ws

    app.router.add_get("/", handle_index)
    app.router.add_get("/api/state", handle_state)
    app.router.add_get("/ws", handle_ws)
    app.router.add_get("/style.css", handle_root_asset)
    app.router.add_get("/app.js", handle_root_asset)
    app.router.add_get("/static/{filename:.+}", handle_static)
    return app


def start_background_server(
    state: LobbyState, host: str = "0.0.0.0", port: int = 8080
) -> tuple[threading.Thread, asyncio.AbstractEventLoop]:
    ready_event = threading.Event()
    loop = asyncio.new_event_loop()
    startup_error: list[BaseException] = []

    async def _serve() -> None:
        app = create_app(state)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()

    def _thread_main() -> None:
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_serve())
        except BaseException as exc:
            startup_error.append(exc)
            ready_event.set()
            return
        ready_event.set()
        loop.run_forever()

    thread = threading.Thread(target=_thread_main, name="famigame-http", daemon=True)
    thread.start()
    ready_event.wait(timeout=5.0)
    if startup_error:
        raise startup_error[0]
    return thread, loop
