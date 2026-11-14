//! Legal move generation for Warp 1 Chess.

use crate::types::*;
use crate::attacks::*;
use crate::board::WarpBoardInner;

/// Generate all legal moves for the side to move.
pub fn legal_moves(board: &WarpBoardInner) -> Vec<WarpMove> {
    let mut moves = Vec::with_capacity(128);
    let color = board.turn;

    // Standard moves + crab promotion
    gen_standard_moves(board, color, &mut moves);
    // Flip moves (pre-flip and post-flip)
    gen_flip_moves(board, color, &mut moves);

    // Deduplicate (castling + crab jump can generate the same move)
    let mut seen = std::collections::HashSet::new();
    moves.retain(|m| {
        let key = (m.from_sq, m.to_sq, m.flip_type, m.flip_to, m.promotion);
        seen.insert(key)
    });

    moves
}

fn gen_standard_moves(board: &WarpBoardInner, color: bool, moves: &mut Vec<WarpMove>) {
    for sq in 0..TOTAL_SQUARES {
        if board.pieces[sq] == 0 || !is_playable(sq) || board.colors[sq] != color {
            continue;
        }
        let pt = board.pieces[sq];
        let side = square_side(sq);
        let base = side as usize * 64;
        let local = sq & 63;

        match pt {
            PAWN => gen_pawn_moves(board, sq, local, side, base, color, moves),
            KNIGHT => {
                for &tl in &KNIGHT_ATTACKS[local] {
                    let target = base + tl as usize;
                    if !is_playable(target) { continue; }
                    if board.pieces[target] == 0 || board.colors[target] != color {
                        let m = WarpMove::new(sq as u8, target as u8);
                        if is_legal_after(board, &m) { moves.push(m); }
                    }
                }
            }
            KING => {
                for &tl in &KING_ATTACKS[local] {
                    let target = base + tl as usize;
                    if !is_playable(target) { continue; }
                    if square_rank(target) == BOARD_RANKS - 1 { continue; } // king can't enter last rank
                    if board.pieces[target] == 0 || board.colors[target] != color {
                        let m = WarpMove::new(sq as u8, target as u8);
                        if is_legal_after(board, &m) { moves.push(m); }
                    }
                }
                // 2-square orthogonal non-capture jumps (can jump over pieces)
                {
                    let r = square_rank(sq);
                    let f = square_file(sq);
                    for &(df, dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                        let nf = f as i32 + df;
                        let nr = r as i32 + dr;
                        if nf >= 0 && (nf as usize) < BOARD_FILES && nr >= 0 && (nr as usize) < BOARD_RANKS {
                            if nr as usize == BOARD_RANKS - 1 { continue; } // king can't enter last rank
                            let target = base + nr as usize * 8 + nf as usize;
                            if board.pieces[target] == 0 {
                                let m = WarpMove::new(sq as u8, target as u8);
                                if is_legal_after(board, &m) { moves.push(m); }
                            }
                        }
                    }
                }
                gen_castling(board, sq, side, color, moves);
            }
            CRAB => {
                let crab_origin = board.origins[sq];
                let on_away = side != crab_origin;
                let promo_rank = if on_away { 0 } else { usize::MAX };
                let r = square_rank(sq);
                let f = square_file(sq);

                // 1-square: vertical is capture-optional, others are capture only
                for &tl in &KING_ATTACKS[local] {
                    let target = base + tl as usize;
                    if !is_playable(target) { continue; }
                    let tf = square_file(target);
                    let tr = square_rank(target);
                    let tp = board.pieces[target];
                    let is_vertical = tf == f && (tr as i32 - r as i32).abs() == 1;
                    if tp == 0 {
                        if !is_vertical { continue; } // non-vertical: capture only
                        let m = WarpMove::new(sq as u8, target as u8);
                        if is_legal_after(board, &m) { moves.push(m); }
                    } else if board.colors[target] != color {
                        if on_away && tr == promo_rank {
                            for promo in [QUEEN, ROOK, BISHOP, KNIGHT] {
                                let m = WarpMove::with_promo(sq as u8, target as u8, promo);
                                if is_legal_after(board, &m) { moves.push(m); }
                            }
                        } else {
                            let m = WarpMove::new(sq as u8, target as u8);
                            if is_legal_after(board, &m) { moves.push(m); }
                        }
                    }
                }

                // 2-square orthogonal: NON-CAPTURE ONLY, can jump
                for &(df, dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                    let nf = f as i32 + df;
                    let nr = r as i32 + dr;
                    if nf >= 0 && (nf as usize) < BOARD_FILES && nr >= 0 && (nr as usize) < BOARD_RANKS {
                        let target = base + nr as usize * 8 + nf as usize;
                        if board.pieces[target] == 0 {
                            let tr = square_rank(target);
                            if on_away && tr == promo_rank {
                                for promo in [QUEEN, ROOK, BISHOP, KNIGHT] {
                                    let m = WarpMove::with_promo(sq as u8, target as u8, promo);
                                    if is_legal_after(board, &m) { moves.push(m); }
                                }
                            } else {
                                let m = WarpMove::new(sq as u8, target as u8);
                                if is_legal_after(board, &m) { moves.push(m); }
                            }
                        }
                    }
                }
            }
            BISHOP | ROOK | QUEEN => {
                let rays = match pt {
                    BISHOP => &BISHOP_RAYS[local],
                    ROOK => &ROOK_RAYS[local],
                    _ => &QUEEN_RAYS[local],
                };
                for ray in rays {
                    for &tl in ray {
                        let target = base + tl as usize;
                        if !is_playable(target) { break; }
                        let tp = board.pieces[target];
                        if tp != 0 && board.colors[target] == color { break; }
                        let m = WarpMove::new(sq as u8, target as u8);
                        if is_legal_after(board, &m) { moves.push(m); }
                        if tp != 0 { break; }
                    }
                }
            }
            _ => {}
        }
    }
}

