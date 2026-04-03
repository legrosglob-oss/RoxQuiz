from __future__ import annotations

import os
import random
import time
import urllib.parse

import httpx

from models import Track

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API = "https://api.spotify.com/v1"

SCOPES = "streaming user-read-email user-read-private user-modify-playback-state user-read-playback-state"

DEFAULT_QUERIES = [
    "top hits france",
    "top hits 2010",
    "classic rock hits",
    "pop hits 2023",
    "best of 1980s",
    "rap francais",
    "best of 1990s",
    "dance hits 2000",
    "disco classics",
    "rnb hits",
    "indie pop 2020",
    "electro french",
]

THEMES: dict[str, dict] = {
    "pop_international": {
        "label": "Pop internationale",
        "queries": ["pop hits 2020", "pop hits 2010", "pop hits 2000", "top pop songs", "best pop anthems"],
        "artist_pool": [
            "Ed Sheeran", "Taylor Swift", "Adele", "Bruno Mars", "Dua Lipa",
            "The Weeknd", "Beyoncé", "Justin Bieber", "Rihanna", "Katy Perry",
            "Lady Gaga", "Ariana Grande", "Billie Eilish", "Harry Styles",
            "Coldplay", "Maroon 5", "Sia", "Sam Smith", "Shawn Mendes",
            "Post Malone", "Olivia Rodrigo", "Miley Cyrus", "Pink",
        ],
    },
    "pop_fr": {
        "label": "Pop française",
        "queries": ["pop francaise", "chanson francaise hits", "variete francaise", "pop fr 2020"],
        "artist_pool": [
            "Stromae", "Angèle", "Vianney", "Clara Luciani", "Julien Doré",
            "Louane", "Amir", "Kendji Girac", "Indila", "Zaz",
            "Christophe Maé", "Patrick Bruel", "Jean-Jacques Goldman", "Francis Cabrel",
            "Renaud", "Céline Dion", "Johnny Hallyday", "Edith Piaf",
            "Charles Aznavour", "Jacques Brel", "Serge Gainsbourg", "France Gall",
            "Mylène Farmer", "Vanessa Paradis", "MC Solaar", "Pomme",
            "Hoshi", "Grand Corps Malade", "Soprano", "Slimane",
        ],
    },
    "rock_classique": {
        "label": "Rock classique",
        "queries": ["classic rock hits", "rock anthems 70s", "rock legends 80s", "best rock songs"],
        "artist_pool": [
            "Queen", "Led Zeppelin", "The Rolling Stones", "Pink Floyd", "AC/DC",
            "The Beatles", "Nirvana", "Guns N' Roses", "Deep Purple", "The Who",
            "Aerosmith", "Eagles", "Bon Jovi", "U2", "Dire Straits",
            "Fleetwood Mac", "The Doors", "Jimi Hendrix", "David Bowie",
            "Bruce Springsteen", "Eric Clapton", "Black Sabbath", "Metallica",
        ],
    },
    "rap_fr": {
        "label": "Rap français",
        "queries": ["rap francais", "rap fr classique", "rap fr 2020", "hip hop francais"],
        "artist_pool": [
            "Nekfeu", "Orelsan", "PNL", "Booba", "Jul",
            "Ninho", "Damso", "Stromae", "MC Solaar", "IAM",
            "NTM", "Oxmo Puccino", "Kery James", "Soprano", "Bigflo & Oli",
            "Lomepal", "Vald", "SCH", "Gazo", "Niska",
            "Aya Nakamura", "Rohff", "La Fouine", "Sniper", "Sexion d'Assaut",
            "Maître Gims", "Black M", "Dadju", "Tayc", "Rim'K",
        ],
    },
    "rap_us": {
        "label": "Rap US",
        "queries": ["hip hop hits", "rap hits 2020", "best rap songs", "rap classics 90s"],
        "artist_pool": [
            "Drake", "Kendrick Lamar", "Eminem", "Jay-Z", "Kanye West",
            "Travis Scott", "J. Cole", "Lil Wayne", "Nicki Minaj", "Cardi B",
            "Post Malone", "21 Savage", "Future", "Megan Thee Stallion",
            "2Pac", "The Notorious B.I.G.", "Nas", "Snoop Dogg", "50 Cent",
            "A$AP Rocky", "Tyler, The Creator", "Childish Gambino", "Lil Nas X",
            "Doja Cat", "Ice Cube", "Dr. Dre", "Missy Elliott",
        ],
    },
    "electro": {
        "label": "Électro / Dance",
        "queries": ["electro hits", "dance hits 2010", "edm best songs", "french electro", "house classics"],
        "artist_pool": [
            "Daft Punk", "David Guetta", "Martin Garrix", "Avicii", "Calvin Harris",
            "Tiësto", "Marshmello", "Kygo", "Disclosure", "Skrillex",
            "Deadmau5", "The Chemical Brothers", "Justice", "Kavinsky",
            "Bob Sinclar", "DJ Snake", "Major Lazer", "Diplo",
            "Swedish House Mafia", "Armin van Buuren", "Kungs", "Ofenbach",
        ],
    },
    "annees_80": {
        "label": "Années 80",
        "queries": ["pop", "rock", "dance", "love songs", "funk", "new wave", "disco", "synthpop"],
        "year_range": (1980, 1989),
    },
    "annees_90": {
        "label": "Années 90",
        "queries": ["pop", "rock", "rnb", "dance", "hip hop", "grunge", "eurodance", "britpop"],
        "year_range": (1990, 1999),
    },
    "annees_2000": {
        "label": "Années 2000",
        "queries": ["pop", "rnb", "rock", "hip hop", "dance", "emo", "indie", "electro"],
        "year_range": (2000, 2009),
    },
    "rnb_soul": {
        "label": "R&B / Soul",
        "queries": ["rnb hits", "soul classics", "rnb 2020", "best rnb songs"],
        "artist_pool": [
            "Beyoncé", "Rihanna", "Usher", "Alicia Keys", "John Legend",
            "The Weeknd", "Frank Ocean", "SZA", "H.E.R.", "Khalid",
            "Chris Brown", "Ne-Yo", "Marvin Gaye", "Stevie Wonder",
            "Whitney Houston", "Aretha Franklin", "Ray Charles", "Al Green",
            "Lauryn Hill", "Erykah Badu", "D'Angelo", "Mary J. Blige",
        ],
    },
    "disco_funk": {
        "label": "Disco / Funk",
        "queries": ["disco classics", "funk hits", "disco 70s", "best funk songs"],
        "artist_pool": [
            "Bee Gees", "Donna Summer", "ABBA", "Earth, Wind & Fire", "Chic",
            "Gloria Gaynor", "KC and the Sunshine Band", "Village People",
            "James Brown", "Prince", "George Clinton", "Kool & The Gang",
            "Stevie Wonder", "Michael Jackson", "Diana Ross", "Rick James",
            "Parliament", "Sly and the Family Stone", "Barry White", "Commodores",
        ],
    },
    "latino": {
        "label": "Latino / Reggaeton",
        "queries": ["reggaeton hits", "latino pop", "latin hits 2020", "salsa hits"],
        "artist_pool": [
            "Bad Bunny", "J Balvin", "Daddy Yankee", "Shakira", "Ozuna",
            "Maluma", "Rosalía", "Enrique Iglesias", "Ricky Martin", "Luis Fonsi",
            "Karol G", "Nicky Jam", "Anuel AA", "Rauw Alejandro", "Becky G",
            "Marc Anthony", "Don Omar", "Wisin & Yandel", "Sech", "Farruko",
        ],
    },
}


