//! FEN serialization for Warp 1 Chess.

use crate::types::*;
use crate::board::WarpBoardInner;

const PIECE_CHARS: [char; 8] = [' ', 'P', 'N', 'B', 'R', 'Q', 'K', 'C'];

pub fn to_fen(board: &WarpBoardInner) -> String {
    let mut parts = Vec::new();

    for side in [LEFT, RIGHT] {
        let mut ranks = Vec::new();
        for ri in 0..BOARD_RANKS {
            let r = BOARD_RANKS - 1 - ri;
            let mut empty = 0;
            let mut rank_str = String::new();
            for f in 0..BOARD_FILES {
                let sq = square(side, f, r);
                let pt = board.pieces[sq];
                if pt == 0 {
                    empty += 1;
                } else {
                    if empty > 0 {
                        rank_str.push_str(&empty.to_string());
                        empty = 0;
                    }
                    let ch = PIECE_CHARS[pt as usize];
                    let color = board.colors[sq];
                    let ch = if color { ch } else { ch.to_lowercase().next().unwrap() };
                    rank_str.push(ch);
                    let default_origin = if color { LEFT } else { RIGHT };
                    if board.origins[sq] != default_origin {
                        rank_str.push('~');
                    }
                }
            }
            if empty > 0 {
                rank_str.push_str(&empty.to_string());
            }
            ranks.push(rank_str);
        }
        parts.push(ranks.join("/"));
    }

    let board_str = parts.join("|||");
    let turn_str = if board.turn { "w" } else { "b" };

    let mut castle_str = String::new();
    if board.castling & WK != 0 { castle_str.push('K'); }
    if board.castling & WQ != 0 { castle_str.push('Q'); }
    if board.castling & BK != 0 { castle_str.push('k'); }
    if board.castling & BQ != 0 { castle_str.push('q'); }
    if castle_str.is_empty() { castle_str.push('-'); }

    let ep_str = if board.en_passant >= 0 {
        let sq = board.en_passant as usize;
        let side_ch = if square_side(sq) == LEFT { 'L' } else { 'R' };
        let file_ch = (b'a' + square_file(sq) as u8) as char;
        let rank_ch = (b'1' + square_rank(sq) as u8) as char;
        format!("{}{}{}", side_ch, file_ch, rank_ch)
    } else {
        "-".into()
    };

    format!("{} {} {} {} {} {}", board_str, turn_str, castle_str, ep_str,
            board.halfmove_clock, board.fullmove_number)
}

pub fn parse_fen(fen: &str) -> Result<WarpBoardInner, String> {
    let parts: Vec<&str> = fen.split(' ').collect();
    if parts.len() != 6 {
        return Err("FEN must have 6 space-separated parts".into());
    }

    let mut board = WarpBoardInner::new();

    let board_parts: Vec<&str> = parts[0].split("|||").collect();
    if board_parts.len() != 2 {
        return Err("Board must have two sides separated by |||".into());
    }

    for (si, &side_str) in board_parts.iter().enumerate() {
        let side = si as u8;
        let ranks: Vec<&str> = side_str.split('/').collect();

        for (ri, rank_str) in ranks.iter().enumerate() {
            if ri >= BOARD_RANKS { continue; } // skip padding rank (rank 8)
            let r = BOARD_RANKS - 1 - ri;
            let mut f = 0usize;
            let mut chars = rank_str.chars().peekable();

            while let Some(ch) = chars.next() {
                if ch.is_ascii_digit() {
                    f += ch.to_digit(10).unwrap() as usize;
                    continue;
                }

                let pt = match ch.to_uppercase().next().unwrap() {
                    'P' => PAWN, 'N' => KNIGHT, 'B' => BISHOP,
                    'R' => ROOK, 'Q' => QUEEN, 'K' => KING, 'C' => CRAB,
                    _ => return Err(format!("Unknown piece: {}", ch)),
                };
                let color = ch.is_uppercase();
                let has_marker = chars.peek() == Some(&'~');
                if has_marker { chars.next(); }

                let sq = square(side, f, r);
                let default_origin = if color { LEFT } else { RIGHT };
                let orig = if has_marker { 1 - default_origin } else { default_origin };

                board.pieces[sq] = pt;
                board.colors[sq] = color;
                board.origins[sq] = orig;
                if pt == KING {
                    let idx = if color { 0 } else { 1 };
                    board.king_sq[idx] = sq as i16;
                }
                f += 1;
            }
        }
    }

    board.turn = parts[1] == "w";

    if parts[2] != "-" {
        for ch in parts[2].chars() {
            match ch {
                'K' => board.castling |= WK,
                'Q' => board.castling |= WQ,
                'k' => board.castling |= BK,
                'q' => board.castling |= BQ,
                _ => {}
            }
        }
    }

    if parts[3] != "-" {
        let ep_chars: Vec<char> = parts[3].chars().collect();
        if ep_chars.len() == 3 {
            let side = if ep_chars[0] == 'L' { LEFT } else { RIGHT };
            let file = (ep_chars[1] as u8 - b'a') as usize;
            let rank = (ep_chars[2] as u8 - b'1') as usize;
            board.en_passant = square(side, file, rank) as i16;
        }
    }

    board.halfmove_clock = parts[4].parse().unwrap_or(0);
    board.fullmove_number = parts[5].parse().unwrap_or(1);
    board.hash = board.compute_hash();

    Ok(board)
}
