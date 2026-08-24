use crate::PortableError;
use cmpct_core::Archive as R24Archive;
use rmpv::Value;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::io::Cursor;
use std::path::Path;
use tempfile::TempDir;

pub const MAGIC: &[u8; 8] = b"C25CC01\0";
const TAIL_MAGIC: &[u8; 8] = b"C25CCT1\0";
const R24_MAGIC: &[u8; 8] = b"CMPCT24\0";
const R24_TAIL_MAGIC: &[u8; 8] = b"CMPTF24\0";
const HEADER_SIZE: usize = 68;
const FOOTER_SIZE: usize = 68;
const MAX_CONTROL_RAW_BYTES: usize = 64 * 1024 * 1024;

#[derive(Debug)]
pub struct CompactControlArchive {
    _temp: TempDir,
    r24: R24Archive,
    tail_authenticated: bool,
}

#[derive(Clone)]
struct ParsedCopies {
    primary: Vec<u8>,
    tail: Vec<u8>,
    primary_raw: usize,
    tail_raw: usize,
    primary_sha: [u8; 32],
    tail_sha: [u8; 32],
    data_start: usize,
    data_span: usize,
}

impl CompactControlArchive {
    pub(crate) fn open(path: &Path) -> Result<Self, PortableError> {
        let payload = fs::read(path)?;
        let copies = parse_copies(&payload)?;
        let primary = decode_copy(&copies.primary, copies.primary_raw, &copies.primary_sha);
        let tail = decode_copy(&copies.tail, copies.tail_raw, &copies.tail_sha);
        let (control, tail_authenticated) = match (primary, tail) {
            (Ok(primary), Ok(tail)) => {
                if primary != tail {
                    return Err(PortableError::Integrity(
                        "C25CC01 authenticated control copies disagree".into(),
                    ));
                }
                (primary, true)
            }
            (Ok(primary), Err(_)) => (primary, false),
            (Err(_), Ok(tail)) => (tail, true),
            (Err(primary_error), Err(tail_error)) => {
                return Err(PortableError::Integrity(format!(
                    "C25CC01 primary and tail control copies both failed: primary={primary_error}; tail={tail_error}"
                )));
            }
        };

        let expanded = expand_compact_control(&control)?;
        let temp = tempfile::tempdir().map_err(PortableError::Io)?;
        let r24_path = temp.path().join("expanded-r24.cmpct");
        materialize_r24_from_compact(&payload, &copies, &expanded, &r24_path)?;
        let r24 = R24Archive::open(&r24_path)?;
        Ok(Self {
            _temp: temp,
            r24,
            tail_authenticated,
        })
    }

    pub(crate) fn r24(&self) -> &R24Archive {
        &self.r24
    }

    pub(crate) fn tail_authenticated(&self) -> bool {
        self.tail_authenticated
    }
}

fn le_u16(raw: &[u8]) -> Result<u16, PortableError> {
    let raw: [u8; 2] = raw
        .try_into()
        .map_err(|_| PortableError::Format("truncated C25CC01 u16".into()))?;
    Ok(u16::from_le_bytes(raw))
}

fn le_u64(raw: &[u8]) -> Result<u64, PortableError> {
    let raw: [u8; 8] = raw
        .try_into()
        .map_err(|_| PortableError::Format("truncated C25CC01 u64".into()))?;
    Ok(u64::from_le_bytes(raw))
}

fn value_u64(value: &Value, label: &str) -> Result<u64, PortableError> {
    value
        .as_u64()
        .or_else(|| value.as_i64().and_then(|v| u64::try_from(v).ok()))
        .ok_or_else(|| PortableError::Format(format!("{label} is not a non-negative integer")))
}

fn value_i64(value: &Value, label: &str) -> Result<i64, PortableError> {
    value
        .as_i64()
        .or_else(|| value.as_u64().and_then(|v| i64::try_from(v).ok()))
        .ok_or_else(|| PortableError::Format(format!("{label} is outside signed 64-bit range")))
}

fn map_get<'a>(value: &'a Value, key: &str) -> Result<&'a Value, PortableError> {
    value
        .as_map()
        .ok_or_else(|| PortableError::Format("expected MessagePack map".into()))?
        .iter()
        .find_map(|(candidate, value)| (candidate.as_str() == Some(key)).then_some(value))
        .ok_or_else(|| PortableError::Format(format!("missing compact-control key {key:?}")))
}

