//! Standard chess for Gerundelle's cognitivechess_v2: the interface of warp_board (Warp 1 Chess's Rust board) on one 8x8 board.
//!
//! Squares 0..63, a1 = 0, rank * 8 + file (python-chess's numbering). Pieces 1..6: pawn, knight, bishop, rook, queen, king (warp's
//! codes); colour true is White. Castling rights as warp's mask: WK 1, WQ 2, BK 4, BQ 8.
//!
//! The moves are every move that doesn't leave the mover's own king attacked. In any legal chess position these are exactly the legal
//! moves. On a position chess calls invalid (the side not to move in check, as on a board whose turn was handed over: PLAN.md), they
//! include taking that king, so a plan search reads "your king taken" as a gain, and checkmate as a king gain that can't be thwarted.
//! A board missing either king has no moves (the game is over): a line in a plan search stops there.

#[cfg(feature = "python")]
use pyo3::exceptions::PyValueError;
#[cfg(feature = "python")]
use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};
#[cfg(feature = "wasm")]
use wasm_bindgen::prelude::*;

const PAWN: u8 = 1;
const KNIGHT: u8 = 2;
const BISHOP: u8 = 3;
const ROOK: u8 = 4;
const QUEEN: u8 = 5;
const KING: u8 = 6;
const WK: u8 = 1;
const WQ: u8 = 2;
const BK: u8 = 4;
const BQ: u8 = 8;

const KNIGHT_D: [(i8, i8); 8] = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)];
const KING_D: [(i8, i8); 8] = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)];
const ROOK_D: [(i8, i8); 4] = [(1, 0), (0, 1), (-1, 0), (0, -1)];
const BISHOP_D: [(i8, i8); 4] = [(1, 1), (-1, 1), (-1, -1), (1, -1)];

fn file(sq: usize) -> i8 {
    (sq & 7) as i8
}
fn rank(sq: usize) -> i8 {
    (sq >> 3) as i8
}
fn at(f: i8, r: i8) -> Option<usize> {
    if (0..8).contains(&f) && (0..8).contains(&r) {
        Some((r * 8 + f) as usize)
    } else {
        None
    }
}

fn splitmix(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9E3779B97F4A7C15);
    let mut z = *state;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
    z ^ (z >> 31)
}

struct Zobrist {
    piece: [[u64; 64]; 12],
    turn: u64,
    castling: [u64; 16],
    ep: [u64; 8],
}

fn zobrist() -> &'static Zobrist {
    use std::sync::OnceLock;
    static Z: OnceLock<Zobrist> = OnceLock::new();
    Z.get_or_init(|| {
        let mut s = 0x5EED_C4E5_5u64;
        let mut piece = [[0u64; 64]; 12];
        for p in piece.iter_mut() {
            for q in p.iter_mut() {
                *q = splitmix(&mut s);
            }
        }
        let turn = splitmix(&mut s);
        let mut castling = [0u64; 16];
        for c in castling.iter_mut() {
            *c = splitmix(&mut s);
        }
        let mut ep = [0u64; 8];
        for e in ep.iter_mut() {
            *e = splitmix(&mut s);
        }
        Zobrist { piece, turn, castling, ep }
    })
}

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
struct Mv {
    from: u8,
    to: u8,
    promo: u8,
}

#[derive(Clone)]
struct Inner {
    pieces: [u8; 64],
    colors: [bool; 64],
    turn: bool,
    castling: u8,
    ep: i16,
    halfmove: u16,
    fullmove: u16,
    hash: u64,
}

impl Inner {
    fn empty() -> Self {
        Inner { pieces: [0; 64], colors: [false; 64], turn: true, castling: 0, ep: -1, halfmove: 0, fullmove: 1, hash: 0 }
    }

