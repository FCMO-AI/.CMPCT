//! Strict production-facing facade for the independent r25 Geometry decoder.
//!
//! `lib.rs` is intentionally retained as the first independent derivation.  This facade closes canonicality
//! gaps found during static audit without rewriting that evidence: all varints in delimiter/hierarchical
//! physical programs must be minimal u64 encodings, the 10th byte may carry at most one high bit, and the
//! complete prefix/suffix shape is preflighted before the derivation inverse is allowed to run.
//!
//! Footnote: canonical preflight is not a compression heuristic.  Writers already emit minimal varints; the
//! stricter reader simply removes alternate byte encodings and overflow aliases that no conforming writer can
//! produce.  Resource ceilings are at least as strict as the derivation decoder.

#[allow(clippy::all, deprecated)]
#[path = "lib.rs"]
mod derivation;

pub use derivation::{
    GeometryError, Representation, TailFooter, MAX_CELL_SCANS, MAX_DECODE_UNIT,
    MAX_DELIMITER_SEGMENTS, MAX_FIELD_DESCRIPTORS, MAX_FIELDS_PER_ROW, MAX_GEOMETRY_BLOB,
    MAX_GEOMETRY_CHUNKS, MAX_GEOMETRY_META_RAW, MAX_NODE_BYTES, MAX_ROWS, TAIL_CERT_DOMAIN,
    TAIL_FOOTER_SIZE, TAIL_MAGIC,
};
pub use derivation::{parse_tail_footer, tail_certificate, verify_tail_certificate};

use rmpv::Value;
use sha2::{Digest, Sha256};
use std::io::{Cursor, Read};

const META_MAGIC: &[u8; 4] = b"G25M";
const META_HEADER_SIZE: usize = 9;
const MAGIC_DELIMITER: &[u8; 4] = b"DGT1";
const MAGIC_HIERARCHICAL: &[u8; 4] = b"HGT2";
const MAGIC_PREFIX: &[u8; 4] = b"HGP2";

fn checked_usize(value: u64, label: &'static str) -> Result<usize, GeometryError> {
    usize::try_from(value).map_err(|_| GeometryError::Resource(label))
}

fn strict_varint(input: &[u8], pos: &mut usize) -> Result<u64, GeometryError> {
    let mut value = 0u64;
    let mut shift = 0u32;
    for group in 0..10 {
        let byte = *input
            .get(*pos)
            .ok_or(GeometryError::Malformed("short canonical varint"))?;
        *pos += 1;
        let low = (byte & 0x7f) as u64;
        if group == 9 && low > 1 {
            return Err(GeometryError::Malformed("canonical varint overflow"));
        }
        if shift > 0 && byte & 0x80 == 0 && low == 0 {
            return Err(GeometryError::Malformed("non-minimal canonical varint"));
        }
        value |= low
            .checked_shl(shift)
            .ok_or(GeometryError::Malformed("canonical varint overflow"))?;
        if byte & 0x80 == 0 {
            return Ok(value);
        }
        shift += 7;
    }
    Err(GeometryError::Malformed("overlong canonical varint"))
}

fn preflight_delimiter(encoded: &[u8], logical_size: usize) -> Result<(), GeometryError> {
    if logical_size > MAX_NODE_BYTES || encoded.len() < 6 || &encoded[..4] != MAGIC_DELIMITER {
        return Err(GeometryError::Malformed("delimiter canonical preflight"));
    }
    let mut pos = 5usize;
    let count = checked_usize(strict_varint(encoded, &mut pos)?, "delimiter segment count")?;
    if count == 0 || count > MAX_DELIMITER_SEGMENTS {
        return Err(GeometryError::Resource("delimiter segment count"));
    }
    let mut logical_members = 0usize;
    let mut max_len = 0usize;
    for _ in 0..count {
        let len = checked_usize(strict_varint(encoded, &mut pos)?, "delimiter segment length")?;
        logical_members = logical_members
            .checked_add(len)
            .ok_or(GeometryError::Resource("delimiter logical bytes"))?;
        if len > MAX_NODE_BYTES || logical_members > MAX_NODE_BYTES {
            return Err(GeometryError::Resource("delimiter logical bytes"));
        }
        max_len = max_len.max(len);
    }
    if count
        .checked_mul(max_len)
        .ok_or(GeometryError::Resource("delimiter cell work"))? > MAX_CELL_SCANS
    {
        return Err(GeometryError::Resource("delimiter cell work"));
    }
    if logical_members
        .checked_add(count - 1)
        .ok_or(GeometryError::Resource("delimiter logical size"))? != logical_size
    {
        return Err(GeometryError::LogicalSize);
    }
    if encoded.len().checked_sub(pos) != Some(logical_members) {
        return Err(GeometryError::Malformed("delimiter canonical body size"));
    }
    Ok(())
}