fn decode_copy(comp: &[u8], raw_len: usize, digest: &[u8; 32]) -> Result<Value, PortableError> {
    if raw_len > MAX_CONTROL_RAW_BYTES {
        return Err(PortableError::Limit(
            "C25CC01 raw control exceeds 64 MiB bound".into(),
        ));
    }
    let raw = zstd::stream::decode_all(Cursor::new(comp))
        .map_err(|error| PortableError::Format(format!("C25CC01 control Zstd decode: {error}")))?;
    if raw.len() != raw_len {
        return Err(PortableError::Integrity(
            "C25CC01 control length mismatch".into(),
        ));
    }
    if Sha256::digest(&raw).as_slice() != digest {
        return Err(PortableError::Integrity(
            "C25CC01 control SHA-256 mismatch".into(),
        ));
    }
    let mut cursor = Cursor::new(raw.as_slice());
    let value = rmpv::decode::read_value(&mut cursor)
        .map_err(|error| PortableError::Format(format!("C25CC01 MessagePack decode: {error}")))?;
    if cursor.position() != raw.len() as u64 {
        return Err(PortableError::Format(
            "trailing bytes after C25CC01 control object".into(),
        ));
    }
    let map = value
        .as_map()
        .ok_or_else(|| PortableError::Format("C25CC01 control envelope is not a map".into()))?;
    let mut saw_x = false;
    let mut saw_c = false;
    for (key, value) in map {
        match key.as_str() {
            Some("x") => saw_x = value.as_array().is_some(),
            Some("c") => saw_c = value.as_map().is_some(),
            _ => {
                return Err(PortableError::Format(
                    "unexpected C25CC01 control envelope key".into(),
                ));
            }
        }
    }
    if !saw_x || !saw_c || map.len() != 2 {
        return Err(PortableError::Format(
            "C25CC01 control envelope shape mismatch".into(),
        ));
    }
    Ok(value)
}

fn parse_copies(payload: &[u8]) -> Result<ParsedCopies, PortableError> {
    if payload.len() < HEADER_SIZE + FOOTER_SIZE {
        return Err(PortableError::Format("truncated C25CC01 archive".into()));
    }
    if &payload[..8] != MAGIC || le_u16(&payload[8..10])? != 25 {
        return Err(PortableError::Format(
            "not a canonical C25CC01 archive".into(),
        ));
    }
    let primary_len = usize::try_from(le_u64(&payload[12..20])?).map_err(|_| {
        PortableError::Limit("C25CC01 primary control length exceeds native width".into())
    })?;
    let primary_raw = usize::try_from(le_u64(&payload[20..28])?).map_err(|_| {
        PortableError::Limit("C25CC01 primary raw length exceeds native width".into())
    })?;
    let data_span = usize::try_from(le_u64(&payload[28..36])?)
        .map_err(|_| PortableError::Limit("C25CC01 data span exceeds native width".into()))?;
    let mut primary_sha = [0u8; 32];
    primary_sha.copy_from_slice(&payload[36..68]);

    let footer_off = payload.len() - FOOTER_SIZE;
    if &payload[footer_off..footer_off + 8] != TAIL_MAGIC {
        return Err(PortableError::Format("C25CC01 tail magic mismatch".into()));
    }
    let tail_len =
        usize::try_from(le_u64(&payload[footer_off + 12..footer_off + 20])?).map_err(|_| {
            PortableError::Limit("C25CC01 tail control length exceeds native width".into())
        })?;
    let tail_raw = usize::try_from(le_u64(&payload[footer_off + 20..footer_off + 28])?)
        .map_err(|_| PortableError::Limit("C25CC01 tail raw length exceeds native width".into()))?;
    let mut tail_sha = [0u8; 32];
    tail_sha.copy_from_slice(&payload[footer_off + 36..footer_off + 68]);

    let primary_start = HEADER_SIZE;
    let primary_end = primary_start
        .checked_add(primary_len)
        .ok_or_else(|| PortableError::Limit("C25CC01 primary end overflow".into()))?;
    let tail_start = footer_off
        .checked_sub(tail_len)
        .ok_or_else(|| PortableError::Format("C25CC01 tail control underflows archive".into()))?;
    let data_end = primary_end
        .checked_add(data_span)
        .ok_or_else(|| PortableError::Limit("C25CC01 data end overflow".into()))?;
    if primary_end > payload.len() || data_end != tail_start {
        return Err(PortableError::Format(
            "C25CC01 physical span accounting mismatch".into(),
        ));
    }
    Ok(ParsedCopies {
        primary: payload[primary_start..primary_end].to_vec(),
        tail: payload[tail_start..footer_off].to_vec(),
        primary_raw,
        tail_raw,
        primary_sha,
        tail_sha,
        data_start: primary_end,
        data_span,
    })
}

