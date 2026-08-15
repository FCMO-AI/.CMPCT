//! Revision-24 committed-generation recovery for the native reader.
//!
//! A CMPCT mutation is committed only when its 68-byte `CMPTF24\0` footer has been durably written.
//! Generation payload bytes and newly appended blob records may precede that marker, so a torn append
//! is ignored by scanning backward for the newest footer whose complete parent chain validates. This
//! module mirrors the Python reference semantics without depending on the primary index being readable.

#[path = "msgpack_guard.rs"]
mod msgpack_guard;

use rmpv::Value;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::fs::File;
use std::io::{Cursor, Read, Seek, SeekFrom};
use thiserror::Error;

const FOOTER_MAGIC: &[u8; 8] = b"CMPTF24\0";
const FOOTER_SIZE: u64 = 68;
const SCAN_BLOCK: usize = 1024 * 1024;
const GENERATION_CHECKPOINT: u8 = 0;
const GENERATION_DELTA: u8 = 1;
const CODEC_RAW: u8 = 0;
const CODEC_ZSTD: u8 = 1;
const MAX_FILES: usize = 4_000_000;
const MAX_BLOBS: usize = 4_000_000;
const MAX_RECIPES: u64 = 1_000_000;
const MAX_PATH_BYTES: u64 = 1024 * 1024;
const MAX_MSGPACK_DEPTH: usize = 1024;
const MAX_MSGPACK_NODES: u64 = 16_000_000;

#[derive(Debug, Error)]
pub enum RecoveryError {
    #[error("generation I/O failed: {0}")]
    Io(#[from] std::io::Error),
    #[error("generation payload exceeds native recovery limit")]
    Limit,
    #[error("generation payload is malformed")]
    Malformed,
}

#[derive(Debug)]
pub struct RecoveredIndex {
    pub index: Value,
    pub footer_pos: u64,
    pub delta_depth: usize,
    /// Exclusive upper bound for physical blob records referenced by this committed generation.
    /// The latest generation payload begins here; uncommitted bytes after its footer are never trusted.
    pub committed_data_end: u64,
}

#[derive(Debug)]
struct Generation {
    kind: u8,
    payload: Value,
    previous_footer: u64,
    payload_start: u64,
}

fn le_u64(bytes: &[u8]) -> u64 {
    u64::from_le_bytes(bytes.try_into().expect("fixed footer slice"))
}

fn map_value<'a>(value: &'a Value, key: &str) -> Option<&'a Value> {
    value
        .as_map()?
        .iter()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
}

fn map_value_mut<'a>(value: &'a mut Value, key: &str) -> Option<&'a mut Value> {
    value
        .as_map_mut()?
        .iter_mut()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
}

fn guard_messagepack(payload: &[u8], max_payload_bytes: u64) -> Result<(), RecoveryError> {
    msgpack_guard::validate(
        payload,
        msgpack_guard::GuardLimits {
            max_string_bytes: MAX_PATH_BYTES.max(1024 * 1024),
            max_binary_bytes: max_payload_bytes,
            max_array_items: MAX_FILES.max(MAX_BLOBS) as u64,
            max_map_items: MAX_FILES.max(MAX_BLOBS).max(MAX_RECIPES as usize) as u64,
            max_depth: MAX_MSGPACK_DEPTH,
            max_nodes: MAX_MSGPACK_NODES,
        },
    )
    .map_err(|error| match error {
        msgpack_guard::GuardError::Limit => RecoveryError::Limit,
        _ => RecoveryError::Malformed,
    })
}

