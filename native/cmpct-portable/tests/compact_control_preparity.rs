use rmpv::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::HashMap,
    fs,
    io::Cursor,
    path::{Path, PathBuf},
    process::Command,
};

const MAGIC: &[u8; 8] = b"C25CC01\0";
const TAIL_MAGIC: &[u8; 8] = b"C25CCT1\0";
const R24_MAGIC: &[u8; 8] = b"CMPCT24\0";
const R24_TAIL_MAGIC: &[u8; 8] = b"CMPTF24\0";
const HEADER_SIZE: usize = 68;
const FOOTER_SIZE: usize = 68;
const MAX_CONTROL_RAW_BYTES: usize = 64 * 1024 * 1024;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("cmpct-portable must live under <repo>/native/")
        .to_path_buf()
}

fn python_fixture(root: &Path) {
    let script = r#"
import random
import sys
from pathlib import Path
from experiments import entropygraph_v030_r24_compact_control_profile as CC

root=Path(sys.argv[1])
src=root/'src'
src.mkdir(parents=True)
rng=random.Random(0xC25CC01)
# A deliberately metadata-heavy, high-entropy tree where compact control is strictly smaller than r24.
for i in range(256):
    p=src/'tiny'/f'block-{i:04d}.bin'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(rng.randbytes(256 + (i % 31)))
for i in range(40):
    p=src/'medium'/f'chunk-{i:03d}.bin'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(rng.randbytes(96*1024 + (i % 5)*1024))
archive=root/'candidate.cmpct'
stats=CC.build(src, archive)
verified=CC.strong_verify(archive)
assert verified['ok'] is True, verified
assert stats['archive_bytes'] < stats['source_r24_bytes'], stats
assert stats['physical_payload_records_unchanged'] is True
assert stats['two_authenticated_control_copies'] is True
print(stats)
"#;
    let repo = repo_root();
    let status = Command::new("python")
        .arg("-c")
        .arg(script)
        .arg(root)
        .current_dir(&repo)
        .env("PYTHONPATH", &repo)
        .status()
        .expect("python compact-control fixture builder must start");
    assert!(
        status.success(),
        "python compact-control fixture builder failed"
    );
}

fn le_u16(raw: &[u8]) -> u16 {
    u16::from_le_bytes(raw.try_into().unwrap())
}

fn le_u64(raw: &[u8]) -> u64 {
    u64::from_le_bytes(raw.try_into().unwrap())
}

fn value_u64(value: &Value, label: &str) -> Result<u64, String> {
    value
        .as_u64()
        .or_else(|| value.as_i64().and_then(|v| u64::try_from(v).ok()))
        .ok_or_else(|| format!("{label} is not a non-negative integer"))
}

fn value_i64(value: &Value, label: &str) -> Result<i64, String> {
    value
        .as_i64()
        .or_else(|| value.as_u64().and_then(|v| i64::try_from(v).ok()))
        .ok_or_else(|| format!("{label} is outside signed 64-bit range"))
}

fn map_get<'a>(value: &'a Value, key: &str) -> Result<&'a Value, String> {
    value
        .as_map()
        .ok_or_else(|| "expected MessagePack map".to_string())?
        .iter()
        .find_map(|(candidate, value)| (candidate.as_str() == Some(key)).then_some(value))
        .ok_or_else(|| format!("missing compact-control key {key:?}"))
}

fn decode_copy(comp: &[u8], raw_len: usize, digest: &[u8]) -> Result<Value, String> {
    if raw_len > MAX_CONTROL_RAW_BYTES {
        return Err("raw control exceeds bound".into());
    }
    let raw = zstd::stream::decode_all(Cursor::new(comp)).map_err(|e| e.to_string())?;
    if raw.len() != raw_len {
        return Err("control length mismatch".into());
    }
    if Sha256::digest(&raw).as_slice() != digest {
        return Err("control SHA mismatch".into());
    }
    let mut cursor = Cursor::new(raw.as_slice());
    let value = rmpv::decode::read_value(&mut cursor).map_err(|e| e.to_string())?;
    if cursor.position() != raw.len() as u64 {
        return Err("trailing bytes after control object".into());
    }
    let map = value.as_map().ok_or("control envelope is not a map")?;
    let mut saw_x = false;
    let mut saw_c = false;
    for (k, v) in map {
        match k.as_str() {
            Some("x") => {
                saw_x = v.as_array().is_some();
            }
            Some("c") => {
                saw_c = v.as_map().is_some();
            }
            _ => return Err("unexpected compact-control envelope key".into()),
        }
    }
    if !saw_x || !saw_c || map.len() != 2 {
        return Err("compact-control envelope shape mismatch".into());
    }
    Ok(value)
}