fn blob_size(blobs: &[Value], index: usize) -> Result<u64, PortableError> {
    let row = blobs.get(index).and_then(Value::as_array).ok_or_else(|| {
        PortableError::Format(format!("C25CC01 blob {index} is missing or malformed"))
    })?;
    row.get(1)
        .ok_or_else(|| {
            PortableError::Format(format!("C25CC01 blob {index} is missing logical size"))
        })
        .and_then(|value| value_u64(value, "blob logical size"))
}

fn derived_size(
    blobs: &[Value],
    recipes: &[Value],
    storage: &Value,
) -> Result<Option<u64>, PortableError> {
    let Some(row) = storage.as_array() else {
        return Ok(None);
    };
    let Some(tag_value) = row.first() else {
        return Ok(None);
    };
    let tag = value_u64(tag_value, "storage tag")?;
    match tag {
        0 => {
            let index = usize::try_from(value_u64(
                row.get(1).ok_or_else(|| {
                    PortableError::Format("direct storage missing blob index".into())
                })?,
                "direct blob index",
            )?)
            .map_err(|_| PortableError::Limit("direct blob index exceeds native width".into()))?;
            Ok(Some(blob_size(blobs, index)?))
        }
        1 => {
            let ids = row.get(1).and_then(Value::as_array).ok_or_else(|| {
                PortableError::Format("fixed-chunk storage missing chunk list".into())
            })?;
            let mut total = 0u64;
            for value in ids {
                let index =
                    usize::try_from(value_u64(value, "fixed chunk index")?).map_err(|_| {
                        PortableError::Limit("fixed chunk index exceeds native width".into())
                    })?;
                total = total.checked_add(blob_size(blobs, index)?).ok_or_else(|| {
                    PortableError::Limit("fixed-chunk logical size overflow".into())
                })?;
            }
            Ok(Some(total))
        }
        2 => {
            let index = usize::try_from(value_u64(
                row.get(1).ok_or_else(|| {
                    PortableError::Format("virtual-ZIP storage missing recipe index".into())
                })?,
                "virtual-ZIP recipe index",
            )?)
            .map_err(|_| {
                PortableError::Limit("virtual-ZIP recipe index exceeds native width".into())
            })?;
            let recipe = recipes
                .get(index)
                .and_then(Value::as_array)
                .ok_or_else(|| {
                    PortableError::Format("virtual-ZIP recipe missing or malformed".into())
                })?;
            Ok(Some(value_u64(
                recipe.get(4).ok_or_else(|| {
                    PortableError::Format("virtual-ZIP recipe missing logical size".into())
                })?,
                "virtual-ZIP logical size",
            )?))
        }
        4 => Ok(Some(value_u64(
            row.get(3)
                .ok_or_else(|| PortableError::Format("pack storage missing length".into()))?,
            "pack length",
        )?)),
        5 => {
            let rows = row
                .get(1)
                .and_then(Value::as_array)
                .ok_or_else(|| PortableError::Format("CDC storage missing chunk rows".into()))?;
            let mut total = 0u64;
            for value in rows {
                let chunk = value
                    .as_array()
                    .ok_or_else(|| PortableError::Format("CDC chunk row is malformed".into()))?;
                total = total
                    .checked_add(value_u64(
                        chunk.first().ok_or_else(|| {
                            PortableError::Format("CDC chunk missing logical length".into())
                        })?,
                        "CDC logical length",
                    )?)
                    .ok_or_else(|| PortableError::Limit("CDC logical size overflow".into()))?;
            }
            Ok(Some(total))
        }
        _ => Ok(None),
    }
}

