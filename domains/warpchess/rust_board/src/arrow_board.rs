//! ArrowBoard: per-square influence maps, hypothetical threat arrows, and BFS distance tables.
//!
//! Three layers of data:
//!
//! 1. influence/control maps  — which pieces currently influence which squares (recomputed on push/pop)
//! 2. hyp_threats[sq][pt]     — what squares piece type `pt` would threaten from `sq`, given current
//!                              board occupancy (blocking-aware for sliders; dirty-tracked per square)
//! 3. Static BFS distance tables (piece_type × from_local × to_local) — precomputed once at startup,
//!                              board-state-independent (empty-board distances); never need updating

use crate::types::*;
use crate::attacks::*;
use crate::board::WarpBoardInner;
use std::sync::LazyLock;
use std::collections::VecDeque;

// ── Static BFS distance tables ───────────────────────────────────────────────
// dist[from_local * 64 + to_local] = min moves on empty board (within one side)
// INF_DIST means unreachable (e.g., opposite-colour bishop squares)

pub const INF_DIST: u8 = 255;
type DistTable = Vec<u8>; // 64 * 64

fn bfs_distances(start: usize, neighbors_fn: &dyn Fn(usize) -> Vec<usize>) -> Vec<u8> {
    let mut dist = vec![INF_DIST; 64];
    dist[start] = 0;
    let mut q = VecDeque::new();
    q.push_back(start);
    while let Some(sq) = q.pop_front() {
        let d = dist[sq];
        if d == INF_DIST - 1 { continue; } // cap depth
        for nb in neighbors_fn(sq) {
            if dist[nb] == INF_DIST {
                dist[nb] = d + 1;
                q.push_back(nb);
            }
        }
    }
    dist
}

fn make_dist_table(neighbors_fn: &dyn Fn(usize) -> Vec<usize>) -> DistTable {
    let mut table = vec![INF_DIST; 64 * 64];
    for from in 0..64usize {
        let row = bfs_distances(from, neighbors_fn);
        table[from * 64..from * 64 + 64].copy_from_slice(&row);
    }
    table
}

// Neighbor generators (local squares 0-55, BOARD_RANKS=7)
fn nb_knight(sq: usize) -> Vec<usize> {
    let f = (sq % 8) as i32; let r = (sq / 8) as i32;
    [(-2i32,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)].iter()
        .filter_map(|&(df,dr)| {
            let nf = f+df; let nr = r+dr;
            if nf>=0 && nf<BOARD_FILES as i32 && nr>=0 && nr<BOARD_RANKS as i32
            { Some(nr as usize * 8 + nf as usize) } else { None }
        }).collect()
}

fn nb_king(sq: usize) -> Vec<usize> {
    let f = (sq % 8) as i32; let r = (sq / 8) as i32;
    (-1i32..=1).flat_map(|df| (-1i32..=1).map(move |dr| (df,dr)))
        .filter(|&(df,dr)| df!=0||dr!=0)
        .filter_map(|(df,dr)| {
            let nf = f+df; let nr = r+dr;
            if nf>=0 && nf<BOARD_FILES as i32 && nr>=0 && nr<BOARD_RANKS as i32
            { Some(nr as usize * 8 + nf as usize) } else { None }
        }).collect()
}

fn nb_crab(sq: usize) -> Vec<usize> {
    let mut out = nb_king(sq);
    let f = (sq % 8) as i32; let r = (sq / 8) as i32;
    for &(df,dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
        let nf = f+df; let nr = r+dr;
        if nf>=0 && nf<BOARD_FILES as i32 && nr>=0 && nr<BOARD_RANKS as i32 {
            out.push(nr as usize * 8 + nf as usize);
        }
    }
    out
}

fn nb_sliding(sq: usize, dirs: &[(i32,i32)]) -> Vec<usize> {
    let f = (sq % 8) as i32; let r = (sq / 8) as i32;
    let mut out = Vec::new();
    for &(df,dr) in dirs {
        let mut nf = f+df; let mut nr = r+dr;
        while nf>=0 && nf<BOARD_FILES as i32 && nr>=0 && nr<BOARD_RANKS as i32 {
            out.push(nr as usize * 8 + nf as usize);
            nf+=df; nr+=dr;
        }
    }
    out
}

