// The WebAssembly board (pkg-node) against the known perft counts (as check_chessboard.py checks the native one).
// node check_wasm.cjs
const { WasmBoard } = require("./pkg-node/chess_board.js");

function perft(b, depth) {
  if (depth === 0) return 1;
  const m = b.legal_moves();
  if (depth === 1) return m.length / 3;
  let n = 0;
  for (let i = 0; i < m.length; i += 3) {
    const c = b.copy();
    c.push_move(m[i], m[i + 1], m[i + 2]);
    n += perft(c, depth - 1);
    c.free();
  }
  return n;
}

const cases = [
  ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 4, 197281],
  ["r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862],
  ["8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238],
  ["r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 3, 9467],
  ["rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62379],
];
let bad = 0;
const t0 = Date.now();
for (const [fen, d, want] of cases) {
  const b = WasmBoard.from_fen(fen);
  const got = perft(b, d);
  const ok = got === want;
  bad += !ok;
  console.log(`${ok ? "ok " : "BAD"} perft(${d}) ${got} (want ${want})  ${fen}`);
}
const b = WasmBoard.starting_position();
console.log("fen round trip:", b.to_fen(), "| hash:", b.zobrist_hash(), "| press_map bytes:", b.press_map(true, true).length);
console.log(bad ? `${bad} BAD` : "ALL OK", `(${Date.now() - t0} ms)`);