const PAWN_START_RANKS: [usize; 8] = [1, 2, 3, 4, 4, 3, 2, 1]; // chevron

fn gen_pawn_moves(board: &WarpBoardInner, sq: usize, local: usize,
                  side: u8, base: usize, color: bool, moves: &mut Vec<WarpMove>) {
    let f = square_file(sq);
    let r = square_rank(sq);
    let up = board.origins[sq] == side;
    let dir: i32 = if up { 1 } else { -1 };
    let start_rank = if up { PAWN_START_RANKS[f] } else { BOARD_RANKS - 1 - PAWN_START_RANKS[f] };
    let promo_rank = if up { BOARD_RANKS - 1 } else { 0 };

    // Single push (pawns auto-promote to crab, no choice)
    let nr = r as i32 + dir;
    if nr >= 0 && (nr as usize) < BOARD_RANKS {
        let target = base + nr as usize * 8 + f;
        if board.pieces[target] == 0 {
            let m = WarpMove::new(sq as u8, target as u8);
            if is_legal_after(board, &m) { moves.push(m); }

            // Double push — only if pawn is on its origin side (hasn't flipped)
            let on_origin_side = (side as u8) == board.origins[sq];
            if nr as usize != promo_rank && r == start_rank && on_origin_side {
                let nr2 = nr + dir;
                if nr2 >= 0 && (nr2 as usize) < BOARD_RANKS {
                    let target2 = base + nr2 as usize * 8 + f;
                    if board.pieces[target2] == 0 {
                        let m = WarpMove::new(sq as u8, target2 as u8);
                        if is_legal_after(board, &m) { moves.push(m); }
                    }
                }
            }
        }
    }

    // Captures
    let attacks = if up { &PAWN_ATTACKS_UP[local] } else { &PAWN_ATTACKS_DOWN[local] };
    for &tl in attacks {
        let target = base + tl as usize;
        if !is_playable(target) { continue; }
        let tp = board.pieces[target];
        // Normal capture (auto-promote to crab at promo rank)
        if tp != 0 && board.colors[target] != color {
            let m = WarpMove::new(sq as u8, target as u8);
            if is_legal_after(board, &m) { moves.push(m); }
        }
        // En passant
        if target as i16 == board.en_passant && board.en_passant >= 0 {
            let m = WarpMove::new(sq as u8, target as u8);
            if is_legal_after(board, &m) { moves.push(m); }
        }
    }
}

