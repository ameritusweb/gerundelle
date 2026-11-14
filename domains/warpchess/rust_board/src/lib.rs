//! Fast Warp 1 Chess board implementation in Rust with PyO3 Python bindings.
//!
//! Provides WarpBoard with legal move generation, push/pop, attack detection,
//! check/checkmate detection, zobrist hashing, and FEN serialization.

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::collections::{HashMap, HashSet};
use std::sync::LazyLock;

mod types;
mod attacks;
mod board;
mod movegen;
mod fen;
mod search;
mod arrow_board;

use types::*;
use board::WarpBoardInner;
use arrow_board::ArrowBoardInner;

/// Python-exposed WarpMove
#[pyclass(frozen)]
#[derive(Clone, Debug)]
pub struct PyWarpMove {
    #[pyo3(get)]
    pub from_square: u8,
    #[pyo3(get)]
    pub to_square: u8,
    #[pyo3(get)]
    pub promotion: Option<u8>,
    #[pyo3(get)]
    pub flip_type: u8,
    #[pyo3(get)]
    pub flip_from: i16,
    #[pyo3(get)]
    pub flip_to: i16,
}

#[pymethods]
impl PyWarpMove {
    #[new]
    #[pyo3(signature = (from_square, to_square, promotion=None, flip_type=0, flip_from=-1, flip_to=-1))]
    fn new(from_square: u8, to_square: u8, promotion: Option<u8>,
           flip_type: u8, flip_from: i16, flip_to: i16) -> Self {
        Self { from_square, to_square, promotion, flip_type, flip_from, flip_to }
    }

    fn __repr__(&self) -> String {
        format!("PyWarpMove({} -> {} flip={} promo={:?})",
                self.from_square, self.to_square, self.flip_type, self.promotion)
    }

    fn __eq__(&self, other: &PyWarpMove) -> bool {
        self.from_square == other.from_square
            && self.to_square == other.to_square
            && self.promotion == other.promotion
            && self.flip_type == other.flip_type
            && self.flip_from == other.flip_from
            && self.flip_to == other.flip_to
    }

    fn __hash__(&self) -> u64 {
        let mut h: u64 = self.from_square as u64;
        h = h * 131 + self.to_square as u64;
        h = h * 131 + self.promotion.unwrap_or(0) as u64;
        h = h * 131 + self.flip_type as u64;
        h = h * 131 + self.flip_from as u64;
        h = h * 131 + self.flip_to as u64;
        h
    }
}

impl From<WarpMove> for PyWarpMove {
    fn from(m: WarpMove) -> Self {
        Self {
            from_square: m.from_sq,
            to_square: m.to_sq,
            promotion: m.promotion,
            flip_type: m.flip_type,
            flip_from: m.flip_from,
            flip_to: m.flip_to,
        }
    }
}

impl From<&PyWarpMove> for WarpMove {
    fn from(m: &PyWarpMove) -> Self {
        WarpMove {
            from_sq: m.from_square,
            to_sq: m.to_square,
            promotion: m.promotion,
            flip_type: m.flip_type,
            flip_from: m.flip_from,
            flip_to: m.flip_to,
        }
    }
}

/// Python-exposed WarpBoard
#[pyclass]
pub struct PyWarpBoard {
    inner: WarpBoardInner,
}

#[pymethods]
impl PyWarpBoard {
    #[new]
    fn new() -> Self {
        Self { inner: WarpBoardInner::new() }
    }

    #[staticmethod]
    fn starting_position() -> Self {
        Self { inner: WarpBoardInner::starting_position() }
    }

    #[staticmethod]
    fn from_fen(fen: &str) -> PyResult<Self> {
        fen::parse_fen(fen)
            .map(|inner| Self { inner })
            .map_err(|e| PyValueError::new_err(e))
    }

    fn to_fen(&self) -> String {
        fen::to_fen(&self.inner)
    }

    fn copy(&self) -> Self {
        Self { inner: self.inner.clone() }
    }

    #[getter]
    fn turn(&self) -> bool {
        self.inner.turn
    }

    // ── Setters and plain reads (added 2026-11-14 for Gerundelle's Warp chess domain, which sets a board's turn and en passant
    //    square to read what a side could do, as it did on the Python board; each write recomputes the hash) ──

    #[setter]
    fn set_turn(&mut self, v: bool) {
        self.inner.turn = v;
        self.inner.hash = self.inner.compute_hash();
    }

    #[getter]
    fn en_passant(&self) -> i16 {
        self.inner.en_passant
    }

    #[setter]
    fn set_en_passant(&mut self, v: i16) {
        self.inner.en_passant = v;
        self.inner.hash = self.inner.compute_hash();
    }