    fn compute_hash(&self) -> u64 {
        let z = zobrist();
        let mut h = 0u64;
        for sq in 0..64 {
            let p = self.pieces[sq];
            if p != 0 {
                let idx = (p as usize - 1) + if self.colors[sq] { 0 } else { 6 };
                h ^= z.piece[idx][sq];
            }
        }
        if self.turn {
            h ^= z.turn;
        }
        h ^= z.castling[(self.castling & 15) as usize];
        if self.ep >= 0 {
            h ^= z.ep[(self.ep & 7) as usize];
        }
        h
    }

    fn rehash(&mut self) {
        self.hash = self.compute_hash();
    }

    fn king_sq(&self, colour: bool) -> Option<usize> {
        (0..64).find(|&sq| self.pieces[sq] == KING && self.colors[sq] == colour)
    }

    fn mine(&self, sq: usize, colour: bool) -> bool {
        self.pieces[sq] != 0 && self.colors[sq] == colour
    }

    fn theirs(&self, sq: usize, colour: bool) -> bool {
        self.pieces[sq] != 0 && self.colors[sq] != colour
    }

    /// Whether `sq` is attacked by a piece of `by` (pseudo-legal: pins don't matter, as in chess's check rule).
    fn attacked_by(&self, sq: usize, by: bool) -> bool {
        let (f, r) = (file(sq), rank(sq));
        for &(df, dr) in KNIGHT_D.iter() {
            if let Some(s) = at(f + df, r + dr) {
                if self.pieces[s] == KNIGHT && self.colors[s] == by {
                    return true;
                }
            }
        }
        for &(df, dr) in KING_D.iter() {
            if let Some(s) = at(f + df, r + dr) {
                if self.pieces[s] == KING && self.colors[s] == by {
                    return true;
                }
            }
        }
        let pr = if by { r - 1 } else { r + 1 };   // a pawn of `by` attacking sq stands one rank behind it
        for df in [-1i8, 1] {
            if let Some(s) = at(f + df, pr) {
                if self.pieces[s] == PAWN && self.colors[s] == by {
                    return true;
                }
            }
        }
        for (dirs, a, b) in [(&ROOK_D, ROOK, QUEEN), (&BISHOP_D, BISHOP, QUEEN)] {
            for &(df, dr) in dirs.iter() {
                let (mut x, mut y) = (f + df, r + dr);
                while let Some(s) = at(x, y) {
                    let p = self.pieces[s];
                    if p != 0 {
                        if self.colors[s] == by && (p == a || p == b) {
                            return true;
                        }
                        break;
                    }
                    x += df;
                    y += dr;
                }
            }
        }
        false
    }

    fn in_check(&self, colour: bool) -> bool {
        match self.king_sq(colour) {
            Some(k) => self.attacked_by(k, !colour),
            None => false,
        }
    }