fn expand_compact_control(envelope: &Value) -> Result<Value, PortableError> {
    let features = map_get(envelope, "x")?
        .as_array()
        .ok_or_else(|| PortableError::Format("C25CC01 features are not an array".into()))?
        .clone();
    let compact = map_get(envelope, "c")?;
    let paths = map_get(compact, "p")?
        .as_array()
        .ok_or_else(|| PortableError::Format("C25CC01 compact paths are not an array".into()))?;
    let encoded_files = map_get(compact, "f")?
        .as_array()
        .ok_or_else(|| PortableError::Format("C25CC01 compact files are not an array".into()))?;
    if paths.len() != encoded_files.len() {
        return Err(PortableError::Format(
            "C25CC01 compact path/file row count mismatch".into(),
        ));
    }
    let defaults = map_get(compact, "d")?
        .as_array()
        .ok_or_else(|| PortableError::Format("C25CC01 compact defaults are not an array".into()))?;
    if defaults.len() != 2 {
        return Err(PortableError::Format(
            "C25CC01 compact defaults have invalid shape".into(),
        ));
    }
    let default_mode = value_u64(&defaults[0], "default mode")?;
    let default_mtime = value_i64(&defaults[1], "default mtime")?;
    let blobs = map_get(compact, "b")?
        .as_array()
        .ok_or_else(|| PortableError::Format("C25CC01 compact blobs are not an array".into()))?
        .clone();
    let recipes = map_get(compact, "r")?
        .as_array()
        .ok_or_else(|| PortableError::Format("C25CC01 compact recipes are not an array".into()))?
        .clone();

    let mut previous = String::new();
    let mut prior_paths = Vec::<String>::new();
    let mut prior_sizes = HashMap::<String, u64>::new();
    let mut files = Vec::<Value>::with_capacity(encoded_files.len());

    for (path_row, encoded) in paths.iter().zip(encoded_files) {
        let path_row = path_row
            .as_array()
            .ok_or_else(|| PortableError::Format("C25CC01 compact path row is malformed".into()))?;
        if path_row.len() != 2 {
            return Err(PortableError::Format(
                "C25CC01 compact path row has invalid shape".into(),
            ));
        }
        let prefix = usize::try_from(value_u64(&path_row[0], "compact path prefix")?)
            .map_err(|_| PortableError::Limit("compact path prefix exceeds native width".into()))?;
        if prefix > previous.len() || !previous.is_char_boundary(prefix) {
            return Err(PortableError::Format(
                "C25CC01 compact path prefix is outside prior UTF-8 path".into(),
            ));
        }
        let suffix = path_row[1].as_str().ok_or_else(|| {
            PortableError::Format("C25CC01 compact path suffix is not UTF-8".into())
        })?;
        let rel = format!("{}{}", &previous[..prefix], suffix);
        previous.clone_from(&rel);

        let encoded = encoded
            .as_array()
            .ok_or_else(|| PortableError::Format("C25CC01 compact file row is malformed".into()))?;
        if encoded.len() < 3 {
            return Err(PortableError::Format(
                "C25CC01 compact file row is too short".into(),
            ));
        }
        let kind = value_u64(&encoded[0], "file kind")?;
        let mode = if matches!(encoded[1], Value::Nil) {
            default_mode
        } else {
            value_u64(&encoded[1], "file mode override")?
        };
        let mtime = default_mtime
            .checked_add(value_i64(&encoded[2], "mtime delta")?)
            .ok_or_else(|| PortableError::Limit("C25CC01 mtime delta overflow".into()))?;

        let (size, digest, storage) = match kind {
            1 => (0, Value::Nil, Value::Nil),
            3 => {
                let owner_index = usize::try_from(value_u64(
                    encoded.get(3).ok_or_else(|| {
                        PortableError::Format("hardlink missing owner index".into())
                    })?,
                    "hardlink owner index",
                )?)
                .map_err(|_| {
                    PortableError::Limit("hardlink owner index exceeds native width".into())
                })?;
                let owner = prior_paths
                    .get(owner_index)
                    .ok_or_else(|| {
                        PortableError::Format("hardlink owner does not precede alias".into())
                    })?
                    .clone();
                let size = *prior_sizes.get(&owner).ok_or_else(|| {
                    PortableError::Format("hardlink owner size is unavailable".into())
                })?;
                (size, Value::Nil, Value::Array(vec![Value::from(owner)]))
            }
            _ => {
                if encoded.len() < 6 {
                    return Err(PortableError::Format(
                        "regular compact file row is too short".into(),
                    ));
                }
                let storage = encoded[3].clone();
                let derived = derived_size(&blobs, &recipes, &storage)?;
                let size = if matches!(encoded[4], Value::Nil) {
                    derived.ok_or_else(|| {
                        PortableError::Format("C25CC01 file row cannot derive logical size".into())
                    })?
                } else {
                    value_u64(&encoded[4], "explicit logical size")?
                };
                let tag = storage
                    .as_array()
                    .and_then(|row| row.first())
                    .map(|value| value_u64(value, "storage tag"))
                    .transpose()?
                    .unwrap_or(u64::MAX);
                let digest = if matches!(tag, 1 | 3 | 5) {
                    encoded[5].clone()
                } else {
                    Value::Nil
                };
                (size, digest, storage)
            }
        };

        files.push(Value::Array(vec![
            Value::from(rel.clone()),
            Value::from(kind),
            Value::from(mode),
            Value::from(mtime),
            Value::from(size),
            digest,
            storage,
        ]));
        prior_paths.push(rel.clone());
        prior_sizes.insert(rel, size);
    }

    Ok(Value::Map(vec![
        (Value::from("v"), Value::from(24u64)),
        (Value::from("files"), Value::Array(files)),
        (Value::from("blobs"), Value::Array(blobs)),
        (Value::from("recipes"), Value::Array(recipes)),
        (Value::from("dict_blob"), map_get(compact, "z")?.clone()),
        (Value::from("fsmeta"), map_get(compact, "m")?.clone()),
        (Value::from("features"), Value::Array(features)),
    ]))
}

