// Telegram Web App bootstrap
const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  // Expand to full height for better UX
  tg.expand();

  // Try to match Telegram theme if provided
  const themeParams = tg.themeParams || {};
  if (themeParams.bg_color) {
    document.body.style.backgroundColor = themeParams.bg_color;
  }
}

const resultBox = document.getElementById("result");
const btnPassword = document.getElementById("btn-password");
const btnRoll = document.getElementById("btn-roll");
const btnFlip = document.getElementById("btn-flip");
const btnCalc = document.getElementById("btn-calc");
const btnTime = document.getElementById("btn-time");
const calcInput = document.getElementById("calc-input");
const btnCalcEval = document.getElementById("btn-calc-eval");

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

// Dice roll 1–6
function rollDice() {
  return Math.floor(Math.random() * 6) + 1;
}

// Coin flip
function flipCoin() {
  return Math.random() < 0.5 ? "🪙 Heads" : "🪙 Tails";
}

// Simple calculator - mirrors bot's basic math behavior
function safeCalc(exprRaw) {
  const expr = String(exprRaw || "")
    .replace(/×/g, "*")
    .replace(/÷/g, "/")
    .trim();

  if (!expr) {
    throw new Error("Empty");
  }

  // Very simple guard: only numbers, operators and parentheses
  if (!/^[0-9+\-*/().\s]+$/.test(expr)) {
    throw new Error("Invalid");
  }

  // eslint-disable-next-line no-new-func
  const fn = new Function(`return (${expr})`);
  const res = fn();

  if (typeof res !== "number" || !isFinite(res)) {
    throw new Error("Invalid");
  }

  // Hide .0 for integers
  if (Number.isInteger(res)) {
    return String(res);
  }
  return String(Number(res.toFixed(10)));
}

btnPassword.addEventListener("click", () => {
  const pwd = generatePassword();
  setResult(`🔐 Generated password:\n${pwd}`);
});

btnRoll.addEventListener("click", () => {
  const value = rollDice();
  setResult(`🎲 You rolled: ${value} (1–6)`);
});

btnFlip.addEventListener("click", () => {
  const value = flipCoin();
  setResult(value);
});

btnTime.addEventListener("click", () => {
  const now = new Date();
  const formatted = now.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  setResult(`🕒 Current time:\n${formatted}`);
});

btnCalc.addEventListener("click", () => {
  calcInput.focus();
  calcInput.select();
});

btnCalcEval.addEventListener("click", () => {
  try {
    const expr = calcInput.value;
    const result = safeCalc(expr);
    setResult(`🧮 ${expr} = ${result}`);
  } catch (e) {
    setResult("⚠️ Invalid expression. Use basic numbers and operators.");
  }
});

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