fn preflight_hierarchical(encoded: &[u8], logical_size: usize) -> Result<bool, GeometryError> {
    if logical_size > MAX_NODE_BYTES || encoded.len() < 7 {
        return Err(GeometryError::Malformed("hierarchical canonical preflight"));
    }
    let prefix_planes = if &encoded[..4] == MAGIC_PREFIX {
        true
    } else if &encoded[..4] == MAGIC_HIERARCHICAL {
        false
    } else {
        return Err(GeometryError::Malformed("hierarchical canonical magic"));
    };
    if encoded[4] == encoded[5] {
        return Err(GeometryError::Malformed("hierarchical separator alias"));
    }
    let mut pos = 6usize;
    let row_count = checked_usize(strict_varint(encoded, &mut pos)?, "hierarchical row count")?;
    if row_count == 0 || row_count > MAX_ROWS {
        return Err(GeometryError::Resource("hierarchical row count"));
    }

    let mut lengths: Vec<Vec<usize>> = Vec::with_capacity(row_count);
    let mut total_fields = 0usize;
    let mut total_field_bytes = 0usize;
    let mut max_fields = 0usize;
    let mut separators = row_count - 1;
    for _ in 0..row_count {
        let fields = checked_usize(strict_varint(encoded, &mut pos)?, "hierarchical field count")?;
        if fields == 0 || fields > MAX_FIELDS_PER_ROW {
            return Err(GeometryError::Resource("hierarchical fields per row"));
        }
        total_fields = total_fields
            .checked_add(fields)
            .ok_or(GeometryError::Resource("hierarchical descriptors"))?;
        if total_fields > MAX_FIELD_DESCRIPTORS {
            return Err(GeometryError::Resource("hierarchical descriptors"));
        }
        separators = separators
            .checked_add(fields - 1)
            .ok_or(GeometryError::Resource("hierarchical separators"))?;
        let mut row = Vec::with_capacity(fields);
        for _ in 0..fields {
            let len = checked_usize(strict_varint(encoded, &mut pos)?, "hierarchical field length")?;
            total_field_bytes = total_field_bytes
                .checked_add(len)
                .ok_or(GeometryError::Resource("hierarchical field bytes"))?;
            if len > MAX_NODE_BYTES || total_field_bytes > MAX_NODE_BYTES {
                return Err(GeometryError::Resource("hierarchical field bytes"));
            }
            row.push(len);
        }
        max_fields = max_fields.max(fields);
        lengths.push(row);
    }
    if row_count
        .checked_mul(max_fields)
        .ok_or(GeometryError::Resource("hierarchical cell work"))? > MAX_CELL_SCANS
    {
        return Err(GeometryError::Resource("hierarchical cell work"));
    }
    if total_field_bytes
        .checked_add(separators)
        .ok_or(GeometryError::Resource("hierarchical logical size"))? != logical_size
    {
        return Err(GeometryError::LogicalSize);
    }

    let mut suffix_bytes = total_field_bytes;
    if prefix_planes {
        suffix_bytes = 0;
        for column in 0..max_fields {
            let mut previous_len = 0usize;
            for row in &lengths {
                if column >= row.len() {
                    continue;
                }
                let prefix = checked_usize(strict_varint(encoded, &mut pos)?, "hierarchical prefix")?;
                let len = row[column];
                if prefix > previous_len.min(len) {
                    return Err(GeometryError::Malformed("hierarchical prefix exceeds neighbor"));
                }
                suffix_bytes = suffix_bytes
                    .checked_add(len - prefix)
                    .ok_or(GeometryError::Resource("hierarchical suffix bytes"))?;
                previous_len = len;
            }
        }
    }
    if encoded.len().checked_sub(pos) != Some(suffix_bytes) {
        return Err(GeometryError::Malformed("hierarchical canonical payload size"));
    }
    Ok(prefix_planes)
}