fn gen_castling(board: &WarpBoardInner, king_sq: usize, side: u8, color: bool, moves: &mut Vec<WarpMove>) {
    let base = side as usize * 64;
    if square_rank(king_sq) != 0 { return; }
    // Can't castle while in check (including cross-board threats)
    if board.is_in_check(color) { return; }

    if color { // WHITE
        if board.castling & WK != 0 {
            if board.pieces[base + 5] == 0 && board.pieces[base + 6] == 0
                && board.pieces[base + 7] == ROOK && board.colors[base + 7] == true
                && !board.is_attacked_by(king_sq, false)
                && !board.is_attacked_by(base + 5, false)
                && !board.is_attacked_by(base + 6, false) {
                // Validate with full is_legal_after (includes cross-board threats)
                let m = WarpMove::new(king_sq as u8, (base + 6) as u8);
                if is_legal_after(board, &m) { moves.push(m); }
            }
        }
        if board.castling & WQ != 0 {
            if board.pieces[base + 3] == 0 && board.pieces[base + 2] == 0 && board.pieces[base + 1] == 0
                && board.pieces[base + 0] == ROOK && board.colors[base + 0] == true
                && !board.is_attacked_by(king_sq, false)
                && !board.is_attacked_by(base + 3, false)
                && !board.is_attacked_by(base + 2, false) {
                let m = WarpMove::new(king_sq as u8, (base + 2) as u8);
                if is_legal_after(board, &m) { moves.push(m); }
            }
        }
    } else { // BLACK
        if board.castling & BK != 0 {
            if board.pieces[base + 5] == 0 && board.pieces[base + 6] == 0
                && board.pieces[base + 7] == ROOK && board.colors[base + 7] == false
                && !board.is_attacked_by(king_sq, true)
                && !board.is_attacked_by(base + 5, true)
                && !board.is_attacked_by(base + 6, true) {
                let m = WarpMove::new(king_sq as u8, (base + 6) as u8);
                if is_legal_after(board, &m) { moves.push(m); }
            }
        }
        if board.castling & BQ != 0 {
            if board.pieces[base + 3] == 0 && board.pieces[base + 2] == 0 && board.pieces[base + 1] == 0
                && board.pieces[base + 0] == ROOK && board.colors[base + 0] == false
                && !board.is_attacked_by(king_sq, true)
                && !board.is_attacked_by(base + 3, true)
                && !board.is_attacked_by(base + 2, true) {
                let m = WarpMove::new(king_sq as u8, (base + 2) as u8);
                if is_legal_after(board, &m) { moves.push(m); }
            }
        }
    }
}

