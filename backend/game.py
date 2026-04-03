from __future__ import annotations

import asyncio
import difflib
import random
import string
import time
import unicodedata
from dataclasses import dataclass, field

from fastapi import WebSocket

from models import (
    GameConfig,
    GameState,
    Player,
    Question,
    QuestionType,
    RoundResult,
    Track,
)
from questions import generate_question
from spotify import THEMES, SpotifyClient


def _generate_code(length: int = 5) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _normalize_string(s: str) -> str:
    """Normalise une chaîne : minuscules, suppression des accents et de la ponctuation."""
    # Enlever accents
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    # Tout en minuscules
    s = s.lower()
    # Enlever ponctuation
    s = "".join(c for c in s if c not in string.punctuation)
    # Enlever espaces en trop
    return " ".join(s.split())


def _is_close_enough(answer: str, correct: str, threshold: float = 0.8) -> bool:
    """Compare deux chaînes avec une tolérance."""
    a = _normalize_string(answer)
    c = _normalize_string(correct)
    if not a or not c:
        return a == c
    if a == c:
        return True
    # On autorise aussi si le titre est contenu dans la réponse ou inversement (pour les titres longs)
    if len(c) > 5 and (c in a or a in c):
        return True
    return difflib.SequenceMatcher(None, a, c).ratio() >= threshold


