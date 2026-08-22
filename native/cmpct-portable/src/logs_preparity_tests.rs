use super::logs::LogsInverseArchive;
use super::logs_public::LogsPublicView;
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

const HEADER_SIZE: usize = 8 + 8 + 8 + 4 + 32;
const FOOTER_SIZE: usize = HEADER_SIZE;

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("cmpct-portable must live under <repo>/native/")
        .to_path_buf()
}

fn python_fixture(root: &Path) {
    let script = r#"
import gzip
import hashlib
import os
import sys
from pathlib import Path
import zstandard as zstd
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS

root=Path(sys.argv[1])
src=root/'src'
src.mkdir(parents=True)
(src/'nested').mkdir()
zstd_plain=(b'2026-08-21T20:00:00Z INFO request=alpha value=42\n' * 4096)
gzip_plain=(b'2026-08-21T20:00:01Z WARN request=beta value=17\n' * 3584)
unmatched=(b'2026-08-21T20:00:02Z INFO request=gamma value=99\n' * 2048)
(src/'zstd.log').write_bytes(zstd_plain)
(src/'zstd.log.zst').write_bytes(zstd.ZstdCompressor(level=3, threads=0).compress(zstd_plain))
(src/'gzip.log').write_bytes(gzip_plain)
(src/'gzip.log.gz').write_bytes(gzip.compress(gzip_plain, compresslevel=6, mtime=0))
(src/'unmatched.log').write_bytes(unmatched)
os.symlink('zstd.log', src/'zstd-link')
archive=root/'candidate.cmpct'
stats=LOGS.build(src, archive)
verified=LOGS.strong_verify(archive)
assert verified['ok'] is True
assert stats['inverse_edges'] >= 2, stats
assert 'gzip.log.gz' in stats['inverse_edge_sources'], stats
assert 'zstd.log.zst' in stats['inverse_edge_sources'], stats
(root/'expected.tsv').write_text(''.join(
    f"{p.relative_to(src).as_posix()}\t{hashlib.sha256(p.read_bytes()).hexdigest()}\t{p.stat().st_size}\n"
    for p in sorted(src.rglob('*')) if p.is_file() and not p.is_symlink()
), encoding='utf-8')
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
        .expect("python logs fixture builder must start");
    assert!(
        status.success(),
        "python logs inverse fixture builder failed"
    );
}

fn expected_rows(path: &Path) -> Vec<(String, String, u64)> {
    fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|line| {
            let mut fields = line.split('\t');
            (
                fields.next().unwrap().to_owned(),
                fields.next().unwrap().to_owned(),
                fields.next().unwrap().parse().unwrap(),
            )
        })
        .collect()
}

fn digest_hex(digest: [u8; 32]) -> String {
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn le_u64(raw: &[u8]) -> u64 {
    u64::from_le_bytes(raw.try_into().unwrap())
}

#[test]
fn python_logs_writer_rust_reader_roundtrips_gzip_zstd_inverse_edges_and_locality() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    assert!(
        crate::PortableArchive::open(&archive_path).is_err(),
        "logs inverse profile must remain outside production native dispatch until promotion is complete"
    );
    let archive =
        LogsInverseArchive::open(&archive_path).expect("Rust must open Python logs output");
    let expected = expected_rows(&temp.path().join("expected.tsv"));

    assert!(archive.tail_authenticated());
    assert_eq!(archive.recovery_route(), "primary");
    archive
        .verify()
        .expect("Rust strong logs inverse verification");

    let mut max_context = 0u64;
    for (rel, sha, size) in &expected {
        let index = archive
            .entries()
            .iter()
            .position(|entry| &entry.path == rel)
            .expect("Python source path must exist in Rust logical table");
        let (identity_size, identity_sha) = archive.entry_identity(index).unwrap();
        assert_eq!(identity_size, *size);
        assert_eq!(digest_hex(identity_sha), *sha);
        let (raw, stats) = archive.read_member(index).unwrap();
        assert_eq!(raw.len() as u64, *size);
        assert_eq!(format!("{:x}", Sha256::digest(&raw)), *sha);
        assert!(stats.amplification <= 8.0);
        max_context = max_context.max(stats.decoded_context_bytes);
    }
    assert!(max_context <= 8 * 1024 * 1024);
}

#[test]
fn native_logs_public_view_uses_authenticated_filesystem_manifest() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let archive = LogsInverseArchive::open(&archive_path).unwrap();
    let view =
        LogsPublicView::new(&archive).expect("canonical filesystem manifest must parse in Rust");

    assert!(
        view.entries()
            .iter()
            .all(|entry| !entry.path.starts_with(".__cmpct_r25_internal__/"))
    );
    let nested = view
        .entries()
        .iter()
        .position(|entry| entry.path == "nested")
        .unwrap();
    let link = view
        .entries()
        .iter()
        .position(|entry| entry.path == "zstd-link")
        .unwrap();
    let zstd = view
        .entries()
        .iter()
        .position(|entry| entry.path == "zstd.log")
        .unwrap();
    assert_eq!(view.entries()[nested].kind, 1);
    assert_eq!(view.entries()[link].kind, 2);
    assert_eq!(view.entries()[zstd].kind, 0);
    assert!(view.read_member(nested).is_err());
    assert!(view.read_member(link).is_err());
    let (raw, stats) = view.read_member(zstd).unwrap();
    assert_eq!(raw.len() as u64, view.entries()[zstd].size);
    assert!(stats.amplification <= 8.0);
}

#[test]
fn native_logs_reader_recovers_either_metadata_copy_and_fails_when_both_are_damaged() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let original_path = temp.path().join("candidate.cmpct");
    let original = fs::read(&original_path).unwrap();
    assert!(original.len() > HEADER_SIZE + FOOTER_SIZE + 8);

    let mut primary = original.clone();
    primary[HEADER_SIZE + 3] ^= 0x5a;
    let primary_path = temp.path().join("primary-damaged.cmpct");
    fs::write(&primary_path, primary).unwrap();
    let recovered =
        LogsInverseArchive::open(&primary_path).expect("tail must recover damaged primary");
    assert_eq!(recovered.recovery_route(), "tail");
    recovered.verify().unwrap();

    let tail_csize =
        le_u64(&original[original.len() - FOOTER_SIZE + 8..original.len() - FOOTER_SIZE + 16])
            as usize;
    let tail_offset = original.len() - FOOTER_SIZE - tail_csize;
    let mut tail = original.clone();
    tail[tail_offset + 3] ^= 0xa5;
    let tail_path = temp.path().join("tail-damaged.cmpct");
    fs::write(&tail_path, tail).unwrap();
    let primary_route =
        LogsInverseArchive::open(&tail_path).expect("primary must survive damaged tail");
    assert_eq!(primary_route.recovery_route(), "primary");
    primary_route.verify().unwrap();

    let mut both = original;
    both[HEADER_SIZE + 3] ^= 0x5a;
    both[tail_offset + 3] ^= 0xa5;
    let both_path = temp.path().join("both-damaged.cmpct");
    fs::write(&both_path, both).unwrap();
    assert!(LogsInverseArchive::open(&both_path).is_err());
}