//! Independent memory-safe conformance decoder for CMPCT revision-25 Geometry.
//!
//! This crate intentionally does **not** call the Python research implementation.  It fixes the reader-visible
//! byte contract independently before codec 5 is wired into the main `cmpct-core` archive reader.  The scope is
//! deliberately narrow: G0/G1/G2/G3/G4/G5 inverse transforms, the bounded `G25M` Geometry-blob envelope, and
//! the self-locating recovery-tail certificate.
//!
//! Footnote: writer-side search heuristics (separator nomination, entropy ordering, histogram chains, exact
//! finalist pricing) do not belong in this crate.  Archives store only the winning reversible descriptor; a
//! production reader must remain stable even when later writers become smarter at discovering that descriptor.

use rmpv::Value;
use sha2::{Digest, Sha256};
use std::io::{Cursor, Read};
use thiserror::Error;

pub const MAX_NODE_BYTES: usize = 512 * 1024;
pub const MAX_DECODE_UNIT: usize = 8 * 1024 * 1024;
pub const MAX_GEOMETRY_BLOB: usize = 64 * 1024 * 1024;
pub const MAX_GEOMETRY_CHUNKS: usize = 256;
pub const MAX_GEOMETRY_META_RAW: usize = 1024 * 1024;
pub const MAX_DELIMITER_SEGMENTS: usize = 65_536;
pub const MAX_ROWS: usize = 65_536;
pub const MAX_FIELDS_PER_ROW: usize = 256;
pub const MAX_FIELD_DESCRIPTORS: usize = 131_072;
pub const MAX_CELL_SCANS: usize = 4_194_304;

pub const TAIL_MAGIC: &[u8; 8] = b"CMPTF25\0";
pub const TAIL_CERT_DOMAIN: &[u8] = b"CMPCT25-TAIL-CERT-V1\0";
pub const TAIL_FOOTER_SIZE: usize = 76;

const META_MAGIC: &[u8; 4] = b"G25M";
const META_HEADER_SIZE: usize = 9;
const MAGIC_DELIMITER: &[u8; 4] = b"DGT1";
const MAGIC_HIERARCHICAL: &[u8; 4] = b"HGT2";
const MAGIC_PREFIX: &[u8; 4] = b"HGP2";

