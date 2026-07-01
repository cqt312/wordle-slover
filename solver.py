"""Wordle solver core logic.

`WordleSolver` maintains the full game context (guess/feedback history) and
filters candidate words by re-deriving, for each candidate, what the official
Wordle feedback *would* have been for every past guess (via `scoring.score`)
and checking it matches what was actually observed. This avoids having to
hand-derive letter-count constraints (min/max occurrences, position
exclusions, etc.) -- the scoring function's two-pass algorithm already
encodes all of that correctly, including repeated-letter edge cases.
"""

from typing import List, Optional, Sequence

from scoring import DEFAULT_WORD_LENGTH, score
from word_loader import load_candidate_words


class GuessRecord:
    """A single recorded guess and its observed feedback.

    Attributes:
        guess: The N-letter word that was guessed.
        feedback: The feedback tokens observed for that guess, e.g.
            ["+a", "-p", "#p", "-l", "-e"].
    """

    __slots__ = ("guess", "feedback")

    def __init__(self, guess: str, feedback: Sequence[str]) -> None:
        """Initialize a GuessRecord.

        Args:
            guess: The N-letter guessed word.
            feedback: The feedback tokens for that guess.
        """
        self.guess = guess
        self.feedback = list(feedback)


class WordleSolver:
    """Maintains Wordle game state and filters candidates accordingly.

    Attributes:
        word_length: Number of letters per word.
        all_words: The full, frequency-sorted list of candidate words,
            loaded once and never reloaded.
        history: The list of GuessRecord entries made so far this game.
        candidates: The current list of candidate words consistent with
            all entries in `history`, in frequency order.
    """

    def __init__(
        self,
        all_words: Optional[List[str]] = None,
        word_length: int = DEFAULT_WORD_LENGTH,
    ) -> None:
        """Initialize the solver.

        Args:
            all_words: Optional pre-loaded, frequency-sorted word list. If
                not provided, words are loaded via `load_candidate_words`.
                Accepting an injected list keeps the class easy to test
                without depending on the real `wordfreq` data.
            word_length: Number of letters per word (default 5).
        """
        self.word_length = word_length
        self.all_words: List[str] = (
            list(all_words)
            if all_words is not None
            else load_candidate_words(word_length=word_length)
        )
        self.history: List[GuessRecord] = []
        self.candidates: List[str] = list(self.all_words)

    def reset(self) -> None:
        """Clear all game history and restore the full candidate list."""
        self.history = []
        self.candidates = list(self.all_words)

    def add_guess(self, guess: str, feedback: Sequence[str]) -> None:
        """Record a new guess/feedback pair and refilter candidates.

        Args:
            guess: The N-letter word that was guessed.
            feedback: The feedback tokens observed, e.g.
                ["+a", "-p", "#p", "-l", "-e"].

        Raises:
            ValueError: If `guess` is not a valid N-letter word, or if
                `feedback` does not have exactly `word_length` entries.
        """
        normalized_guess = guess.strip().lower()
        if (
            len(normalized_guess) != self.word_length
            or not normalized_guess.isalpha()
        ):
            raise ValueError(
                f"guess must be a {self.word_length}-letter alphabetic string, "
                f"got {guess!r}"
            )

        normalized_feedback = [token.strip().lower() for token in feedback]
        if len(normalized_feedback) != self.word_length:
            raise ValueError(
                f"feedback must have exactly {self.word_length} entries, got "
                f"{len(normalized_feedback)}"
            )

        self.history.append(GuessRecord(normalized_guess, normalized_feedback))
        self.filter_candidates()

    def filter_candidates(self) -> None:
        """Recompute `candidates` from scratch against the full history.

        A word remains a candidate only if, for every past guess in
        `history`, scoring that guess against the candidate (as if the
        candidate were the true answer) reproduces exactly the feedback
        that was actually observed.
        """
        self.candidates = [
            word
            for word in self.all_words
            if self._is_consistent(word)
        ]

    def _is_consistent(self, candidate: str) -> bool:
        """Check whether a candidate word is consistent with all history.

        Args:
            candidate: The candidate word to test.

        Returns:
            True if `candidate` would have produced every observed
            feedback entry in `history`, False otherwise.
        """
        for record in self.history:
            if (
                score(record.guess, candidate, word_length=self.word_length)
                != record.feedback
            ):
                return False
        return True

    def top_words(self, n: int = 5) -> List[str]:
        """Return the top `n` current candidates by frequency rank.

        Args:
            n: Number of words to return (default 5).

        Returns:
            Up to `n` candidate words, in descending frequency order.
        """
        return self.candidates[:n]