fn gen_flip_moves(board: &WarpBoardInner, color: bool, moves: &mut Vec<WarpMove>) {
    for sq in 0..TOTAL_SQUARES {
        if board.pieces[sq] == 0 || !is_playable(sq) || board.colors[sq] != color {
            continue;
        }
        let pt = board.pieces[sq];
        let flip_target = flip_square(sq);

        // Forward flip restriction (crabs exempt)
        // Pre-flip: check starting square. Post-flip: check target square (below).
        let current_side = square_side(sq);
        let orig = board.origins[sq];
        let is_forward = current_side == orig;
        let pre_flip_allowed = if is_forward && pt != CRAB && pt != KING {
            square_rank(sq) + 2 >= BOARD_RANKS
        } else {
            true
        };

        // ── Pre-flip: flip then move ──
        // Pre-flip: flip_target must be unoccupied, playable, not last rank, and not in danger
        if pre_flip_allowed && is_playable(flip_target)
            && square_rank(flip_target) < BOARD_RANKS - 1
            && board.pieces[flip_target] == 0
            && !board.is_attacked_by(flip_target, !color) {
            // Temporarily flip
            let mut b = board.clone();
            b.raw_move(sq, flip_target);
            let new_side = square_side(flip_target);
            let new_base = new_side as usize * 64;
            let new_local = flip_target & 63;

            match pt {
                PAWN => gen_pawn_preflip(&b, sq, flip_target, new_local, new_side, new_base, color, moves),
                KNIGHT => {
                    for &tl in &KNIGHT_ATTACKS[new_local] {
                        let t = new_base + tl as usize;
                        if !is_playable(t) { continue; }
                        if b.pieces[t] == 0 || b.colors[t] != color {
                            let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                            if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                        }
                    }
                }
                KING => {
                    for &tl in &KING_ATTACKS[new_local] {
                        let t = new_base + tl as usize;
                        if !is_playable(t) { continue; }
                        if square_rank(t) == BOARD_RANKS - 1 { continue; } // king can't enter last rank
                        if b.pieces[t] == 0 || b.colors[t] != color {
                            let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                            if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                        }
                    }
                    // 2-square orthogonal non-capture jumps (can jump over pieces)
                    {
                        let kr = square_rank(flip_target);
                        let kf = square_file(flip_target);
                        for &(df, dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                            let nf = kf as i32 + df;
                            let nr = kr as i32 + dr;
                            if nf >= 0 && (nf as usize) < BOARD_FILES && nr >= 0 && (nr as usize) < BOARD_RANKS {
                                if nr as usize == BOARD_RANKS - 1 { continue; }
                                let t = new_base + nr as usize * 8 + nf as usize;
                                if b.pieces[t] == 0 {
                                    let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                                    if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                                }
                            }
                        }
                    }
                }
                CRAB => {
                    let crab_origin = board.origins[sq];
                    let on_away = new_side != crab_origin;
                    let promo_rank = if on_away { 0 } else { usize::MAX };
                    let cr = square_rank(flip_target);
                    let cf = square_file(flip_target);

                    // 1-square: vertical is capture-optional, others are capture only
                    for &tl in &KING_ATTACKS[new_local] {
                        let t = new_base + tl as usize;
                        if !is_playable(t) { continue; }
                        let tf = square_file(t);
                        let tr = square_rank(t);
                        let tp = b.pieces[t];
                        let is_vertical = tf == cf && (tr as i32 - cr as i32).abs() == 1;
                        if tp == 0 {
                            if !is_vertical { continue; }
                            let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                            if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                        } else if b.colors[t] != color {
                            if on_away && tr == promo_rank {
                                for promo in [QUEEN, ROOK, BISHOP, KNIGHT] {
                                    let m = WarpMove::with_flip_promo(sq as u8, t as u8, promo, PRE_FLIP, sq as i16, flip_target as i16);
                                    if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                                }
                            } else {
                                let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                                if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                            }
                        }
                    }

                    // 2-square orthogonal: non-capture only, can jump
                    for &(df, dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                        let nf = cf as i32 + df;
                        let nr = cr as i32 + dr;
                        if nf >= 0 && (nf as usize) < BOARD_FILES && nr >= 0 && (nr as usize) < BOARD_RANKS {
                            let t = new_base + nr as usize * 8 + nf as usize;
                            if b.pieces[t] == 0 {
                                let tr = square_rank(t);
                                if on_away && tr == promo_rank {
                                    for promo in [QUEEN, ROOK, BISHOP, KNIGHT] {
                                        let m = WarpMove::with_flip_promo(sq as u8, t as u8, promo, PRE_FLIP, sq as i16, flip_target as i16);
                                        if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                                    }
                                } else {
                                    let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                                    if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                                }
                            }
                        }
                    }
                }
                BISHOP | ROOK | QUEEN => {
                    let rays = match pt {
                        BISHOP => &BISHOP_RAYS[new_local],
                        ROOK => &ROOK_RAYS[new_local],
                        _ => &QUEEN_RAYS[new_local],
                    };
                    for ray in rays {
                        for &tl in ray {
                            let t = new_base + tl as usize;
                            if !is_playable(t) { break; }
                            let tp = b.pieces[t];
                            if tp != 0 && b.colors[t] == color { break; }
                            let m = WarpMove::with_flip(sq as u8, t as u8, PRE_FLIP, sq as i16, flip_target as i16);
                            if is_legal_after_flip(&b, &m, sq, flip_target) { moves.push(m); }
                            if tp != 0 { break; }
                        }
                    }
                }
                _ => {}
            }
        }

        // ── Post-flip: move then flip ──
        let same_side = square_side(sq);
        let same_base = same_side as usize * 64;
        let same_local = sq & 63;

        let targets = get_non_capture_targets(board, sq, pt, same_local, same_base, color);
        for t in targets {
            let post_flip_dest = flip_square(t);
            if !is_playable(post_flip_dest) { continue; }
            if square_rank(post_flip_dest) == BOARD_RANKS - 1 { continue; }
            // Forward flip check for post-flip: based on target t, not starting sq
            if is_forward && pt != CRAB && pt != KING {
                if square_rank(t) + 2 < BOARD_RANKS { continue; }
            }
            if board.pieces[post_flip_dest] != 0 {
                let is_two_sq_jump = (pt == CRAB || pt == KING) &&
                    ((square_rank(t) as i32 - square_rank(sq) as i32).abs() == 2 ||
                     (square_file(t) as i32 - square_file(sq) as i32).abs() == 2);
                if board.colors[post_flip_dest] == color || pt == PAWN || is_two_sq_jump { continue; }
            }
            // Crab promotion: if crab lands on rank 0 of non-origin side after flip
            if pt == CRAB {
                let crab_origin = board.origins[sq];
                let dest_side = square_side(post_flip_dest);
                let on_away = dest_side != crab_origin;
                if on_away && square_rank(post_flip_dest) == 0 {
                    for promo in [QUEEN, ROOK, BISHOP, KNIGHT] {
                        let m = WarpMove::with_flip_promo(sq as u8, t as u8, promo, POST_FLIP, t as i16, post_flip_dest as i16);
                        if is_legal_after(board, &m) { moves.push(m); }
                    }
                    continue;
                }
            }
            let m = WarpMove::with_flip(sq as u8, t as u8, POST_FLIP, t as i16, post_flip_dest as i16);
            if is_legal_after(board, &m) { moves.push(m); }
        }
    }
}

