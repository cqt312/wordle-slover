"""Wordle feedback scoring logic.

This module implements the official Wordle scoring algorithm, which must be
applied in two passes to correctly handle repeated letters:

1. First pass: mark all exact position matches as green ("+").
2. Second pass: for remaining (non-green) guess letters, consume from the
   remaining pool of answer letters (those not already claimed by a green
   match) to mark yellow ("#"); anything left over is gray ("-").

This two-pass approach is what makes repeated letters behave correctly. For
example, guess "apple" against answer "adapt" produces:

    +a  -p  #p  -l  -e

because "adapt" contains exactly one "p". The first "p" in "apple" (index 1)
does not align with the "p" in "adapt" (index 2), so it cannot be green; the
single available "p" in the answer's remaining pool is consumed by it,
making it yellow. By the time we reach the second "p" (index 2), the
remaining pool no longer has a "p" to consume, so it is gray -- even though
"adapt" does contain a "p" somewhere overall.
"""

from collections import Counter
from typing import List

DEFAULT_WORD_LENGTH = 5

GREEN = "+"
YELLOW = "#"
GRAY = "-"


def score(guess: str, answer: str, word_length: int = DEFAULT_WORD_LENGTH) -> List[str]:
    """Compute official Wordle feedback for a guess against an answer.

    Args:
        guess: The guessed word.
        answer: The true answer word.
        word_length: Number of letters per word (default 5).

    Returns:
        A list of feedback tokens, one per letter position, each of the
        form "+X", "#X", or "-X" where X is the uppercase-independent
        (lowercase) letter at that position in `guess`.

    Raises:
        ValueError: If `guess` or `answer` is not exactly `word_length`
            alphabetic characters.
    """
    guess = _validate_word(guess, "guess", word_length)
    answer = _validate_word(answer, "answer", word_length)

    result: List[str] = [""] * word_length

    # Pass 1: mark greens, and build a pool of answer letters that were
    # NOT consumed by a green match. Only letters in this remaining pool
    # are eligible to satisfy a yellow match in pass 2.
    remaining_answer_letters: Counter = Counter()
    for i in range(word_length):
        if guess[i] == answer[i]:
            result[i] = f"{GREEN}{guess[i]}"
        else:
            remaining_answer_letters[answer[i]] += 1

    # Pass 2: for every non-green position, try to consume a letter from
    # the remaining pool to mark yellow; otherwise it is gray.
    for i in range(word_length):
        if result[i]:  # already green
            continue
        letter = guess[i]
        if remaining_answer_letters[letter] > 0:
            result[i] = f"{YELLOW}{letter}"
            remaining_answer_letters[letter] -= 1
        else:
            result[i] = f"{GRAY}{letter}"

    return result


def _validate_word(word: str, field_name: str, word_length: int) -> str:
    """Validate and normalize a word to lowercase.

    Args:
        word: The word to validate.
        field_name: Name used in error messages (e.g. "guess").
        word_length: Expected number of letters.

    Returns:
        The lowercase version of `word`.

    Raises:
        ValueError: If the word is not exactly `word_length` alphabetic
            characters.
    """
    if not isinstance(word, str) or len(word) != word_length or not word.isalpha():
        raise ValueError(
            f"{field_name!r} must be a {word_length}-letter alphabetic "
            f"string, got {word!r}"
        )
    return word.lower()