    #[getter]
    fn castling(&self) -> u8 {
        self.inner.castling
    }

    #[setter]
    fn set_castling(&mut self, v: u8) {
        self.inner.castling = v;
        self.inner.hash = self.inner.compute_hash();
    }

    #[getter]
    fn halfmove_clock(&self) -> u16 {
        self.inner.halfmove_clock
    }

    #[getter]
    fn fullmove_number(&self) -> u16 {
        self.inner.fullmove_number
    }

    /// (pieces, colors, origins), one entry per square (128); an empty square has piece 0 and origin 255.
    fn arrays(&self) -> (Vec<u8>, Vec<bool>, Vec<u8>) {
        (self.inner.pieces.to_vec(), self.inner.colors.to_vec(), self.inner.origins.to_vec())
    }

    /// A square set outright: piece 0 empties it. The kings' squares and the hash follow (set_piece_at keeps neither).
    fn set_square(&mut self, sq: u8, piece_type: u8, color: bool, orig_side: u8) {
        let s = sq as usize;
        if self.inner.pieces[s] == KING {
            let idx = if self.inner.colors[s] { 0 } else { 1 };
            if self.inner.king_sq[idx] == s as i16 {
                self.inner.king_sq[idx] = -1;
            }
        }
        if piece_type == 0 {
            self.inner.pieces[s] = 0;
            self.inner.colors[s] = false;
            self.inner.origins[s] = 255;
        } else {
            self.inner.set_piece_at(s, piece_type, color, orig_side);
        }
        self.inner.hash = self.inner.compute_hash();
    }

    /// The squares a colour's pieces press, each with the squares pressing it from (Gerundelle's Warp chess, plans.press and
    /// warpworld.WarpWorld.pressure): the colour's legal moves with the turn set to it and no en passant square, by where each move
    /// ends (a post-flip's flip square); a pawn's push and a king's or crab's two-square jump press nothing (they can't capture).
    /// need_kings: nothing is pressed on a board missing a king (plans.py: the game is over).
    #[pyo3(signature = (colour, need_kings=true))]
    fn press_map(&self, colour: bool, need_kings: bool) -> HashMap<u8, HashSet<u8>> {
        press_map(&self.inner, colour, need_kings)
    }

    /// Every square some move of `me`'s (turn set to me) would leave pressed by me, as press_map reads it after the move (plans.reach).
    fn reach(&self, me: bool) -> HashSet<u8> {
        let mut out = HashSet::new();
        if !both_kings(&self.inner) {
            return out;
        }
        let t = turned(&self.inner, me);
        for m in movegen::legal_moves(&t) {
            let mut c = t.clone();
            c.push(&m);
            out.extend(press_map(&c, me, true).into_keys());
        }
        out
    }

    /// The legal moves as plain tuples (from, to, promotion or 0, flip_type, flip_from, flip_to): cheaper to read than move objects.
    fn legal_move_tuples(&self) -> Vec<(u8, u8, u8, u8, i16, i16)> {
        movegen::legal_moves(&self.inner)
            .into_iter()
            .map(|m| {
                let p = PyWarpMove::from(m);
                (p.from_square, p.to_square, p.promotion.unwrap_or(0), p.flip_type, p.flip_from, p.flip_to)
            })
            .collect()
    }

    #[getter]
    fn legal_moves(&self) -> Vec<PyWarpMove> {
        movegen::legal_moves(&self.inner)
            .into_iter()
            .map(PyWarpMove::from)
            .collect()
    }

    fn push(&mut self, m: &PyWarpMove) {
        self.inner.push(&WarpMove::from(m));
    }

    fn pop(&mut self) {
        self.inner.pop();
    }

    fn is_game_over(&self) -> bool {
        self.inner.is_game_over()
    }

    fn is_checkmate(&self) -> bool {
        self.inner.is_checkmate()
    }

    fn is_stalemate(&self) -> bool {
        self.inner.is_stalemate()
    }

    fn is_capture(&self, m: &PyWarpMove) -> bool {
        self.inner.is_capture(&WarpMove::from(m))
    }

    fn is_king_capture(&self, m: &PyWarpMove) -> bool {
        self.inner.is_king_capture(&WarpMove::from(m))
    }

    fn gives_check(&self, m: &PyWarpMove) -> bool {
        self.inner.gives_check(&WarpMove::from(m))
    }

    fn is_in_check(&self, color: bool) -> bool {
        self.inner.is_in_check(color)
    }

    fn is_attacked_by(&self, sq: u8, attacker_color: bool) -> bool {
        self.inner.is_attacked_by(sq as usize, attacker_color)
    }

