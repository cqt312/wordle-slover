"""Interactive command-line interface for the Wordle solver.

Run with:

    python cli.py

At each prompt, enter a guess and its feedback in the form:

    guess: apple
    feedback: +a -p #p -l -e

Feedback tokens:
    +X  green  (X is correct in this position)
    #X  yellow (X is in the word, wrong position)
    -X  gray   (X is not present, or no further occurrences remain)

Type "quit" at the guess prompt to exit.
"""

from typing import List

from solver import WordleSolver


def _read_feedback() -> List[str]:
    """Prompt for and parse a feedback line into a list of tokens.

    Returns:
        A list of feedback tokens, e.g. ["+a", "-p", "#p", "-l", "-e"].
    """
    raw = input("feedback: ")
    return raw.split()


def run_cli() -> None:
    """Run the interactive Wordle solver loop."""
    solver = WordleSolver()

    while True:
        guess = input("guess: ").strip()
        if guess.lower() == "quit":
            break

        feedback = _read_feedback()

        try:
            solver.add_guess(guess, feedback)
        except ValueError as exc:
            print(f"Invalid input: {exc}")
            continue

        print()
        print(f"Candidates: {len(solver.candidates)}")
        print()
        for i, word in enumerate(solver.top_words(), start=1):
            print(f"{i}. {word}")
        print()


if __name__ == "__main__":
    run_cli()
