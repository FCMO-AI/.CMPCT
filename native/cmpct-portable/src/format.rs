use crate::PortableError;
use rmpv::Value;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::io::{BufReader, Cursor, Read};
use std::path::PathBuf;

pub(crate) const MAX_META_BYTES: u64 = 8 * 1024 * 1024;
pub(crate) const MAX_PATH_BYTES: usize = 16 * 1024;
pub(crate) const MAX_VALUE_DEPTH: usize = 64;
pub(crate) const MAX_VALUE_NODES: usize = 1_000_000;

pub(crate) fn u32_le(bytes: &[u8]) -> Result<u32, PortableError> {
    let raw: [u8; 4] = bytes
        .try_into()
        .map_err(|_| PortableError::Format("short little-endian u32".into()))?;
    Ok(u32::from_le_bytes(raw))
}

pub(crate) fn u64_le(bytes: &[u8]) -> Result<u64, PortableError> {
    let raw: [u8; 8] = bytes
        .try_into()
        .map_err(|_| PortableError::Format("short little-endian u64".into()))?;
    Ok(u64::from_le_bytes(raw))
}

pub(crate) fn sha256(data: &[u8]) -> [u8; 32] {
    Sha256::digest(data).into()
}

pub(crate) fn digest32(value: &Value, label: &str) -> Result<[u8; 32], PortableError> {
    let Value::Binary(bytes) = value else {
        return Err(PortableError::Format(format!("{label} must be binary")));
    };
    bytes
        .as_slice()
        .try_into()
        .map_err(|_| PortableError::Format(format!("{label} must be a 32-byte digest")))
}

pub(crate) fn bounded_zstd_decode(
    compressed: &[u8],
    expected_size: u64,
    limit: u64,
    dictionary: Option<&[u8]>,
) -> Result<Vec<u8>, PortableError> {
    if expected_size > limit || compressed.len() as u64 > limit.saturating_add(1024 * 1024) {
        return Err(PortableError::Limit(
            "zstd decode declaration exceeds policy".into(),
        ));
    }
    let capacity = usize::try_from(expected_size)
        .map_err(|_| PortableError::Limit("zstd output does not fit host address space".into()))?;
    // Footnote: `Decoder::new(Read)` inserts its own `BufReader`, while `with_dictionary` accepts an
    // already-buffered reader. Feeding both branches the same explicit `BufReader<Cursor<_>>` and using
    // `with_buffer` for the dictionary-free branch keeps one concrete decoder type without dynamic dispatch.
    let reader = BufReader::new(Cursor::new(compressed));
    let decoder = match dictionary {
        Some(dict) => zstd::stream::read::Decoder::with_dictionary(reader, dict),
        None => zstd::stream::read::Decoder::with_buffer(reader),
    }
    .map_err(|error| PortableError::Format(format!("zstd decoder init: {error}")))?;
    let mut limited = decoder.take(expected_size.saturating_add(1));
    let mut out = Vec::with_capacity(capacity);
    limited
        .read_to_end(&mut out)
        .map_err(|error| PortableError::Format(format!("zstd decode: {error}")))?;
    if out.len() as u64 != expected_size {
        return Err(PortableError::Integrity(format!(
            "zstd decoded {} bytes, expected {expected_size}",
            out.len()
        )));
    }
    Ok(out)
}

fn key_token(value: &Value) -> Result<Vec<u8>, PortableError> {
    let mut out = Vec::new();
    match value {
        Value::Nil => out.extend_from_slice(b"n"),
        Value::Boolean(value) => {
            out.extend_from_slice(b"b");
            out.push(u8::from(*value));
        }
        Value::Integer(value) => {
            out.extend_from_slice(b"i");
            out.extend_from_slice(value.to_string().as_bytes());
        }
        Value::String(value) => {
            out.extend_from_slice(b"s");
            let text = value.as_str().ok_or_else(|| {
                PortableError::Format("MessagePack map key is not valid UTF-8".into())
            })?;
            out.extend_from_slice(text.as_bytes());
        }
        Value::Binary(value) => {
            out.extend_from_slice(b"x");
            out.extend_from_slice(value);
        }
        _ => {
            return Err(PortableError::Format(
                "container/float MessagePack map keys are not admitted by r25 metadata".into(),
            ));
        }
    }
    Ok(out)
}