    fn find_checkers(&self, king_color: bool) -> Vec<u8> {
        self.inner.find_checkers(king_color).into_iter().map(|s| s as u8).collect()
    }

    fn is_repetition(&self, count: usize) -> bool {
        self.inner.is_repetition(count)
    }

    fn zobrist_hash(&self) -> u64 {
        self.inner.hash
    }

    fn result(&self) -> String {
        self.inner.result()
    }

    fn set_piece_at(&mut self, sq: u8, piece_type: u8, color: bool, orig_side: i8) {
        self.inner.set_piece_at(sq as usize, piece_type, color,
                                 if orig_side >= 0 { orig_side as u8 } else { (sq >> 6) as u8 });
    }

    fn piece_map(&self) -> HashMap<u8, (u8, bool)> {
        let mut m = HashMap::new();
        for sq in 0..TOTAL_SQUARES {
            if self.inner.pieces[sq] != 0 && is_playable(sq) {
                m.insert(sq as u8, (self.inner.pieces[sq], self.inner.colors[sq]));
            }
        }
        m
    }

    fn __repr__(&self) -> String {
        format!("PyWarpBoard({})", self.to_fen())
    }
}

/// Python-exposed ArrowRustBoard: per-square attack/defend/influence maps.
#[pyclass]
pub struct PyArrowBoard {
    inner: ArrowBoardInner,
}

#[pymethods]
impl PyArrowBoard {
    #[new]
    fn new(board: &PyWarpBoard) -> Self {
        Self { inner: ArrowBoardInner::new(board.inner.clone()) }
    }

    #[staticmethod]
    fn starting_position() -> Self {
        Self { inner: ArrowBoardInner::new(WarpBoardInner::starting_position()) }
    }

    fn push(&mut self, m: &PyWarpMove) {
        self.inner.push(&WarpMove::from(m));
    }

    fn pop(&mut self) {
        self.inner.pop();
    }

    #[getter]
    fn turn(&self) -> bool {
        self.inner.board.turn
    }

    #[getter]
    fn legal_moves(&self) -> Vec<PyWarpMove> {
        movegen::legal_moves(&self.inner.board)
            .into_iter()
            .map(PyWarpMove::from)
            .collect()
    }

    fn is_game_over(&self) -> bool {
        self.inner.board.is_game_over()
    }

    fn is_capture(&self, m: &PyWarpMove) -> bool {
        self.inner.board.is_capture(&WarpMove::from(m))
    }

    fn gives_check(&self, m: &PyWarpMove) -> bool {
        self.inner.board.gives_check(&WarpMove::from(m))
    }

    fn zobrist_hash(&self) -> u64 {
        self.inner.board.hash
    }

    /// Squares influenced by the piece at sq (attacks + reachable squares).
    fn influence_of(&self, sq: u8) -> Vec<u8> {
        self.inner.influence[sq as usize].clone()
    }

    /// White piece squares that influence sq (attack or defend it).
    fn white_control_of(&self, sq: u8) -> Vec<u8> {
        self.inner.white_control[sq as usize].clone()
    }

    /// Black piece squares that influence sq (attack or defend it).
    fn black_control_of(&self, sq: u8) -> Vec<u8> {
        self.inner.black_control[sq as usize].clone()
    }

    /// Squares piece type `pt` would threaten from `sq` given current board state.
    fn hyp_threats_of(&self, sq: u8, pt: u8) -> Vec<u8> {
        let sq = sq as usize;
        let pt = pt as usize;
        if pt < self.inner.hyp_threats[sq].len() {
            self.inner.hyp_threats[sq][pt].clone()
        } else {
            Vec::new()
        }
    }

    /// All piece types' hypothetical threats from sq: returns list of (pt, threatened_sq) pairs.
    fn all_hyp_threats_of(&self, sq: u8) -> Vec<(u8, u8)> {
        let sq = sq as usize;
        let mut out = Vec::new();
        for pt in 1..self.inner.hyp_threats[sq].len() {
            for &t in &self.inner.hyp_threats[sq][pt] {
                out.push((pt as u8, t));
            }
        }
        out
    }

    /// Min moves for piece at `attacker_sq` to reach a square from which it threatens `target_sq`.
    /// Returns (distance, staging_square). INF_DIST (255) = unreachable.
    fn min_moves_to_threaten(&self, attacker_sq: u8, target_sq: u8) -> (u8, u8) {
        let (d, s) = self.inner.min_moves_to_threaten(attacker_sq as usize, target_sq as usize);
        (d, s as u8)
    }

