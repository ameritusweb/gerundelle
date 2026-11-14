//! Pre-computed attack tables for Warp 1 Chess (8x7 boards padded to 8x8).

use crate::types::*;
use std::sync::LazyLock;

const KNIGHT_DELTAS: [(i32, i32); 8] = [
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
];

const KING_DELTAS: [(i32, i32); 8] = [
    (-1, -1), (-1, 0), (-1, 1), (0, -1),
    (0, 1), (1, -1), (1, 0), (1, 1),
];

const BISHOP_DIRS: [(i32, i32); 4] = [(-1, -1), (-1, 1), (1, -1), (1, 1)];
const ROOK_DIRS: [(i32, i32); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];

/// Attack table: for each local square (0-63), a list of attacked local squares.
pub type AttackTable = Vec<Vec<u8>>;

/// Ray table: for each local square, for each direction, ordered list of squares.
pub type RayTable = Vec<Vec<Vec<u8>>>;

fn compute_jump_attacks(deltas: &[(i32, i32)]) -> AttackTable {
    let mut table = Vec::with_capacity(64);
    for sq in 0..64u8 {
        let f = (sq % 8) as i32;
        let r = (sq / 8) as i32;
        let mut targets = Vec::new();
        for &(df, dr) in deltas {
            let nf = f + df;
            let nr = r + dr;
            if nf >= 0 && nf < BOARD_FILES as i32 && nr >= 0 && nr < BOARD_RANKS as i32 {
                targets.push((nr * 8 + nf) as u8);
            }
        }
        table.push(targets);
    }
    table
}

fn compute_rays(dirs: &[(i32, i32)]) -> RayTable {
    let mut table = Vec::with_capacity(64);
    for sq in 0..64u8 {
        let f = (sq % 8) as i32;
        let r = (sq / 8) as i32;
        let mut sq_rays = Vec::new();
        for &(df, dr) in dirs {
            let mut ray = Vec::new();
            let mut nf = f + df;
            let mut nr = r + dr;
            while nf >= 0 && nf < BOARD_FILES as i32 && nr >= 0 && nr < BOARD_RANKS as i32 {
                ray.push((nr * 8 + nf) as u8);
                nf += df;
                nr += dr;
            }
            sq_rays.push(ray);
        }
        table.push(sq_rays);
    }
    table
}

fn compute_pawn_attacks(up: bool) -> AttackTable {
    let mut table = Vec::with_capacity(64);
    let dr = if up { 1i32 } else { -1 };
    for sq in 0..64u8 {
        let f = (sq % 8) as i32;
        let r = (sq / 8) as i32;
        let mut targets = Vec::new();
        for df in [-1i32, 1] {
            let nf = f + df;
            let nr = r + dr;
            if nf >= 0 && nf < BOARD_FILES as i32 && nr >= 0 && nr < BOARD_RANKS as i32 {
                targets.push((nr * 8 + nf) as u8);
            }
        }
        table.push(targets);
    }
    table
}

pub static KNIGHT_ATTACKS: LazyLock<AttackTable> = LazyLock::new(|| compute_jump_attacks(&KNIGHT_DELTAS));
pub static KING_ATTACKS: LazyLock<AttackTable> = LazyLock::new(|| compute_jump_attacks(&KING_DELTAS));
pub static PAWN_ATTACKS_UP: LazyLock<AttackTable> = LazyLock::new(|| compute_pawn_attacks(true));
pub static PAWN_ATTACKS_DOWN: LazyLock<AttackTable> = LazyLock::new(|| compute_pawn_attacks(false));
pub static BISHOP_RAYS: LazyLock<RayTable> = LazyLock::new(|| compute_rays(&BISHOP_DIRS));
pub static ROOK_RAYS: LazyLock<RayTable> = LazyLock::new(|| compute_rays(&ROOK_DIRS));
pub static QUEEN_RAYS: LazyLock<RayTable> = LazyLock::new(|| {
    let mut dirs = Vec::from(BISHOP_DIRS);
    dirs.extend_from_slice(&ROOK_DIRS);
    compute_rays(&dirs)
});

/// Crab attacks = king attacks
#[inline(always)]
pub fn crab_attacks(local_sq: u8) -> &'static Vec<u8> {
    &KING_ATTACKS[local_sq as usize]
}

/// Get sliding piece attacks given occupancy bitmask for one side.
pub fn sliding_attacks(local_sq: u8, piece_type: u8, occupied: u64) -> Vec<u8> {
    let rays = match piece_type {
        BISHOP => &BISHOP_RAYS[local_sq as usize],
        ROOK => &ROOK_RAYS[local_sq as usize],
        QUEEN => &QUEEN_RAYS[local_sq as usize],
        _ => return Vec::new(),
    };
    let mut targets = Vec::new();
    for ray in rays {
        for &rsq in ray {
            targets.push(rsq);
            if occupied & (1u64 << rsq) != 0 {
                break;
            }
        }
    }
    targets
}
