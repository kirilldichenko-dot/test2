/* global Chess */

export function createChessGame({ root, onResult }) {
  const chess = new Chess();
  let selected = null;
  let legalTargets = new Set();
  let finished = false;

  const boardEl = document.createElement("div");
  boardEl.className = "board";

  const infoEl = document.createElement("div");
  infoEl.className = "game-info";

  root.innerHTML = "";
  root.appendChild(boardEl);
  root.appendChild(infoEl);

  function pieceToChar(p) {
    if (!p) return "";
    const map = {
      p: "♟",
      r: "♜",
      n: "♞",
      b: "♝",
      q: "♛",
      k: "♚",
    };
    const m = map[p.type] || "";
    return p.color === "w" ? m.toUpperCase() : m;
  }

  function squareColor(file, rank) {
    const f = file.charCodeAt(0) - "a".charCodeAt(0);
    const r = rank - 1;
    return (f + r) % 2 === 0 ? "light" : "dark";
  }

  function render() {
    boardEl.innerHTML = "";

    const fenRows = chess.fen().split(" ")[0].split("/");
    const files = ["a", "b", "c", "d", "e", "f", "g", "h"];

    for (let r = 8; r >= 1; r--) {
      const rowFen = fenRows[8 - r];
      let fileIdx = 0;
      for (const ch of rowFen) {
        if (/\d/.test(ch)) {
          fileIdx += Number(ch);
          continue;
        }
        const file = files[fileIdx];
        const sq = `${file}${r}`;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `sq ${squareColor(file, r)}`;
        btn.dataset.sq = sq;

        const piece = chess.get(sq);
        btn.textContent = pieceToChar(piece);

        if (selected === sq) btn.classList.add("is-selected");
        if (legalTargets.has(sq)) btn.classList.add("is-move");

        btn.addEventListener("click", () => onSquare(sq));
        boardEl.appendChild(btn);
        fileIdx += 1;
      }
      // Fill empty squares (digits)
      // Rebuild row precisely by iterating again:
    }

    // Re-render correctly using chess.board()
    boardEl.innerHTML = "";
    const board = chess.board(); // 8x8 from 8th rank
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const rank = 8 - row;
        const file = String.fromCharCode("a".charCodeAt(0) + col);
        const sq = `${file}${rank}`;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `sq ${squareColor(file, rank)}`;
        btn.dataset.sq = sq;
        const piece = board[row][col];
        btn.textContent = pieceToChar(piece);
        if (selected === sq) btn.classList.add("is-selected");
        if (legalTargets.has(sq)) btn.classList.add("is-move");
        btn.addEventListener("click", () => onSquare(sq));
        boardEl.appendChild(btn);
      }
    }

    const turn = chess.turn() === "w" ? "Белые" : "Чёрные";
    const status = chess.isGameOver()
      ? "Игра окончена"
      : `Ход: ${turn}. Нажмите фигуру, затем клетку.`;
    infoEl.textContent = status;
  }

  function setSelection(sq) {
    selected = sq;
    legalTargets.clear();
    const moves = chess.moves({ square: sq, verbose: true });
    for (const m of moves) legalTargets.add(m.to);
  }

  function clearSelection() {
    selected = null;
    legalTargets.clear();
  }

  function botMove() {
    if (chess.isGameOver()) return;
    if (chess.turn() !== "b") return;
    const moves = chess.moves();
    if (!moves.length) return;
    const mv = moves[Math.floor(Math.random() * moves.length)];
    chess.move(mv);
  }

  function finalizeIfOver() {
    if (!chess.isGameOver() || finished) return;
    finished = true;
    let outcome = "draw";
    if (chess.isCheckmate()) {
      // Side to move is checkmated
      const sideToMove = chess.turn();
      outcome = sideToMove === "b" ? "win" : "loss"; // user is white vs bot black
    }
    const score_delta = outcome === "win" ? 10 : outcome === "draw" ? 3 : 0;
    onResult({ type: "result", game: "chess", outcome, score_delta });
  }

  function onSquare(sq) {
    if (finished) return;
    // user is always white, bot is black
    if (chess.turn() !== "w") return;

    const piece = chess.get(sq);
    if (!selected) {
      if (!piece || piece.color !== "w") return;
      setSelection(sq);
      render();
      return;
    }

    if (selected === sq) {
      clearSelection();
      render();
      return;
    }

    // attempt move
    const mv = chess.move({ from: selected, to: sq, promotion: "q" });
    if (!mv) {
      // maybe selecting another own piece
      if (piece && piece.color === "w") {
        setSelection(sq);
        render();
      }
      return;
    }

    clearSelection();
    botMove();
    finalizeIfOver();
    render();
  }

  render();

  return {
    reset() {
      chess.reset();
      selected = null;
      legalTargets.clear();
      finished = false;
      render();
    },
  };
}