fn validate_value(value: &Value, depth: usize, nodes: &mut usize) -> Result<(), PortableError> {
    if depth > MAX_VALUE_DEPTH {
        return Err(PortableError::Limit(
            "MessagePack nesting exceeds policy".into(),
        ));
    }
    *nodes = nodes
        .checked_add(1)
        .ok_or_else(|| PortableError::Limit("MessagePack node counter overflow".into()))?;
    if *nodes > MAX_VALUE_NODES {
        return Err(PortableError::Limit(
            "MessagePack node count exceeds policy".into(),
        ));
    }
    match value {
        Value::Array(values) => {
            for child in values {
                validate_value(child, depth + 1, nodes)?;
            }
        }
        Value::Map(rows) => {
            let mut seen = HashSet::with_capacity(rows.len().min(65_536));
            for (key, child) in rows {
                let token = key_token(key)?;
                if !seen.insert(token) {
                    return Err(PortableError::Format(
                        "duplicate MessagePack map key".into(),
                    ));
                }
                validate_value(key, depth + 1, nodes)?;
                validate_value(child, depth + 1, nodes)?;
            }
        }
        Value::String(value) => {
            let text = value
                .as_str()
                .ok_or_else(|| PortableError::Format("invalid UTF-8 MessagePack string".into()))?;
            if text.len() > MAX_META_BYTES as usize {
                return Err(PortableError::Limit(
                    "MessagePack string exceeds policy".into(),
                ));
            }
        }
        Value::Binary(value) if value.len() > MAX_META_BYTES as usize => {
            return Err(PortableError::Limit(
                "MessagePack binary exceeds policy".into(),
            ));
        }
        _ => {}
    }
    Ok(())
}

fn require_bytes(raw: &[u8], pos: usize, count: usize) -> Result<usize, PortableError> {
    let end = pos
        .checked_add(count)
        .ok_or_else(|| PortableError::Limit("MessagePack offset overflow".into()))?;
    if end > raw.len() {
        return Err(PortableError::Format(
            "truncated MessagePack declaration/body".into(),
        ));
    }
    Ok(end)
}

fn read_be_u16(raw: &[u8], pos: usize) -> Result<(usize, usize), PortableError> {
    let end = require_bytes(raw, pos, 2)?;
    Ok((u16::from_be_bytes([raw[pos], raw[pos + 1]]) as usize, end))
}

fn read_be_u32(raw: &[u8], pos: usize) -> Result<(usize, usize), PortableError> {
    let end = require_bytes(raw, pos, 4)?;
    let value = u32::from_be_bytes([raw[pos], raw[pos + 1], raw[pos + 2], raw[pos + 3]]);
    let value = usize::try_from(value).map_err(|_| {
        PortableError::Limit("MessagePack length does not fit host address space".into())
    })?;
    Ok((value, end))
}

fn preflight_leaf(raw: &[u8], pos: usize, body: usize) -> Result<usize, PortableError> {
    require_bytes(raw, pos, body)
}

fn preflight_blob(raw: &[u8], pos: usize, declared: usize) -> Result<usize, PortableError> {
    if declared > MAX_META_BYTES as usize {
        return Err(PortableError::Limit(
            "MessagePack string/binary declaration exceeds policy".into(),
        ));
    }
    require_bytes(raw, pos, declared)
}

fn preflight_children(
    raw: &[u8],
    mut pos: usize,
    count: usize,
    depth: usize,
    nodes: &mut usize,
) -> Result<usize, PortableError> {
    if count > MAX_VALUE_NODES.saturating_sub(*nodes) {
        return Err(PortableError::Limit(
            "MessagePack container declaration exceeds node policy".into(),
        ));
    }
    for _ in 0..count {
        pos = preflight_value(raw, pos, depth + 1, nodes)?;
    }
    Ok(pos)
}

