"""Word list loading utilities.

Isolates all interaction with the `wordfreq` package so the rest of the
codebase does not need to know how candidate words are sourced or ranked.
"""

from typing import List

from scoring import DEFAULT_WORD_LENGTH


def load_candidate_words(
    language: str = "en",
    word_length: int = DEFAULT_WORD_LENGTH,
) -> List[str]:
    """Load and rank all N-letter candidate words from wordfreq.

    Words are filtered to be exactly `word_length` characters, fully
    alphabetic, lowercased, and de-duplicated, then sorted by descending
    Zipf frequency (most common words first).

    Args:
        language: The wordfreq language code to load (default "en").
        word_length: Number of letters per word (default 5).

    Returns:
        A list of N-letter lowercase words, sorted from most to least
        frequent.
    """
    from wordfreq import iter_wordlist, zipf_frequency

    seen = set()
    words: List[str] = []
    for word in iter_wordlist(language):
        lowered = word.lower()
        if (
            len(lowered) == word_length
            and lowered.isalpha()
            and lowered not in seen
        ):
            seen.add(lowered)
            words.append(lowered)

    words.sort(key=lambda w: zipf_frequency(w, language), reverse=True)
    return words
