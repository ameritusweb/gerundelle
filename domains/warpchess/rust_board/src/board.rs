//! WarpBoard: game state, push/pop, attack detection, game queries.

use crate::types::*;
use crate::attacks::*;

/// Zobrist keys (deterministic, matching Python implementation)
struct ZobristKeys {
    piece: [[u64; NUM_PIECE_TYPES * 2]; TOTAL_SQUARES],
    side: u64,
    castling: [u64; 16],
    ep: [u64; TOTAL_SQUARES + 1],
}

fn make_zobrist() -> ZobristKeys {
    // Simple deterministic PRNG matching Python's Random(0x57415250)
    // We use a basic xorshift for reproducibility
    let mut state: u64 = 0x57415250;
    let mut next = move || -> u64 {
        // xorshift64
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        state
    };

    let mut keys = ZobristKeys {
        piece: [[0u64; NUM_PIECE_TYPES * 2]; TOTAL_SQUARES],
        side: 0,
        castling: [0u64; 16],
        ep: [0u64; TOTAL_SQUARES + 1],
    };

    for sq in 0..TOTAL_SQUARES {
        for pc in 0..NUM_PIECE_TYPES * 2 {
            keys.piece[sq][pc] = next();
        }
    }
    keys.side = next();
    for i in 0..16 {
        keys.castling[i] = next();
    }
    for i in 0..=TOTAL_SQUARES {
        keys.ep[i] = next();
    }
    keys
}

use std::sync::LazyLock;
static ZOBRIST: LazyLock<ZobristKeys> = LazyLock::new(make_zobrist);

#[inline]
fn piece_code(pt: u8, color: bool) -> usize {
    let c = if color { 0 } else { NUM_PIECE_TYPES };
    c + pt as usize - 1
}

/// Undo information for one move
#[derive(Clone)]
pub struct UndoInfo {
    pub square_changes: Vec<(usize, u8, bool, u8)>, // (sq, piece, color, origin)
    pub turn: bool,
    pub castling: u8,
    pub en_passant: i16,
    pub halfmove_clock: u16,
    pub hash: u64,
    pub king_sq: [i16; 2], // [white, black]
}

#[derive(Clone)]
pub struct WarpBoardInner {
    pub pieces: [u8; TOTAL_SQUARES],
    pub colors: [bool; TOTAL_SQUARES],
    pub origins: [u8; TOTAL_SQUARES], // 0=LEFT, 1=RIGHT, 255=none
    pub turn: bool,    // true=WHITE
    pub castling: u8,
    pub en_passant: i16, // -1 = none
    pub halfmove_clock: u16,
    pub fullmove_number: u16,
    pub hash: u64,
    pub king_sq: [i16; 2], // [white_king_sq, black_king_sq]
    undo_stack: Vec<UndoInfo>,
    move_stack: Vec<WarpMove>,
}

impl WarpBoardInner {
    /// A king's 2-square move from e1 along rank 1 is castling only when castling is possible: the side still has the right for that
    /// wing, its rook stands on the corner, and the squares between are empty. Otherwise it is the king's 2-square jump and no rook
    /// moves. Ported 2026-11-13 from the Python board's _is_castle (its 2026-11-06 fix); before, any such move was treated as castling,
    /// rights or not, and the corner piece (in one checked position Black's king on h1) was moved to f1.
    pub fn is_castle(&self, m: &WarpMove, pt: u8, color: bool) -> bool {
        if pt != KING || m.flip_type == PRE_FLIP {
            return false;
        }
        let from = m.from_sq as usize;
        let to = m.to_sq as usize;
        let (ff, ft) = (from & 7, to & 7);
        if !((ff as i32 - ft as i32).unsigned_abs() == 2 && ff == 4 && square_rank(from) == 0 && (from >> 6) == (to >> 6)) {
            return false;
        }
        let base = (from >> 6) * 64;
        let (right, corner, between): (u8, usize, &[usize]) = if ft == 6 {
            (if color { WK } else { BK }, base + 7, &[5, 6])
        } else {
            (if color { WQ } else { BQ }, base, &[1, 2, 3])
        };
        self.castling & right != 0 && self.pieces[corner] == ROOK && self.colors[corner] == color
            && between.iter().all(|&k| self.pieces[base + k] == 0)
    }

