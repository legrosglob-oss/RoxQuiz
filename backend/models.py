from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class GameState(str, Enum):
    LOBBY = "lobby"
    PLAYING = "playing"
    ROUND_RESULTS = "round_results"
    FINISHED = "finished"


class QuestionType(str, Enum):
    MCQ = "mcq"
    TEXT = "text"


class GameConfig(BaseModel):
    num_rounds: int = 10
    listen_duration: int = 15  # secondes d'écoute
    answer_duration: int = 15  # secondes pour répondre
    playlist_id: str | None = None  # playlist Spotify source
    theme: str | None = None  # thème musical (clé THEMES ou requête libre)
    play_on_all_devices: bool = False


class Player(BaseModel):
    name: str
    score: int = 0
    is_host: bool = False


class Track(BaseModel):
    id: str
    name: str
    artist: str
    album: str
    year: int
    preview_url: str | None = None
    spotify_uri: str | None = None
    image_url: str | None = None


class Question(BaseModel):
    type: QuestionType
    text: str
    choices: list[str] | None = None  # pour QCM
    correct_answer: str
    track_id: str


class PlayerAnswer(BaseModel):
    player_name: str
    answer: str
    timestamp: float  # pour bonus vitesse


class RoundResult(BaseModel):
    question: Question
    track: Track
    answers: dict[str, str]  # player_name -> answer
    correct_players: list[str]
    scores: dict[str, int]  # player_name -> score total


# Messages WebSocket

class WSMessage(BaseModel):
    type: str
    data: dict = {}
