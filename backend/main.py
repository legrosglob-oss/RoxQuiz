from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from game import GameManager
from models import GameConfig
from spotify import SpotifyClient, THEMES

load_dotenv()

REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/api/spotify/callback")

spotify = SpotifyClient()
manager = GameManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await spotify.close()


app = FastAPI(title="Hitster", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST endpoints ---


@app.post("/api/game")
async def create_game():
    game = manager.create_game()
    return {"code": game.code, "config": game.config.model_dump()}


@app.get("/api/themes")
async def get_themes():
    return [{"key": k, "label": v["label"]} for k, v in THEMES.items()]


@app.get("/api/game/{code}")
async def get_game(code: str):
    game = manager.get_game(code)
    if not game:
        return {"error": "Partie introuvable"}, 404
    return {
        "code": game.code,
        "state": game.state,
        "players": game.players_info(),
        "config": game.config.model_dump(),
    }


# --- Spotify OAuth ---


@app.get("/api/spotify/login")
async def spotify_login(game_code: str = ""):
    """Redirige l'hôte vers Spotify pour s'authentifier."""
    url = spotify.get_auth_url(REDIRECT_URI, state=game_code)
    return RedirectResponse(url)


@app.get("/api/spotify/callback")
async def spotify_callback(code: str = "", state: str = "", error: str = ""):
    """Callback OAuth — échange le code contre un token."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    if error:
        return RedirectResponse(f"{frontend_url}/?error={error}")
    tokens = await spotify.exchange_code(code, REDIRECT_URI)
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token", "")
    return RedirectResponse(
        f"{frontend_url}/callback#access_token={access_token}&refresh_token={refresh_token}&game_code={state}"
    )


@app.post("/api/spotify/refresh")
async def spotify_refresh(body: dict):
    """Rafraîchit le token utilisateur."""
    refresh_token = body.get("refresh_token", "")
    if not refresh_token:
        return {"error": "missing refresh_token"}, 400
    tokens = await spotify.refresh_user_token(refresh_token)
    return {"access_token": tokens["access_token"]}


# --- WebSocket ---


@app.websocket("/ws/{game_code}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, game_code: str, player_name: str):
    game = manager.get_game(game_code)
    if not game:
        await websocket.close(code=4004, reason="Partie introuvable")
        return

    await websocket.accept()

    existing = game.players.get(player_name)
    if existing:
        game.connections[player_name] = websocket
        await websocket.send_json({"type": "reconnected", "data": {
            "state": game.state,
            "players": game.players_info(),
        }})
    else:
        is_host = len(game.players) == 0
        game.add_player(player_name, is_host=is_host)
        game.connections[player_name] = websocket
        await game.broadcast("player_joined", {
            "player": player_name,
            "is_host": is_host,
            "players": game.players_info(),
        })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "start_game":
                if player_name == game.get_host():
                    asyncio.create_task(game.start(spotify))

            elif msg_type == "submit_answer":
                answer = data.get("data", {}).get("answer", "")
                game.submit_answer(player_name, answer)

            elif msg_type == "update_config":
                if player_name == game.get_host():
                    new_config = data.get("data", {})
                    for key, value in new_config.items():
                        if hasattr(game.config, key):
                            setattr(game.config, key, value)
                    await game.broadcast("config_updated", {
                        "config": game.config.model_dump(),
                    })

            elif msg_type == "set_spotify_token":
                token = data.get("data", {}).get("access_token", "")
                device_id = data.get("data", {}).get("device_id", "")
                print(f"[WS] set_spotify_token from {player_name}, host={game.get_host()}, device_id={device_id!r}, token={'yes' if token else 'no'}")
                if player_name == game.get_host() and token:
                    game.spotify_user_token = token
                    game.spotify_device_id = device_id
                    print(f"[Game] Spotify device set: {device_id}")

    except WebSocketDisconnect:
        game.remove_player(player_name)
        await game.broadcast("player_left", {
            "player": player_name,
            "players": game.players_info(),
        })
        if not game.players:
            manager.remove_game(game_code)


# --- Servir le frontend buildé en production ---

_backend_dir = Path(__file__).resolve().parent
FRONTEND_DIST = _backend_dir / "static"  # copié par le build
if not FRONTEND_DIST.is_dir():
    FRONTEND_DIST = _backend_dir.parent / "frontend" / "dist"  # dev local

print(f"[Hitster] Frontend dist: {FRONTEND_DIST} (exists={FRONTEND_DIST.is_dir()})")

if FRONTEND_DIST.is_dir():
    # Fichiers statiques (JS, CSS, images)
    if (FRONTEND_DIST / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # Toutes les autres routes → index.html (SPA routing Vue.js)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = FRONTEND_DIST / full_path
        if full_path and file.is_file():
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
