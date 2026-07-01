/* Wordle Solver frontend (vanilla JS).
 *
 * Only handles input, display, and calling the backend. All solving/scoring
 * happens server-side in the existing Python WordleSolver.
 *
 * Board dimensions are driven by the CSS variable --cols plus state/tiles
 * arrays sized to COLS, so any word length renders correctly. A `generation`
 * counter invalidates any in-flight fetch whose result would otherwise
 * clobber a newer board configuration.
 */

var ROWS = 6;
var COLOR_CYCLE = ["white", "gray", "yellow", "green"];

var COLS = 5;
var state = newGameState(COLS);
var generation = 0;

function newGameState(cols) {
  return {
    letters: Array.from({ length: ROWS }, function () { return Array(cols).fill(""); }),
    colors: Array.from({ length: ROWS }, function () { return Array(cols).fill("white"); }),
    locked: Array(ROWS).fill(false),
    activeRow: 0,
    activeCol: 0,
  };
}

var boardEl = document.getElementById("board");
var messageEl = document.getElementById("message");
var countEl = document.getElementById("count");
var topListEl = document.getElementById("top-list");
var allListEl = document.getElementById("all-list");
var wordlenSelect = document.getElementById("wordlen-select");
var tiles = [];

/* ---------------- Board / keyboard construction ---------------- */

function buildBoard() {
  boardEl.style.setProperty("--cols", COLS);
  boardEl.innerHTML = "";
  tiles = [];
  for (var r = 0; r < ROWS; r++) {
    var rowEl = document.createElement("div");
    rowEl.className = "board-row";
    rowEl.dataset.row = r;
    tiles[r] = [];
    for (var c = 0; c < COLS; c++) {
      var tile = document.createElement("div");
      tile.className = "tile";
      tile.dataset.row = r;
      tile.dataset.col = c;
      tile.addEventListener("click", (function (rr, cc) {
        return function () { onTileClick(rr, cc); };
      })(r, c));
      rowEl.appendChild(tile);
      tiles[r][c] = tile;
    }
    boardEl.appendChild(rowEl);
  }
  render();
}

function buildKeyboard() {
  var layout = [
    ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
    ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
    ["enter", "z", "x", "c", "v", "b", "n", "m", "back"],
  ];
  var keyboardEl = document.getElementById("keyboard");
  if (!keyboardEl) return;
  keyboardEl.innerHTML = "";

  layout.forEach(function (rowKeys, rowIdx) {
    var rowEl = document.createElement("div");
    rowEl.className = "kb-row";

    if (rowIdx === 1) rowEl.appendChild(makeSpacer());

    rowKeys.forEach(function (k) {
      var key = document.createElement("button");
      key.type = "button";
      key.className = "key";

      if (k === "enter") {
        key.classList.add("wide");
        key.textContent = "Enter";
        key.addEventListener("click", submitRow);
      } else if (k === "back") {
        key.classList.add("wide");
        key.textContent = "\u232B";
        key.addEventListener("click", deleteLetter);
      } else {
        key.textContent = k;
        key.addEventListener("click", (function (letter) {
          return function () { typeLetter(letter); };
        })(k));
      }
      rowEl.appendChild(key);
    });

    if (rowIdx === 1) rowEl.appendChild(makeSpacer());
    keyboardEl.appendChild(rowEl);
  });
}

function makeSpacer() {
  var s = document.createElement("div");
  s.className = "key spacer";
  return s;
}

/* ---------------- Input handling ---------------- */

function setActive(r, c) {
  state.activeRow = r;
  state.activeCol = c;
  render();
}

function onTileClick(r, c) {
  if (state.locked[r]) return;
  if (state.letters[r][c]) {
    var idx = COLOR_CYCLE.indexOf(state.colors[r][c]);
    state.colors[r][c] = COLOR_CYCLE[(idx + 1) % COLOR_CYCLE.length];
  }
  setActive(r, c);
}

function typeLetter(letter) {
  var r = state.activeRow;
  if (state.locked[r]) return;
  state.letters[r][state.activeCol] = letter.toUpperCase();
  if (state.colors[r][state.activeCol] === "white") {
    state.colors[r][state.activeCol] = "gray";
  }
  if (state.activeCol < COLS - 1) state.activeCol++;
  render();
}

function deleteLetter() {
  var r = state.activeRow;
  if (state.locked[r]) return;
  if (state.letters[r][state.activeCol]) {
    state.letters[r][state.activeCol] = "";
    state.colors[r][state.activeCol] = "white";
  } else if (state.activeCol > 0) {
    state.activeCol--;
    state.letters[r][state.activeCol] = "";
    state.colors[r][state.activeCol] = "white";
  }
  render();
}

document.addEventListener("keydown", function (e) {
  var r = state.activeRow;
  if (state.locked[r]) return;

  if (e.key === "Enter") { submitRow(); e.preventDefault(); return; }
  if (e.key === "Backspace") { deleteLetter(); e.preventDefault(); return; }
  if (e.key === "ArrowLeft") {
    state.activeCol = Math.max(0, state.activeCol - 1);
    render(); e.preventDefault(); return;
  }
  if (e.key === "ArrowRight") {
    state.activeCol = Math.min(COLS - 1, state.activeCol + 1);
    render(); e.preventDefault(); return;
  }
  if (e.key === "ArrowUp") { moveRow(-1); e.preventDefault(); return; }
  if (e.key === "ArrowDown") { moveRow(1); e.preventDefault(); return; }
  if (/^[a-zA-Z]$/.test(e.key)) { typeLetter(e.key); e.preventDefault(); }
});

function moveRow(delta) {
  var nr = state.activeRow + delta;
  while (nr >= 0 && nr < ROWS && state.locked[nr]) nr += delta;
  if (nr >= 0 && nr < ROWS && !state.locked[nr]) {
    state.activeRow = nr;
    render();
  }
}