fn gen_pawn_preflip(board: &WarpBoardInner, orig_sq: usize, flipped_sq: usize,
                    local: usize, side: u8, base: usize, color: bool, moves: &mut Vec<WarpMove>) {
    let f = square_file(flipped_sq);
    let r = square_rank(flipped_sq);
    let up = board.origins[flipped_sq] == side;
    let dir: i32 = if up { 1 } else { -1 };

    // Single push
    let nr = r as i32 + dir;
    if nr >= 0 && (nr as usize) < BOARD_RANKS {
        let target = base + nr as usize * 8 + f;
        if board.pieces[target] == 0 {
            let m = WarpMove::with_flip(orig_sq as u8, target as u8, PRE_FLIP, orig_sq as i16, flipped_sq as i16);
            if is_legal_after_flip(board, &m, orig_sq, flipped_sq) { moves.push(m); }
        }
    }

    // Captures
    let attacks = if up { &PAWN_ATTACKS_UP[local] } else { &PAWN_ATTACKS_DOWN[local] };
    for &tl in attacks {
        let target = base + tl as usize;
        if !is_playable(target) { continue; }
        if board.pieces[target] != 0 && board.colors[target] != color {
            let m = WarpMove::with_flip(orig_sq as u8, target as u8, PRE_FLIP, orig_sq as i16, flipped_sq as i16);
            if is_legal_after_flip(board, &m, orig_sq, flipped_sq) { moves.push(m); }
        }
    }
}