pub fn decode_representation(
    representation: &Representation,
    physical: &[u8],
    logical_size: usize,
) -> Result<Vec<u8>, GeometryError> {
    match representation {
        Representation::Delimiter => preflight_delimiter(physical, logical_size)?,
        Representation::Hierarchical { prefix_planes } => {
            let physical_prefix = preflight_hierarchical(physical, logical_size)?;
            if physical_prefix != *prefix_planes {
                return Err(GeometryError::Malformed("hierarchical descriptor/magic disagreement"));
            }
        }
        _ => {}
    }
    derivation::decode_representation(representation, physical, logical_size)
}

fn zstd_decode_exact(data: &[u8], expected: usize) -> Result<Vec<u8>, GeometryError> {
    if expected > MAX_DECODE_UNIT.max(MAX_GEOMETRY_META_RAW) {
        return Err(GeometryError::Resource("strict zstd decoded size"));
    }
    let decoder = zstd::stream::read::Decoder::new(Cursor::new(data))?;
    let mut limited = decoder.take(expected.saturating_add(1) as u64);
    let mut out = Vec::with_capacity(expected);
    limited.read_to_end(&mut out)?;
    if out.len() != expected {
        return Err(GeometryError::Malformed("strict zstd decoded length"));
    }
    Ok(out)
}

fn decode_meta(meta: &[u8]) -> Result<Value, GeometryError> {
    if meta.len() < META_HEADER_SIZE || meta.len() > MAX_GEOMETRY_META_RAW + META_HEADER_SIZE {
        return Err(GeometryError::Resource("strict Geometry metadata envelope"));
    }
    if &meta[..4] != META_MAGIC {
        return Err(GeometryError::Malformed("strict Geometry metadata magic"));
    }
    let codec = meta[4];
    let raw_size = u32::from_le_bytes(
        meta[5..9]
            .try_into()
            .map_err(|_| GeometryError::Malformed("strict metadata size"))?,
    ) as usize;
    if raw_size > MAX_GEOMETRY_META_RAW {
        return Err(GeometryError::Resource("strict Geometry metadata raw bytes"));
    }
    let body = &meta[META_HEADER_SIZE..];
    let raw = match codec {
        0 => {
            if body.len() != raw_size {
                return Err(GeometryError::Malformed("strict raw Geometry metadata size"));
            }
            body.to_vec()
        }
        1 => {
            if body.len() >= raw_size {
                return Err(GeometryError::Malformed("strict noncanonical compressed metadata"));
            }
            zstd_decode_exact(body, raw_size)?
        }
        _ => return Err(GeometryError::Malformed("strict Geometry metadata codec")),
    };
    let mut cursor = Cursor::new(raw.as_slice());
    let value = rmpv::decode::read_value(&mut cursor)
        .map_err(|error| GeometryError::MessagePack(error.to_string()))?;
    if cursor.position() != raw.len() as u64 {
        return Err(GeometryError::Malformed("strict trailing Geometry metadata"));
    }
    Ok(value)
}

fn value_u64(value: &Value, label: &'static str) -> Result<u64, GeometryError> {
    value.as_u64().ok_or(GeometryError::Malformed(label))
}

