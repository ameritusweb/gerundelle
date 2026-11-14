//! Alpha-beta search with PST evaluation, entirely in Rust.

use crate::types::*;
use crate::board::WarpBoardInner;
use crate::movegen::legal_moves;
use std::collections::HashMap;

const MATE_SCORE: i32 = 100_000;

// Piece values in centipawns
const CP_VALUES: [i32; 8] = [0, 100, 320, 330, 500, 900, 0, 300];

// PST tables [piece_type][rank][file] — from White's perspective
static PAWN_PST: [[i32; 8]; 7] = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
];

static KNIGHT_PST: [[i32; 8]; 7] = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
];

static BISHOP_PST: [[i32; 8]; 7] = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
];

static ROOK_PST: [[i32; 8]; 7] = [
    [  0,   0,   0,   5,   5,   0,   0,   0],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0],
];

static QUEEN_PST: [[i32; 8]; 7] = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
];

static KING_PST: [[i32; 8]; 7] = [
    [ 20,  30,  10,   0,   0,  10,  30,  20],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
];

static CRAB_PST: [[i32; 8]; 7] = [
    [-10, -10,  -5,   0,   0,  -5, -10, -10],
    [ -5,   0,   5,  10,  10,   5,   0,  -5],
    [ -5,   5,  10,  15,  15,  10,   5,  -5],
    [  0,   5,  15,  20,  20,  15,   5,   0],
    [  0,   5,  15,  20,  20,  15,   5,   0],
    [ -5,   0,  10,  15,  15,  10,   0,  -5],
    [-10,  -5,   0,   5,   5,   0,  -5, -10],
];

const FLIP_PRESENCE_BONUS: i32 = 15;

fn get_pst(pt: u8, r: usize, f: usize) -> i32 {
    if r >= BOARD_RANKS || f >= BOARD_FILES { return 0; }
    match pt {
        PAWN => PAWN_PST[r][f],
        KNIGHT => KNIGHT_PST[r][f],
        BISHOP => BISHOP_PST[r][f],
        ROOK => ROOK_PST[r][f],
        QUEEN => QUEEN_PST[r][f],
        KING => KING_PST[r][f],
        CRAB => CRAB_PST[r][f],
        _ => 0,
    }
}

/// Static evaluation from White's perspective (centipawns).
pub fn pst_evaluate(board: &WarpBoardInner) -> i32 {
    let mut score: i32 = 0;
    for sq in 0..TOTAL_SQUARES {
        let pt = board.pieces[sq];
        if pt == 0 || !is_playable(sq) { continue; }
        let color = board.colors[sq];
        let r = square_rank(sq);
        let f = square_file(sq);
        let side = square_side(sq);

        let cp = CP_VALUES[pt as usize];
        let mut pst_val = get_pst(pt, r, f);

        // Flip presence bonus
        let home = if color { LEFT } else { RIGHT };
        if side != home && pt != KING {
            pst_val += FLIP_PRESENCE_BONUS;
        }

        if color { score += cp + pst_val; } else { score -= cp + pst_val; }
    }
    score
}

/// Transposition table entry
#[derive(Clone, Copy)]
struct TTEntry {
    score: i32,
    depth: i32,
    flag: u8, // 0=exact, 1=alpha, 2=beta
}

const TT_EXACT: u8 = 0;
const TT_ALPHA: u8 = 1;
const TT_BETA: u8 = 2;
const TT_MAX: usize = 100_000;

/// Alpha-beta search with internal TT.
pub fn alphabeta_simple(board: &mut WarpBoardInner, depth: i32) -> i32 {
    let mut tt = HashMap::new();
    alphabeta(board, depth, -MATE_SCORE * 2, MATE_SCORE * 2, &mut tt)
}

/// Quiescence search: only explore captures until position is quiet.
fn quiescence(
    board: &mut WarpBoardInner,
    mut alpha: i32,
    beta: i32,
    tt: &mut HashMap<u64, TTEntry>,
) -> i32 {
    let stand_pat = if board.turn { pst_evaluate(board) } else { -pst_evaluate(board) };

    if stand_pat >= beta {
        return beta; // beta cutoff
    }
    if stand_pat > alpha {
        alpha = stand_pat;
    }

    // Delta pruning: if even capturing the best piece can't raise alpha, skip
    // Queen=900 is max capture value
    if stand_pat + 900 < alpha {
        return alpha;
    }

    let moves = legal_moves(board);
    for m in &moves {
        if !board.is_capture(m) { continue; }

        // SEE-like pruning: skip captures of low-value pieces if we're far below alpha
        let captured_pt = board.pieces[m.to_sq as usize];
        let captured_val = CP_VALUES[captured_pt as usize];
        if stand_pat + captured_val + 200 < alpha {
            continue; // futility: even this capture won't help
        }

        board.push(m);
        let score = -quiescence(board, -beta, -alpha, tt);
        board.pop();

        if score >= beta { return beta; }
        if score > alpha { alpha = score; }
    }

    alpha
}