fn get_non_capture_targets(board: &WarpBoardInner, sq: usize, pt: u8,
                           local: usize, base: usize, color: bool) -> Vec<usize> {
    let mut targets = Vec::new();
    match pt {
        PAWN => {
            let f = square_file(sq);
            let r = square_rank(sq);
            let up = board.origins[sq] == square_side(sq);
            let dir: i32 = if up { 1 } else { -1 };
            let nr = r as i32 + dir;
            if nr >= 0 && (nr as usize) < BOARD_RANKS {
                let t = base + nr as usize * 8 + f;
                if board.pieces[t] == 0 {
                    targets.push(t);
                    // Double push from start rank
                    let promo_rank = if up { BOARD_RANKS - 1 } else { 0 };
                    let start_rank = if up { PAWN_START_RANKS[f] } else { BOARD_RANKS - 1 - PAWN_START_RANKS[f] };
                    let on_origin_side = (square_side(sq) as u8) == board.origins[sq];
                    if (nr as usize) != promo_rank && r == start_rank && on_origin_side {
                        let nr2 = nr + dir;
                        if nr2 >= 0 && (nr2 as usize) < BOARD_RANKS {
                            let t2 = base + nr2 as usize * 8 + f;
                            if board.pieces[t2] == 0 { targets.push(t2); }
                        }
                    }
                }
            }
        }
        KNIGHT => {
            for &tl in &KNIGHT_ATTACKS[local] {
                let t = base + tl as usize;
                if is_playable(t) && board.pieces[t] == 0 { targets.push(t); }
            }
        }
        KING => {
            for &tl in &KING_ATTACKS[local] {
                let t = base + tl as usize;
                if is_playable(t) && board.pieces[t] == 0 { targets.push(t); }
            }
            // 2-square orthogonal non-capture jumps (can jump over pieces)
            let r = square_rank(sq);
            let f = square_file(sq);
            for &(df, dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                let nf = f as i32 + df;
                let nr = r as i32 + dr;
                if nf >= 0 && (nf as usize) < BOARD_FILES && nr >= 0 && (nr as usize) < BOARD_RANKS {
                    let t = base + nr as usize * 8 + nf as usize;
                    if board.pieces[t] == 0 { targets.push(t); }
                }
            }
        }
        CRAB => {
            let r = square_rank(sq);
            let f = square_file(sq);
            // 1-square vertical: capture-optional, include empty targets for post-flip
            for dr in [-1i32, 1] {
                let nr = r as i32 + dr;
                if nr >= 0 && (nr as usize) < BOARD_RANKS {
                    let t = base + nr as usize * 8 + f;
                    if board.pieces[t] == 0 { targets.push(t); }
                }
            }
            // 2-square orthogonal: non-capture only
            for &(df, dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                let nf = f as i32 + df;
                let nr = r as i32 + dr;
                if nf >= 0 && (nf as usize) < BOARD_FILES && nr >= 0 && (nr as usize) < BOARD_RANKS {
                    let t = base + nr as usize * 8 + nf as usize;
                    if board.pieces[t] == 0 { targets.push(t); }
                }
            }
        }
        BISHOP | ROOK | QUEEN => {
            let rays = match pt {
                BISHOP => &BISHOP_RAYS[local],
                ROOK => &ROOK_RAYS[local],
                _ => &QUEEN_RAYS[local],
            };
            for ray in rays {
                for &tl in ray {
                    let t = base + tl as usize;
                    if !is_playable(t) { break; }
                    if board.pieces[t] != 0 { break; }
                    targets.push(t);
                }
            }
        }
        _ => {}
    }
    targets
}

// ── Legality checking ──