    /// Pseudo-legal moves of the side to move (castling checked for empty and unattacked squares here).
    fn pseudo(&self) -> Vec<Mv> {
        let c = self.turn;
        let mut out = Vec::with_capacity(48);
        for sq in 0..64 {
            if !self.mine(sq, c) {
                continue;
            }
            let (f, r) = (file(sq), rank(sq));
            match self.pieces[sq] {
                PAWN => {
                    let dir: i8 = if c { 1 } else { -1 };
                    let last: i8 = if c { 7 } else { 0 };
                    let start: i8 = if c { 1 } else { 6 };
                    let add = |to: usize, out: &mut Vec<Mv>| {
                        if rank(to) == last {
                            for p in [QUEEN, ROOK, BISHOP, KNIGHT] {
                                out.push(Mv { from: sq as u8, to: to as u8, promo: p });
                            }
                        } else {
                            out.push(Mv { from: sq as u8, to: to as u8, promo: 0 });
                        }
                    };
                    if let Some(t) = at(f, r + dir) {
                        if self.pieces[t] == 0 {
                            add(t, &mut out);
                            if r == start {
                                if let Some(t2) = at(f, r + 2 * dir) {
                                    if self.pieces[t2] == 0 {
                                        add(t2, &mut out);
                                    }
                                }
                            }
                        }
                    }
                    for df in [-1i8, 1] {
                        if let Some(t) = at(f + df, r + dir) {
                            if self.theirs(t, c) || (self.ep == t as i16 && self.pieces[t] == 0) {
                                add(t, &mut out);
                            }
                        }
                    }
                }
                KNIGHT | KING => {
                    let ds: &[(i8, i8); 8] = if self.pieces[sq] == KNIGHT { &KNIGHT_D } else { &KING_D };
                    for &(df, dr) in ds.iter() {
                        if let Some(t) = at(f + df, r + dr) {
                            if !self.mine(t, c) {
                                out.push(Mv { from: sq as u8, to: t as u8, promo: 0 });
                            }
                        }
                    }
                }
                p => {
                    let dirs: Vec<(i8, i8)> = match p {
                        BISHOP => BISHOP_D.to_vec(),
                        ROOK => ROOK_D.to_vec(),
                        _ => ROOK_D.iter().chain(BISHOP_D.iter()).copied().collect(),
                    };
                    for (df, dr) in dirs {
                        let (mut x, mut y) = (f + df, r + dr);
                        while let Some(t) = at(x, y) {
                            if self.mine(t, c) {
                                break;
                            }
                            out.push(Mv { from: sq as u8, to: t as u8, promo: 0 });
                            if self.pieces[t] != 0 {
                                break;
                            }
                            x += df;
                            y += dr;
                        }
                    }
                }
            }
        }
        // castling: the king on its home square, the rook on its corner, the squares between empty, the king not in check and not
        // passing or landing on an attacked square
        let (home, kr, qr, kf, qf) = if c { (4usize, WK, WQ, 7usize, 0usize) } else { (60usize, BK, BQ, 63usize, 56usize) };
        if self.pieces[home] == KING && self.colors[home] == c && !self.attacked_by(home, !c) {
            if self.castling & kr != 0 && self.pieces[kf] == ROOK && self.colors[kf] == c
                && self.pieces[home + 1] == 0 && self.pieces[home + 2] == 0
                && !self.attacked_by(home + 1, !c) && !self.attacked_by(home + 2, !c)
            {
                out.push(Mv { from: home as u8, to: (home + 2) as u8, promo: 0 });
            }
            if self.castling & qr != 0 && self.pieces[qf] == ROOK && self.colors[qf] == c
                && self.pieces[home - 1] == 0 && self.pieces[home - 2] == 0 && self.pieces[home - 3] == 0
                && !self.attacked_by(home - 1, !c) && !self.attacked_by(home - 2, !c)
            {
                out.push(Mv { from: home as u8, to: (home - 2) as u8, promo: 0 });
            }
        }
        out
    }

    /// Every move that doesn't leave the mover's own king attacked (PLAN.md: exactly chess's legal moves in a legal position; on a
    /// turned board they include taking the opponent's king). A side without a king has no moves, and none are made against a board
    /// missing either king: the game is over.
    fn moves(&self) -> Vec<Mv> {
        if self.king_sq(true).is_none() || self.king_sq(false).is_none() {
            return Vec::new();
        }
        let c = self.turn;
        self.pseudo()
            .into_iter()
            .filter(|m| {
                let mut b = self.clone();
                b.apply(*m);
                match b.king_sq(c) {
                    Some(k) => !b.attacked_by(k, !c),
                    None => false,
                }
            })
            .collect()
    }

