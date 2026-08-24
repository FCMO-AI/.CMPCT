use sha2::{Digest, Sha256};
use std::{
    fs,
    io::Cursor,
    path::{Path, PathBuf},
    process::Command,
};

const MAGIC: &[u8; 8] = b"C25CC01\0";
const TAIL_MAGIC: &[u8; 8] = b"C25CCT1\0";
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
    assert!(status.success(), "python compact-control fixture builder failed");
}

fn le_u16(raw: &[u8]) -> u16 {
    u16::from_le_bytes(raw.try_into().unwrap())
}

fn le_u64(raw: &[u8]) -> u64 {
    u64::from_le_bytes(raw.try_into().unwrap())
}

fn decode_copy(comp: &[u8], raw_len: usize, digest: &[u8]) -> Result<rmpv::Value, String> {
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

#[test]
fn python_c25cc01_writer_has_bounded_authenticated_two_copy_control() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let payload = fs::read(&archive_path).unwrap();
    let copies = parse_copies(&payload);
    assert!(copies.data_span > 0);

    let primary = decode_copy(
        &copies.primary,
        copies.primary_raw,
        &copies.primary_sha,
    )
    .expect("primary compact-control copy must authenticate");
    let tail = decode_copy(&copies.tail, copies.tail_raw, &copies.tail_sha)
        .expect("tail compact-control copy must authenticate");
    assert_eq!(primary, tail, "both authenticated control copies must be semantic peers");

    // Pre-dispatch contract: native production dispatch must remain closed until full r24-index expansion/member
    // parity is implemented. This test makes preparity useful without manufacturing a portability green.
    assert!(
        cmpct_portable::PortableArchive::open(&archive_path).is_err(),
        "C25CC01 must remain outside production portable dispatch during preparity"
    );
}

#[test]
fn c25cc01_control_copies_fail_and_recover_independently() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let payload = fs::read(temp.path().join("candidate.cmpct")).unwrap();
    let copies = parse_copies(&payload);

    let mut bad_primary = copies.primary.clone();
    bad_primary[bad_primary.len() / 2] ^= 0x01;
    assert!(decode_copy(&bad_primary, copies.primary_raw, &copies.primary_sha).is_err());
    assert!(decode_copy(&copies.tail, copies.tail_raw, &copies.tail_sha).is_ok());

    let mut bad_tail = copies.tail.clone();
    bad_tail[bad_tail.len() / 2] ^= 0x01;
    assert!(decode_copy(&copies.primary, copies.primary_raw, &copies.primary_sha).is_ok());
    assert!(decode_copy(&bad_tail, copies.tail_raw, &copies.tail_sha).is_err());

    assert!(decode_copy(&bad_primary, copies.primary_raw, &copies.primary_sha).is_err());
    assert!(decode_copy(&bad_tail, copies.tail_raw, &copies.tail_sha).is_err());
}