/// Check that no enemy piece can move on its board then post-flip directly
/// onto the king's square (capturing it). Returns true if safe.
pub fn post_flip_capture_safe(b: &WarpBoardInner, king_sq: usize, color: bool) -> bool {
    use crate::attacks::{KING_ATTACKS, KNIGHT_ATTACKS};

    let king_side = square_side(king_sq) as usize;
    let opp_side = 1 - king_side;
    let opp_base = opp_side * 64;
    let mirror_sq = flip_square(king_sq);

    // Mirror square must be empty for a post-flip landing
    if b.pieces[mirror_sq] != 0 { return true; }

    let local_to = mirror_sq - opp_base;

    for sq_local in 0..64usize {
        let sq_opp = opp_base + sq_local;
        let opp_pt = b.pieces[sq_opp];
        if opp_pt == 0 || b.colors[sq_opp] == color { continue; }

        // Check flip zone restriction for post-flip from mirror_sq
        let opp_origin = b.origins[sq_opp];
        let mirror_side = square_side(mirror_sq);
        let is_forward = mirror_side == opp_origin;
        if is_forward && opp_pt != CRAB && opp_pt != KING {
            if square_rank(mirror_sq) + 2 < BOARD_RANKS { continue; }
        }

        let local_from = sq_opp - opp_base;
        let mut can_reach = false;

        if opp_pt == KING {
            // Only 1-sq king moves count (capture-optional).
            // 2-sq jumps are non-capture and can't post-flip capture.
            if KING_ATTACKS[local_from].contains(&(local_to as u8)) {
                can_reach = true;
            }
        } else if opp_pt == CRAB {
            // Crab 1-sq moves can capture. 2-sq jumps can't.
            use crate::attacks::crab_attacks;
            if crab_attacks(local_from as u8).contains(&(local_to as u8)) {
                can_reach = true;
            }
        } else if opp_pt == KNIGHT {
            if KNIGHT_ATTACKS[local_from].contains(&(local_to as u8)) {
                can_reach = true;
            }
        }

        if opp_pt == BISHOP || opp_pt == QUEEN {
            let fr = square_rank(sq_opp) as i32;
            let ff = square_file(sq_opp) as i32;
            let tr = square_rank(mirror_sq) as i32;
            let tf = square_file(mirror_sq) as i32;
            let dr = tr - fr;
            let df = tf - ff;
            if dr.abs() == df.abs() && dr != 0 {
                let step_r = if dr > 0 { 1 } else { -1 };
                let step_f = if df > 0 { 1 } else { -1 };
                let mut cr = fr + step_r;
                let mut cf = ff + step_f;
                let mut blocked = false;
                while cr != tr || cf != tf {
                    if b.pieces[opp_base + (cr as usize) * 8 + (cf as usize)] != 0 {
                        blocked = true;
                        break;
                    }
                    cr += step_r;
                    cf += step_f;
                }
                if !blocked { can_reach = true; }
            }
        }

        if !can_reach && (opp_pt == ROOK || opp_pt == QUEEN) {
            let fr = square_rank(sq_opp) as i32;
            let ff = square_file(sq_opp) as i32;
            let tr = square_rank(mirror_sq) as i32;
            let tf = square_file(mirror_sq) as i32;
            if fr == tr || ff == tf {
                let mut blocked = false;
                if fr == tr {
                    let step = if tf > ff { 1 } else { -1 };
                    let mut cf = ff + step;
                    while cf != tf {
                        if b.pieces[opp_base + (fr as usize) * 8 + (cf as usize)] != 0 {
                            blocked = true;
                            break;
                        }
                        cf += step;
                    }
                } else {
                    let step = if tr > fr { 1 } else { -1 };
                    let mut cr = fr + step;
                    while cr != tr {
                        if b.pieces[opp_base + (cr as usize) * 8 + (ff as usize)] != 0 {
                            blocked = true;
                            break;
                        }
                        cr += step;
                    }
                }
                if !blocked { can_reach = true; }
            }
        }

        if can_reach { return false; }
    }

    true
}

