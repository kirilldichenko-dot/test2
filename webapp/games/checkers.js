export function createCheckersGame({ root, onResult }) {
  const EMPTY = ".";
  const W = "w";
  const WK = "W";
  const B = "b";
  const BK = "B";

  let board = initialBoard();
  let whiteTurn = true; // user is white
  let selected = null;
  let legal = new Map(); // dest -> move
  let finished = false;

  const boardEl = document.createElement("div");
  boardEl.className = "board";

  const infoEl = document.createElement("div");
  infoEl.className = "game-info";

  root.innerHTML = "";
  root.appendChild(boardEl);
  root.appendChild(infoEl);

  function initialBoard() {
    const b = Array.from({ length: 8 }, () => Array.from({ length: 8 }, () => EMPTY));
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 8; c++) {
        if ((r + c) % 2 === 1) b[r][c] = B;
      }
    }
    for (let r = 5; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        if ((r + c) % 2 === 1) b[r][c] = W;
      }
    }
    return b;
  }

  function inBounds(r, c) {
    return r >= 0 && r < 8 && c >= 0 && c < 8;
  }

  function isWhite(p) {
    return p === W || p === WK;
  }
  function isBlack(p) {
    return p === B || p === BK;
  }
  function isKing(p) {
    return p === WK || p === BK;
  }

  function dirs(p) {
    if (p === W) return [[-1, -1], [-1, 1]];
    if (p === B) return [[1, -1], [1, 1]];
    return [[-1, -1], [-1, 1], [1, -1], [1, 1]];
  }

  function cloneBoard(b) {
    return b.map((row) => row.slice());
  }

  function findMovesFor(r, c) {
    const p = board[r][c];
    if (p === EMPTY) return [];
    const my = whiteTurn ? isWhite : isBlack;
    if (!my(p)) return [];

    const captures = [];
    const normals = [];

    for (const [dr, dc] of dirs(p)) {
      const rr = r + dr;
      const cc = c + dc;
      if (inBounds(rr, cc) && board[rr][cc] === EMPTY) {
        normals.push({ from: [r, c], to: [rr, cc], captures: [] });
      }

      const mr = r + dr;
      const mc = c + dc;
      const lr = r + 2 * dr;
      const lc = c + 2 * dc;
      if (!inBounds(lr, lc) || !inBounds(mr, mc)) continue;
      if (board[lr][lc] !== EMPTY) continue;
      const mid = board[mr][mc];
      if (mid === EMPTY) continue;
      if (whiteTurn ? isWhite(mid) : isBlack(mid)) continue;
      captures.push({ from: [r, c], to: [lr, lc], captures: [[mr, mc]] });
    }

    return captures.length ? captures : normals;
  }

  function allMoves() {
    const moves = [];
    const captures = [];
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const ms = findMovesFor(r, c);
        for (const m of ms) {
          if (m.captures.length) captures.push(m);
          else moves.push(m);
        }
      }
    }
    return captures.length ? captures : moves;
  }

  function applyMove(m) {
    const b2 = cloneBoard(board);
    const [sr, sc] = m.from;
    const [er, ec] = m.to;
    const piece = b2[sr][sc];
    b2[sr][sc] = EMPTY;
    b2[er][ec] = piece;
    for (const [cr, cc] of m.captures) b2[cr][cc] = EMPTY;

    // promotion
    if (piece === W && er === 0) b2[er][ec] = WK;
    if (piece === B && er === 7) b2[er][ec] = BK;

    board = b2;
  }

  function winner() {
    let w = false, b = false;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        if (isWhite(board[r][c])) w = true;
        if (isBlack(board[r][c])) b = true;
      }
    }
    if (w && !b) return "white";
    if (b && !w) return "black";
    return null;
  }

  function botMove() {
    if (finished) return;
    if (whiteTurn) return;
    const ms = allMoves();
    if (!ms.length) {
      finished = true;
      onResult({ type: "result", game: "checkers", outcome: "win", score_delta: 10 });
      return;
    }
    const m = ms[Math.floor(Math.random() * ms.length)];
    applyMove(m);
    whiteTurn = true;
  }

  function squareColor(r, c) {
    return (r + c) % 2 === 0 ? "light" : "dark";
  }

  function pieceChar(p) {
    if (p === W) return "⚪";
    if (p === WK) return "⚪";
    if (p === B) return "⚫";
    if (p === BK) return "⚫";
    return "";
  }

  function setSelection(r, c) {
    selected = [r, c];
    legal = new Map();
    const ms = findMovesFor(r, c);
    for (const m of ms) legal.set(`${m.to[0]}:${m.to[1]}`, m);
  }

  function clearSelection() {
    selected = null;
    legal = new Map();
  }

  function render() {
    boardEl.innerHTML = "";
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `sq ${squareColor(r, c)}`;
        if (selected && selected[0] === r && selected[1] === c) btn.classList.add("is-selected");
        if (legal.has(`${r}:${c}`)) btn.classList.add("is-move");
        btn.textContent = pieceChar(board[r][c]) || ((r + c) % 2 === 1 ? "▫️" : "");
        btn.addEventListener("click", () => onCell(r, c));
        boardEl.appendChild(btn);
      }
    }
    const t = whiteTurn ? "Ваш ход (белые)" : "Ход бота (чёрные)";
    infoEl.textContent = finished ? "Игра окончена" : t;
  }

  function finalize() {
    const w = winner();
    if (!w) return false;
    finished = true;
    const outcome = w === "white" ? "win" : "loss";
    const score_delta = outcome === "win" ? 10 : 0;
    onResult({ type: "result", game: "checkers", outcome, score_delta });
    return true;
  }

  function onCell(r, c) {
    if (finished) return;
    if (!whiteTurn) return;
    const p = board[r][c];

    if (!selected) {
      if (!isWhite(p)) return;
      const ms = findMovesFor(r, c);
      if (!ms.length) return;
      setSelection(r, c);
      render();
      return;
    }

    // destination?
    const m = legal.get(`${r}:${c}`);
    if (m) {
      applyMove(m);
      clearSelection();
      if (finalize()) {
        render();
        return;
      }
      whiteTurn = false;
      botMove();
      finalize();
      render();
      return;
    }

    // change selection
    if (isWhite(p)) {
      setSelection(r, c);
      render();
      return;
    }

    clearSelection();
    render();
  }

  render();

  return {
    reset() {
      board = initialBoard();
      whiteTurn = true;
      selected = null;
      legal = new Map();
      finished = false;
      render();
    },
  };
}