fn decode_payload(
    file: &mut File,
    footer_pos: u64,
    file_len: u64,
    max_payload_bytes: u64,
) -> Result<Generation, RecoveryError> {
    if footer_pos.checked_add(FOOTER_SIZE).is_none() || footer_pos + FOOTER_SIZE > file_len {
        return Err(RecoveryError::Malformed);
    }
    file.seek(SeekFrom::Start(footer_pos))?;
    let mut footer = [0u8; FOOTER_SIZE as usize];
    file.read_exact(&mut footer)?;
    if &footer[0..8] != FOOTER_MAGIC {
        return Err(RecoveryError::Malformed);
    }
    let kind = footer[8];
    let codec = footer[9];
    let flags = footer[10];
    let reserved = footer[11];
    if kind != GENERATION_CHECKPOINT && kind != GENERATION_DELTA {
        return Err(RecoveryError::Malformed);
    }
    if codec != CODEC_RAW && codec != CODEC_ZSTD || flags != 0 || reserved != 0 {
        return Err(RecoveryError::Malformed);
    }
    let compressed_len = le_u64(&footer[12..20]);
    let uncompressed_len = le_u64(&footer[20..28]);
    let previous_footer = le_u64(&footer[28..36]);
    if compressed_len > max_payload_bytes || uncompressed_len > max_payload_bytes {
        return Err(RecoveryError::Limit);
    }
    if compressed_len > footer_pos {
        return Err(RecoveryError::Malformed);
    }
    if previous_footer != 0
        && (previous_footer >= footer_pos
            || previous_footer
                .checked_add(FOOTER_SIZE)
                .is_none_or(|end| end > file_len))
    {
        return Err(RecoveryError::Malformed);
    }
    let payload_start = footer_pos - compressed_len;
    let compressed_len_usize =
        usize::try_from(compressed_len).map_err(|_| RecoveryError::Limit)?;
    file.seek(SeekFrom::Start(payload_start))?;
    let mut encoded = vec![0u8; compressed_len_usize];
    file.read_exact(&mut encoded)?;

    let payload_bytes = if codec == CODEC_RAW {
        if compressed_len != uncompressed_len {
            return Err(RecoveryError::Malformed);
        }
        encoded
    } else {
        let decoder = zstd::stream::read::Decoder::new(Cursor::new(encoded))?;
        let mut limited = decoder.take(uncompressed_len.saturating_add(1));
        let capacity = usize::try_from(uncompressed_len).map_err(|_| RecoveryError::Limit)?;
        let mut decoded = Vec::with_capacity(capacity);
        limited.read_to_end(&mut decoded)?;
        if decoded.len() as u64 != uncompressed_len {
            return Err(RecoveryError::Malformed);
        }
        decoded
    };

    if payload_bytes.len() as u64 != uncompressed_len
        || Sha256::digest(&payload_bytes).as_slice() != &footer[36..68]
    {
        return Err(RecoveryError::Malformed);
    }
    guard_messagepack(&payload_bytes, max_payload_bytes)?;
    let mut cursor = Cursor::new(payload_bytes.as_slice());
    let payload =
        rmpv::decode::read_value(&mut cursor).map_err(|_| RecoveryError::Malformed)?;
    if cursor.position() != payload_bytes.len() as u64 {
        return Err(RecoveryError::Malformed);
    }
    Ok(Generation {
        kind,
        payload,
        previous_footer,
        payload_start,
    })
}

fn file_row_path(value: &Value) -> Option<&str> {
    value.as_array()?.first()?.as_str()
}

fn apply_delta(index: &mut Value, delta: &Value) -> Result<(), RecoveryError> {
    let new_blobs = map_value(delta, "blobs")
        .and_then(Value::as_array)
        .ok_or(RecoveryError::Malformed)?;
    let blobs = map_value_mut(index, "blobs")
        .and_then(Value::as_array_mut)
        .ok_or(RecoveryError::Malformed)?;
    if blobs.len().saturating_add(new_blobs.len()) > MAX_BLOBS {
        return Err(RecoveryError::Limit);
    }
    blobs.extend(new_blobs.iter().cloned());

    let operations = map_value(delta, "ops")
        .and_then(Value::as_array)
        .ok_or(RecoveryError::Malformed)?;
    let files = map_value_mut(index, "files")
        .and_then(Value::as_array_mut)
        .ok_or(RecoveryError::Malformed)?;

    for operation in operations {
        let row = operation.as_array().ok_or(RecoveryError::Malformed)?;
        let opcode = row
            .first()
            .and_then(Value::as_str)
            .ok_or(RecoveryError::Malformed)?;
        match opcode {
            "put" if row.len() == 2 => {
                let replacement = row.get(1).cloned().ok_or(RecoveryError::Malformed)?;
                // Footnote: own the path before moving `replacement` into the canonical file table.
                // Borrowing the path from the MessagePack row while replacing/pushing that same row
                // is both unnecessary and rejected by Rust's aliasing rules.
                let path = file_row_path(&replacement)
                    .ok_or(RecoveryError::Malformed)?
                    .to_owned();
                if let Some(slot) = files
                    .iter_mut()
                    .find(|candidate| file_row_path(candidate) == Some(path.as_str()))
                {
                    *slot = replacement;
                } else {
                    if files.len() >= MAX_FILES {
                        return Err(RecoveryError::Limit);
                    }
                    files.push(replacement);
                }
            }
            "del" if row.len() == 2 => {
                let path = row
                    .get(1)
                    .and_then(Value::as_str)
                    .ok_or(RecoveryError::Malformed)?;
                files.retain(|candidate| file_row_path(candidate) != Some(path));
            }
            "ren" if row.len() == 3 => {
                let old = row
                    .get(1)
                    .and_then(Value::as_str)
                    .ok_or(RecoveryError::Malformed)?;
                let new = row
                    .get(2)
                    .and_then(Value::as_str)
                    .ok_or(RecoveryError::Malformed)?;
                if let Some(candidate) = files
                    .iter_mut()
                    .find(|candidate| file_row_path(candidate) == Some(old))
                {
                    let candidate = candidate.as_array_mut().ok_or(RecoveryError::Malformed)?;
                    if candidate.is_empty() {
                        return Err(RecoveryError::Malformed);
                    }
                    candidate[0] = Value::from(new);
                }
            }
            _ => return Err(RecoveryError::Malformed),
        }
    }
    files.sort_by(|left, right| file_row_path(left).cmp(&file_row_path(right)));
    Ok(())
}

