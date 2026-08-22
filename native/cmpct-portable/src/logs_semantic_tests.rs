use super::logs::LogsInverseArchive;
use super::logs_public::LogsPublicView;
use std::{
    path::{Path, PathBuf},
    process::Command,
};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("cmpct-portable must live under <repo>/native/")
        .to_path_buf()
}

fn python_hardlink_fixture(root: &Path) {
    let script = r#"
import os
import sys
from pathlib import Path
import zstandard as zstd
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS

root=Path(sys.argv[1])
src=root/'src'
src.mkdir(parents=True)
owner=src/'a-owner.log'
raw=(b'2026-08-21T21:00:00Z INFO hardlink-owner value=42\n' * 4096)
owner.write_bytes(raw)
os.link(owner, src/'z-alias.log')
(src/'a-owner.log.zst').write_bytes(zstd.ZstdCompressor(level=3, threads=0).compress(raw))
archive=root/'candidate.cmpct'
stats=LOGS.build(src, archive)
verified=LOGS.strong_verify(archive)
assert verified['ok'] is True
assert stats['edge_detection']['inverse_edges'] >= 1, stats
"#;
    let repo = repo_root();
    let status = Command::new("python")
        .arg("-c")
        .arg(script)
        .arg(root)
        .current_dir(&repo)
        .env("PYTHONPATH", &repo)
        .status()
        .expect("python hardlink fixture builder must start");
    assert!(status.success(), "python hardlink fixture builder failed");
}

#[test]
fn logs_public_view_resolves_authenticated_hardlink_to_owner_bytes() {
    let temp = tempfile::tempdir().unwrap();
    python_hardlink_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let archive =
        LogsInverseArchive::open(&archive_path).expect("Rust must open Python logs output");
    let view =
        LogsPublicView::new(&archive).expect("Rust must parse canonical filesystem manifest");

    let owner = view
        .entries()
        .iter()
        .position(|entry| entry.path == "a-owner.log")
        .expect("owner must be public");
    let alias = view
        .entries()
        .iter()
        .position(|entry| entry.path == "z-alias.log")
        .expect("hardlink alias must be public");
    assert_eq!(view.entries()[owner].kind, 0);
    assert_eq!(view.entries()[alias].kind, 3);

    let (owner_raw, owner_stats) = view.read_member(owner).expect("owner read");
    let (alias_raw, alias_stats) = view.read_member(alias).expect("hardlink read");
    assert_eq!(alias_raw, owner_raw);
    assert_eq!(alias_stats.logical_bytes, owner_stats.logical_bytes);
    assert!(alias_stats.amplification <= 8.0);
    assert!(alias_stats.decoded_context_bytes <= 8 * 1024 * 1024);
}