    /// Raw BFS distance for piece at `from_sq` to reach `to_sq` (empty-board, same side).
    fn distance(&self, from_sq: u8, to_sq: u8) -> u8 {
        self.inner.distance(from_sq as usize, to_sq as usize)
    }

    /// Per-square influence balance: positive = white dominates, negative = black.
    /// Returns a 128-length list of f32 in [-1, 1].
    fn influence_balance(&self) -> Vec<f32> {
        self.inner.influence_balance()
    }

    /// How many white and black pieces influence sq: (white_count, black_count).
    fn control_counts(&self, sq: u8) -> (usize, usize) {
        let sq = sq as usize;
        (self.inner.white_control[sq].len(), self.inner.black_control[sq].len())
    }
}

/// Python-exposed alpha-beta search.
/// Returns (score, best_move) where score is from side-to-move's perspective (centipawns).
#[pyfunction]
#[pyo3(signature = (board, depth=8))]
fn alphabeta_search(board: &mut PyWarpBoard, depth: i32) -> (i32, Option<PyWarpMove>) {
    let (score, best_move) = search::search_root(&mut board.inner, depth);
    (score, best_move.map(PyWarpMove::from))
}

/// Python-exposed static evaluation (centipawns from White's perspective).
#[pyfunction]
fn pst_eval(board: &PyWarpBoard) -> i32 {
    search::pst_evaluate(&board.inner)
}

/// Python-exposed alpha-beta eval (score from side-to-move, centipawns).
#[pyfunction]
#[pyo3(signature = (board, depth=8))]
fn alphabeta_eval(board: &mut PyWarpBoard, depth: i32) -> i32 {
    search::alphabeta_simple(&mut board.inner, depth)
}

#[pymodule]
fn warp_board(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyWarpMove>()?;
    m.add_class::<PyWarpBoard>()?;
    m.add_class::<PyArrowBoard>()?;
    m.add_function(wrap_pyfunction!(alphabeta_search, m)?)?;
    m.add_function(wrap_pyfunction!(pst_eval, m)?)?;
    m.add_function(wrap_pyfunction!(alphabeta_eval, m)?)?;

    // Constants
    m.add("PAWN", PAWN)?;
    m.add("KNIGHT", KNIGHT)?;
    m.add("BISHOP", BISHOP)?;
    m.add("ROOK", ROOK)?;
    m.add("QUEEN", QUEEN)?;
    m.add("KING", KING)?;
    m.add("CRAB", CRAB)?;
    m.add("WHITE", true)?;
    m.add("BLACK", false)?;
    m.add("NO_FLIP", NO_FLIP)?;
    m.add("PRE_FLIP", PRE_FLIP)?;
    m.add("POST_FLIP", POST_FLIP)?;
    m.add("LEFT", LEFT)?;
    m.add("RIGHT", RIGHT)?;

    Ok(())
}


// ── For Gerundelle's Warp chess domain (press_map, reach; 2026-11-14) ──

fn turned(b: &WarpBoardInner, colour: bool) -> WarpBoardInner {
    let mut c = b.clone();
    c.turn = colour;
    c.en_passant = -1;
    c.hash = c.compute_hash();
    c
}

fn both_kings(b: &WarpBoardInner) -> bool {
    let (mut w, mut k) = (false, false);
    for sq in 0..TOTAL_SQUARES {
        if b.pieces[sq] == KING {
            if b.colors[sq] { w = true } else { k = true }
        }
    }
    w && k
}

fn press_map(b: &WarpBoardInner, colour: bool, need_kings: bool) -> HashMap<u8, HashSet<u8>> {
    let mut out: HashMap<u8, HashSet<u8>> = HashMap::new();
    if need_kings && !both_kings(b) {
        return out;
    }
    let t = turned(b, colour);
    for m in movegen::legal_moves(&t) {
        let kind = t.pieces[m.from_sq as usize];
        let (f0, r0) = ((m.from_sq & 7) as i16, ((m.from_sq >> 3) & 7) as i16);
        let (f1, r1) = ((m.to_sq & 7) as i16, ((m.to_sq >> 3) & 7) as i16);
        let (d_file, d_rank) = ((f0 - f1).abs(), (r0 - r1).abs());
        if kind == PAWN && d_file == 0 {
            continue;
        }
        if (kind == KING || kind == CRAB) && (d_file == 2 || d_rank == 2) && (d_file == 0 || d_rank == 0) {
            continue;
        }
        let fin = if m.flip_type == POST_FLIP { m.flip_to as u8 } else { m.to_sq };
        out.entry(fin).or_default().insert(m.from_sq);
    }
    out
}