#[derive(Clone)]
struct ParsedCopies {
    primary: Vec<u8>,
    tail: Vec<u8>,
    primary_raw: usize,
    tail_raw: usize,
    primary_sha: [u8; 32],
    tail_sha: [u8; 32],
    data_span: usize,
}

fn parse_copies(payload: &[u8]) -> ParsedCopies {
    assert!(payload.len() >= HEADER_SIZE + FOOTER_SIZE);
    assert_eq!(&payload[..8], MAGIC);
    assert_eq!(le_u16(&payload[8..10]), 25);
    let primary_len = le_u64(&payload[12..20]) as usize;
    let primary_raw = le_u64(&payload[20..28]) as usize;
    let data_span = le_u64(&payload[28..36]) as usize;
    let mut primary_sha = [0u8; 32];
    primary_sha.copy_from_slice(&payload[36..68]);

    let footer_off = payload.len() - FOOTER_SIZE;
    assert_eq!(&payload[footer_off..footer_off + 8], TAIL_MAGIC);
    let tail_len = le_u64(&payload[footer_off + 12..footer_off + 20]) as usize;
    let tail_raw = le_u64(&payload[footer_off + 20..footer_off + 28]) as usize;
    let mut tail_sha = [0u8; 32];
    tail_sha.copy_from_slice(&payload[footer_off + 36..footer_off + 68]);

    let primary_start = HEADER_SIZE;
    let primary_end = primary_start + primary_len;
    let tail_start = footer_off - tail_len;
    assert_eq!(primary_end + data_span, tail_start);
    ParsedCopies {
        primary: payload[primary_start..primary_end].to_vec(),
        tail: payload[tail_start..footer_off].to_vec(),
        primary_raw,
        tail_raw,
        primary_sha,
        tail_sha,
        data_span,
    }
}

fn blob_size(blobs: &[Value], index: usize) -> Result<u64, String> {
    let row = blobs
        .get(index)
        .and_then(Value::as_array)
        .ok_or_else(|| format!("blob {index} is missing or malformed"))?;
    row.get(1)
        .ok_or_else(|| format!("blob {index} is missing logical size"))
        .and_then(|value| value_u64(value, "blob logical size"))
}

fn derived_size(blobs: &[Value], recipes: &[Value], storage: &Value) -> Result<Option<u64>, String> {
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
                row.get(1).ok_or("direct storage missing blob index")?,
                "direct blob index",
            )?)
            .map_err(|_| "direct blob index exceeds native width".to_string())?;
            Ok(Some(blob_size(blobs, index)?))
        }
        1 => {
            let ids = row
                .get(1)
                .and_then(Value::as_array)
                .ok_or("fixed-chunk storage missing chunk list")?;
            let mut total = 0u64;
            for value in ids {
                let index = usize::try_from(value_u64(value, "fixed chunk index")?)
                    .map_err(|_| "fixed chunk index exceeds native width".to_string())?;
                total = total
                    .checked_add(blob_size(blobs, index)?)
                    .ok_or("fixed-chunk logical size overflow")?;
            }
            Ok(Some(total))
        }
        2 => {
            let index = usize::try_from(value_u64(
                row.get(1).ok_or("virtual-ZIP storage missing recipe index")?,
                "virtual-ZIP recipe index",
            )?)
            .map_err(|_| "virtual-ZIP recipe index exceeds native width".to_string())?;
            let recipe = recipes
                .get(index)
                .and_then(Value::as_array)
                .ok_or("virtual-ZIP recipe missing or malformed")?;
            Ok(Some(value_u64(
                recipe.get(4).ok_or("virtual-ZIP recipe missing logical size")?,
                "virtual-ZIP logical size",
            )?))
        }
        4 => Ok(Some(value_u64(
            row.get(3).ok_or("pack storage missing length")?,
            "pack length",
        )?)),
        5 => {
            let rows = row
                .get(1)
                .and_then(Value::as_array)
                .ok_or("CDC storage missing chunk rows")?;
            let mut total = 0u64;
            for value in rows {
                let chunk = value.as_array().ok_or("CDC chunk row is malformed")?;
                total = total
                    .checked_add(value_u64(
                        chunk.first().ok_or("CDC chunk missing logical length")?,
                        "CDC logical length",
                    )?)
                    .ok_or("CDC logical size overflow")?;
            }
            Ok(Some(total))
        }
        _ => Ok(None),
    }
}