fn preflight_value(
    raw: &[u8],
    pos: usize,
    depth: usize,
    nodes: &mut usize,
) -> Result<usize, PortableError> {
    if depth > MAX_VALUE_DEPTH {
        return Err(PortableError::Limit(
            "MessagePack nesting exceeds policy".into(),
        ));
    }
    let marker_end = require_bytes(raw, pos, 1)?;
    *nodes = nodes
        .checked_add(1)
        .ok_or_else(|| PortableError::Limit("MessagePack node counter overflow".into()))?;
    if *nodes > MAX_VALUE_NODES {
        return Err(PortableError::Limit(
            "MessagePack node count exceeds policy".into(),
        ));
    }
    let marker = raw[pos];
    match marker {
        0x00..=0x7f | 0xc0 | 0xc2 | 0xc3 | 0xe0..=0xff => Ok(marker_end),
        0x80..=0x8f => {
            let pairs = (marker & 0x0f) as usize;
            let children = pairs.checked_mul(2).ok_or_else(|| {
                PortableError::Limit("MessagePack map child count overflow".into())
            })?;
            preflight_children(raw, marker_end, children, depth, nodes)
        }
        0x90..=0x9f => preflight_children(raw, marker_end, (marker & 0x0f) as usize, depth, nodes),
        0xa0..=0xbf => preflight_blob(raw, marker_end, (marker & 0x1f) as usize),
        0xc1 => Err(PortableError::Format(
            "reserved MessagePack marker 0xc1 is not admitted".into(),
        )),
        0xc4 | 0xd9 => {
            let len_end = require_bytes(raw, marker_end, 1)?;
            preflight_blob(raw, len_end, raw[marker_end] as usize)
        }
        0xc5 | 0xda => {
            let (len, len_end) = read_be_u16(raw, marker_end)?;
            preflight_blob(raw, len_end, len)
        }
        0xc6 | 0xdb => {
            let (len, len_end) = read_be_u32(raw, marker_end)?;
            preflight_blob(raw, len_end, len)
        }
        // r25 metadata has no extension-type grammar. Rejecting ext declarations before rmpv runs prevents a
        // future caller from accidentally allocating an unbounded/unsupported extension payload.
        0xc7..=0xc9 | 0xd4..=0xd8 => Err(PortableError::Format(
            "MessagePack extension markers are not admitted by r25 metadata".into(),
        )),
        0xca => preflight_leaf(raw, marker_end, 4),
        0xcb => preflight_leaf(raw, marker_end, 8),
        0xcc | 0xd0 => preflight_leaf(raw, marker_end, 1),
        0xcd | 0xd1 => preflight_leaf(raw, marker_end, 2),
        0xce | 0xd2 => preflight_leaf(raw, marker_end, 4),
        0xcf | 0xd3 => preflight_leaf(raw, marker_end, 8),
        0xdc => {
            let (count, len_end) = read_be_u16(raw, marker_end)?;
            preflight_children(raw, len_end, count, depth, nodes)
        }
        0xdd => {
            let (count, len_end) = read_be_u32(raw, marker_end)?;
            preflight_children(raw, len_end, count, depth, nodes)
        }
        0xde => {
            let (pairs, len_end) = read_be_u16(raw, marker_end)?;
            let children = pairs.checked_mul(2).ok_or_else(|| {
                PortableError::Limit("MessagePack map child count overflow".into())
            })?;
            preflight_children(raw, len_end, children, depth, nodes)
        }
        0xdf => {
            let (pairs, len_end) = read_be_u32(raw, marker_end)?;
            let children = pairs.checked_mul(2).ok_or_else(|| {
                PortableError::Limit("MessagePack map child count overflow".into())
            })?;
            preflight_children(raw, len_end, children, depth, nodes)
        }
    }
}

fn preflight_msgpack(raw: &[u8]) -> Result<(), PortableError> {
    let mut nodes = 0usize;
    let end = preflight_value(raw, 0, 0, &mut nodes)?;
    if end != raw.len() {
        return Err(PortableError::Format(
            "trailing bytes after MessagePack root".into(),
        ));
    }
    Ok(())
}

pub(crate) fn parse_msgpack(raw: &[u8]) -> Result<Value, PortableError> {
    if raw.len() as u64 > MAX_META_BYTES {
        return Err(PortableError::Limit(
            "metadata exceeds decode-unit bound".into(),
        ));
    }
    // Footnote: this scan happens before rmpv sees hostile bytes. A ten-byte stream may declare a 4 GiB
    // array/string even though the compressed metadata itself is tiny; post-decode validation is too late if the
    // general decoder already reserved from that declaration. Keep the second validator as defense in depth.
    preflight_msgpack(raw)?;
    let mut cursor = Cursor::new(raw);
    let value = rmpv::decode::read_value(&mut cursor)
        .map_err(|error| PortableError::Format(format!("MessagePack decode: {error}")))?;
    if cursor.position() != raw.len() as u64 {
        return Err(PortableError::Format(
            "trailing bytes after MessagePack root".into(),
        ));
    }
    let mut nodes = 0;
    validate_value(&value, 0, &mut nodes)?;
    Ok(value)
}

pub(crate) fn as_map<'a>(
    value: &'a Value,
    label: &str,
) -> Result<&'a [(Value, Value)], PortableError> {
    value
        .as_map()
        .map(Vec::as_slice)
        .ok_or_else(|| PortableError::Format(format!("{label} must be a map")))
}

pub(crate) fn as_array<'a>(value: &'a Value, label: &str) -> Result<&'a [Value], PortableError> {
    value
        .as_array()
        .map(Vec::as_slice)
        .ok_or_else(|| PortableError::Format(format!("{label} must be an array")))
}

pub(crate) fn field<'a>(map: &'a [(Value, Value)], name: &str) -> Result<&'a Value, PortableError> {
    optional_field(map, name)
        .ok_or_else(|| PortableError::Format(format!("missing metadata field {name}")))
}

pub(crate) fn optional_field<'a>(map: &'a [(Value, Value)], name: &str) -> Option<&'a Value> {
    map.iter()
        .find_map(|(key, value)| (key.as_str() == Some(name)).then_some(value))
}