fn nb_pawn(sq: usize, up: bool) -> Vec<usize> {
    let f = (sq % 8) as i32; let r = (sq / 8) as i32;
    let dr: i32 = if up { 1 } else { -1 };
    let nr = r + dr;
    if nr < 0 || nr >= BOARD_RANKS as i32 { return Vec::new(); }
    let mut out = vec![nr as usize * 8 + f as usize];
    for df in [-1i32, 1] {
        let nf = f + df;
        if nf >= 0 && nf < BOARD_FILES as i32 { out.push(nr as usize * 8 + nf as usize); }
    }
    out
}

const BISHOP_DIRS: [(i32,i32);4] = [(-1,-1),(-1,1),(1,-1),(1,1)];
const ROOK_DIRS:   [(i32,i32);4] = [(-1,0),(1,0),(0,-1),(0,1)];
const QUEEN_DIRS:  [(i32,i32);8] = [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)];

static DIST_KNIGHT:    LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&nb_knight));
static DIST_BISHOP:    LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&|sq| nb_sliding(sq, &BISHOP_DIRS)));
static DIST_ROOK:      LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&|sq| nb_sliding(sq, &ROOK_DIRS)));
static DIST_QUEEN:     LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&|sq| nb_sliding(sq, &QUEEN_DIRS)));
static DIST_KING:      LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&nb_king));
static DIST_CRAB:      LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&nb_crab));
static DIST_PAWN_UP:   LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&|sq| nb_pawn(sq, true)));
static DIST_PAWN_DOWN: LazyLock<DistTable> = LazyLock::new(|| make_dist_table(&|sq| nb_pawn(sq, false)));

pub fn piece_dist(pt: u8, up: bool, from_local: usize, to_local: usize) -> u8 {
    let table = match pt {
        KNIGHT => &*DIST_KNIGHT,
        BISHOP => &*DIST_BISHOP,
        ROOK   => &*DIST_ROOK,
        QUEEN  => &*DIST_QUEEN,
        KING   => &*DIST_KING,
        CRAB   => &*DIST_CRAB,
        PAWN   => if up { &*DIST_PAWN_UP } else { &*DIST_PAWN_DOWN },
        _      => &*DIST_KING,
    };
    table[from_local * 64 + to_local]
}

// ── Hypothetical threat computation ─────────────────────────────────────────
// "What squares would piece type `pt` threaten if it were on `sq`?"
// Uses current board occupancy for sliding pieces (blocking-aware).
// For non-sliding pieces, this is purely geometric.

fn compute_hyp_threats(board: &WarpBoardInner, sq: usize, pt: u8) -> Vec<u8> {
    if !is_playable(sq) { return Vec::new(); }
    let side = square_side(sq);
    let base = side as usize * 64;
    let local = sq & 63;
    let r = square_rank(sq) as i32;
    let f = square_file(sq) as i32;
    let mut out = Vec::new();

    match pt {
        PAWN => {
            // Pawn threatens diagonally; assume native direction for the side
            let up = board.origins[sq] == side || board.pieces[sq] == 0;
            let atk = if up { &PAWN_ATTACKS_UP[local] } else { &PAWN_ATTACKS_DOWN[local] };
            for &tl in atk { out.push((base + tl as usize) as u8); }
            // Also include push square as "influence"
            let dr: i32 = if up { 1 } else { -1 };
            let nr = r + dr;
            if nr >= 0 && nr < BOARD_RANKS as i32 {
                out.push((base + nr as usize * 8 + f as usize) as u8);
            }
        }
        KNIGHT => {
            for &tl in &KNIGHT_ATTACKS[local] { out.push((base + tl as usize) as u8); }
        }
        BISHOP | ROOK | QUEEN => {
            let rays = match pt {
                BISHOP => &BISHOP_RAYS[local],
                ROOK   => &ROOK_RAYS[local],
                _      => &QUEEN_RAYS[local],
            };
            for ray in rays {
                for &tl in ray {
                    let t = base + tl as usize;
                    out.push(t as u8);
                    // Blocked by any piece currently there (excluding the hypothetical piece itself)
                    if board.pieces[t] != 0 { break; }
                }
            }
        }
        KING => {
            for &tl in &KING_ATTACKS[local] { out.push((base + tl as usize) as u8); }
        }
        CRAB => {
            for &tl in &KING_ATTACKS[local] { out.push((base + tl as usize) as u8); }
            for &(df,dr) in &[(0i32,2i32),(0,-2),(2,0),(-2,0)] {
                let nr = r+dr; let nf = f+df;
                if nr>=0 && nr<BOARD_RANKS as i32 && nf>=0 && nf<BOARD_FILES as i32 {
                    out.push((base + nr as usize * 8 + nf as usize) as u8);
                }
            }
        }
        _ => {}
    }
    out
}

