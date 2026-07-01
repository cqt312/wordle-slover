
# Wordle Solver

Wordle helper tool with a **web UI**. Enter your guesses and observed feedback to narrow thousands of candidates down to a handful, ranked by Zipf word frequency.

Supports **3‑to‑7‑letter games**, preserves full game context across multiple guesses, and uses the official two‑pass Wordle scoring algorithm (repeated‑letter edge cases handled correctly).

![](https://img.shields.io/badge/python-3.10%2B-blue) ![](https://img.shields.io/badge/license-MIT-green)

## Quick start

```bash
git clone https://github.com/yourname/wordle-solver.git
cd wordle-solver
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:8964** in your browser.

## How it works

1. Play Wordle normally in another tab (or on your phone).
2. On the solver page, type the word you guessed into the board.
3. Click each tile to set its color: **white → gray → yellow → green**.
4. Press **Submit** (or hit Enter).
5. The sidebar refreshes with the remaining candidates, sorted by frequency.

Repeat for each guess. The solver remembers your history across rounds.

## Web UI features

- Wordle‑style 6‑row board with flip animations.
- On‑screen QWERTY keyboard (works on mobile).
- Selectable word length (3–7 letters) – the board, backend, and word list all adapt automatically.
- Dark‑mode aware, responsive layout.
- Zero‑dependency frontend (vanilla HTML/CSS/JS).

## CLI mode

If you prefer the terminal:

```bash
python cli.py
```

```
guess: apple
feedback: +a -p #p -l -e

Candidates: 42

1. adapt
2. adult
3. after
...
```

## Project structure

```
.
├── scoring.py          # score(guess, answer) – official two-pass Wordle algorithm
├── word_loader.py      # loads and ranks candidates via wordfreq
├── solver.py           # WordleSolver class: history, filtering, ranking
├── cli.py              # interactive CLI
├── app.py              # FastAPI web server + REST API
├── static/             # frontend (index.html, style.css, app.js)
└── requirements.txt
```

## API

All solving logic lives in the existing Python `WordleSolver` – the API is a thin transport layer.

| Method | Endpoint     | Description                                    |
|--------|-------------|------------------------------------------------|
| GET    | `/api/state?word_length=5`  | Current candidates, top 5, history |
| POST   | `/api/guess` | Submit one guess with per‑cell colors          |
| POST   | `/api/reset` | Reset the solver                               |

## Deployment

### Render / Railway / Fly.io

Deploy as a standard Python web app. Use **`uvicorn app:app --host 0.0.0.0 --port 8964`** as the start command.

The app has no database – state lives in memory, so a single process is fine for personal use. For multi‑user deployment, add a session layer.

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8964
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8964"]
```

```bash
docker build -t wordle-solver .
docker run -p 8964:8964 wordle-solver
```

### Cloudflare Tunnel (no server needed)

If you're behind NAT or just want a quick shareable link:

```bash
pip install cloudflared
cloudflared tunnel --url http://127.0.0.1:8964
```

This gives you a temporary public `https://....trycloudflare.com` URL that tunnels to your local solver.

## Requirements

- Python **3.10+**
- `fastapi`, `uvicorn`, `wordfreq` (see `requirements.txt`)
- No JavaScript build tools – just a browser
```
