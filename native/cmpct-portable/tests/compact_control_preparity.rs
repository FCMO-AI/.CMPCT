use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

const MAGIC: &[u8; 8] = b"C25CC01\0";
const TAIL_MAGIC: &[u8; 8] = b"C25CCT1\0";
const HEADER_SIZE: usize = 68;
const FOOTER_SIZE: usize = 68;

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

fn le_u64(raw: &[u8]) -> u64 {
    u64::from_le_bytes(raw.try_into().unwrap())
}

#[derive(Debug, Clone, Copy)]
struct ControlRanges {
    primary_start: usize,
    primary_end: usize,
    tail_start: usize,
    tail_end: usize,
}

fn control_ranges(payload: &[u8]) -> ControlRanges {
    assert!(payload.len() >= HEADER_SIZE + FOOTER_SIZE);
    assert_eq!(&payload[..8], MAGIC);
    let primary_len = le_u64(&payload[12..20]) as usize;
    let data_span = le_u64(&payload[28..36]) as usize;
    let footer_off = payload.len() - FOOTER_SIZE;
    assert_eq!(&payload[footer_off..footer_off + 8], TAIL_MAGIC);
    let tail_len = le_u64(&payload[footer_off + 12..footer_off + 20]) as usize;
    let primary_start = HEADER_SIZE;
    let primary_end = primary_start + primary_len;
    let tail_start = footer_off - tail_len;
    assert_eq!(primary_end + data_span, tail_start);
    ControlRanges {
        primary_start,
        primary_end,
        tail_start,
        tail_end: footer_off,
    }
}

fn corrupt_middle(payload: &mut [u8], start: usize, end: usize) {
    assert!(end > start);
    payload[start + (end - start) / 2] ^= 0x01;
}

#[test]
fn c25cc01_uses_real_production_portable_dispatch_and_mature_r24_semantics() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");

    let archive = cmpct_portable::PortableArchive::open(&archive_path)
        .expect("production portable dispatch must accept C25CC01");
    assert_eq!(archive.profile(), cmpct_portable::Profile::CompactControl);
    assert_eq!(archive.revision(), 25);
    assert!(archive.tail_metadata_authenticated());
    archive.verify().expect("production C25CC01 verification must pass");

    let entries = archive.entries();
    assert_eq!(entries.len(), 296);
    for (index, entry) in entries.iter().enumerate() {
        assert_eq!(entry.kind, 0, "fixture is intentionally regular-file only");
        let expected = fs::read(temp.path().join("src").join(&entry.path))
            .expect("fixture source member must exist");
        let (actual, _stats) = archive
            .read_member(index)
            .expect("production C25CC01 member read must delegate through mature r24 semantics");
        assert_eq!(actual, expected, "portable dispatch changed {}", entry.path);
    }
}

#[test]
fn c25cc01_production_dispatch_recovers_one_control_copy_and_fails_when_both_are_corrupt() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let source = temp.path().join("candidate.cmpct");
    let original = fs::read(&source).unwrap();
    let ranges = control_ranges(&original);

    let mut primary_bad = original.clone();
    corrupt_middle(&mut primary_bad, ranges.primary_start, ranges.primary_end);
    let primary_bad_path = temp.path().join("primary-bad.cmpct");
    fs::write(&primary_bad_path, &primary_bad).unwrap();
    let recovered_from_tail = cmpct_portable::PortableArchive::open(&primary_bad_path)
        .expect("valid tail control must recover a corrupt primary copy");
    assert!(recovered_from_tail.tail_metadata_authenticated());
    recovered_from_tail.verify().expect("tail recovery must preserve complete verification");

    let mut tail_bad = original.clone();
    corrupt_middle(&mut tail_bad, ranges.tail_start, ranges.tail_end);
    let tail_bad_path = temp.path().join("tail-bad.cmpct");
    fs::write(&tail_bad_path, &tail_bad).unwrap();
    let recovered_from_primary = cmpct_portable::PortableArchive::open(&tail_bad_path)
        .expect("valid primary control must recover a corrupt tail copy");
    assert!(!recovered_from_primary.tail_metadata_authenticated());
    recovered_from_primary.verify().expect("primary recovery must preserve complete verification");

    let mut both_bad = primary_bad;
    corrupt_middle(&mut both_bad, ranges.tail_start, ranges.tail_end);
    let both_bad_path = temp.path().join("both-bad.cmpct");
    fs::write(&both_bad_path, &both_bad).unwrap();
    assert!(
        cmpct_portable::PortableArchive::open(&both_bad_path).is_err(),
        "C25CC01 must fail closed when both authenticated control copies are corrupt"
    );
}