fn expand_compact_control(envelope: &Value) -> Result<Value, String> {
    let features = map_get(envelope, "x")?
        .as_array()
        .ok_or("features are not an array")?
        .clone();
    let compact = map_get(envelope, "c")?;
    let paths = map_get(compact, "p")?
        .as_array()
        .ok_or("compact paths are not an array")?;
    let encoded_files = map_get(compact, "f")?
        .as_array()
        .ok_or("compact files are not an array")?;
    if paths.len() != encoded_files.len() {
        return Err("compact path/file row count mismatch".into());
    }
    let defaults = map_get(compact, "d")?
        .as_array()
        .ok_or("compact defaults are not an array")?;
    if defaults.len() != 2 {
        return Err("compact defaults have invalid shape".into());
    }
    let default_mode = value_u64(&defaults[0], "default mode")?;
    let default_mtime = value_i64(&defaults[1], "default mtime")?;
    let blobs = map_get(compact, "b")?
        .as_array()
        .ok_or("compact blobs are not an array")?
        .clone();
    let recipes = map_get(compact, "r")?
        .as_array()
        .ok_or("compact recipes are not an array")?
        .clone();

    let mut previous = String::new();
    let mut prior_paths = Vec::<String>::new();
    let mut prior_sizes = HashMap::<String, u64>::new();
    let mut files = Vec::<Value>::with_capacity(encoded_files.len());

    for (path_row, encoded) in paths.iter().zip(encoded_files) {
        let path_row = path_row.as_array().ok_or("compact path row is malformed")?;
        if path_row.len() != 2 {
            return Err("compact path row has invalid shape".into());
        }
        let prefix = usize::try_from(value_u64(&path_row[0], "compact path prefix")?)
            .map_err(|_| "compact path prefix exceeds native width".to_string())?;
        if prefix > previous.len() || !previous.is_char_boundary(prefix) {
            return Err("compact path prefix is outside prior UTF-8 path".into());
        }
        let suffix = path_row[1]
            .as_str()
            .ok_or("compact path suffix is not UTF-8")?;
        let rel = format!("{}{}", &previous[..prefix], suffix);
        previous.clone_from(&rel);

        let encoded = encoded.as_array().ok_or("compact file row is malformed")?;
        if encoded.len() < 3 {
            return Err("compact file row is too short".into());
        }
        let kind = value_u64(&encoded[0], "file kind")?;
        let mode = if matches!(encoded[1], Value::Nil) {
            default_mode
        } else {
            value_u64(&encoded[1], "file mode override")?
        };
        let mtime = default_mtime
            .checked_add(value_i64(&encoded[2], "mtime delta")?)
            .ok_or("mtime delta overflow")?;

        let (size, digest, storage) = match kind {
            1 => (0, Value::Nil, Value::Nil),
            3 => {
                let owner_index = usize::try_from(value_u64(
                    encoded.get(3).ok_or("hardlink missing owner index")?,
                    "hardlink owner index",
                )?)
                .map_err(|_| "hardlink owner index exceeds native width".to_string())?;
                let owner = prior_paths
                    .get(owner_index)
                    .ok_or("hardlink owner does not precede alias")?
                    .clone();
                let size = *prior_sizes
                    .get(&owner)
                    .ok_or("hardlink owner size is unavailable")?;
                (size, Value::Nil, Value::Array(vec![Value::from(owner)]))
            }
            _ => {
                if encoded.len() < 6 {
                    return Err("regular compact file row is too short".into());
                }
                let storage = encoded[3].clone();
                let derived = derived_size(&blobs, &recipes, &storage)?;
                let size = if matches!(encoded[4], Value::Nil) {
                    derived.ok_or("compact file row cannot derive logical size")?
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
    envelope: &Value,
    out: &Path,
) -> Result<(), String> {
    let expanded = expand_compact_control(envelope)?;
    let mut raw = Vec::new();
    rmpv::encode::write_value(&mut raw, &expanded).map_err(|e| e.to_string())?;
    let compressed = zstd::stream::encode_all(Cursor::new(&raw), 12).map_err(|e| e.to_string())?;
    let digest = Sha256::digest(&raw);
    let data_start = HEADER_SIZE
        .checked_add(copies.primary.len())
        .ok_or("candidate data offset overflow")?;
    let data_end = data_start
        .checked_add(copies.data_span)
        .ok_or("candidate data end overflow")?;
    let data = candidate_payload
        .get(data_start..data_end)
        .ok_or("candidate data span is truncated")?;

    let mut payload = Vec::with_capacity(HEADER_SIZE + compressed.len() * 2 + data.len() + FOOTER_SIZE);
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
    fs::write(out, payload).map_err(|e| e.to_string())
}

#[test]
fn python_c25cc01_writer_has_bounded_authenticated_two_copy_control() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let payload = fs::read(&archive_path).unwrap();
    let copies = parse_copies(&payload);
    assert!(copies.data_span > 0);

    let primary = decode_copy(&copies.primary, copies.primary_raw, &copies.primary_sha)
        .expect("primary compact-control copy must authenticate");
    let tail = decode_copy(&copies.tail, copies.tail_raw, &copies.tail_sha)
        .expect("tail compact-control copy must authenticate");
    assert_eq!(
        primary, tail,
        "both authenticated control copies must be semantic peers"
    );

    // Pre-dispatch contract: native production dispatch must remain closed until the compact-control semantic
    // expansion below is moved behind the shared production PortableArchive surface.
    assert!(
        cmpct_portable::PortableArchive::open(&archive_path).is_err(),
        "C25CC01 must remain outside production portable dispatch during preparity"
    );
}

#[test]
fn c25cc01_rust_expansion_reuses_mature_r24_core_for_all_regular_members() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let payload = fs::read(&archive_path).unwrap();
    let copies = parse_copies(&payload);
    let control = decode_copy(&copies.primary, copies.primary_raw, &copies.primary_sha)
        .expect("primary compact-control copy must authenticate");
    let r24_path = temp.path().join("rust-expanded-r24.cmpct");
    materialize_r24_from_compact(&payload, &copies, &control, &r24_path)
        .expect("Rust compact-control expansion must produce a valid r24 envelope");

    let archive = cmpct_core::Archive::open(&r24_path)
        .expect("mature native r24 core must accept Rust-expanded compact control");
    let mut checked = 0usize;
    for (index, entry) in archive.entries().iter().enumerate() {
        if entry.kind != 0 {
            continue;
        }
        let expected = fs::read(temp.path().join("src").join(&entry.path))
            .expect("fixture source member must exist");
        let mut actual = vec![0u8; expected.len()];
        let read = archive
            .read_range(index, 0, &mut actual)
            .expect("mature r24 core must read expanded compact-control member");
        assert_eq!(read, expected.len());
        assert_eq!(actual, expected, "native semantic expansion changed {}", entry.path);
        checked += 1;
    }
    assert_eq!(checked, 296, "fixture must exercise every regular member through native r24 semantics");
}

#[test]
fn c25cc01_control_copies_fail_and_recover_independently() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let payload = fs::read(temp.path().join("candidate.cmpct")).unwrap();
    let copies = parse_copies(&payload);

    let mut bad_primary = copies.primary.clone();
    let primary_mid = bad_primary.len() / 2;
    bad_primary[primary_mid] ^= 0x01;
    assert!(decode_copy(&bad_primary, copies.primary_raw, &copies.primary_sha).is_err());
    assert!(decode_copy(&copies.tail, copies.tail_raw, &copies.tail_sha).is_ok());

    let mut bad_tail = copies.tail.clone();
    let tail_mid = bad_tail.len() / 2;
    bad_tail[tail_mid] ^= 0x01;
    assert!(decode_copy(&copies.primary, copies.primary_raw, &copies.primary_sha).is_ok());
    assert!(decode_copy(&bad_tail, copies.tail_raw, &copies.tail_sha).is_err());

    assert!(decode_copy(&bad_primary, copies.primary_raw, &copies.primary_sha).is_err());
    assert!(decode_copy(&bad_tail, copies.tail_raw, &copies.tail_sha).is_err());
}