#[derive(Debug, Error)]
pub enum GeometryError {
    #[error("resource bound exceeded: {0}")]
    Resource(&'static str),
    #[error("malformed Geometry representation: {0}")]
    Malformed(&'static str),
    #[error("unsupported Geometry representation: {0}")]
    Unsupported(String),
    #[error("Geometry logical size mismatch")]
    LogicalSize,
    #[error("Geometry SHA-256 mismatch")]
    Hash,
    #[error("zstd decode failure: {0}")]
    Io(#[from] std::io::Error),
    #[error("MessagePack decode failure: {0}")]
    MessagePack(String),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Representation {
    Direct,
    Lane(u8),
    Delimiter,
    Hierarchical { prefix_planes: bool },
    LanePermutation { width: u8, order: Vec<u8> },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TailFooter {
    pub kind: u8,
    pub codec: u8,
    pub flags: u8,
    pub reserved: u8,
    pub index_csize: u64,
    pub index_usize: u64,
    pub prev_footer: u64,
    pub record_base: u64,
    pub certificate: [u8; 32],
}

fn le_u32(bytes: &[u8]) -> u32 {
    u32::from_le_bytes(bytes.try_into().expect("fixed-width u32 slice"))
}

fn le_u64(bytes: &[u8]) -> u64 {
    u64::from_le_bytes(bytes.try_into().expect("fixed-width u64 slice"))
}

fn checked_usize(value: u64, label: &'static str) -> Result<usize, GeometryError> {
    usize::try_from(value).map_err(|_| GeometryError::Resource(label))
}

fn read_varint(input: &[u8], pos: &mut usize) -> Result<u64, GeometryError> {
    let mut value = 0u64;
    let mut shift = 0u32;
    for _ in 0..10 {
        let byte = *input.get(*pos).ok_or(GeometryError::Malformed("short varint"))?;
        *pos += 1;
        let low = (byte & 0x7f) as u64;
        if shift >= 64 && low != 0 {
            return Err(GeometryError::Malformed("varint overflow"));
        }
        value |= low.checked_shl(shift).ok_or(GeometryError::Malformed("varint overflow"))?;
        if byte & 0x80 == 0 {
            return Ok(value);
        }
        shift += 7;
    }
    Err(GeometryError::Malformed("overlong varint"))
}

fn zstd_decode_exact(data: &[u8], expected: usize) -> Result<Vec<u8>, GeometryError> {
    if expected > MAX_DECODE_UNIT.max(MAX_GEOMETRY_META_RAW) {
        return Err(GeometryError::Resource("zstd decoded size"));
    }
    let decoder = zstd::stream::read::Decoder::new(Cursor::new(data))?;
    let mut limited = decoder.take(expected.saturating_add(1) as u64);
    let mut out = Vec::with_capacity(expected);
    limited.read_to_end(&mut out)?;
    if out.len() != expected {
        return Err(GeometryError::Malformed("zstd decoded length"));
    }
    Ok(out)
}

fn validate_width(width: u8) -> Result<usize, GeometryError> {
    match width {
        2 | 4 | 8 | 16 => Ok(width as usize),
        _ => Err(GeometryError::Malformed("unsupported lane width")),
    }
}

fn lane_inverse(stored: &[u8], width: u8, logical_size: usize) -> Result<Vec<u8>, GeometryError> {
    let width = validate_width(width)?;
    if logical_size > MAX_NODE_BYTES || stored.len() != logical_size {
        return Err(GeometryError::LogicalSize);
    }
    let full = logical_size - (logical_size % width);
    let rows = full / width;
    let mut out = vec![0u8; logical_size];
    for lane in 0..width {
        let start = lane.checked_mul(rows).ok_or(GeometryError::Resource("lane offset"))?;
        let end = start.checked_add(rows).ok_or(GeometryError::Resource("lane offset"))?;
        let block = stored.get(start..end).ok_or(GeometryError::Malformed("short lane body"))?;
        for (row, byte) in block.iter().enumerate() {
            out[row * width + lane] = *byte;
        }
    }
    out[full..].copy_from_slice(&stored[full..]);
    Ok(out)
}

fn lane_permutation_inverse(
    stored: &[u8],
    width: u8,
    order: &[u8],
    logical_size: usize,
) -> Result<Vec<u8>, GeometryError> {
    let width_usize = validate_width(width)?;
    if order.len() != width_usize || logical_size > MAX_NODE_BYTES || stored.len() != logical_size {
        return Err(GeometryError::Malformed("lane permutation shape"));
    }
    let mut seen = vec![false; width_usize];
    for &lane in order {
        let lane = lane as usize;
        if lane >= width_usize || seen[lane] {
            return Err(GeometryError::Malformed("lane permutation is not bijective"));
        }
        seen[lane] = true;
    }
    let full = logical_size - (logical_size % width_usize);
    let rows = full / width_usize;
    let mut canonical = vec![Vec::<u8>::new(); width_usize];
    for (slot, &lane) in order.iter().enumerate() {
        let start = slot.checked_mul(rows).ok_or(GeometryError::Resource("lane permutation offset"))?;
        let end = start.checked_add(rows).ok_or(GeometryError::Resource("lane permutation offset"))?;
        canonical[lane as usize] = stored
            .get(start..end)
            .ok_or(GeometryError::Malformed("short permuted lane body"))?
            .to_vec();
    }
    let mut out = vec![0u8; logical_size];
    for lane in 0..width_usize {
        for (row, byte) in canonical[lane].iter().enumerate() {
            out[row * width_usize + lane] = *byte;
        }
    }
    out[full..].copy_from_slice(&stored[full..]);
    Ok(out)
}

fn delimiter_inverse(encoded: &[u8], logical_size: usize) -> Result<Vec<u8>, GeometryError> {
    if logical_size > MAX_NODE_BYTES || encoded.len() < 6 || &encoded[..4] != MAGIC_DELIMITER {
        return Err(GeometryError::Malformed("delimiter magic/size"));
    }
    let delimiter = encoded[4];
    let mut pos = 5usize;
    let count = checked_usize(read_varint(encoded, &mut pos)?, "delimiter segment count")?;
    if count == 0 || count > MAX_DELIMITER_SEGMENTS {
        return Err(GeometryError::Resource("delimiter segment count"));
    }
    let mut lengths = Vec::with_capacity(count);
    let mut logical_members = 0usize;
    let mut max_len = 0usize;
    for _ in 0..count {
        let len = checked_usize(read_varint(encoded, &mut pos)?, "delimiter segment length")?;
        logical_members = logical_members
            .checked_add(len)
            .ok_or(GeometryError::Resource("delimiter logical bytes"))?;
        if len > MAX_NODE_BYTES || logical_members > MAX_NODE_BYTES {
            return Err(GeometryError::Resource("delimiter logical bytes"));
        }
        max_len = max_len.max(len);
        lengths.push(len);
    }
    if count.checked_mul(max_len).ok_or(GeometryError::Resource("delimiter cell work"))? > MAX_CELL_SCANS {
        return Err(GeometryError::Resource("delimiter cell work"));
    }
    if logical_members
        .checked_add(count - 1)
        .ok_or(GeometryError::Resource("delimiter logical size"))? != logical_size
    {
        return Err(GeometryError::LogicalSize);
    }
    let body = encoded.get(pos..).ok_or(GeometryError::Malformed("delimiter body"))?;
    if body.len() != logical_members {
        return Err(GeometryError::Malformed("delimiter body size"));
    }
    let mut rows: Vec<Vec<u8>> = lengths.iter().map(|&len| vec![0u8; len]).collect();
    let mut cursor = 0usize;
    for column in 0..max_len {
        for (index, &len) in lengths.iter().enumerate() {
            if column < len {
                rows[index][column] = *body.get(cursor).ok_or(GeometryError::Malformed("short delimiter body"))?;
                cursor += 1;
            }
        }
    }
    if cursor != body.len() {
        return Err(GeometryError::Malformed("trailing delimiter body"));
    }
    let mut out = Vec::with_capacity(logical_size);
    for (index, row) in rows.iter().enumerate() {
        if index != 0 {
            out.push(delimiter);
        }
        out.extend_from_slice(row);
    }
    if out.len() != logical_size {
        return Err(GeometryError::LogicalSize);
    }
    Ok(out)
}

fn hierarchical_inverse(encoded: &[u8], logical_size: usize) -> Result<(Vec<u8>, bool), GeometryError> {
    if logical_size > MAX_NODE_BYTES || encoded.len() < 7 {
        return Err(GeometryError::Malformed("hierarchical size"));
    }
    let prefix_planes = if &encoded[..4] == MAGIC_PREFIX {
        true
    } else if &encoded[..4] == MAGIC_HIERARCHICAL {
        false
    } else {
        return Err(GeometryError::Malformed("hierarchical magic"));
    };
    let primary = encoded[4];
    let secondary = encoded[5];
    if primary == secondary {
        return Err(GeometryError::Malformed("hierarchical separator alias"));
    }
    let mut pos = 6usize;
    let row_count = checked_usize(read_varint(encoded, &mut pos)?, "hierarchical row count")?;
    if row_count == 0 || row_count > MAX_ROWS {
        return Err(GeometryError::Resource("hierarchical row count"));
    }

    let mut lengths: Vec<Vec<usize>> = Vec::with_capacity(row_count);
    let mut total_fields = 0usize;
    let mut total_field_bytes = 0usize;
    let mut max_fields = 0usize;
    let mut separator_bytes = row_count - 1;
    for _ in 0..row_count {
        let field_count = checked_usize(read_varint(encoded, &mut pos)?, "hierarchical field count")?;
        if field_count == 0 || field_count > MAX_FIELDS_PER_ROW {
            return Err(GeometryError::Resource("hierarchical fields per row"));
        }
        total_fields = total_fields
            .checked_add(field_count)
            .ok_or(GeometryError::Resource("hierarchical field descriptors"))?;
        if total_fields > MAX_FIELD_DESCRIPTORS {
            return Err(GeometryError::Resource("hierarchical field descriptors"));
        }
        separator_bytes = separator_bytes
            .checked_add(field_count - 1)
            .ok_or(GeometryError::Resource("hierarchical separator bytes"))?;
        let mut row = Vec::with_capacity(field_count);
        for _ in 0..field_count {
            let len = checked_usize(read_varint(encoded, &mut pos)?, "hierarchical field length")?;
            total_field_bytes = total_field_bytes
                .checked_add(len)
                .ok_or(GeometryError::Resource("hierarchical field bytes"))?;
            if len > MAX_NODE_BYTES || total_field_bytes > MAX_NODE_BYTES {
                return Err(GeometryError::Resource("hierarchical field bytes"));
            }
            row.push(len);
        }
        max_fields = max_fields.max(field_count);
        lengths.push(row);
    }
    if row_count
        .checked_mul(max_fields)
        .ok_or(GeometryError::Resource("hierarchical cell work"))? > MAX_CELL_SCANS
    {
        return Err(GeometryError::Resource("hierarchical cell work"));
    }
    if total_field_bytes
        .checked_add(separator_bytes)
        .ok_or(GeometryError::Resource("hierarchical logical size"))? != logical_size
    {
        return Err(GeometryError::LogicalSize);
    }

    let mut prefixes: Vec<Vec<usize>> = lengths.iter().map(|row| vec![0; row.len()]).collect();
    if prefix_planes {
        for column in 0..max_fields {
            let mut previous_length = 0usize;
            for (row_index, row) in lengths.iter().enumerate() {
                if column >= row.len() {
                    continue;
                }
                let prefix = checked_usize(read_varint(encoded, &mut pos)?, "hierarchical prefix")?;
                if prefix > previous_length.min(row[column]) {
                    return Err(GeometryError::Malformed("hierarchical prefix exceeds neighbor"));
                }
                prefixes[row_index][column] = prefix;
                previous_length = row[column];
            }
        }
    }

    let mut rows: Vec<Vec<Vec<u8>>> = lengths
        .iter()
        .map(|row| row.iter().map(|_| Vec::new()).collect())
        .collect();
    let mut cursor = pos;
    for column in 0..max_fields {
        let mut previous: Vec<u8> = Vec::new();
        for (row_index, row) in lengths.iter().enumerate() {
            if column >= row.len() {
                continue;
            }
            let len = row[column];
            let prefix = prefixes[row_index][column];
            let suffix_len = len
                .checked_sub(prefix)
                .ok_or(GeometryError::Malformed("hierarchical suffix underflow"))?;
            let end = cursor
                .checked_add(suffix_len)
                .ok_or(GeometryError::Resource("hierarchical payload cursor"))?;
            let suffix = encoded
                .get(cursor..end)
                .ok_or(GeometryError::Malformed("short hierarchical payload"))?;
            let mut field = Vec::with_capacity(len);
            field.extend_from_slice(&previous[..prefix]);
            field.extend_from_slice(suffix);
            if field.len() != len {
                return Err(GeometryError::Malformed("hierarchical field reconstruction"));
            }
            rows[row_index][column] = field.clone();
            previous = field;
            cursor = end;
        }
    }
    if cursor != encoded.len() {
        return Err(GeometryError::Malformed("trailing hierarchical payload"));
    }

    let mut out = Vec::with_capacity(logical_size);
    for (row_index, row) in rows.iter().enumerate() {
        if row_index != 0 {
            out.push(primary);
        }
        for (field_index, field) in row.iter().enumerate() {
            if field_index != 0 {
                out.push(secondary);
            }
            out.extend_from_slice(field);
        }
    }
    if out.len() != logical_size {
        return Err(GeometryError::LogicalSize);
    }
    Ok((out, prefix_planes))
}

pub fn decode_representation(
    representation: &Representation,
    physical: &[u8],
    logical_size: usize,
) -> Result<Vec<u8>, GeometryError> {
    if logical_size > MAX_NODE_BYTES || physical.len() > MAX_DECODE_UNIT {
        return Err(GeometryError::Resource("representation size"));
    }
    match representation {
        Representation::Direct => {
            if physical.len() != logical_size {
                return Err(GeometryError::LogicalSize);
            }
            Ok(physical.to_vec())
        }
        Representation::Lane(width) => lane_inverse(physical, *width, logical_size),
        Representation::Delimiter => delimiter_inverse(physical, logical_size),
        Representation::Hierarchical { prefix_planes } => {
            let (raw, actual_prefix) = hierarchical_inverse(physical, logical_size)?;
            if actual_prefix != *prefix_planes {
                return Err(GeometryError::Malformed("hierarchical descriptor/magic disagreement"));
            }
            Ok(raw)
        }
        Representation::LanePermutation { width, order } => {
            lane_permutation_inverse(physical, *width, order, logical_size)
        }
    }
}

fn value_u64(value: &Value, label: &'static str) -> Result<u64, GeometryError> {
    value.as_u64().ok_or(GeometryError::Malformed(label))
}

fn require_zero_param(value: &Value) -> Result<(), GeometryError> {
    if value_u64(value, "representation parameter")? != 0 {
        return Err(GeometryError::Malformed("noncanonical zero representation parameter"));
    }
    Ok(())
}

fn parse_representation(kind: &str, param: &Value, physical: &[u8]) -> Result<Representation, GeometryError> {
    match kind {
        "direct" => {
            require_zero_param(param)?;
            Ok(Representation::Direct)
        }
        "lane" => {
            let width = value_u64(param, "lane width")?;
            if width > u8::MAX as u64 {
                return Err(GeometryError::Malformed("lane width"));
            }
            validate_width(width as u8)?;
            Ok(Representation::Lane(width as u8))
        }
        "delimiter" => {
            require_zero_param(param)?;
            Ok(Representation::Delimiter)
        }
        "hierarchical" => {
            let flag = value_u64(param, "hierarchical prefix flag")?;
            if flag > 1 {
                return Err(GeometryError::Malformed("hierarchical prefix flag"));
            }
            let physical_prefix = physical.get(..4) == Some(MAGIC_PREFIX.as_slice());
            if physical_prefix != (flag == 1) {
                return Err(GeometryError::Malformed("hierarchical descriptor/magic disagreement"));
            }
            Ok(Representation::Hierarchical { prefix_planes: flag == 1 })
        }
        "lane_perm" => {
            let row = param
                .as_array()
                .ok_or(GeometryError::Malformed("lane permutation parameter"))?;
            if row.len() != 2 {
                return Err(GeometryError::Malformed("lane permutation parameter shape"));
            }
            let width = value_u64(&row[0], "lane permutation width")?;
            if width > u8::MAX as u64 {
                return Err(GeometryError::Malformed("lane permutation width"));
            }
            let order = match &row[1] {
                Value::Binary(bytes) => bytes.clone(),
                _ => return Err(GeometryError::Malformed("lane permutation bytes")),
            };
            validate_width(width as u8)?;
            if order.len() != width as usize {
                return Err(GeometryError::Malformed("lane permutation length"));
            }
            Ok(Representation::LanePermutation { width: width as u8, order })
        }
        other => Err(GeometryError::Unsupported(other.to_owned())),
    }
}

fn decode_meta(meta: &[u8]) -> Result<Value, GeometryError> {
    if meta.len() < META_HEADER_SIZE || meta.len() > MAX_GEOMETRY_META_RAW + META_HEADER_SIZE {
        return Err(GeometryError::Resource("Geometry metadata envelope"));
    }
    if &meta[..4] != META_MAGIC {
        return Err(GeometryError::Malformed("Geometry metadata magic"));
    }
    let codec = meta[4];
    let raw_size = le_u32(&meta[5..9]) as usize;
    if raw_size > MAX_GEOMETRY_META_RAW {
        return Err(GeometryError::Resource("Geometry metadata raw bytes"));
    }
    let body = &meta[META_HEADER_SIZE..];
    let raw = match codec {
        0 => {
            if body.len() != raw_size {
                return Err(GeometryError::Malformed("raw Geometry metadata size"));
            }
            body.to_vec()
        }
        1 => {
            if body.len() >= raw_size {
                return Err(GeometryError::Malformed("noncanonical compressed Geometry metadata"));
            }
            zstd_decode_exact(body, raw_size)?
        }
        _ => return Err(GeometryError::Malformed("Geometry metadata codec")),
    };
    let mut cursor = Cursor::new(raw.as_slice());
    let value = rmpv::decode::read_value(&mut cursor)
        .map_err(|e| GeometryError::MessagePack(e.to_string()))?;
    if cursor.position() != raw.len() as u64 {
        return Err(GeometryError::Malformed("trailing Geometry metadata bytes"));
    }
    Ok(value)
}

pub fn decode_geometry_blob(comp: &[u8], meta: &[u8], logical_size: usize) -> Result<Vec<u8>, GeometryError> {
    if logical_size > MAX_GEOMETRY_BLOB || comp.len() > logical_size {
        return Err(GeometryError::Resource("Geometry blob size"));
    }
    let root = decode_meta(meta)?;
    let root = root.as_array().ok_or(GeometryError::Malformed("Geometry metadata root"))?;
    if root.len() != 2 || value_u64(&root[0], "Geometry metadata version")? != 1 {
        return Err(GeometryError::Malformed("Geometry metadata version"));
    }
    let rows = root[1]
        .as_array()
        .ok_or(GeometryError::Malformed("Geometry metadata rows"))?;
    if rows.is_empty() || rows.len() > MAX_GEOMETRY_CHUNKS {
        return Err(GeometryError::Resource("Geometry chunk count"));
    }

    let mut payload_cursor = 0usize;
    let mut logical_total = 0usize;
    let mut out = Vec::with_capacity(logical_size);
    for row_value in rows {
        let row = row_value
            .as_array()
            .ok_or(GeometryError::Malformed("Geometry chunk descriptor"))?;
        if row.len() != 7 {
            return Err(GeometryError::Malformed("Geometry chunk descriptor length"));
        }
        let kind = row[0]
            .as_str()
            .ok_or(GeometryError::Malformed("Geometry representation kind"))?;
        let chunk_size = checked_usize(value_u64(&row[2], "Geometry logical chunk size")?, "Geometry chunk size")?;
        let physical_size = checked_usize(value_u64(&row[3], "Geometry physical chunk size")?, "Geometry physical size")?;
        let inner_codec = value_u64(&row[4], "Geometry inner codec")?;
        let csize = checked_usize(value_u64(&row[5], "Geometry inner csize")?, "Geometry inner csize")?;
        let expected_hash = match &row[6] {
            Value::Binary(bytes) if bytes.len() == 32 => bytes.as_slice(),
            _ => return Err(GeometryError::Malformed("Geometry chunk SHA-256")),
        };
        if chunk_size > MAX_NODE_BYTES || physical_size > MAX_DECODE_UNIT {
            return Err(GeometryError::Resource("Geometry chunk declaration"));
        }
        let end = payload_cursor
            .checked_add(csize)
            .ok_or(GeometryError::Resource("Geometry payload cursor"))?;
        let payload = comp
            .get(payload_cursor..end)
            .ok_or(GeometryError::Malformed("short Geometry inner payload"))?;
        let physical = match inner_codec {
            0 => {
                if csize != physical_size {
                    return Err(GeometryError::Malformed("noncanonical raw Geometry inner payload"));
                }
                payload.to_vec()
            }
            1 => {
                if csize >= physical_size {
                    return Err(GeometryError::Malformed("noncanonical zstd Geometry inner payload"));
                }
                zstd_decode_exact(payload, physical_size)?
            }
            _ => return Err(GeometryError::Malformed("Geometry inner codec")),
        };
        let representation = parse_representation(kind, &row[1], &physical)?;
        let raw = decode_representation(&representation, &physical, chunk_size)?;
        if Sha256::digest(&raw).as_slice() != expected_hash {
            return Err(GeometryError::Hash);
        }
        logical_total = logical_total
            .checked_add(raw.len())
            .ok_or(GeometryError::Resource("Geometry logical total"))?;
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

pub fn tail_certificate(
    kind: u8,
    codec: u8,
    flags: u8,
    reserved: u8,
    index_csize: u64,
    index_usize: u64,
    prev_footer: u64,
    record_base: u64,
    index_raw: &[u8],
) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(TAIL_CERT_DOMAIN);
    hasher.update([kind, codec, flags, reserved]);
    hasher.update(index_csize.to_le_bytes());
    hasher.update(index_usize.to_le_bytes());
    hasher.update(prev_footer.to_le_bytes());
    hasher.update(record_base.to_le_bytes());
    hasher.update(index_raw);
    hasher.finalize().into()
}

pub fn parse_tail_footer(bytes: &[u8]) -> Result<TailFooter, GeometryError> {
    if bytes.len() != TAIL_FOOTER_SIZE || &bytes[..8] != TAIL_MAGIC {
        return Err(GeometryError::Malformed("r25 tail footer"));
    }
    let kind = bytes[8];
    let codec = bytes[9];
    let flags = bytes[10];
    let reserved = bytes[11];
    let index_csize = le_u64(&bytes[12..20]);
    let index_usize = le_u64(&bytes[20..28]);
    let prev_footer = le_u64(&bytes[28..36]);
    let record_base = le_u64(&bytes[36..44]);
    let mut certificate = [0u8; 32];
    certificate.copy_from_slice(&bytes[44..76]);
    if kind != 0 || flags != 0 || reserved != 0 || prev_footer != 0 || !(codec == 0 || codec == 1) {
        return Err(GeometryError::Malformed("unsupported fresh r25 tail footer"));
    }
    Ok(TailFooter {
        kind,
        codec,
        flags,
        reserved,
        index_csize,
        index_usize,
        prev_footer,
        record_base,
        certificate,
    })
}

pub fn verify_tail_certificate(footer: &TailFooter, index_raw: &[u8]) -> bool {
    footer.certificate
        == tail_certificate(
            footer.kind,
            footer.codec,
            footer.flags,
            footer.reserved,
            footer.index_csize,
            footer.index_usize,
            footer.prev_footer,
            footer.record_base,
            index_raw,
        )
}

#[cfg(test)]
mod tests {
    use super::*;
    use rmpv::encode::write_value;

    #[test]
    fn lane_golden_and_tail_round_trip() {
        let raw = b"abcdefg";
        let transformed = b"acebdfg";
        assert_eq!(lane_inverse(transformed, 2, raw.len()).unwrap(), raw);
    }

    #[test]
    fn lane_permutation_golden_round_trip() {
        let raw = b"abcdefg";
        let transformed = b"bdfaceg";
        assert_eq!(
            lane_permutation_inverse(transformed, 2, &[1, 0], raw.len()).unwrap(),
            raw
        );
    }

    #[test]
    fn delimiter_golden_round_trip() {
        let encoded = b"DGT1=\x03\x02\x05\x02a12a12\nbb";
        assert_eq!(delimiter_inverse(encoded, 11).unwrap(), b"aa=11\nbb=22");
    }

    #[test]
    fn hierarchical_plain_golden_round_trip() {
        let encoded = b"HGT2\n=\x02\x02\x02\x02\x02\x02\x02aabb1122";
        let (raw, prefix) = hierarchical_inverse(encoded, 11).unwrap();
        assert!(!prefix);
        assert_eq!(raw, b"aa=11\nbb=22");
    }

    #[test]
    fn hierarchical_prefix_golden_round_trip() {
        let encoded = b"HGP2\n=\x02\x02\x02\x02\x02\x02\x02\x00\x02\x00\x01aa112";
        let (raw, prefix) = hierarchical_inverse(encoded, 11).unwrap();
        assert!(prefix);
        assert_eq!(raw, b"aa=11\naa=12");
    }

    #[test]
    fn geometry_blob_envelope_decodes_lane_independently() {
        let raw = b"abcdefg";
        let physical = b"acebdfg";
        let hash = Sha256::digest(raw).to_vec();
        let metadata = Value::Array(vec![
            Value::from(1u64),
            Value::Array(vec![Value::Array(vec![
                Value::from("lane"),
                Value::from(2u64),
                Value::from(raw.len() as u64),
                Value::from(physical.len() as u64),
                Value::from(0u64),
                Value::from(physical.len() as u64),
                Value::Binary(hash),
            ])]),
        ]);
        let mut raw_meta = Vec::new();
        write_value(&mut raw_meta, &metadata).unwrap();
        let mut envelope = Vec::new();
        envelope.extend_from_slice(META_MAGIC);
        envelope.push(0);
        envelope.extend_from_slice(&(raw_meta.len() as u32).to_le_bytes());
        envelope.extend_from_slice(&raw_meta);
        assert_eq!(decode_geometry_blob(physical, &envelope, raw.len()).unwrap(), raw);
    }

    #[test]
    fn hierarchical_descriptor_must_match_physical_magic() {
        let physical = b"HGP2\n=\x02\x02\x02\x02\x02\x02\x02\x00\x02\x00\x01aa112";
        let err = decode_representation(
            &Representation::Hierarchical { prefix_planes: false },
            physical,
            11,
        )
        .unwrap_err();
        assert!(matches!(err, GeometryError::Malformed(_)));
    }

    #[test]
    fn tail_certificate_binds_record_base_and_index() {
        let index = b"canonical-index";
        let a = tail_certificate(0, 1, 0, 0, 100, 200, 0, 1234, index);
        let b = tail_certificate(0, 1, 0, 0, 100, 200, 0, 1235, index);
        let c = tail_certificate(0, 1, 0, 0, 100, 200, 0, 1234, b"canonical-index!");
        assert_ne!(a, b);
        assert_ne!(a, c);
    }

    #[test]
    fn malformed_delimiter_cell_work_fails_before_rectangular_loop() {
        // One logical byte per segment, enough rows that count*max_len is still legal; then use impossible
        // logical size to ensure shape validation happens without attempting attacker-sized output joins.
        let mut encoded = b"DGT1|".to_vec();
        encoded.push(0x81); encoded.push(0x01); // count=129
        for _ in 0..129 { encoded.push(1); }
        encoded.extend(std::iter::repeat(b'x').take(129));
        assert!(delimiter_inverse(&encoded, 1).is_err());
    }
}