fn is_legal_after(board: &WarpBoardInner, m: &WarpMove) -> bool {
    let color = board.turn;
    let mut b = board.clone();

    // Minimal simulation: just move the piece and check king safety
    let pt = b.pieces[m.from_sq as usize];
    let from = m.from_sq as usize;
    let to = m.to_sq as usize;

    // Handle en passant
    if pt == PAWN && m.to_sq as i16 == b.en_passant && b.en_passant >= 0 {
        let up = b.origins[from] == square_side(from);
        let behind: i32 = if up { -1 } else { 1 };
        let ep_r = square_rank(b.en_passant as usize) as i32 + behind;
        let ep_f = b.en_passant as usize & 7;
        let ep_side = b.en_passant as usize >> 6;
        let ep_sq = ep_side * 64 + ep_r as usize * 8 + ep_f;
        b.pieces[ep_sq] = 0;
    }

    // Move piece
    let dest_pt = m.promotion.unwrap_or(pt);
    b.pieces[to] = dest_pt;
    b.colors[to] = color;
    b.origins[to] = b.origins[from];
    b.pieces[from] = 0;

    // Handle post-flip
    if m.flip_type == POST_FLIP && m.flip_to >= 0 {
        let ft = m.flip_to as usize;
        b.pieces[ft] = b.pieces[to];
        b.colors[ft] = color;
        b.origins[ft] = b.origins[to];
        b.pieces[to] = 0;
    }

    // Handle castling rook — only from e-file rank 0 (king's starting square)
    // Castling can be combined with a post-flip (king castles, then flips)
    if b.is_castle(m, pt, color) {   // (as the Python board's _is_legal_after: read on the board with the king already moved)
        let ft = square_file(to);
        {
            let base = (from >> 6) * 64;
            if ft == 6 {
                b.pieces[base + 5] = ROOK;
                b.colors[base + 5] = color;
                b.pieces[base + 7] = 0;
            } else if ft == 2 {
                b.pieces[base + 3] = ROOK;
                b.colors[base + 3] = color;
                b.pieces[base + 0] = 0;
            }
        }
    }

    // Find king (post-flip: king ends at flip_to, not to_square)
    let king_sq = if pt == KING {
        if m.flip_type == POST_FLIP && m.flip_to >= 0 { m.flip_to as usize } else { to }
    } else {
        let idx = if color { 0 } else { 1 };
        board.king_sq[idx] as usize
    };

    if b.is_attacked_by(king_sq, !color) {
        return false;
    }

    // Cross-board pre-flip threats on the king
    // Only pieces that could legally flip: not kings, must be in flip zone (or crab)
    {
        let king_side = square_side(king_sq) as usize;
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
            let is_forward = opp_side == opp_origin;
            if is_forward && opp_pt != CRAB && opp_pt != KING {
                if square_rank(sq_other) + 2 < BOARD_RANKS { continue; }
            }
            b.pieces[sq_here] = opp_pt;
            b.colors[sq_here] = !color;
            // Pre-flip is only legal if the destination is safe for the enemy.
            // If WE attack sq_here, the enemy can't legally pre-flip there.
            let flip_safe = !b.is_attacked_by(sq_here, color);
            let attacks_king = b.is_attacked_by(king_sq, !color);
            let threatened = flip_safe && attacks_king;
            b.pieces[sq_here] = 0;
            b.colors[sq_here] = false;
            if threatened { return false; }
        }
    }

    // Post-flip capture threat: can an enemy piece move on its board then
    // post-flip directly onto the king's square?
    if !post_flip_capture_safe(&b, king_sq, color) { return false; }

    true
}

fn is_legal_after_flip(board: &WarpBoardInner, m: &WarpMove, _orig_sq: usize, flip_sq: usize) -> bool {
    // Pre-flip destination can't be the last rank
    if square_rank(m.to_sq as usize) == BOARD_RANKS - 1 {
        return false;
    }
    let color = board.turn;
    let pt = board.pieces[flip_sq];
    let to = m.to_sq as usize;

    let mut b = board.clone();
    let dest_pt = m.promotion.unwrap_or(pt);
    b.pieces[to] = dest_pt;
    b.colors[to] = color;
    b.origins[to] = b.origins[flip_sq];
    b.pieces[flip_sq] = 0;

    let king_sq = if pt == KING { to } else {
        let idx = if color { 0 } else { 1 };
        board.king_sq[idx] as usize
    };

    if b.is_attacked_by(king_sq, !color) {
        return false;
    }

    // Cross-board pre-flip threats on the king
    {
        let king_side = square_side(king_sq) as usize;
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
            let is_forward = opp_side == opp_origin;
            if is_forward && opp_pt != CRAB && opp_pt != KING {
                if square_rank(sq_other) + 2 < BOARD_RANKS { continue; }
            }
            b.pieces[sq_here] = opp_pt;
            b.colors[sq_here] = !color;
            let flip_safe = !b.is_attacked_by(sq_here, color);
            let threatened = flip_safe && b.is_attacked_by(king_sq, !color);
            b.pieces[sq_here] = 0;
            b.colors[sq_here] = false;
            if threatened { return false; }
        }
    }

    if !post_flip_capture_safe(&b, king_sq, color) { return false; }

    true
}