fn recover_from_footer(
    file: &mut File,
    footer_pos: u64,
    file_len: u64,
    max_payload_bytes: u64,
    max_generations: usize,
) -> Result<RecoveredIndex, RecoveryError> {
    let mut chain = Vec::new();
    let mut seen = HashSet::new();
    let mut pos = footer_pos;
    let mut newest_payload_start = None;

    for depth in 0..=max_generations {
        if pos == 0 || !seen.insert(pos) {
            return Err(RecoveryError::Malformed);
        }
        let generation = decode_payload(file, pos, file_len, max_payload_bytes)?;
        if newest_payload_start.is_none() {
            newest_payload_start = Some(generation.payload_start);
        }
        if generation.kind == GENERATION_CHECKPOINT {
            let mut index = generation.payload;
            for delta in chain.iter().rev() {
                apply_delta(&mut index, delta)?;
            }
            return Ok(RecoveredIndex {
                index,
                footer_pos,
                delta_depth: depth,
                committed_data_end: newest_payload_start.ok_or(RecoveryError::Malformed)?,
            });
        }
        chain.push(generation.payload);
        pos = generation.previous_footer;
    }
    Err(RecoveryError::Limit)
}

/// Return the newest fully committed generation whose complete parent chain validates.
///
/// Footnote: a false-positive `CMPTF24\0` byte sequence inside compressed data is harmless. It is
/// accepted only if its footer bounds, payload hash, MessagePack value, generation kind, and entire
/// backward parent chain all validate. If the newest append is torn, scanning continues to the prior
/// valid footer exactly as the Python reference does.
pub fn latest_committed_index(
    file: &mut File,
    file_len: u64,
    max_payload_bytes: u64,
    max_generations: usize,
) -> Result<Option<RecoveredIndex>, RecoveryError> {
    if file_len < FOOTER_SIZE {
        return Ok(None);
    }
    let overlap = FOOTER_MAGIC.len().saturating_sub(1);
    let mut pos = file_len;
    let mut carry = Vec::new();

    while pos > 0 {
        let read_len = usize::try_from(pos.min(SCAN_BLOCK as u64)).map_err(|_| RecoveryError::Limit)?;
        pos -= read_len as u64;
        file.seek(SeekFrom::Start(pos))?;
        let mut chunk = vec![0u8; read_len];
        file.read_exact(&mut chunk)?;
        chunk.extend_from_slice(&carry);

        let mut search_end = chunk.len();
        while search_end >= FOOTER_MAGIC.len() {
            let found = chunk[..search_end]
                .windows(FOOTER_MAGIC.len())
                .rposition(|window| window == FOOTER_MAGIC);
            let Some(index) = found else { break };
            let absolute = pos
                .checked_add(index as u64)
                .ok_or(RecoveryError::Limit)?;
            if absolute
                .checked_add(FOOTER_SIZE)
                .is_some_and(|end| end <= file_len)
            {
                if let Ok(recovered) = recover_from_footer(
                    file,
                    absolute,
                    file_len,
                    max_payload_bytes,
                    max_generations,
                ) {
                    return Ok(Some(recovered));
                }
            }
            search_end = index;
        }

        let keep = overlap.min(chunk.len());
        carry.clear();
        carry.extend_from_slice(&chunk[..keep]);
    }
    Ok(None)
}