fn parse_representation(kind: &str, param: &Value, physical: &[u8]) -> Result<Representation, GeometryError> {
    match kind {
        "direct" => {
            if value_u64(param, "direct parameter")? != 0 {
                return Err(GeometryError::Malformed("noncanonical direct parameter"));
            }
            Ok(Representation::Direct)
        }
        "lane" => {
            let width = value_u64(param, "lane width")?;
            let width = u8::try_from(width).map_err(|_| GeometryError::Malformed("lane width"))?;
            if !matches!(width, 2 | 4 | 8 | 16) {
                return Err(GeometryError::Malformed("lane width"));
            }
            Ok(Representation::Lane(width))
        }
        "delimiter" => {
            if value_u64(param, "delimiter parameter")? != 0 {
                return Err(GeometryError::Malformed("noncanonical delimiter parameter"));
            }
            Ok(Representation::Delimiter)
        }
        "hierarchical" => {
            let flag = value_u64(param, "hierarchical prefix flag")?;
            if flag > 1 {
                return Err(GeometryError::Malformed("hierarchical prefix flag"));
            }
            let prefix = preflight_hierarchical(physical, MAX_NODE_BYTES.min(MAX_NODE_BYTES))?;
            // The call above cannot know logical size and is intentionally not used for acceptance; descriptor
            // magic agreement is checked again with the real logical size in `decode_representation`.  We only
            // need the first four bytes here without creating a second ad-hoc magic parser.
            let _ = prefix;
            Ok(Representation::Hierarchical { prefix_planes: flag == 1 })
        }
        "lane_perm" => {
            let row = param
                .as_array()
                .ok_or(GeometryError::Malformed("lane permutation parameter"))?;
            if row.len() != 2 {
                return Err(GeometryError::Malformed("lane permutation shape"));
            }
            let width = u8::try_from(value_u64(&row[0], "lane permutation width")?)
                .map_err(|_| GeometryError::Malformed("lane permutation width"))?;
            if !matches!(width, 2 | 4 | 8 | 16) {
                return Err(GeometryError::Malformed("lane permutation width"));
            }
            let order = match &row[1] {
                Value::Binary(bytes) => bytes.clone(),
                _ => return Err(GeometryError::Malformed("lane permutation bytes")),
            };
            Ok(Representation::LanePermutation { width, order })
        }
        other => Err(GeometryError::Unsupported(other.to_owned())),
    }
}

