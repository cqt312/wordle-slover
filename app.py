"""FastAPI web frontend for the Wordle solver.

This module is a thin presentation/transport layer on top of the existing
:class:`solver.WordleSolver`. It does **not** re-implement any solving,
scoring, or word-loading logic -- it only:

    * serves the static single-page UI,
    * exposes a small JSON API, and
    * forwards guesses/feedback to a shared ``WordleSolver`` instance.

The browser sends, for each submitted row, the guessed word plus a list of
per-cell colors ("green"/"yellow"/"gray"). Those colors are translated into
the exact feedback-token format the existing solver already understands
("+a", "#p", "-l", ...) and handed straight to ``WordleSolver.add_guess``.

Run with:

    python app.py

then open http://127.0.0.1:8964 in a browser.
"""

from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from scoring import DEFAULT_WORD_LENGTH, GRAY, GREEN, YELLOW
from solver import WordleSolver

# --------------------------------------------------------------------------
# Global solver instance, created on first use with the chosen word length.
# --------------------------------------------------------------------------

_solver: "WordleSolver | None" = None
_ZIPF: Dict[int, Dict[str, float]] = {}


def _get_solver(word_length: int) -> WordleSolver:
    global _solver
    if _solver is None or _solver.word_length != word_length:
        _solver = WordleSolver(word_length=word_length)
        _ensure_zipf_cache(word_length)
    return _solver


def _ensure_zipf_cache(word_length: int) -> None:
    if word_length in _ZIPF:
        return
    try:
        from wordfreq import zipf_frequency
        solver = _get_solver(word_length)
        _ZIPF[word_length] = {
            word: round(zipf_frequency(word, "en"), 2)
            for word in solver.all_words
        }
    except Exception:
        _ZIPF[word_length] = {}


_COLOR_TO_MARK = {
    "green": GREEN,
    "yellow": YELLOW,
    "gray": GRAY,
    "white": GRAY,
}

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Wordle Solver Web")


class GuessRequest(BaseModel):
    guess: str = Field(..., description="The guessed word")
    colors: List[str] = Field(..., description="Per-cell feedback colors")
    word_length: int = Field(
        default=DEFAULT_WORD_LENGTH,
        description="Number of letters per word",
    )


class ResetRequest(BaseModel):
    word_length: int = Field(
        default=DEFAULT_WORD_LENGTH,
        description="Number of letters per word",
    )


def _zipf(word: str, word_length: int) -> float:
    cache = _ZIPF.get(word_length, {})
    return cache.get(word, 0.0)


def _word_entry(word: str, word_length: int) -> Dict[str, object]:
    return {"word": word, "zipf": _zipf(word, word_length)}


def _state(word_length: int) -> Dict[str, object]:
    solver = _get_solver(word_length)
    candidates = solver.candidates
    return {
        "word_length": solver.word_length,
        "max_rows": 6,
        "count": len(candidates),
        "top": [_word_entry(w, word_length) for w in solver.top_words(5)],
        "candidates": [_word_entry(w, word_length) for w in candidates],
        "history": [
            {"guess": record.guess, "feedback": record.feedback}
            for record in solver.history
        ],
    }


def _colors_to_feedback(guess: str, colors: List[str]) -> List[str]:
    feedback: List[str] = []
    for letter, color in zip(guess, colors):
        mark = _COLOR_TO_MARK.get(color.lower())
        if mark is None:
            raise HTTPException(
                status_code=400, detail=f"Unknown color: {color!r}"
            )
        feedback.append(f"{mark}{letter}")
    return feedback


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/state")
def get_state(word_length: int = DEFAULT_WORD_LENGTH) -> Dict[str, object]:
    return _state(word_length)


@app.post("/api/guess")
def post_guess(payload: GuessRequest) -> Dict[str, object]:
    wl = payload.word_length
    solver = _get_solver(wl)

    guess = payload.guess.strip().lower()
    if len(guess) != wl or not guess.isalpha():
        raise HTTPException(
            status_code=400,
            detail=f"guess must be {wl} alphabetic letters",
        )
    if len(payload.colors) != wl:
        raise HTTPException(
            status_code=400,
            detail=f"colors must have exactly {wl} entries",
        )

    feedback = _colors_to_feedback(guess, payload.colors)
    try:
        solver.add_guess(guess, feedback)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _state(wl)


@app.post("/api/reset")
def post_reset(payload: ResetRequest) -> Dict[str, object]:
    wl = payload.word_length
    solver = _get_solver(wl)
    solver.reset()
    _ensure_zipf_cache(wl)
    return _state(wl)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8964)