@dataclass
class Game:
    code: str
    config: GameConfig
    state: GameState = GameState.LOBBY
    players: dict[str, Player] = field(default_factory=dict)
    connections: dict[str, WebSocket] = field(default_factory=dict)
    tracks: list[Track] = field(default_factory=list)
    current_round: int = 0
    rounds_results: list[RoundResult] = field(default_factory=list)
    _current_answers: dict[str, tuple[str, float]] = field(default_factory=dict)
    spotify_user_token: str | None = None
    spotify_device_id: str | None = None
    _spotify_client: SpotifyClient | None = None
    _all_answered: asyncio.Event = field(default_factory=asyncio.Event)

    # --- Broadcast ---

    async def broadcast(self, msg_type: str, data: dict | None = None) -> None:
        payload = {"type": msg_type, "data": data or {}}
        dead: list[str] = []
        for name, ws in self.connections.items():
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(name)
        for name in dead:
            self.connections.pop(name, None)

    async def send_to(self, player_name: str, msg_type: str, data: dict | None = None) -> None:
        ws = self.connections.get(player_name)
        if ws:
            try:
                await ws.send_json({"type": msg_type, "data": data or {}})
            except Exception:
                self.connections.pop(player_name, None)

    # --- Lobby ---

    def add_player(self, name: str, is_host: bool = False) -> Player:
        player = Player(name=name, is_host=is_host)
        self.players[name] = player
        return player

    def remove_player(self, name: str) -> None:
        self.players.pop(name, None)
        self.connections.pop(name, None)

    def get_host(self) -> str | None:
        for p in self.players.values():
            if p.is_host:
                return p.name
        return None

    def players_info(self) -> list[dict]:
        return [p.model_dump() for p in self.players.values()]

    # --- Game flow ---

    async def start(self, spotify: SpotifyClient) -> None:
        self._spotify_client = spotify
        try:
            limit = max(self.config.num_rounds * 2, 50)
            if self.config.theme:
                self.tracks = await spotify.get_tracks_by_theme(self.config.theme, limit=limit)
            else:
                self.tracks = await spotify.get_playlist_tracks(self.config.playlist_id, limit=limit)
        except Exception as e:
            await self.broadcast("error", {"message": f"Erreur Spotify : {e}"})
            self.state = GameState.LOBBY
            return

        if not self.tracks:
            await self.broadcast("error", {"message": "Aucun morceau trouvé dans la playlist"})
            self.state = GameState.LOBBY
            return

        self.state = GameState.PLAYING
        random.shuffle(self.tracks)
        self.current_round = 0
        await self.broadcast("game_started", {
            "num_rounds": self.config.num_rounds,
            "config": self.config.model_dump(),
        })
        await self.next_round()

    async def next_round(self) -> None:
        if self.current_round >= self.config.num_rounds or self.current_round >= len(self.tracks):
            await self.finish()
            return

        track = self.tracks[self.current_round]
        # Récupérer les contraintes du thème pour les questions
        year_range = None
        artist_pool = None
        if self.config.theme and self.config.theme in THEMES:
            year_range = THEMES[self.config.theme].get("year_range")
            artist_pool = THEMES[self.config.theme].get("artist_pool")
        question = generate_question(track, self.tracks, year_range=year_range, artist_pool=artist_pool)
        self._current_question = question
        self._current_track = track
        self._current_answers = {}
        self._all_answered = asyncio.Event()
        self.current_round += 1

        # La lecture est gérée côté frontend :
        # - Premium : Web Playback SDK (hôte uniquement, piste complète)
        # - Fallback : preview_url 30s via <audio> (tous les clients)
        has_premium_audio = self.spotify_user_token is not None and track.spotify_uri is not None
        has_preview = track.preview_url is not None
        has_audio = has_premium_audio or has_preview

        # Calculer la deadline avant le broadcast pour synchroniser les clients
        wait = (self.config.listen_duration + self.config.answer_duration) if has_audio else self.config.answer_duration
        self._round_deadline = time.time() + wait

        await self.broadcast("new_round", {
            "round": self.current_round,
            "total_rounds": self.config.num_rounds,
            "question": question.model_dump(),
            "track": {
                "preview_url": track.preview_url,
                "spotify_uri": track.spotify_uri,
                "image_url": track.image_url,
            },
            "has_audio": has_audio,
            "has_premium_audio": has_premium_audio,
            "listen_duration": self.config.listen_duration,
            "answer_duration": self.config.answer_duration,
            "round_deadline": self._round_deadline,
        })

        # Lancer la lecture côté serveur via l'API Spotify
        if has_premium_audio and self._spotify_client:
            try:
                await self._spotify_client.play_track(
                    self.spotify_user_token, track.spotify_uri, self.spotify_device_id,
                )
            except Exception as e:
                print(f"[Game] Server-side play failed: {e}")

        # Attendre le timeout OU que tous les joueurs aient répondu
        try:
            await asyncio.wait_for(self._all_answered.wait(), timeout=wait)
        except asyncio.TimeoutError:
            pass
        await self.end_round()

    def submit_answer(self, player_name: str, answer: str) -> None:
        if player_name not in self._current_answers:
            self._current_answers[player_name] = (answer, time.time())
            # Si tous les joueurs ont répondu, passer au résultat immédiatement
            if len(self._current_answers) >= len(self.players):
                self._all_answered.set()

    async def end_round(self) -> None:
        question: Question = self._current_question
        track: Track = self._current_track

        correct_players: list[str] = []
        answers_map: dict[str, str] = {}

        for player_name, (answer, _ts) in self._current_answers.items():
            answers_map[player_name] = answer
            
            is_correct = False
            if question.type == QuestionType.MCQ:
                is_correct = answer.lower().strip() == question.correct_answer.lower().strip()
            else:
                is_correct = _is_close_enough(answer, question.correct_answer)

            if is_correct:
                correct_players.append(player_name)
                self.players[player_name].score += 1

        result = RoundResult(
            question=question,
            track=track,
            answers=answers_map,
            correct_players=correct_players,
            scores={name: p.score for name, p in self.players.items()},
        )
        self.rounds_results.append(result)

        # Stopper la lecture
        if self.spotify_user_token and self._spotify_client:
            try:
                await self._spotify_client.pause_playback(
                    self.spotify_user_token, self.spotify_device_id,
                )
            except Exception:
                pass

        self.state = GameState.ROUND_RESULTS
        await self.broadcast("round_result", {
            "correct_answer": question.correct_answer,
            "track": track.model_dump(),
            "correct_players": correct_players,
            "scores": result.scores,
            "round": self.current_round,
        })

        # Pause avant le prochain round
        await asyncio.sleep(5)
        self.state = GameState.PLAYING
        await self.next_round()

    async def finish(self) -> None:
        self.state = GameState.FINISHED
        ranking = sorted(self.players.values(), key=lambda p: p.score, reverse=True)
        await self.broadcast("game_over", {
            "ranking": [p.model_dump() for p in ranking],
        })


class GameManager:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}

    def create_game(self, config: GameConfig | None = None) -> Game:
        code = _generate_code()
        while code in self.games:
            code = _generate_code()
        game = Game(code=code, config=config or GameConfig())
        self.games[code] = game
        return game

    def get_game(self, code: str) -> Game | None:
        return self.games.get(code.upper())

    def remove_game(self, code: str) -> None:
        self.games.pop(code.upper(), None)
