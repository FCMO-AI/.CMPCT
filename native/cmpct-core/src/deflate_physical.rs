//! Authenticated access to the exact physical RFC-1951 payload of a revision-24 codec-4 blob.
//!
//! Virtual-ZIP Deflate stream mode 0 reuses those compressed bytes directly. The caller must never
//! decode and recompress: an equivalent Deflate stream is insufficient because the nested ZIP is
//! required to reconstruct byte-for-byte. This component therefore authenticates the compressed
//! stream by decoding it to the blob's declared logical bytes and checking the logical SHA-256 before
//! exposing any requested physical compressed slice.

use flate2::read::DeflateDecoder;
use sha2::{Digest, Sha256};
use std::io::{Cursor, Read};
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum PhysicalDeflateError {
    #[error("physical Deflate object exceeds the native handler resource limit")]
    ResourceLimit,
    #[error("requested physical Deflate range is outside the compressed payload")]
    Range,
    #[error("raw Deflate stream is malformed")]
    Decode,
    #[error("decoded Deflate length disagrees with authenticated blob metadata")]
    LogicalLength,
    #[error("decoded Deflate SHA-256 disagrees with authenticated blob identity")]
    LogicalHash,
}

/// Copy an exact range from a raw RFC-1951 payload only after authenticating its logical content.
///
/// `max_object_bytes` applies independently to both the compressed and decoded sizes. This is a
/// correctness-first bridge for virtual-ZIP mode 0: revision 24 does not carry a separate hash over
/// compressed payload bytes, so the safe way to trust the physical stream is to decode the bounded
/// object and verify the blob's authenticated logical identity before returning any compressed bytes.
pub fn authenticated_range(
    compressed: &[u8],
    logical_size: u64,
    expected_logical_sha256: &[u8; 32],
    start: u64,
    out: &mut [u8],
    max_object_bytes: u64,
) -> Result<(), PhysicalDeflateError> {
    let compressed_len = u64::try_from(compressed.len()).map_err(|_| PhysicalDeflateError::ResourceLimit)?;
    if compressed_len > max_object_bytes || logical_size > max_object_bytes {
        return Err(PhysicalDeflateError::ResourceLimit);
    }

    let end = start
        .checked_add(u64::try_from(out.len()).map_err(|_| PhysicalDeflateError::Range)?)
        .ok_or(PhysicalDeflateError::Range)?;
    if end > compressed_len {
        return Err(PhysicalDeflateError::Range);
    }

    let logical_capacity = usize::try_from(logical_size).map_err(|_| PhysicalDeflateError::ResourceLimit)?;
    let decoder = DeflateDecoder::new(Cursor::new(compressed));
    let mut limited = decoder.take(logical_size.saturating_add(1));
    let mut decoded = Vec::with_capacity(logical_capacity);
    limited
        .read_to_end(&mut decoded)
        .map_err(|_| PhysicalDeflateError::Decode)?;
    if decoded.len() as u64 != logical_size {
        return Err(PhysicalDeflateError::LogicalLength);
    }
    if Sha256::digest(&decoded).as_slice() != expected_logical_sha256 {
        return Err(PhysicalDeflateError::LogicalHash);
    }

    let start = usize::try_from(start).map_err(|_| PhysicalDeflateError::Range)?;
    let end = start.checked_add(out.len()).ok_or(PhysicalDeflateError::Range)?;
    out.copy_from_slice(&compressed[start..end]);
    Ok(())
}