    /// A move made (no legality check), the clocks, rights, en passant square, turn and hash updated.
    fn apply(&mut self, m: Mv) {
        let (from, to) = (m.from as usize, m.to as usize);
        let p = self.pieces[from];
        let c = self.colors[from];
        let mut capture = self.pieces[to] != 0;
        if p == PAWN && to as i16 == self.ep && self.pieces[to] == 0 && file(from) != file(to) {
            let behind = if c { to - 8 } else { to + 8 };
            self.pieces[behind] = 0;
            self.colors[behind] = false;
            capture = true;
        }
        self.pieces[to] = if m.promo != 0 { m.promo } else { p };
        self.colors[to] = c;
        self.pieces[from] = 0;
        self.colors[from] = false;
        if p == KING && (file(from) - file(to)).abs() == 2 {
            let (rf, rt) = if file(to) == 6 { (to + 1, to - 1) } else { (to - 2, to + 1) };
            self.pieces[rt] = self.pieces[rf];
            self.colors[rt] = self.colors[rf];
            self.pieces[rf] = 0;
            self.colors[rf] = false;
        }
        for sq in [from, to] {
            match sq {
                4 => self.castling &= !(WK | WQ),
                60 => self.castling &= !(BK | BQ),
                0 => self.castling &= !WQ,
                7 => self.castling &= !WK,
                56 => self.castling &= !BQ,
                63 => self.castling &= !BK,
                _ => {}
            }
        }
        self.ep = if p == PAWN && (rank(from) - rank(to)).abs() == 2 { ((from + to) / 2) as i16 } else { -1 };
        self.halfmove = if p == PAWN || capture { 0 } else { self.halfmove + 1 };
        if !self.turn {
            self.fullmove += 1;
        }
        self.turn = !self.turn;
        self.rehash();
    }

    fn game_over(&self) -> bool {
        self.moves().is_empty()
    }

    fn result(&self) -> String {
        let (wk, bk) = (self.king_sq(true).is_some(), self.king_sq(false).is_some());
        if !wk || !bk {
            return if wk { "1-0".into() } else if bk { "0-1".into() } else { "*".into() };
        }
        if !self.moves().is_empty() {
            return "*".into();
        }
        if self.in_check(self.turn) {
            if self.turn { "0-1".into() } else { "1-0".into() }
        } else {
            "1/2-1/2".into()
        }
    }

    fn turned(&self, colour: bool) -> Inner {
        let mut t = self.clone();
        t.turn = colour;
        t.ep = -1;
        t.rehash();
        t
    }

    /// warp_board's press_map: a colour's moves with the turn set to it and no en passant square, by landing square; a pawn's push and
    /// a castling king's two-square move press nothing (they can't capture).
    fn press_map(&self, colour: bool, need_kings: bool) -> HashMap<u8, HashSet<u8>> {
        let mut out: HashMap<u8, HashSet<u8>> = HashMap::new();
        if need_kings && (self.king_sq(true).is_none() || self.king_sq(false).is_none()) {
            return out;
        }
        let t = self.turned(colour);
        for m in t.moves() {
            let (from, to) = (m.from as usize, m.to as usize);
            let p = t.pieces[from];
            if p == PAWN && file(from) == file(to) {
                continue;
            }
            if p == KING && (file(from) - file(to)).abs() == 2 {
                continue;
            }
            out.entry(m.to).or_default().insert(m.from);
        }
        out
    }

    fn to_fen(&self) -> String {
        let mut s = String::new();
        for r in (0..8).rev() {
            let mut empty = 0;
            for f in 0..8 {
                let sq = r * 8 + f;
                let p = self.pieces[sq];
                if p == 0 {
                    empty += 1;
                    continue;
                }
                if empty > 0 {
                    s.push_str(&empty.to_string());
                    empty = 0;
                }
                let ch = b"?pnbrqk"[p as usize] as char;
                s.push(if self.colors[sq] { ch.to_ascii_uppercase() } else { ch });
            }
            if empty > 0 {
                s.push_str(&empty.to_string());
            }
            if r > 0 {
                s.push('/');
            }
        }
        s.push(' ');
        s.push(if self.turn { 'w' } else { 'b' });
        s.push(' ');
        let mut cr = String::new();
        for (bit, ch) in [(WK, 'K'), (WQ, 'Q'), (BK, 'k'), (BQ, 'q')] {
            if self.castling & bit != 0 {
                cr.push(ch);
            }
        }
        s.push_str(if cr.is_empty() { "-" } else { &cr });
        s.push(' ');
        if self.ep >= 0 {
            let e = self.ep as usize;
            s.push((b'a' + (e & 7) as u8) as char);
            s.push((b'1' + (e >> 3) as u8) as char);
        } else {
            s.push('-');
        }
        s.push_str(&format!(" {} {}", self.halfmove, self.fullmove));
        s
    }

