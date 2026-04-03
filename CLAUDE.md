# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Jeu musical multijoueur en ligne inspiré de Hitster. Les joueurs rejoignent via un code, écoutent des extraits Spotify, et répondent à des questions (QCM ou texte) sur les morceaux. Le projet est en français.

## Stack

- **Backend** : Python / FastAPI + WebSockets — `backend/`
- **Frontend** : Vue.js 3 (Composition API) + Vite — `frontend/`
- **Musique** : API Spotify (Client Credentials) + Web Playback SDK (fallback preview 30s)
- **Stockage** : En mémoire uniquement (pas de DB)

## Commands

```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend (proxy vers backend sur :8000)
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build
```

## Architecture

- `backend/main.py` — FastAPI app, routes REST (`/api/game`), WebSocket (`/ws/{code}/{name}`)
- `backend/game.py` — `GameManager` (crée/supprime les parties), `Game` (logique : lobby, rounds, scoring, broadcast WS)
- `backend/spotify.py` — `SpotifyClient` (auth Client Credentials, fetch playlist tracks, search)
- `backend/questions.py` — Génération auto de questions depuis les métadonnées Spotify (artiste, titre, année, album)
- `backend/models.py` — Modèles Pydantic (Player, Track, Question, GameConfig, WSMessage)
- `frontend/src/composables/useWebSocket.js` — Connexion WS, handlers par type de message
- `frontend/src/composables/useSpotify.js` — Lecture audio (preview URL via `<audio>`)
- `frontend/src/views/` — HomeView (créer/rejoindre), LobbyView (attente + config), GameView (jeu), ScoreView (résultats)

## WebSocket Protocol

Messages JSON `{ type, data }`. Types serveur→client : `player_joined`, `player_left`, `game_started`, `new_round`, `round_result`, `game_over`, `config_updated`. Types client→serveur : `start_game`, `submit_answer`, `update_config`.

## Environment

Requires `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `backend/.env` (see `.env.example`).
