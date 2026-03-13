// Telegram Web App bootstrap
const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  // Expand to full height for better UX
  tg.expand();

  // Keep our custom theme (we handle styling in CSS)
}

const resultBox = document.getElementById("result");
const btnPassword = document.getElementById("btn-password");
const btnNewGame = document.getElementById("btn-new-game");
const btnFlagMode = document.getElementById("btn-flag-mode");
const msGrid = document.getElementById("ms-grid");
const msStatus = document.getElementById("ms-status");
const msMines = document.getElementById("ms-mines");

function setResult(text) {
  resultBox.textContent = text;
}

// Password generator (12 chars, like in the bot)
function generatePassword() {
  const alphabet =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+=[]{};:,.<>/?";
  const length = 12;
  let pwd = "";
  const array = new Uint32Array(length);
  window.crypto.getRandomValues(array);
  for (let i = 0; i < length; i++) {
    const idx = array[i] % alphabet.length;
    pwd += alphabet[idx];
  }
  return pwd;
}

btnPassword.addEventListener("click", () => {
  const pwd = generatePassword();
  setResult(`🔐 Generated password:\n${pwd}`);
});

// ---------------------------------------------------------------------------
// Minesweeper
// ---------------------------------------------------------------------------

const MS_ROWS = 9;
const MS_COLS = 9;
const MS_MINES = 10;

let ms = null;
let flagMode = false;

function createMsState() {
  const cells = Array.from({ length: MS_ROWS * MS_COLS }, () => ({
    mine: false,
    open: false,
    flag: false,
    adj: 0,
  }));

  // Place mines
  const picks = new Set();
  while (picks.size < MS_MINES) {
    picks.add(Math.floor(Math.random() * cells.length));
  }
  for (const idx of picks) cells[idx].mine = true;

  // Compute adjacency
  for (let r = 0; r < MS_ROWS; r++) {
    for (let c = 0; c < MS_COLS; c++) {
      const i = r * MS_COLS + c;
      if (cells[i].mine) continue;
      let count = 0;
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const rr = r + dr;
          const cc = c + dc;
          if (rr < 0 || rr >= MS_ROWS || cc < 0 || cc >= MS_COLS) continue;
          if (cells[rr * MS_COLS + cc].mine) count++;
        }
      }
      cells[i].adj = count;
    }
  }

  return {
    cells,
    over: false,
    won: false,
    opened: 0,
  };
}

function msIndexFromEl(el) {
  const idx = Number(el?.dataset?.idx);
  return Number.isFinite(idx) ? idx : -1;
}

function msRemainingMines() {
  const flags = ms.cells.reduce((acc, x) => acc + (x.flag ? 1 : 0), 0);
  return Math.max(0, MS_MINES - flags);
}

function setMsStatus(text) {
  msStatus.textContent = text;
  msMines.textContent = `💣 ${msRemainingMines()}`;
}

function openCell(idx) {
  if (ms.over) return;
  const cell = ms.cells[idx];
  if (!cell || cell.open || cell.flag) return;

  cell.open = true;
  ms.opened += 1;

  if (cell.mine) {
    ms.over = true;
    ms.won = false;
    revealAllMines();
    setMsStatus("Boom! 💥");
    return;
  }

  if (cell.adj === 0) {
    floodOpen(idx);
  }

  checkWin();
}

function floodOpen(startIdx) {
  const q = [startIdx];
  const seen = new Set([startIdx]);
  while (q.length) {
    const idx = q.shift();
    const r = Math.floor(idx / MS_COLS);
    const c = idx % MS_COLS;
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        const rr = r + dr;
        const cc = c + dc;
        if (rr < 0 || rr >= MS_ROWS || cc < 0 || cc >= MS_COLS) continue;
        const ni = rr * MS_COLS + cc;
        if (seen.has(ni)) continue;
        const ncell = ms.cells[ni];
        if (ncell.open || ncell.flag) continue;
        if (ncell.mine) continue;
        ncell.open = true;
        ms.opened += 1;
        seen.add(ni);
        if (ncell.adj === 0) q.push(ni);
      }
    }
  }
}

function toggleFlag(idx) {
  if (ms.over) return;
  const cell = ms.cells[idx];
  if (!cell || cell.open) return;
  cell.flag = !cell.flag;
  checkWin();
}

function revealAllMines() {
  for (const c of ms.cells) {
    if (c.mine) c.open = true;
  }
}

function checkWin() {
  const totalSafe = MS_ROWS * MS_COLS - MS_MINES;
  const openedSafe = ms.cells.reduce(
    (acc, c) => acc + (!c.mine && c.open ? 1 : 0),
    0
  );
  if (openedSafe === totalSafe) {
    ms.over = true;
    ms.won = true;
    setMsStatus("You win! ✅");
  } else if (!ms.over) {
    setMsStatus(flagMode ? "Flag mode: ON 🚩" : "Tap to open");
  }
}

function renderGrid() {
  msGrid.style.setProperty("--ms-cols", String(MS_COLS));
  msGrid.innerHTML = "";

  for (let i = 0; i < ms.cells.length; i++) {
    const cell = ms.cells[i];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ms-cell";
    btn.dataset.idx = String(i);

    if (cell.open) {
      btn.classList.add("is-open");
      if (cell.mine) {
        btn.classList.add("is-mine");
        btn.textContent = "💣";
      } else if (cell.adj > 0) {
        btn.textContent = String(cell.adj);
        btn.dataset.adj = String(cell.adj);
      } else {
        btn.textContent = "";
      }
    } else if (cell.flag) {
      btn.classList.add("is-flag");
      btn.textContent = "🚩";
    } else {
      btn.textContent = "";
    }

    btn.addEventListener("click", () => {
      const idx = msIndexFromEl(btn);
      if (idx < 0) return;
      if (flagMode) toggleFlag(idx);
      else openCell(idx);
      renderGrid();
    });

    // Right-click for flags (desktop)
    btn.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      const idx = msIndexFromEl(btn);
      if (idx < 0) return;
      toggleFlag(idx);
      renderGrid();
    });

    msGrid.appendChild(btn);
  }
}

function newGame() {
  ms = createMsState();
  setMsStatus("Tap to open");
  renderGrid();
}

function setFlagMode(next) {
  flagMode = Boolean(next);
  btnFlagMode.setAttribute("aria-pressed", flagMode ? "true" : "false");
  btnFlagMode.textContent = flagMode ? "🚩 On" : "🚩 Off";
  checkWin();
}

btnNewGame.addEventListener("click", () => {
  setFlagMode(false);
  newGame();
});

btnFlagMode.addEventListener("click", () => {
  setFlagMode(!flagMode);
});

newGame();

// ---------------------------------------------------------------------------
// NOTES FOR DEPLOYMENT (Vercel / BotFather)
// ---------------------------------------------------------------------------
// 1) Deploy to Vercel:
//    - Place this "webapp" folder in a small static project.
//    - On Vercel, create a new project from your repo.
//    - Set "webapp" (or the folder where index.html lives) as the public root.
//    - After deployment you'll get a URL like:
//         https://your-project-name.vercel.app
//
// 2) Use that URL in bot.py:
//    - In bot.py, find the WebAppInfo(url="...") in the /start handler.
//    - Replace the placeholder with your real Vercel URL.
//
// 3) Configure in BotFather:
//    - Open @BotFather → your bot → Bot Settings → Menu Button / Web Apps.
//    - Add a Web App button with the same URL and a name.
//    - Optionally configure a "Menu button" so users see your Web App entry.