// ── Determine which squares are "dirty" after a move ─────────────────────────
// A square's hyp_threats need recomputing if its rays (for sliding pieces) were
// blocked or unblocked by the move. We track dirty per square.

fn sliding_ray_passes_through(sq: usize, pt: u8, blocker: usize) -> bool {
    if square_side(sq) != square_side(blocker) { return false; }
    let local = sq & 63;
    let rays = match pt {
        BISHOP => &BISHOP_RAYS[local],
        ROOK   => &ROOK_RAYS[local],
        QUEEN  => &QUEEN_RAYS[local],
        _      => return false,
    };
    let blocker_local = (blocker & 63) as u8;
    rays.iter().any(|ray| ray.contains(&blocker_local))
}

fn mark_dirty_for_move(
    board: &WarpBoardInner,
    from_sq: usize, to_sq: usize,
    dirty: &mut Vec<bool>,
) {
    // The moved piece itself is always dirty at its new square
    dirty[to_sq] = true;
    // The departure square is now empty — its hyp_threats change
    dirty[from_sq] = true;
    // Any sliding piece whose ray passes through from_sq or to_sq is dirty
    for sq in 0..TOTAL_SQUARES {
        if !is_playable(sq) || board.pieces[sq] == 0 { continue; }
        let pt = board.pieces[sq];
        if matches!(pt, BISHOP | ROOK | QUEEN) {
            if sliding_ray_passes_through(sq, pt, from_sq)
                || sliding_ray_passes_through(sq, pt, to_sq)
            {
                dirty[sq] = true;
            }
        }
    }
}

// ── ArrowBoardInner ──────────────────────────────────────────────────────────

pub struct ArrowBoardInner {
    pub board: WarpBoardInner,

    // Layer 1: current influence/control maps
    pub influence:     Vec<Vec<u8>>,   // influence[sq] = squares the piece at sq influences
    pub white_control: Vec<Vec<u8>>,   // white_control[sq] = white squares that influence sq
    pub black_control: Vec<Vec<u8>>,   // black_control[sq] = black squares that influence sq

    // Layer 2: hypothetical threats per (square, piece_type)
    // hyp_threats[sq][pt] = squares piece type pt would threaten from sq
    // Indexed by pt: 0=unused,1=PAWN,2=KNIGHT,3=BISHOP,4=ROOK,5=QUEEN,6=KING,7=CRAB
    pub hyp_threats: Vec<Vec<Vec<u8>>>,  // [sq][pt] -> threatened squares

    // Dirty tracking: which squares need hyp_threats recompute
    dirty: Vec<bool>,
}

impl ArrowBoardInner {
    pub fn new(board: WarpBoardInner) -> Self {
        let mut ab = Self {
            board,
            influence:     vec![Vec::new(); TOTAL_SQUARES],
            white_control: vec![Vec::new(); TOTAL_SQUARES],
            black_control: vec![Vec::new(); TOTAL_SQUARES],
            hyp_threats:   vec![vec![Vec::new(); NUM_PIECE_TYPES + 1]; TOTAL_SQUARES],
            dirty:         vec![false; TOTAL_SQUARES],
        };
        ab.recompute_all();
        ab
    }

    fn recompute_influence(&mut self) {
        for sq in 0..TOTAL_SQUARES {
            self.influence[sq].clear();
            self.white_control[sq].clear();
            self.black_control[sq].clear();
        }
        for sq in 0..TOTAL_SQUARES {
            if self.board.pieces[sq] == 0 || !is_playable(sq) { continue; }
            let color = self.board.colors[sq];
            let influenced = compute_piece_influence_at(&self.board, sq);
            for &t in &influenced {
                if color { self.white_control[t as usize].push(sq as u8); }
                else      { self.black_control[t as usize].push(sq as u8); }
            }
            self.influence[sq] = influenced;
        }
    }

