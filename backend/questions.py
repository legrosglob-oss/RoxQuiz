from __future__ import annotations

import random

from models import Question, QuestionType, Track


def _pick_wrong_answers(correct: str, pool: list[str], count: int = 3) -> list[str]:
    """Choisit des mauvaises réponses depuis un pool, en excluant la bonne."""
    candidates = [v for v in pool if v.lower() != correct.lower()]
    # dédupliquer
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return random.sample(unique, min(count, len(unique)))


def generate_question(
    track: Track,
    all_tracks: list[Track],
    year_range: tuple[int, int] | None = None,
    artist_pool: list[str] | None = None,
) -> Question:
    """Génère une question aléatoire à partir des métadonnées d'un track."""
    generators = [
        _question_artist,
        _question_title,
        _question_year,
        _question_album,
    ]
    gen = random.choice(generators)
    return gen(track, all_tracks, year_range=year_range, artist_pool=artist_pool)


def _question_artist(
    track: Track,
    all_tracks: list[Track],
    artist_pool: list[str] | None = None,
    **_kwargs,
) -> Question:
    # Utiliser le pool thématique s'il est disponible, sinon les artistes des tracks
    if artist_pool:
        pool = artist_pool
    else:
        pool = [t.artist for t in all_tracks]
    wrong = _pick_wrong_answers(track.artist, pool)
    choices = [track.artist] + wrong
    random.shuffle(choices)
    return Question(
        type=QuestionType.MCQ,
        text="Qui chante cette chanson ?",
        choices=choices,
        correct_answer=track.artist,
        track_id=track.id,
    )


def _question_title(track: Track, all_tracks: list[Track], **_kwargs) -> Question:
    return Question(
        type=QuestionType.TEXT,
        text="Quel est le titre de cette chanson ?",
        choices=None,
        correct_answer=track.name,
        track_id=track.id,
    )


def _question_year(
    track: Track,
    all_tracks: list[Track],
    year_range: tuple[int, int] | None = None,
    **_kwargs,
) -> Question:
    if track.year == 0:
        return _question_artist(track, all_tracks, artist_pool=_kwargs.get("artist_pool"))
    correct = str(track.year)

    # Si un year_range est défini, contraindre les propositions à cette plage
    if year_range:
        pool_years = [
            str(y) for y in range(year_range[0], year_range[1] + 1) if str(y) != correct
        ]
        wrong_years = random.sample(pool_years, min(3, len(pool_years)))
    else:
        wrong_years = _pick_wrong_answers(
            correct, [str(t.year) for t in all_tracks if t.year != 0]
        )

    if len(wrong_years) < 3:
        # Générer des années proches (dans la plage si définie)
        lo = year_range[0] if year_range else track.year - 5
        hi = year_range[1] if year_range else track.year + 5
        for offset in [-2, -1, 1, 2, 3, -3, 4, -4, 5]:
            y = str(track.year + offset)
            yr = track.year + offset
            if y != correct and y not in wrong_years and lo <= yr <= hi:
                wrong_years.append(y)
            if len(wrong_years) >= 3:
                break
    choices = [correct] + wrong_years[:3]
    random.shuffle(choices)
    return Question(
        type=QuestionType.MCQ,
        text="En quelle année est sortie cette chanson ?",
        choices=choices,
        correct_answer=correct,
        track_id=track.id,
    )


def _question_album(track: Track, all_tracks: list[Track], **_kwargs) -> Question:
    if not track.album:
        return _question_artist(track, all_tracks, artist_pool=_kwargs.get("artist_pool"))
    wrong = _pick_wrong_answers(track.album, [t.album for t in all_tracks if t.album])
    if len(wrong) < 3:
        return _question_title(track, all_tracks)
    choices = [track.album] + wrong[:3]
    random.shuffle(choices)
    return Question(
        type=QuestionType.MCQ,
        text="De quel album est tiré ce titre ?",
        choices=choices,
        correct_answer=track.album,
        track_id=track.id,
    )