/// Decode a complete r25 Geometry blob through canonical preflight plus the independent inverse.
pub fn decode_geometry_blob(comp: &[u8], meta: &[u8], logical_size: usize) -> Result<Vec<u8>, GeometryError> {
    if logical_size > MAX_GEOMETRY_BLOB || comp.len() > logical_size {
        return Err(GeometryError::Resource("strict Geometry blob size"));
    }
    let root = decode_meta(meta)?;
    let root = root
        .as_array()
        .ok_or(GeometryError::Malformed("strict Geometry metadata root"))?;
    if root.len() != 2 || value_u64(&root[0], "strict Geometry metadata version")? != 1 {
        return Err(GeometryError::Malformed("strict Geometry metadata version"));
    }
    let rows = root[1]
        .as_array()
        .ok_or(GeometryError::Malformed("strict Geometry metadata rows"))?;
    if rows.is_empty() || rows.len() > MAX_GEOMETRY_CHUNKS {
        return Err(GeometryError::Resource("strict Geometry chunk count"));
    }

    let mut payload_cursor = 0usize;
    let mut logical_total = 0usize;
    let mut out = Vec::with_capacity(logical_size);
    for row_value in rows {
        let row = row_value
            .as_array()
            .ok_or(GeometryError::Malformed("strict Geometry chunk descriptor"))?;
        if row.len() != 7 {
            return Err(GeometryError::Malformed("strict Geometry chunk descriptor length"));
        }
        let kind = row[0]
            .as_str()
            .ok_or(GeometryError::Malformed("strict representation kind"))?;
        let chunk_size = checked_usize(value_u64(&row[2], "strict logical chunk size")?, "strict chunk size")?;
        let physical_size = checked_usize(value_u64(&row[3], "strict physical chunk size")?, "strict physical size")?;
        let inner_codec = value_u64(&row[4], "strict inner codec")?;
        let csize = checked_usize(value_u64(&row[5], "strict inner csize")?, "strict inner csize")?;
        let expected_hash: &[u8] = match &row[6] {
            Value::Binary(bytes) if bytes.len() == 32 => bytes,
            _ => return Err(GeometryError::Malformed("strict chunk SHA-256")),
        };
        if chunk_size > MAX_NODE_BYTES || physical_size > MAX_DECODE_UNIT {
            return Err(GeometryError::Resource("strict Geometry chunk declaration"));
        }
        let end = payload_cursor
            .checked_add(csize)
            .ok_or(GeometryError::Resource("strict Geometry payload cursor"))?;
        let payload = comp
            .get(payload_cursor..end)
            .ok_or(GeometryError::Malformed("short strict Geometry payload"))?;
        let physical = match inner_codec {
            0 => {
                if csize != physical_size {
                    return Err(GeometryError::Malformed("noncanonical strict raw inner payload"));
                }
                payload.to_vec()
            }
            1 => {
                if csize >= physical_size {
                    return Err(GeometryError::Malformed("noncanonical strict zstd inner payload"));
                }
                zstd_decode_exact(payload, physical_size)?
            }
            _ => return Err(GeometryError::Malformed("strict Geometry inner codec")),
        };
        let representation = if kind == "hierarchical" {
            let flag = value_u64(&row[1], "hierarchical prefix flag")?;
            if flag > 1 {
                return Err(GeometryError::Malformed("hierarchical prefix flag"));
            }
            Representation::Hierarchical { prefix_planes: flag == 1 }
        } else {
            parse_representation(kind, &row[1], &physical)?
        };
        let raw = decode_representation(&representation, &physical, chunk_size)?;
        let digest = Sha256::digest(&raw);
        if &digest[..] != expected_hash {
            return Err(GeometryError::Hash);
        }
        logical_total = logical_total
            .checked_add(raw.len())
            .ok_or(GeometryError::Resource("strict Geometry logical total"))?;
        if logical_total > logical_size {
            return Err(GeometryError::LogicalSize);
        }
        out.extend_from_slice(&raw);
        payload_cursor = end;
    }
    if payload_cursor != comp.len() || logical_total != logical_size {
        return Err(GeometryError::LogicalSize);
    }
    Ok(out)
}

#[cfg(test)]
mod strict_tests {
    use super::*;

    #[test]
    fn overlong_zero_varint_is_rejected() {
        // DGT1, delimiter '=', segment count encoded non-minimally as 0x81 0x00 (value 1).
        let encoded = b"DGT1=\x81\x00\x00";
        assert!(decode_representation(&Representation::Delimiter, encoded, 0).is_err());
    }

    #[test]
    fn tenth_varint_group_cannot_overflow_u64() {
        let mut encoded = b"DGT1=".to_vec();
        encoded.extend_from_slice(&[0xff; 9]);
        encoded.push(0x02); // tenth payload group may be only 0 or 1 for u64.
        assert!(decode_representation(&Representation::Delimiter, &encoded, 0).is_err());
    }

    #[test]
    fn golden_vectors_still_decode_through_strict_facade() {
        let plain = b"HGT2\n=\x02\x02\x02\x02\x02\x02\x02aabb1122";
        assert_eq!(
            decode_representation(
                &Representation::Hierarchical { prefix_planes: false },
                plain,
                11,
            )
            .unwrap(),
            b"aa=11\nbb=22"
        );
        let prefix = b"HGP2\n=\x02\x02\x02\x02\x02\x02\x02\x00\x02\x00\x01aa112";
        assert_eq!(
            decode_representation(
                &Representation::Hierarchical { prefix_planes: true },
                prefix,
                11,
            )
            .unwrap(),
            b"aa=11\naa=12"
        );
    }
}