/* ---------------- Rendering ---------------- */

function render() {
  for (var r = 0; r < ROWS; r++) {
    if (!tiles[r]) continue;
    for (var c = 0; c < COLS; c++) {
      var tile = tiles[r][c];
      if (!tile) continue;
      var letter = state.letters[r][c];
      tile.textContent = letter;
      tile.className = "tile";
      if (letter) tile.classList.add("filled");
      var color = state.colors[r][c];
      if (color !== "white") tile.classList.add(color);
      if (!state.locked[r] && r === state.activeRow && c === state.activeCol) {
        tile.classList.add("active");
      }
    }
  }
}

function showMessage(text, isError) {
  if (isError === undefined) isError = true;
  messageEl.textContent = text || "";
  messageEl.style.color = isError ? "#c0392b" : "var(--muted)";
}

function animateFlip(r) {
  for (var c = 0; c < COLS; c++) {
    (function (cc) {
      setTimeout(function () {
        if (tiles[r] && tiles[r][cc]) {
          tiles[r][cc].classList.add("flip");
          tiles[r][cc].addEventListener("animationend", function () {
            if (tiles[r] && tiles[r][cc]) tiles[r][cc].classList.remove("flip");
          }, { once: true });
        }
      }, cc * 90);
    })(c);
  }
}

function updateResults(data) {
  if (!data) return;
  countEl.textContent = data.count;

  topListEl.innerHTML = "";
  (data.top || []).forEach(function (entry) {
    var li = document.createElement("li");
    li.innerHTML =
      '<span class="word">' + entry.word + "</span>" +
      '<span class="zipf">' + entry.zipf.toFixed(2) + "</span>";
    topListEl.appendChild(li);
  });

  allListEl.innerHTML = "";
  var frag = document.createDocumentFragment();
  (data.candidates || []).forEach(function (entry) {
    var li = document.createElement("li");
    li.innerHTML =
      '<span class="word">' + entry.word + "</span>" +
      '<span class="zipf">' + entry.zipf.toFixed(2) + "</span>";
    frag.appendChild(li);
  });
  allListEl.appendChild(frag);
}

/* ---------------- Server communication ---------------- */

function submitRow() {
  var r = state.activeRow;
  if (state.locked[r]) return;

  var guess = state.letters[r].join("");
  if (guess.length !== COLS || !/^[A-Za-z]+$/.test(guess)) {
    showMessage("Enter all " + COLS + " letters before submitting.");
    return;
  }

  var colors = state.colors[r].slice();
  var myGen = generation;
  showMessage("");

  fetch("/api/guess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guess: guess.toLowerCase(), colors: colors, word_length: COLS }),
  })
    .then(function (res) {
      if (!res.ok) {
        return res.json()
          .then(function (err) { showMessage(err.detail || "Request failed."); })
          .catch(function () { showMessage("Request failed."); });
      }
      return res.json().then(function (data) {
        if (myGen !== generation) return;
        animateFlip(r);
        state.locked[r] = true;
        if (r + 1 < ROWS) { state.activeRow = r + 1; state.activeCol = 0; }
        render();
        updateResults(data);
      });
    })
    .catch(function () { showMessage("Could not reach the server."); });
}

function restoreHistory(data) {
  (data.history || []).forEach(function (rec, i) {
    if (i >= ROWS) return;
    if (!rec.feedback || rec.feedback.length !== COLS) return;
    for (var c = 0; c < COLS; c++) {
      var token = rec.feedback[c];
      var mark = token[0];
      var letter = token.slice(1);
      state.letters[i][c] = letter.toUpperCase();
      state.colors[i][c] =
        mark === "+" ? "green" : mark === "#" ? "yellow" : "gray";
    }
    state.locked[i] = true;
  });
  state.activeRow = Math.min((data.history || []).length, ROWS - 1);
  state.activeCol = 0;
}

function fetchState() {
  var myGen = generation;
  fetch("/api/state?word_length=" + COLS)
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (myGen !== generation) return;
      restoreHistory(data);
      render();
      updateResults(data);
    })
    .catch(function () { showMessage("Could not reach the server."); });
}

/* Configure the board for a given column count (synchronous UI rebuild),
   then reset the server-side solver for that word length. */
function configureBoard(cols) {
  COLS = cols;
  state = newGameState(COLS);
  generation++;
  buildBoard();
  buildKeyboard();
  showMessage("");
}

function resetServerForLength() {
  var myGen = generation;
  fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word_length: COLS }),
  })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (myGen !== generation) return;
      updateResults(data);
    })
    .catch(function () {
      if (myGen === generation) showMessage("Could not reach the server.");
    });
}

function resetGame() {
  generation++;
  var myGen = generation;
  state = newGameState(COLS);
  render();
  showMessage("");
  fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word_length: COLS }),
  })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (myGen !== generation) return;
      updateResults(data);
    })
    .catch(function () {
      if (myGen === generation) showMessage("Could not reach the server.");
    });
}

/* ---------------- Wiring & init ---------------- */

wordlenSelect.addEventListener("change", function () {
  var newLen = parseInt(wordlenSelect.value, 10);
  if (!newLen || newLen === COLS) return;
  configureBoard(newLen);      // rebuild board immediately for the new length
  resetServerForLength();      // reset the server-side solver for that length
});

document.getElementById("submit-btn").addEventListener("click", submitRow);
document.getElementById("reset-btn").addEventListener("click", resetGame);

// Adopt whatever length the dropdown currently shows (handles browser-restored
// selection after a refresh), build the board, then load server state.
COLS = parseInt(wordlenSelect.value, 10) || 5;
configureBoard(COLS);
fetchState();
