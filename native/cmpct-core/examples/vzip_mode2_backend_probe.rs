//! Scientific native raw-Deflate equivalence probe for revision-24 VZIP stream mode 2.
//!
//! This is a detached experiment binary; it does not implement native archive dispatch, does not
//! change the reader, and must not be treated as native VZIP mode-2 product support.
//! Raw DEFLATE via flate2's exact current Cargo backend is compared by the separate Python court
//! against CPython's zlib(-15) stream, *not* against only decoded payload equality.
use flate2::{write::DeflateEncoder, Compression};
use std::io::{self, Read, Write};

const MAX_PROBE_BYTES: usize = 1024 * 1024;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let level: u32 = std::env::args()
        .nth(1)
        .ok_or("usage: vzip_mode2_backend_probe <level 0..9> < input > raw-deflate")?
        .parse()?;
    if level > 9 {
        return Err("level must be 0..9".into());
    }

    // Deliberately bounded because this is an oracle, not a streaming product implementation.
    let mut input = Vec::new();
    io::stdin()
        .take((MAX_PROBE_BYTES + 1) as u64)
        .read_to_end(&mut input)?;
    if input.len() > MAX_PROBE_BYTES {
        return Err("probe input exceeds 1 MiB scientific budget".into());
    }
    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::new(level));
    encoder.write_all(&input)?;
    let deflate = encoder.finish()?;
    io::stdout().write_all(&deflate)?;
    Ok(())
}