    fn recompute_hyp_dirty(&mut self) {
        for sq in 0..TOTAL_SQUARES {
            if !self.dirty[sq] || !is_playable(sq) { continue; }
            for pt in 1..=NUM_PIECE_TYPES as u8 {
                self.hyp_threats[sq][pt as usize] = compute_hyp_threats(&self.board, sq, pt);
            }
            self.dirty[sq] = false;
        }
    }

    fn recompute_all(&mut self) {
        self.recompute_influence();
        // Mark all squares dirty and recompute hyp_threats
        for sq in 0..TOTAL_SQUARES { self.dirty[sq] = is_playable(sq); }
        self.recompute_hyp_dirty();
    }

    pub fn push(&mut self, m: &WarpMove) {
        let from = m.from_sq as usize;
        let to   = m.to_sq as usize;
        // Mark dirty squares BEFORE the push (board state used for ray lookup)
        mark_dirty_for_move(&self.board, from, to, &mut self.dirty);
        // Handle flip squares too
        if m.flip_type != NO_FLIP {
            let ff = m.flip_from.max(0) as usize;
            let ft = m.flip_to.max(0) as usize;
            mark_dirty_for_move(&self.board, ff, ft, &mut self.dirty);
        }
        self.board.push(m);
        self.recompute_influence();
        self.recompute_hyp_dirty();
    }

    pub fn pop(&mut self) {
        self.board.pop();
        // After pop, just fully recompute — undo makes dirty tracking complex
        self.recompute_all();
    }

    /// Min moves for the piece at `attacker_sq` to reach `target_sq` (same side, empty-board BFS).
    pub fn distance(&self, attacker_sq: usize, target_sq: usize) -> u8 {
        if square_side(attacker_sq) != square_side(target_sq) { return INF_DIST; }
        let pt = self.board.pieces[attacker_sq];
        if pt == 0 { return INF_DIST; }
        let side = square_side(attacker_sq);
        let up = self.board.origins[attacker_sq] == side;
        piece_dist(pt, up, attacker_sq & 63, target_sq & 63)
    }

    /// Min moves for piece at `attacker_sq` to reach a square from which it threatens `target_sq`.
    /// Returns (distance, staging_square).
    pub fn min_moves_to_threaten(&self, attacker_sq: usize, target_sq: usize) -> (u8, usize) {
        let pt = self.board.pieces[attacker_sq];
        if pt == 0 { return (INF_DIST, 0); }
        let side = square_side(attacker_sq);
        let up = self.board.origins[attacker_sq] == side;
        let mut best_dist = INF_DIST;
        let mut best_staging = 0usize;
        // Check all squares on the same side as a potential staging square
        for staging in 0..TOTAL_SQUARES {
            if square_side(staging) != side || !is_playable(staging) { continue; }
            let threats = &self.hyp_threats[staging][pt as usize];
            if threats.contains(&(target_sq as u8)) {
                let d = piece_dist(pt, up, attacker_sq & 63, staging & 63);
                if d < best_dist {
                    best_dist = d;
                    best_staging = staging;
                }
            }
        }
        (best_dist, best_staging)
    }

    /// Balance per square: positive = white dominates, negative = black. Range [-1, 1].
    pub fn influence_balance(&self) -> Vec<f32> {
        (0..TOTAL_SQUARES).map(|sq| {
            if !is_playable(sq) { return 0.0f32; }
            let w = self.white_control[sq].len() as f32;
            let b = self.black_control[sq].len() as f32;
            let total = w + b;
            if total == 0.0 { 0.0 } else { (w - b) / total }
        }).collect()
    }
}

/// Compute all squares the piece at `sq` currently influences.
fn compute_piece_influence_at(board: &WarpBoardInner, sq: usize) -> Vec<u8> {
    let pt = board.pieces[sq];
    if pt == 0 || !is_playable(sq) { return Vec::new(); }
    compute_hyp_threats(board, sq, pt)
}