    fn from_fen(fen: &str) -> Result<Inner, String> {
        let parts: Vec<&str> = fen.split_whitespace().collect();
        if parts.is_empty() {
            return Err("empty FEN".into());
        }
        let mut b = Inner::empty();
        let rows: Vec<&str> = parts[0].split('/').collect();
        if rows.len() != 8 {
            return Err(format!("FEN needs 8 ranks: {fen}"));
        }
        for (i, row) in rows.iter().enumerate() {
            let r = 7 - i;
            let mut f = 0usize;
            for ch in row.chars() {
                if let Some(d) = ch.to_digit(10) {
                    f += d as usize;
                    continue;
                }
                let p = match ch.to_ascii_lowercase() {
                    'p' => PAWN,
                    'n' => KNIGHT,
                    'b' => BISHOP,
                    'r' => ROOK,
                    'q' => QUEEN,
                    'k' => KING,
                    _ => return Err(format!("bad piece {ch} in {fen}")),
                };
                if f > 7 {
                    return Err(format!("rank too long in {fen}"));
                }
                b.pieces[r * 8 + f] = p;
                b.colors[r * 8 + f] = ch.is_ascii_uppercase();
                f += 1;
            }
        }
        b.turn = parts.get(1).map(|t| *t != "b").unwrap_or(true);
        if let Some(cs) = parts.get(2) {
            for ch in cs.chars() {
                b.castling |= match ch {
                    'K' => WK,
                    'Q' => WQ,
                    'k' => BK,
                    'q' => BQ,
                    _ => 0,
                };
            }
        }
        if let Some(e) = parts.get(3) {
            let e = e.as_bytes();
            if e.len() == 2 {
                b.ep = ((e[1] - b'1') as i16) * 8 + (e[0] - b'a') as i16;
            }
        }
        b.halfmove = parts.get(4).and_then(|x| x.parse().ok()).unwrap_or(0);
        b.fullmove = parts.get(5).and_then(|x| x.parse().ok()).unwrap_or(1);
        b.rehash();
        Ok(b)
    }
}

#[cfg(feature = "python")]
#[pyclass]
#[derive(Clone)]
pub struct ChessBoard {
    inner: Inner,
}

#[cfg(feature = "python")]
#[pymethods]
impl ChessBoard {
    #[new]
    fn new() -> Self {
        Self::starting_position()
    }

    #[staticmethod]
    fn starting_position() -> Self {
        ChessBoard { inner: Inner::from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap() }
    }

    #[staticmethod]
    fn from_fen(fen: &str) -> PyResult<Self> {
        Inner::from_fen(fen).map(|inner| ChessBoard { inner }).map_err(PyValueError::new_err)
    }

    fn to_fen(&self) -> String {
        self.inner.to_fen()
    }

    fn copy(&self) -> Self {
        self.clone()
    }

    #[getter]
    fn turn(&self) -> bool {
        self.inner.turn
    }

    #[setter]
    fn set_turn(&mut self, v: bool) {
        self.inner.turn = v;
        self.inner.rehash();
    }

    #[getter]
    fn castling(&self) -> u8 {
        self.inner.castling
    }

    #[setter]
    fn set_castling(&mut self, v: u8) {
        self.inner.castling = v;
        self.inner.rehash();
    }

    #[getter]
    fn en_passant(&self) -> i16 {
        self.inner.ep
    }

    #[setter]
    fn set_en_passant(&mut self, v: i16) {
        self.inner.ep = v;
        self.inner.rehash();
    }

    #[getter]
    fn halfmove_clock(&self) -> u16 {
        self.inner.halfmove
    }

