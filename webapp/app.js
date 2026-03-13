import { createChessGame } from "./games/chess.js";
import { createCheckersGame } from "./games/checkers.js";
import { createDurakGame } from "./games/durak.js";

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const btnClose = document.getElementById("btn-close");
const btnBack = document.getElementById("btn-back");
const btnSendResult = document.getElementById("btn-send-result");
const gameScreen = document.getElementById("game-screen");
const gameRoot = document.getElementById("game-root");
const gameTitle = document.getElementById("game-title");

const profileBox = document.getElementById("profile-box");
const ratingBox = document.getElementById("rating-box");
const musicToggle = document.getElementById("music-toggle");
const btnSaveSettings = document.getElementById("btn-save-settings");

let activeGame = null;
let pendingResult = null;

function setTab(tab) {
  document.querySelectorAll(".tab-btn").forEach((b) => {
    b.classList.toggle("is-active", b.dataset.tab === tab);
  });
  document.querySelectorAll(".tab-panel").forEach((p) => {
    p.classList.toggle("is-active", p.id === `tab-${tab}`);
  });
}

function openGame(id) {
  pendingResult = null;
  gameScreen.classList.add("is-active");
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("is-active"));
  gameTitle.textContent =
    id === "chess"
      ? "♟ Шахматы"
      : id === "checkers"
      ? "⭕ Шашки"
      : id === "dice"
      ? "🎲 Дуэль кубиков"
      : "Игра";

  const onResult = (res) => {
    pendingResult = res;
  };

  if (id === "chess") activeGame = createChessGame({ root: gameRoot, onResult });
  else if (id === "checkers") activeGame = createCheckersGame({ root: gameRoot, onResult });
  else if (id === "durak") activeGame = createDurakGame({ root: gameRoot, onResult });
  else if (id === "dice") {
    gameRoot.innerHTML =
      "<div class='game-info'>🎲 Нажмите «Бросить» ниже, чтобы сыграть против бота.</div>";
    const btn = document.createElement("button");
    btn.className = "primary-btn";
    btn.type = "button";
    btn.textContent = "🎲 Бросить";
    btn.addEventListener("click", () => {
      const user = 1 + Math.floor(Math.random() * 6);
      const bot = 1 + Math.floor(Math.random() * 6);
      let outcome = "draw";
      if (user > bot) outcome = "win";
      else if (user < bot) outcome = "loss";
      const score_delta = outcome === "win" ? 3 : outcome === "draw" ? 1 : 0;
      gameRoot.innerHTML =
        `<div class='game-info'>Вы: ${user} | Бот: ${bot}\n` +
        `Исход: ${outcome}\nОчки: +${score_delta}</div>`;
      pendingResult = { type: "result", game: "dice", outcome, score_delta };
    });
    gameRoot.appendChild(btn);
    activeGame = { reset() {} };
  }
}

function closeGame() {
  gameScreen.classList.remove("is-active");
  setTab("games");
  if (activeGame && activeGame.reset) activeGame.reset();
  activeGame = null;
  pendingResult = null;
}

function sendResult() {
  if (!tg) return;
  if (!pendingResult) {
    tg.showAlert("Сначала доиграйте раунд/партию, чтобы появился результат.");
    return;
  }
  tg.sendData(JSON.stringify(pendingResult));
  tg.showAlert("Результат отправлен боту.");
}

document.querySelectorAll(".tab-btn").forEach((b) => {
  b.addEventListener("click", () => {
    closeGame();
    setTab(b.dataset.tab);
  });
});

document.querySelectorAll("[data-open-game]").forEach((b) => {
  b.addEventListener("click", () => openGame(b.dataset.openGame));
});

btnBack.addEventListener("click", closeGame);
btnSendResult.addEventListener("click", sendResult);
btnClose.addEventListener("click", () => (tg ? tg.close() : window.close()));

function loadBasics() {
  const u = tg?.initDataUnsafe?.user;
  if (u) {
    const username = u.username ? `@${u.username}` : "—";
    profileBox.textContent =
      `ID: ${u.id}\n` +
      `Имя: ${u.first_name || "—"} ${u.last_name || ""}`.trim() +
      `\nUsername: ${username}\n\n` +
      "Очки и рейтинг обновляются после отправки результата боту.";
  } else {
    profileBox.textContent = "Откройте Web App из Telegram, чтобы увидеть профиль.";
  }
  ratingBox.textContent = "Рейтинг отображается в боте (🏆 Рейтинг).";
}

btnSaveSettings.addEventListener("click", () => {
  const s = { music_on: Boolean(musicToggle.checked) };
  localStorage.setItem("hub_settings", JSON.stringify(s));
  if (tg) tg.showAlert("Настройки сохранены.");
});

try {
  const s = JSON.parse(localStorage.getItem("hub_settings") || "{}");
  musicToggle.checked = Boolean(s.music_on);
} catch {}

setTab("games");
loadBasics();

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