class SpotifyClient:
    """Client pour les requêtes API Spotify (Client Credentials flow — métadonnées)."""

    def __init__(self) -> None:
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
        self._token: str | None = None
        self._token_expires: float = 0
        self._http = httpx.AsyncClient()

    async def _ensure_token(self) -> None:
        if self._token and time.time() < self._token_expires - 60:
            return
        resp = await self._http.post(
            SPOTIFY_TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + data["expires_in"]

    async def _get(self, path: str, params: dict | None = None) -> dict:
        await self._ensure_token()
        resp = await self._http.get(
            f"{SPOTIFY_API}{path}",
            headers={"Authorization": f"Bearer {self._token}"},
            params=params,
        )
        if resp.status_code != 200:
            print(f"[Spotify] {resp.status_code} {path} -> {resp.text[:500]}")
        resp.raise_for_status()
        return resp.json()

    def _parse_track(self, t: dict) -> Track | None:
        if not t:
            return None
        album = t.get("album", {})
        year = 0
        release = album.get("release_date", "")
        if release:
            year = int(release[:4])
        images = album.get("images", [])
        return Track(
            id=t["id"],
            name=t["name"],
            artist=", ".join(a["name"] for a in t.get("artists", [])),
            album=album.get("name", ""),
            year=year,
            preview_url=t.get("preview_url"),
            spotify_uri=t.get("uri"),
            image_url=images[0]["url"] if images else None,
        )

    async def get_playlist_tracks(
        self, playlist_id: str | None = None, limit: int = 50
    ) -> list[Track]:
        if not playlist_id:
            return await self._get_default_tracks(limit)
        data = await self._get(f"/playlists/{playlist_id}/tracks", {"limit": limit})
        tracks: list[Track] = []
        for item in data.get("items", []):
            track = self._parse_track(item.get("track"))
            if track:
                tracks.append(track)
        return tracks

    async def _get_default_tracks(self, limit: int = 50) -> list[Track]:
        tracks: list[Track] = []
        seen_ids: set[str] = set()
        queries = random.sample(DEFAULT_QUERIES, len(DEFAULT_QUERIES))
        for query in queries:
            if len(tracks) >= limit:
                break
            try:
                results = await self.search_tracks(query, limit=10)
            except Exception as e:
                print(f"[Spotify] Search failed for '{query}': {e}")
                continue
            for t in results:
                if t.id not in seen_ids:
                    seen_ids.add(t.id)
                    tracks.append(t)
        return tracks[:limit]

    async def get_tracks_by_theme(self, theme: str, limit: int = 50) -> list[Track]:
        """Récupère des morceaux par thème prédéfini ou requête libre."""
        year_range = None
        if theme in THEMES:
            queries = THEMES[theme]["queries"]
            year_range = THEMES[theme].get("year_range")
        else:
            queries = [theme]
        tracks: list[Track] = []
        seen_ids: set[str] = set()
        search_limit = 10
        for query in queries:
            if len(tracks) >= limit:
                break
            # Ajouter le filtre année Spotify si disponible
            effective_query = query
            if year_range:
                effective_query = f"{query} year:{year_range[0]}-{year_range[1]}"
            try:
                results = await self.search_tracks(effective_query, limit=search_limit)
            except Exception as e:
                print(f"[Spotify] Search failed for '{effective_query}': {e}")
                continue
            for t in results:
                if t.id in seen_ids:
                    continue
                # Filtrer côté serveur les tracks hors de la plage d'années
                if year_range and t.year != 0:
                    if t.year < year_range[0] or t.year > year_range[1]:
                        continue
                seen_ids.add(t.id)
                tracks.append(t)
        return tracks[:limit]

    async def search_tracks(self, query: str, limit: int = 10) -> list[Track]:
        # Spotify limite à 10 résultats quand un filtre year: est utilisé
        max_limit = 10 if "year:" in query else 50
        data = await self._get("/search", {"q": query, "type": "track", "limit": min(limit, max_limit), "market": "FR"})
        tracks: list[Track] = []
        for t in data.get("tracks", {}).get("items", []):
            track = self._parse_track(t)
            if track:
                tracks.append(track)
        return tracks

    async def close(self) -> None:
        await self._http.aclose()

    # --- OAuth (Authorization Code flow) ---

    def get_auth_url(self, redirect_uri: str, state: str = "") -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
        return f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        resp = await self._http.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            auth=(self.client_id, self.client_secret),
        )
        resp.raise_for_status()
        return resp.json()

    async def refresh_user_token(self, refresh_token: str) -> dict:
        resp = await self._http.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(self.client_id, self.client_secret),
        )
        resp.raise_for_status()
        return resp.json()

    async def transfer_playback(self, user_token: str, device_id: str) -> None:
        """Transfère la lecture active vers le device du Web Playback SDK."""
        resp = await self._http.put(
            f"{SPOTIFY_API}/me/player",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"device_ids": [device_id], "play": False},
        )
        if resp.status_code not in (200, 202, 204):
            print(f"[Spotify] transfer error: {resp.status_code} {resp.text[:300]}")

    async def play_track(self, user_token: str, spotify_uri: str, device_id: str | None = None) -> None:
        """Lance la lecture d'un track sur l'appareil de l'utilisateur."""
        url = f"{SPOTIFY_API}/me/player/play"
        params = {}
        if device_id:
            params["device_id"] = device_id
        resp = await self._http.put(
            url,
            headers={"Authorization": f"Bearer {user_token}"},
            json={"uris": [spotify_uri]},
            params=params,
        )
        if resp.status_code not in (200, 202, 204):
            print(f"[Spotify] play error: {resp.status_code} {resp.text[:300]}")

    async def pause_playback(self, user_token: str, device_id: str | None = None) -> None:
        url = f"{SPOTIFY_API}/me/player/pause"
        params = {}
        if device_id:
            params["device_id"] = device_id
        await self._http.put(
            url,
            headers={"Authorization": f"Bearer {user_token}"},
            params=params,
        )