/// Alpha-beta with null-move pruning, LMR, futility pruning, and quiescence.
fn alphabeta(
    board: &mut WarpBoardInner,
    depth: i32,
    mut alpha: i32,
    beta: i32,
    tt: &mut HashMap<u64, TTEntry>,
) -> i32 {
    if board.is_game_over() {
        if board.is_checkmate() {
            return -MATE_SCORE + (10 - depth);
        }
        return 0;
    }

    // Drop into quiescence at depth 0
    if depth <= 0 {
        return quiescence(board, alpha, beta, tt);
    }

    // TT lookup
    let hash = board.hash;
    if let Some(entry) = tt.get(&hash) {
        if entry.depth >= depth {
            match entry.flag {
                TT_EXACT => return entry.score,
                TT_ALPHA => { if entry.score <= alpha { return entry.score; } }
                TT_BETA => { if entry.score >= beta { return entry.score; } }
                _ => {}
            }
        }
    }

    let in_check = board.is_in_check(board.turn);

    // Null-move pruning: if we can skip our turn and still beat beta, prune
    // Don't do in check or at shallow depth
    if !in_check && depth >= 3 {
        let static_eval = if board.turn { pst_evaluate(board) } else { -pst_evaluate(board) };
        // Only if we're not losing badly
        if static_eval >= beta - 100 {
            // Make null move (just flip turn)
            let saved_turn = board.turn;
            let saved_ep = board.en_passant;
            let saved_hash = board.hash;
            board.turn = !board.turn;
            board.en_passant = -1;
            board.hash = board.compute_hash();

            let r = if depth >= 6 { 3 } else { 2 }; // reduction
            let null_score = -alphabeta(board, depth - 1 - r, -beta, -beta + 1, tt);

            board.turn = saved_turn;
            board.en_passant = saved_ep;
            board.hash = saved_hash;

            if null_score >= beta {
                return beta; // null-move cutoff
            }
        }
    }

    // Futility pruning: if static eval is far below alpha, skip quiet moves
    let futility_margin = depth as i32 * 150; // 150cp per depth
    let static_eval = if board.turn { pst_evaluate(board) } else { -pst_evaluate(board) };
    let do_futility = !in_check && depth <= 3 && static_eval + futility_margin < alpha;

    let moves = legal_moves(board);
    if moves.is_empty() {
        return 0;
    }

    // Move ordering: TT move first, then captures (MVV-LVA), then quiet
    let tt_move = tt.get(&hash).and_then(|_| None::<WarpMove>); // TODO: store best move in TT
    let mut ordered: Vec<(WarpMove, i32)> = moves.into_iter().map(|m| {
        let mut order_score = 0i32;
        if board.is_capture(&m) {
            // MVV-LVA: value of captured piece - value of capturing piece
            let victim = CP_VALUES[board.pieces[m.to_sq as usize] as usize];
            let attacker = CP_VALUES[board.pieces[m.from_sq as usize] as usize];
            order_score += 10000 + victim - attacker / 10;
        }
        if m.promotion.is_some() { order_score += 9000; }
        (m, order_score)
    }).collect();
    ordered.sort_unstable_by(|a, b| b.1.cmp(&a.1));

    let mut best = -MATE_SCORE * 2;
    let mut flag = TT_ALPHA;
    let mut moves_searched = 0u32;

    for (i, (m, order_score)) in ordered.iter().enumerate() {
        let is_capture = *order_score >= 10000;
        let is_promo = m.promotion.is_some();
        let is_tactical = is_capture || is_promo;

        // Futility pruning: skip quiet moves when we're losing badly
        if do_futility && !is_tactical && moves_searched > 0 {
            continue;
        }

        // Late Move Reduction: search later quiet moves with reduced depth
        let mut reduction = 0i32;
        if moves_searched >= 4 && depth >= 3 && !is_tactical && !in_check {
            reduction = 1;
            if moves_searched >= 8 { reduction = 2; }
        }

        board.push(m);

        let score;
        if reduction > 0 {
            // Reduced search first
            let reduced = -alphabeta(board, depth - 1 - reduction, -beta, -alpha, tt);
            if reduced > alpha {
                // Re-search at full depth if it looks promising
                score = -alphabeta(board, depth - 1, -beta, -alpha, tt);
            } else {
                score = reduced;
            }
        } else {
            score = -alphabeta(board, depth - 1, -beta, -alpha, tt);
        }

        board.pop();
        moves_searched += 1;

        if score > best { best = score; }
        if score > alpha {
            alpha = score;
            flag = TT_EXACT;
        }
        if alpha >= beta {
            flag = TT_BETA;
            break;
        }
    }

    // TT store
    if tt.len() < TT_MAX {
        tt.insert(hash, TTEntry { score: best, depth, flag });
    }

    best
}

/// Top-level search: returns (score, best_move).
/// Creates its own transposition table internally.
pub fn search_root(
    board: &mut WarpBoardInner,
    depth: i32,
) -> (i32, Option<WarpMove>) {
    let mut tt = HashMap::new();
    search_root_with_tt(board, depth, &mut tt)
}

fn search_root_with_tt(
    board: &mut WarpBoardInner,
    depth: i32,
    tt: &mut HashMap<u64, TTEntry>,
) -> (i32, Option<WarpMove>) {
    let moves = legal_moves(board);
    if moves.is_empty() {
        return (0, None);
    }

    let mut best_score = -MATE_SCORE * 2;
    let mut best_move = None;
    let alpha_init = -MATE_SCORE * 2;
    let beta = MATE_SCORE * 2;
    let mut alpha = alpha_init;

    for m in &moves {
        board.push(m);
        let score = -alphabeta(board, depth - 1, -beta, -alpha, tt);
        board.pop();

        if score > best_score {
            best_score = score;
            best_move = Some(*m);
        }
        if score > alpha {
            alpha = score;
        }
    }

    (best_score, best_move)
}