    #[getter]
    fn fullmove_number(&self) -> u16 {
        self.inner.fullmove
    }

    /// (pieces, colors, origins), 64 each; an empty square has piece 0 and origin 255; an occupied one origin 0 (one board).
    fn arrays(&self) -> (Vec<u8>, Vec<bool>, Vec<u8>) {
        let origins = self.inner.pieces.iter().map(|&p| if p == 0 { 255 } else { 0 }).collect();
        (self.inner.pieces.to_vec(), self.inner.colors.to_vec(), origins)
    }

    /// A square set outright: piece 0 empties it.
    #[pyo3(signature = (sq, piece_type, color, orig_side=0))]
    fn set_square(&mut self, sq: u8, piece_type: u8, color: bool, orig_side: u8) {
        let _ = orig_side;
        let s = sq as usize;
        self.inner.pieces[s] = piece_type;
        self.inner.colors[s] = piece_type != 0 && color;
        self.inner.rehash();
    }

    /// The moves as (from, to, promotion or 0, 0, -1, -1): warp_board's tuple shape, with no flips.
    fn legal_move_tuples(&self) -> Vec<(u8, u8, u8, u8, i16, i16)> {
        self.inner.moves().into_iter().map(|m| (m.from, m.to, m.promo, 0, -1, -1)).collect()
    }

    #[pyo3(signature = (from_square, to_square, promotion=0))]
    fn push_move(&mut self, from_square: u8, to_square: u8, promotion: u8) {
        self.inner.apply(Mv { from: from_square, to: to_square, promo: promotion });
    }

    #[pyo3(signature = (colour, need_kings=true))]
    fn press_map(&self, colour: bool, need_kings: bool) -> HashMap<u8, HashSet<u8>> {
        self.inner.press_map(colour, need_kings)
    }

    /// Every square some move of `me`'s (turn set to me) would leave pressed by me, as press_map reads it after the move.
    fn reach(&self, me: bool) -> HashSet<u8> {
        let mut out = HashSet::new();
        if self.inner.king_sq(true).is_none() || self.inner.king_sq(false).is_none() {
            return out;
        }
        let t = self.inner.turned(me);
        for m in t.moves() {
            let mut c = t.clone();
            c.apply(m);
            out.extend(c.press_map(me, true).into_keys());
        }
        out
    }

    fn zobrist_hash(&self) -> u64 {
        self.inner.hash
    }

    fn is_attacked_by(&self, sq: u8, attacker_color: bool) -> bool {
        self.inner.attacked_by(sq as usize, attacker_color)
    }

    fn is_in_check(&self, color: bool) -> bool {
        self.inner.in_check(color)
    }

    fn is_game_over(&self) -> bool {
        self.inner.game_over()
    }

    fn is_checkmate(&self) -> bool {
        self.inner.moves().is_empty() && self.inner.in_check(self.inner.turn)
    }

    fn is_stalemate(&self) -> bool {
        self.inner.king_sq(true).is_some() && self.inner.king_sq(false).is_some()
            && self.inner.moves().is_empty() && !self.inner.in_check(self.inner.turn)
    }

    fn result(&self) -> String {
        self.inner.result()
    }

    fn __repr__(&self) -> String {
        format!("ChessBoard({})", self.inner.to_fen())
    }
}

#[cfg(feature = "python")]
#[pymodule]
fn chess_board(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ChessBoard>()?;
    Ok(())
}

