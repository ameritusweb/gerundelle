//! Core types and constants for Warp 1 Chess.

pub const BOARD_FILES: usize = 8;
pub const BOARD_RANKS: usize = 7;
pub const SQUARES_PER_SIDE: usize = 64; // padded 8x8
pub const TOTAL_SQUARES: usize = 128;
pub const LEFT: u8 = 0;
pub const RIGHT: u8 = 1;

// Piece types
pub const PAWN: u8 = 1;
pub const KNIGHT: u8 = 2;
pub const BISHOP: u8 = 3;
pub const ROOK: u8 = 4;
pub const QUEEN: u8 = 5;
pub const KING: u8 = 6;
pub const CRAB: u8 = 7;
pub const NUM_PIECE_TYPES: usize = 7;

// Flip types
pub const NO_FLIP: u8 = 0;
pub const PRE_FLIP: u8 = 1;
pub const POST_FLIP: u8 = 2;

// Castling flags
pub const WK: u8 = 1;
pub const WQ: u8 = 2;
pub const BK: u8 = 4;
pub const BQ: u8 = 8;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct WarpMove {
    pub from_sq: u8,
    pub to_sq: u8,
    pub promotion: Option<u8>,
    pub flip_type: u8,
    pub flip_from: i16,
    pub flip_to: i16,
}

impl WarpMove {
    pub fn new(from_sq: u8, to_sq: u8) -> Self {
        Self { from_sq, to_sq, promotion: None, flip_type: NO_FLIP, flip_from: -1, flip_to: -1 }
    }

    pub fn with_promo(from_sq: u8, to_sq: u8, promo: u8) -> Self {
        Self { from_sq, to_sq, promotion: Some(promo), flip_type: NO_FLIP, flip_from: -1, flip_to: -1 }
    }

    pub fn with_flip(from_sq: u8, to_sq: u8, flip_type: u8, flip_from: i16, flip_to: i16) -> Self {
        Self { from_sq, to_sq, promotion: None, flip_type, flip_from, flip_to }
    }

    pub fn with_flip_promo(from_sq: u8, to_sq: u8, promo: u8, flip_type: u8, flip_from: i16, flip_to: i16) -> Self {
        Self { from_sq, to_sq, promotion: Some(promo), flip_type, flip_from, flip_to }
    }
}

// Square utilities
#[inline(always)]
pub fn square(side: u8, file: usize, rank: usize) -> usize {
    side as usize * 64 + rank * 8 + file
}

#[inline(always)]
pub fn square_side(sq: usize) -> u8 {
    (sq >> 6) as u8
}

#[inline(always)]
pub fn square_file(sq: usize) -> usize {
    sq & 7
}

#[inline(always)]
pub fn square_rank(sq: usize) -> usize {
    (sq >> 3) & 7
}

#[inline(always)]
pub fn flip_square(sq: usize) -> usize {
    sq ^ 64
}

#[inline(always)]
pub fn is_playable(sq: usize) -> bool {
    square_rank(sq) < BOARD_RANKS
}

// Piece values (for material counting)
pub const PIECE_VALUES: [i32; 8] = [0, 1, 3, 3, 5, 9, 0, 3]; // indexed by piece type
