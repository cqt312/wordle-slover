# Wordle Solver

A Wordle-assistant CLI that maintains full game context across multiple
guesses and narrows the candidate word list using the official Wordle
feedback rules, including correct handling of repeated letters.

## Project layout

```
wordle_solver/
├── scoring.py        # score(guess, answer) -- official two-pass Wordle algorithm
├── word_loader.py     # loads/filters/ranks the candidate word list via wordfreq
├── solver.py          # WordleSolver class: history, filtering, ranking
├── cli.py              # interactive command-line interface
├── requirements.txt
└── tests/
    ├── conftest.py
    ├── test_scoring.py
    └── test_solver.py
```

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python cli.py
```

At each prompt:

```
guess: apple
feedback: +a -p #p -l -e
```

Feedback tokens, one per letter position:

- `+X` green — `X` is correct in this position
- `#X` yellow — `X` is in the word, but in the wrong position
- `-X` gray — no further occurrences of `X` remain to be placed

Type `quit` to exit.

## Why repeated letters need a two-pass algorithm

Wordle does **not** simply mark every occurrence of a letter not present in
the answer as gray. The correct (official) algorithm is:

1. **Pass 1 — greens:** mark every position where `guess[i] == answer[i]`.
2. **Pass 2 — yellows/grays:** for each remaining (non-green) guess
   position, check a *pool* of answer letters that were **not** already
   consumed by a green match. If the guessed letter is still available in
   that pool, mark it yellow and remove one copy from the pool; otherwise
   mark it gray.

Example: answer `adapt`, guess `apple`.

- `adapt` contains exactly one `p`.
- Guess position 1 (`p`) doesn't align with answer position 1 (`d`), but the
  pool still has a `p` available (since the only `p` in `adapt` wasn't
  consumed by a green match elsewhere) → **yellow**.
- Guess position 2 (`p`) doesn't align either, but by now the pool's single
  `p` has already been consumed by position 1 → **gray**.

Result: `+a #p -p -l -e` — *not* "p is absent"; rather "there's exactly one
p, and it's not in position 2 or 3."

This module (`scoring.score`) implements exactly this two-pass logic, and
`WordleSolver` reuses it directly to filter candidates: a word is only kept
if re-scoring every past guess against that word reproduces the feedback
that was actually observed. This sidesteps needing to hand-derive min/max
letter-count constraints — the scoring function already encodes them.

## Testing

```bash
pytest tests/ -v
```

Tests use an injected, deterministic fake word list (not the real
`wordfreq` data) so they run quickly and deterministically, and so the
`WordleSolver` class can be exercised independently of any external data
source — `WordleSolver(all_words=[...])` accepts an explicit word list for
exactly this purpose.
