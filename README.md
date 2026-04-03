# RoxQuiz

Multiplayer online music quiz game inspired by Hitster. Players join a room via a code, listen to Spotify tracks, and answer questions (multiple choice or free text) about the songs — artist, title, year, or album.

## Stack

- **Backend**: Python / FastAPI + WebSockets
- **Frontend**: Vue.js 3 (Composition API) + Vite
- **Music**: Spotify API (Client Credentials) + Web Playback SDK
- **Storage**: In-memory only (no database)

## Prerequisites

- Python 3.11+
- Node.js 20+
- A Spotify Developer application ([developer.spotify.com](https://developer.spotify.com))

## Local Development

### 1. Configure Spotify credentials

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your Spotify app credentials:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/api/spotify/callback
```

In the Spotify Developer Dashboard, add `http://127.0.0.1:8000/api/spotify/callback` as a Redirect URI.

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs on `http://localhost:8000`.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` and `/ws` requests to the backend.

### 4. Play

Open `http://localhost:5173` in your browser, create a game, and share the code with other players.

## Deployment (Render)

RoxQuiz can be deployed as a single service on [Render](https://render.com) (free tier available). The backend serves both the API and the built frontend.

### 1. Push to GitHub

Make sure your code is pushed to a GitHub repository.

### 2. Create a Web Service on Render

- Connect your GitHub repo
- **Runtime**: Python
- **Build Command**:
  ```
  cd frontend && npm ci && npm run build && cp -r dist ../backend/static && cd ../backend && pip install -r requirements.txt
  ```
- **Start Command**:
  ```
  cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### 3. Environment variables

Set these in the Render dashboard:

| Variable | Value |
|---|---|
| `PYTHON_VERSION` | `3.11.6` |
| `NODE_VERSION` | `20.11.0` |
| `SPOTIFY_CLIENT_ID` | Your Spotify Client ID |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify Client Secret |
| `SPOTIFY_REDIRECT_URI` | `https://your-app.onrender.com/api/spotify/callback` |
| `FRONTEND_URL` | `https://your-app.onrender.com` |

### 4. Update Spotify Dashboard

Add your Render URL as a Redirect URI in the Spotify Developer Dashboard:
```
https://your-app.onrender.com/api/spotify/callback
```

### 5. Deploy

Render will build and deploy automatically on every push to `main`.

## How It Works

1. The host creates a game and gets a room code
2. Other players join using the code
3. The host connects their Spotify account and selects a theme
4. Each round: a track plays on the host's device, and all players answer a question
5. Points are awarded for correct answers; the round ends early when all players have answered
6. Final scores are displayed at the end

## License

MIT