    pub fn new() -> Self {
        Self {
            pieces: [0; TOTAL_SQUARES],
            colors: [false; TOTAL_SQUARES],
            origins: [255; TOTAL_SQUARES],
            turn: true,
            castling: 0,
            en_passant: -1,
            halfmove_clock: 0,
            fullmove_number: 1,
            hash: 0,
            king_sq: [-1, -1],
            undo_stack: Vec::new(),
            move_stack: Vec::new(),
        }
    }

    pub fn starting_position() -> Self {
        let mut b = Self::new();
        let back_rank = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK];
        let pawn_ranks: [usize; 8] = [1, 2, 3, 4, 4, 3, 2, 1]; // chevron
        // White on LEFT
        for f in 0..8 {
            let sq_back = square(LEFT, f, 0);
            b.pieces[sq_back] = back_rank[f];
            b.colors[sq_back] = true;
            b.origins[sq_back] = LEFT;
            let sq_pawn = square(LEFT, f, pawn_ranks[f]);
            b.pieces[sq_pawn] = PAWN;
            b.colors[sq_pawn] = true;
            b.origins[sq_pawn] = LEFT;
        }
        // Black on RIGHT
        for f in 0..8 {
            let sq_back = square(RIGHT, f, 0);
            b.pieces[sq_back] = back_rank[f];
            b.colors[sq_back] = false;
            b.origins[sq_back] = RIGHT;
            let sq_pawn = square(RIGHT, f, pawn_ranks[f]);
            b.pieces[sq_pawn] = PAWN;
            b.colors[sq_pawn] = false;
            b.origins[sq_pawn] = RIGHT;
        }
        b.castling = WK | WQ | BK | BQ;
        b.king_sq[0] = square(LEFT, 4, 0) as i16;  // white
        b.king_sq[1] = square(RIGHT, 4, 0) as i16; // black
        b.hash = b.compute_hash();
        b
    }

    pub fn set_piece_at(&mut self, sq: usize, pt: u8, color: bool, orig: u8) {
        self.pieces[sq] = pt;
        self.colors[sq] = color;
        self.origins[sq] = orig;
        if pt == KING {
            let idx = if color { 0 } else { 1 };
            self.king_sq[idx] = sq as i16;
        }
    }

    pub fn compute_hash(&self) -> u64 {
        let z = &*ZOBRIST;
        let mut h: u64 = 0;
        for sq in 0..TOTAL_SQUARES {
            if self.pieces[sq] != 0 && is_playable(sq) {
                h ^= z.piece[sq][piece_code(self.pieces[sq], self.colors[sq])];
            }
        }
        if !self.turn {
            h ^= z.side;
        }
        h ^= z.castling[self.castling as usize];
        let ep_idx = if self.en_passant >= 0 { self.en_passant as usize } else { TOTAL_SQUARES };
        h ^= z.ep[ep_idx];
        h
    }

    // ── Side occupancy (bitmask for one board side) ──

    fn side_occupancy(&self, side: u8) -> u64 {
        let base = side as usize * 64;
        let mut occ: u64 = 0;
        for local in 0..64usize {
            if self.pieces[base + local] != 0 {
                occ |= 1u64 << local;
            }
        }
        occ
    }

    // ── Attack detection ──

    pub fn is_attacked_by(&self, sq: usize, attacker_color: bool) -> bool {
        let side = square_side(sq);
        let local = sq & 63;
        let base = side as usize * 64;

        // Knight
        for &ksq in &KNIGHT_ATTACKS[local] {
            let gsq = base + ksq as usize;
            if self.pieces[gsq] == KNIGHT && self.colors[gsq] == attacker_color {
                return true;
            }
        }

        // King / Crab
        for &ksq in &KING_ATTACKS[local] {
            let gsq = base + ksq as usize;
            let p = self.pieces[gsq];
            if (p == KING || p == CRAB) && self.colors[gsq] == attacker_color {
                return true;
            }
        }

        // Pawn
        let r = local >> 3;
        let f = local & 7;
        for df in [-1i32, 1] {
            let nf = f as i32 + df;
            if nf < 0 || nf >= 8 { continue; }
            // Pawn below attacking upward
            if r > 0 {
                let gsq = base + (r - 1) * 8 + nf as usize;
                if self.pieces[gsq] == PAWN && self.colors[gsq] == attacker_color
                    && self.origins[gsq] == side {
                    return true;
                }
            }
            // Pawn above attacking downward
            if r + 1 < BOARD_RANKS {
                let gsq = base + (r + 1) * 8 + nf as usize;
                if self.pieces[gsq] == PAWN && self.colors[gsq] == attacker_color
                    && self.origins[gsq] != side {
                    return true;
                }
            }
        }

        // Sliding: bishop/queen diagonals
        for ray in &BISHOP_RAYS[local] {
            for &rsq in ray {
                let gsq = base + rsq as usize;
                let p = self.pieces[gsq];
                if p == 0 { continue; }
                if (p == BISHOP || p == QUEEN) && self.colors[gsq] == attacker_color {
                    return true;
                }
                break; // blocked
            }
        }

        // Sliding: rook/queen straights
        for ray in &ROOK_RAYS[local] {
            for &rsq in ray {
                let gsq = base + rsq as usize;
                let p = self.pieces[gsq];
                if p == 0 { continue; }
                if (p == ROOK || p == QUEEN) && self.colors[gsq] == attacker_color {
                    return true;
                }
                break;
            }
        }

        false
    }

    pub fn is_in_check(&self, color: bool) -> bool {
        let idx = if color { 0 } else { 1 };
        let ksq = self.king_sq[idx];
        if ksq < 0 { return false; }
        let ksq = ksq as usize;
        if self.is_attacked_by(ksq, !color) { return true; }
        // Cross-board pre-flip threats — one clone, mutate and restore
        let mut b = self.clone();
        let king_side = square_side(ksq) as usize;
        let base_here = king_side * 64;
        for local in 0..64usize {
            let sq_here = base_here + local;
            if b.pieces[sq_here] != 0 { continue; }
            let sq_other = flip_square(sq_here);
            let opp_pt = b.pieces[sq_other];
            if opp_pt == 0 || b.colors[sq_other] == color { continue; }
            // Kings CAN flip (exempt from flip zone like crabs)
            let opp_origin = b.origins[sq_other];
            let opp_side = square_side(sq_other);
            if opp_side == opp_origin && opp_pt != CRAB && opp_pt != KING {
                if square_rank(sq_other) + 2 < BOARD_RANKS { continue; }
            }
            b.pieces[sq_here] = opp_pt;
            b.colors[sq_here] = !color;
            let flip_safe = !b.is_attacked_by(sq_here, color);
            if flip_safe && b.is_attacked_by(ksq, !color) { return true; }
            b.pieces[sq_here] = 0;
            b.colors[sq_here] = false;
        }

        // Post-flip capture threat: can an enemy piece move then flip onto king's square?
        use crate::movegen::post_flip_capture_safe;
        if !post_flip_capture_safe(&b, ksq, color) { return true; }

        false
    }

    /// Find all squares of pieces giving check to the specified color's king.
    pub fn find_checkers(&self, king_color: bool) -> Vec<usize> {
        let idx = if king_color { 0 } else { 1 };
        let ksq = self.king_sq[idx];
        if ksq < 0 { return Vec::new(); }
        let ksq = ksq as usize;
        let attacker_color = !king_color;
        let side = square_side(ksq);
        let local = ksq & 63;
        let base = side as usize * 64;
        let mut checkers = Vec::new();

        for &asq in &KNIGHT_ATTACKS[local] {
            let gsq = base + asq as usize;
            if self.pieces[gsq] == KNIGHT && self.colors[gsq] == attacker_color {
                checkers.push(gsq);
            }
        }
        for &asq in &KING_ATTACKS[local] {
            let gsq = base + asq as usize;
            let p = self.pieces[gsq];
            if (p == KING || p == CRAB) && self.colors[gsq] == attacker_color {
                checkers.push(gsq);
            }
        }
        let r = local >> 3;
        let f = local & 7;
        for df in [-1i32, 1] {
            let nf = f as i32 + df;
            if nf < 0 || nf >= 8 { continue; }
            if r > 0 {
                let gsq = base + (r - 1) * 8 + nf as usize;
                if self.pieces[gsq] == PAWN && self.colors[gsq] == attacker_color
                    && self.origins[gsq] == side {
                    checkers.push(gsq);
                }
            }
            if r + 1 < BOARD_RANKS {
                let gsq = base + (r + 1) * 8 + nf as usize;
                if self.pieces[gsq] == PAWN && self.colors[gsq] == attacker_color
                    && self.origins[gsq] != side {
                    checkers.push(gsq);
                }
            }
        }
        for ray in &BISHOP_RAYS[local] {
            for &rsq in ray {
                let gsq = base + rsq as usize;
                let p = self.pieces[gsq];
                if p == 0 { continue; }
                if (p == BISHOP || p == QUEEN) && self.colors[gsq] == attacker_color {
                    checkers.push(gsq);
                }
                break;
            }
        }
        for ray in &ROOK_RAYS[local] {
            for &rsq in ray {
                let gsq = base + rsq as usize;
                let p = self.pieces[gsq];
                if p == 0 { continue; }
                if (p == ROOK || p == QUEEN) && self.colors[gsq] == attacker_color {
                    checkers.push(gsq);
                }
                break;
            }
        }
        checkers
    }

    // ── Push / Pop ──

    fn snapshot_sq(&self, sq: usize) -> (usize, u8, bool, u8) {
        (sq, self.pieces[sq], self.colors[sq], self.origins[sq])
    }

    pub fn raw_move(&mut self, from: usize, to: usize) {
        self.pieces[to] = self.pieces[from];
        self.colors[to] = self.colors[from];
        self.origins[to] = self.origins[from];
        self.pieces[from] = 0;
        self.colors[from] = false;
        self.origins[from] = 255;
    }

    fn pawn_moves_up(&self, sq: usize) -> bool {
        let current_side = square_side(sq);
        let orig = self.origins[sq];
        current_side == orig
    }

    fn must_force_flip(&self, sq: usize) -> bool {
        if self.pieces[sq] == 0 { return false; }
        let orig = self.origins[sq];
        let current_side = square_side(sq);
        if current_side != orig { return false; } // no forced flip on away side
        square_rank(sq) == BOARD_RANKS - 1
    }

    pub fn push(&mut self, m: &WarpMove) {
        let color = self.turn;
        let pt = self.pieces[m.from_sq as usize];

        // Build undo
        let mut undo = UndoInfo {
            square_changes: Vec::new(),
            turn: self.turn,
            castling: self.castling,
            en_passant: self.en_passant,
            halfmove_clock: self.halfmove_clock,
            hash: self.hash,
            king_sq: self.king_sq,
        };

        // Snapshot all affected squares
        undo.square_changes.push(self.snapshot_sq(m.from_sq as usize));
        undo.square_changes.push(self.snapshot_sq(m.to_sq as usize));
        if m.flip_type == PRE_FLIP && m.flip_to >= 0 {
            undo.square_changes.push(self.snapshot_sq(m.flip_to as usize));
        }
        if m.flip_type == POST_FLIP && m.flip_to >= 0 {
            undo.square_changes.push(self.snapshot_sq(m.flip_to as usize));
        }

        // Detect en passant capture
        let is_ep = pt == PAWN && m.to_sq as i16 == self.en_passant && self.en_passant >= 0;
        let mut ep_sq: i16 = -1;
        if is_ep {
            let up = self.pawn_moves_up(m.from_sq as usize);
            let behind = if up { -1i32 } else { 1 };
            let ep_r = square_rank(self.en_passant as usize) as i32 + behind;
            let ep_f = self.en_passant as usize & 7;
            let ep_side = self.en_passant as usize >> 6;
            ep_sq = (ep_side * 64 + ep_r as usize * 8 + ep_f) as i16;
            undo.square_changes.push(self.snapshot_sq(ep_sq as usize));
        }

        // Detect castling — only from e-file rank 0 (king's starting square)
        // Castling can be combined with a post-flip (king castles, then flips)
        let is_castle = self.is_castle(m, pt, self.turn);   // (as the Python board's push: read before the move is applied)
        if is_castle {
            let base = (m.from_sq as usize >> 6) * 64;
            let ft = square_file(m.to_sq as usize);
            if ft == 6 {
                undo.square_changes.push(self.snapshot_sq(base + 7));
                undo.square_changes.push(self.snapshot_sq(base + 5));
            } else if ft == 2 {
                undo.square_changes.push(self.snapshot_sq(base + 0));
                undo.square_changes.push(self.snapshot_sq(base + 3));
            }
        }

        // POST_FLIP: piece lands at flip_to, not to_sq
        let cap_sq = if m.flip_type == POST_FLIP && m.flip_to >= 0 {
            m.flip_to as usize
        } else {
            m.to_sq as usize
        };
        let captured = self.pieces[cap_sq] != 0;

        // Step 1: Pre-flip
        let actual_from;
        if m.flip_type == PRE_FLIP && m.flip_to >= 0 {
            self.raw_move(m.from_sq as usize, m.flip_to as usize);
            actual_from = m.flip_to as usize;
        } else {
            actual_from = m.from_sq as usize;
        }

        // Step 2: En passant capture
        if is_ep && ep_sq >= 0 {
            self.pieces[ep_sq as usize] = 0;
            self.colors[ep_sq as usize] = false;
            self.origins[ep_sq as usize] = 255;
        }

        // Step 3: Move piece
        let saved_origin = self.origins[actual_from];
        let dest_pt = if let Some(p) = m.promotion { p } else { pt };
        self.pieces[m.to_sq as usize] = dest_pt;
        self.colors[m.to_sq as usize] = color;
        self.origins[m.to_sq as usize] = saved_origin;
        if actual_from != m.to_sq as usize {
            self.pieces[actual_from] = 0;
            self.colors[actual_from] = false;
            self.origins[actual_from] = 255;
        }

        // Step 3b: Auto-promote pawn to crab at promo rank
        if dest_pt == PAWN && m.promotion.is_none() {
            let to_side = square_side(m.to_sq as usize);
            let to_rank = square_rank(m.to_sq as usize);
            let promo_r = if to_side == saved_origin { BOARD_RANKS - 1 } else { 0 };
            if to_rank == promo_r {
                self.pieces[m.to_sq as usize] = CRAB;
            }
        }

        // Step 4: Post-flip
        if m.flip_type == POST_FLIP && m.flip_to >= 0 {
            let ft = m.flip_to as usize;
            self.pieces[ft] = self.pieces[m.to_sq as usize];
            self.colors[ft] = color;
            self.origins[ft] = self.origins[m.to_sq as usize];
            self.pieces[m.to_sq as usize] = 0;
            self.colors[m.to_sq as usize] = false;
            self.origins[m.to_sq as usize] = 255;
        }

        // Step 5: Forced flip
        let mut final_sq = if m.flip_type == POST_FLIP && m.flip_to >= 0 {
            m.flip_to as usize
        } else {
            m.to_sq as usize
        };
        if m.flip_type == NO_FLIP && self.must_force_flip(final_sq) {
            // Auto-promote pawn to crab on own-side last rank
            if self.pieces[final_sq] == PAWN {
                let orig = self.origins[final_sq];
                let current_side = square_side(final_sq);
                if current_side == orig {
                    self.pieces[final_sq] = CRAB;
                }
            }
            let ff_sq = flip_square(final_sq);
            undo.square_changes.push(self.snapshot_sq(ff_sq));
            self.pieces[ff_sq] = self.pieces[final_sq];
            self.colors[ff_sq] = color;
            self.origins[ff_sq] = self.origins[final_sq];
            self.pieces[final_sq] = 0;
            self.colors[final_sq] = false;
            self.origins[final_sq] = 255;
            final_sq = ff_sq;
        }

        // Step 6: Castling rook
        if is_castle {
            let base = (m.from_sq as usize >> 6) * 64;
            let ft = square_file(m.to_sq as usize);
            if ft == 6 {
                self.raw_move(base + 7, base + 5);
            } else if ft == 2 {
                self.raw_move(base + 0, base + 3);
            }
        }

        // Update king tracking
        if pt == KING {
            let idx = if color { 0 } else { 1 };
            self.king_sq[idx] = final_sq as i16;
        }

        // Update castling rights
        if pt == KING {
            if color {
                self.castling &= !(WK | WQ);
            } else {
                self.castling &= !(BK | BQ);
            }
        }
        if pt == ROOK {
            let from = m.from_sq as usize;
            if from == square(LEFT, 7, 0) { self.castling &= !WK; }
            if from == square(LEFT, 0, 0) { self.castling &= !WQ; }
            if from == square(RIGHT, 7, 0) { self.castling &= !BK; }
            if from == square(RIGHT, 0, 0) { self.castling &= !BQ; }
        }

        // En passant
        self.en_passant = -1;
        if pt == PAWN && m.flip_type == NO_FLIP {
            let r_from = square_rank(m.from_sq as usize);
            let r_to = square_rank(m.to_sq as usize);
            if (r_from as i32 - r_to as i32).unsigned_abs() == 2 {
                let ep_rank = (r_from + r_to) / 2;
                let side = square_side(m.from_sq as usize);
                self.en_passant = (side as usize * 64 + ep_rank * 8 + square_file(m.from_sq as usize)) as i16;
            }
        }

        // Clocks
        if pt == PAWN || captured || is_ep {
            self.halfmove_clock = 0;
        } else {
            self.halfmove_clock += 1;
        }
        if !color {
            self.fullmove_number += 1;
        }

        self.turn = !self.turn;
        self.undo_stack.push(undo);
        self.move_stack.push(*m);
        self.hash = self.compute_hash();
    }

    pub fn pop(&mut self) {
        let m = self.move_stack.pop().expect("pop on empty stack");
        let undo = self.undo_stack.pop().expect("pop on empty stack");

        // Restore squares
        for &(sq, pt, col, orig) in undo.square_changes.iter().rev() {
            self.pieces[sq] = pt;
            self.colors[sq] = col;
            self.origins[sq] = orig;
        }

        self.turn = undo.turn;
        self.castling = undo.castling;
        self.en_passant = undo.en_passant;
        self.halfmove_clock = undo.halfmove_clock;
        self.hash = undo.hash;
        self.king_sq = undo.king_sq;
        if !self.turn {
            self.fullmove_number = self.fullmove_number.saturating_sub(1);
        }
    }

    // ── Game queries ──

    pub fn is_game_over(&self) -> bool {
        if self.king_sq[0] < 0 || self.king_sq[1] < 0 {
            return true;
        }
        if self.halfmove_clock >= 100 {
            return true;
        }
        // Check for no legal moves (expensive — only call when needed)
        crate::movegen::legal_moves(self).is_empty()
    }

    pub fn is_checkmate(&self) -> bool {
        let idx = if self.turn { 0 } else { 1 };
        if self.king_sq[idx] < 0 { return false; }
        self.is_in_check(self.turn) && crate::movegen::legal_moves(self).is_empty()
    }

    pub fn is_stalemate(&self) -> bool {
        let idx = if self.turn { 0 } else { 1 };
        if self.king_sq[idx] < 0 { return false; }
        !self.is_in_check(self.turn) && crate::movegen::legal_moves(self).is_empty()
    }

    pub fn is_capture(&self, m: &WarpMove) -> bool {
        // POST_FLIP: piece lands at flip_to, not to_sq
        let cap_sq = if m.flip_type == POST_FLIP && m.flip_to >= 0 {
            m.flip_to as usize
        } else {
            m.to_sq as usize
        };
        let tp = self.pieces[cap_sq];
        if tp != 0 && self.colors[cap_sq] != self.turn {
            return true;
        }
        // En passant
        if self.pieces[m.from_sq as usize] == PAWN
            && m.to_sq as i16 == self.en_passant
            && self.en_passant >= 0 {
            return true;
        }
        false
    }

    pub fn is_king_capture(&self, m: &WarpMove) -> bool {
        let cap_sq = if m.flip_type == POST_FLIP && m.flip_to >= 0 {
            m.flip_to as usize
        } else {
            m.to_sq as usize
        };
        self.pieces[cap_sq] == KING && self.colors[cap_sq] != self.turn
    }

    pub fn gives_check(&self, m: &WarpMove) -> bool {
        let mut b = self.clone();
        b.push(m);
        b.is_in_check(b.turn)  // after push, b.turn is the opponent — check if they're in check
    }

    pub fn is_repetition(&self, count: usize) -> bool {
        let mut seen = 0;
        for undo in self.undo_stack.iter().rev() {
            if undo.hash == self.hash {
                seen += 1;
                if seen >= count {
                    return true;
                }
            }
        }
        false
    }

    pub fn result(&self) -> String {
        if self.king_sq[0] < 0 { return "0-1".into(); }
        if self.king_sq[1] < 0 { return "1-0".into(); }
        if self.is_checkmate() {
            if self.turn { "0-1".into() } else { "1-0".into() }
        } else {
            "1/2-1/2".into()
        }
    }
}