pub(crate) fn text<'a>(value: &'a Value, label: &str) -> Result<&'a str, PortableError> {
    value
        .as_str()
        .ok_or_else(|| PortableError::Format(format!("{label} must be UTF-8 text")))
}

pub(crate) fn uint(value: &Value, label: &str, maximum: u64) -> Result<u64, PortableError> {
    value
        .as_u64()
        .filter(|value| *value <= maximum)
        .ok_or_else(|| PortableError::Format(format!("{label} integer declaration")))
}

pub(crate) fn number(value: &Value, label: &str) -> Result<f64, PortableError> {
    let number = if let Some(value) = value.as_f64() {
        value
    } else if let Some(value) = value.as_i64() {
        value as f64
    } else if let Some(value) = value.as_u64() {
        value as f64
    } else {
        return Err(PortableError::Format(format!(
            "{label} numeric declaration"
        )));
    };
    if !number.is_finite() {
        return Err(PortableError::Format(format!(
            "{label} must be a finite numeric declaration"
        )));
    }
    Ok(number)
}

pub(crate) fn tree_digest(text: &str) -> Result<[u8; 32], PortableError> {
    if text.len() != 64 || !text.as_bytes().iter().all(u8::is_ascii_hexdigit) {
        return Err(PortableError::Format("tree SHA-256 declaration".into()));
    }
    let mut out = [0u8; 32];
    for (index, slot) in out.iter_mut().enumerate() {
        let pair = &text[index * 2..index * 2 + 2];
        *slot = u8::from_str_radix(pair, 16)
            .map_err(|_| PortableError::Format("tree SHA-256 hex declaration".into()))?;
    }
    Ok(out)
}

pub(crate) fn safe_relpath(rel: &str) -> Result<PathBuf, PortableError> {
    if rel.is_empty() || rel.starts_with('/') || rel.contains('\\') || rel.contains('\0') {
        return Err(PortableError::Path(rel.into()));
    }
    if rel.len() > MAX_PATH_BYTES {
        return Err(PortableError::Limit("logical path exceeds policy".into()));
    }
    let mut out = PathBuf::new();
    for part in rel.split('/') {
        if part.is_empty() || part == "." || part == ".." {
            return Err(PortableError::Path(rel.into()));
        }
        out.push(part);
    }
    Ok(out)
}

pub(crate) fn merkle_root(leaves: &[[u8; 32]]) -> [u8; 32] {
    if leaves.is_empty() {
        return sha256(b"cmpct-merkle-empty-v1");
    }
    let mut level: Vec<[u8; 32]> = leaves
        .iter()
        .map(|leaf| {
            let mut hasher = Sha256::new();
            hasher.update([0]);
            hasher.update(leaf);
            hasher.finalize().into()
        })
        .collect();
    while level.len() > 1 {
        if level.len() % 2 == 1 {
            let last = *level.last().expect("non-empty Merkle level");
            level.push(last);
        }
        level = level
            .chunks_exact(2)
            .map(|pair| {
                let mut hasher = Sha256::new();
                hasher.update([1]);
                hasher.update(pair[0]);
                hasher.update(pair[1]);
                hasher.finalize().into()
            })
            .collect();
    }
    level[0]
}

pub(crate) fn tree_hasher_prefix(hasher: &mut Sha256, rel: &str, size: u64) {
    let rel = rel.as_bytes();
    hasher.update((rel.len() as u32).to_le_bytes());
    hasher.update(rel);
    hasher.update(size.to_le_bytes());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preflight_rejects_huge_container_declarations_before_decode() {
        for raw in [
            vec![0xdd, 0xff, 0xff, 0xff, 0xff],
            vec![0xdf, 0x7f, 0xff, 0xff, 0xff],
            vec![0xc6, 0xff, 0xff, 0xff, 0xff],
            vec![0xdb, 0xff, 0xff, 0xff, 0xff],
        ] {
            assert!(parse_msgpack(&raw).is_err());
        }
    }

    #[test]
    fn preflight_rejects_truncated_and_reserved_markers() {
        assert!(parse_msgpack(&[0xcd, 0x01]).is_err());
        assert!(parse_msgpack(&[0xc1]).is_err());
        assert!(parse_msgpack(&[0xd9, 0x04, b'a']).is_err());
    }

    #[test]
    fn finite_number_policy_rejects_nan_and_infinity() {
        for value in [
            Value::F64(f64::NAN),
            Value::F64(f64::INFINITY),
            Value::F64(f64::NEG_INFINITY),
        ] {
            assert!(number(&value, "policy").is_err());
        }
        assert_eq!(number(&Value::F64(8.0), "policy").unwrap(), 8.0);
    }
}