fn materialize_r24_from_compact(
    candidate_payload: &[u8],
    copies: &ParsedCopies,
    expanded: &Value,
    out: &Path,
) -> Result<(), PortableError> {
    let mut raw = Vec::new();
    rmpv::encode::write_value(&mut raw, expanded).map_err(|error| {
        PortableError::Format(format!("C25CC01 r24 MessagePack encode: {error}"))
    })?;
    let compressed = zstd::stream::encode_all(Cursor::new(&raw), 12).map_err(|error| {
        PortableError::Format(format!("C25CC01 r24 index Zstd encode: {error}"))
    })?;
    let digest = Sha256::digest(&raw);
    let data_end = copies
        .data_start
        .checked_add(copies.data_span)
        .ok_or_else(|| PortableError::Limit("C25CC01 data span overflow".into()))?;
    let data = candidate_payload
        .get(copies.data_start..data_end)
        .ok_or_else(|| PortableError::Format("C25CC01 physical payload is truncated".into()))?;

    let mut payload =
        Vec::with_capacity(HEADER_SIZE + compressed.len() * 2 + data.len() + FOOTER_SIZE);
    payload.extend_from_slice(R24_MAGIC);
    payload.extend_from_slice(&24u16.to_le_bytes());
    payload.extend_from_slice(&0u16.to_le_bytes());
    payload.extend_from_slice(&(compressed.len() as u64).to_le_bytes());
    payload.extend_from_slice(&(raw.len() as u64).to_le_bytes());
    payload.extend_from_slice(&(data.len() as u64).to_le_bytes());
    payload.extend_from_slice(&digest);
    payload.extend_from_slice(&compressed);
    payload.extend_from_slice(data);
    payload.extend_from_slice(&compressed);
    payload.extend_from_slice(R24_TAIL_MAGIC);
    payload.extend_from_slice(&[0, 1, 0, 0]);
    payload.extend_from_slice(&(compressed.len() as u64).to_le_bytes());
    payload.extend_from_slice(&(raw.len() as u64).to_le_bytes());
    payload.extend_from_slice(&0u64.to_le_bytes());
    payload.extend_from_slice(&digest);
    fs::write(out, payload)?;
    Ok(())
}