/// The same board for the browser (site/chess): wasm-bindgen bindings, each method the pyo3 class's, with flat returns a JS bridge
/// carries cheaply. Read by site/chess's Python shim (chess_board.py in the bundle), which gives rustboard.py the pyo3 interface.
#[cfg(feature = "wasm")]
#[wasm_bindgen]
#[derive(Clone)]
pub struct WasmBoard {
    inner: Inner,
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
impl WasmBoard {
    pub fn starting_position() -> WasmBoard {
        WasmBoard { inner: Inner::from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").unwrap() }
    }

    pub fn from_fen(fen: &str) -> Result<WasmBoard, JsValue> {
        Inner::from_fen(fen).map(|inner| WasmBoard { inner }).map_err(|e| JsValue::from_str(&e))
    }

    pub fn to_fen(&self) -> String {
        self.inner.to_fen()
    }

    pub fn copy(&self) -> WasmBoard {
        self.clone()
    }

    pub fn turn(&self) -> bool {
        self.inner.turn
    }

    pub fn set_turn(&mut self, v: bool) {
        self.inner.turn = v;
        self.inner.rehash();
    }

    pub fn castling(&self) -> u8 {
        self.inner.castling
    }

    pub fn set_castling(&mut self, v: u8) {
        self.inner.castling = v;
        self.inner.rehash();
    }

    pub fn en_passant(&self) -> i16 {
        self.inner.ep
    }

    pub fn set_en_passant(&mut self, v: i16) {
        self.inner.ep = v;
        self.inner.rehash();
    }

    pub fn halfmove_clock(&self) -> u16 {
        self.inner.halfmove
    }

    pub fn fullmove_number(&self) -> u16 {
        self.inner.fullmove
    }

    /// pieces then colours, 128 bytes: 64 piece codes (0 empty), 64 colours (1 White)
    pub fn arrays(&self) -> Vec<u8> {
        let mut out = self.inner.pieces.to_vec();
        out.extend(self.inner.colors.iter().map(|&c| c as u8));
        out
    }

    pub fn set_square(&mut self, sq: u8, piece_type: u8, color: bool) {
        let s = sq as usize;
        self.inner.pieces[s] = piece_type;
        self.inner.colors[s] = piece_type != 0 && color;
        self.inner.rehash();
    }

    /// the moves, flat: from, to, promotion (0 none), three bytes each
    pub fn legal_moves(&self) -> Vec<u8> {
        self.inner.moves().into_iter().flat_map(|m| [m.from, m.to, m.promo]).collect()
    }

    pub fn push_move(&mut self, from_square: u8, to_square: u8, promotion: u8) {
        self.inner.apply(Mv { from: from_square, to: to_square, promo: promotion });
    }

    /// press_map, flat: for each pressed square, the square, the number of its sources, the sources
    pub fn press_map(&self, colour: bool, need_kings: bool) -> Vec<u8> {
        let mut out = Vec::new();
        for (t, srcs) in self.inner.press_map(colour, need_kings) {
            out.push(t);
            out.push(srcs.len() as u8);
            out.extend(srcs);
        }
        out
    }

    pub fn reach(&self, me: bool) -> Vec<u8> {
        let mut out = HashSet::new();
        if self.inner.king_sq(true).is_none() || self.inner.king_sq(false).is_none() {
            return Vec::new();
        }
        let t = self.inner.turned(me);
        for m in t.moves() {
            let mut c = t.clone();
            c.apply(m);
            out.extend(c.press_map(me, true).into_keys());
        }
        out.into_iter().collect()
    }

    /// the position's hash as a decimal string (a u64 is past what a JS number holds exactly)
    pub fn zobrist_hash(&self) -> String {
        self.inner.hash.to_string()
    }

    pub fn is_attacked_by(&self, sq: u8, attacker_color: bool) -> bool {
        self.inner.attacked_by(sq as usize, attacker_color)
    }

    pub fn is_in_check(&self, color: bool) -> bool {
        self.inner.in_check(color)
    }

    pub fn is_game_over(&self) -> bool {
        self.inner.game_over()
    }

    pub fn is_checkmate(&self) -> bool {
        self.inner.moves().is_empty() && self.inner.in_check(self.inner.turn)
    }

    pub fn is_stalemate(&self) -> bool {
        self.inner.king_sq(true).is_some() && self.inner.king_sq(false).is_some()
            && self.inner.moves().is_empty() && !self.inner.in_check(self.inner.turn)
    }

    pub fn result(&self) -> String {
        self.inner.result()
    }
}
