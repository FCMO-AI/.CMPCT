// Pre-dispatch parity harness for the bounded ZIP-factor reader.
//
// The production crate intentionally does not advertise CMP25Z2 yet. This integration-test crate compiles the
// exact shared format/manifest modules plus the candidate decoder, asks the Python fused writer to produce real
// bytes, then proves native verification and member reconstruction. Promotion can wire the identity only after
// this preparatory surface is green.

#[path = "../src/format.rs"]
mod format;
#[path = "../src/manifest.rs"]
mod manifest;
#[path = "../src/zipfactor.rs"]
mod zipfactor;

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum PortableError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("I/O state error: {0}")]
    IoState(String),
    #[error("format error: {0}")]
    Format(String),
    #[error("integrity error: {0}")]
    Integrity(String),
    #[error("resource limit: {0}")]
    Limit(String),
    #[error("unsafe logical path: {0}")]
    Path(String),
    #[error("unsupported operation: {0}")]
    Unsupported(String),
    #[error("requested range/buffer is invalid")]
    Range,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PortableEntry {
    pub path: String,
    pub size: u64,
    pub kind: u8,
    pub mode: u32,
    pub mtime_ns: i64,
}

#[derive(Debug, Clone, Copy)]
pub struct MemberReadStats {
    pub logical_bytes: u64,
    pub decoded_context_bytes: u64,
    pub amplification: f64,
    pub profile: &'static str,
}

fn work_root(label: &str) -> PathBuf {
    let stamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    let root = std::env::temp_dir().join(format!("cmpct-zf-{label}-{}-{stamp}", std::process::id()));
    fs::create_dir_all(&root).unwrap();
    root
}

fn python_fixture(root: &Path, corrupt: bool) -> PathBuf {
    let source = root.join("source");
    let archive = root.join("candidate.cmpct");
    let script = r#"
import pathlib, sys, zipfile
from experiments import entropygraph_v030_zipfactor_fused as ZFF
root=pathlib.Path(sys.argv[1]); source=root/'source'; source.mkdir()
date=(2024,1,2,4,6,8)
for bundle in range(7):
    path=source/f'bundle-{bundle:02d}.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zf:
        for member in range(4):
            info=zipfile.ZipInfo(f'member-{member:02d}.txt',date)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644 << 16
            raw=''.join(f'row={row:04d} member={member} bundle={bundle} value={(row*313+member*17+bundle)%65521:05d}\n' for row in range(160+member*9)).encode()
            zf.writestr(info,raw,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
ZFF.build(source, root/'candidate.cmpct', level=6, group_size=7)
"#;
    let status = Command::new("python")
        .arg("-c")
        .arg(script)
        .arg(root)
        .env("PYTHONPATH", std::env::var("PYTHONPATH").unwrap_or_else(|_| ".".into()))
        .status()
        .expect("launch Python ZIP-factor fixture writer");
    assert!(status.success(), "Python ZIP-factor fixture writer failed");
    if corrupt {
        let mut bytes = fs::read(&archive).unwrap();
        let last = bytes.len() - 5;
        bytes[last] ^= 0x40;
        fs::write(&archive, bytes).unwrap();
    }
    assert!(source.is_dir());
    archive
}

#[test]
fn python_fused_writer_round_trips_through_native_candidate_decoder() {
    let root = work_root("roundtrip");
    let archive_path = python_fixture(&root, false);
    let archive = zipfactor::ZipFactorArchive::open(&archive_path).expect("open Python compact-v2 bytes natively");

    assert_eq!(archive.entries().len(), 8, "manifest + seven ZIP owners");
    assert!(archive.declared_amplification() <= 8.0);
    assert!(!archive.tail_authenticated(), "recovery remains a promotion blocker, not a synthetic green");
    archive.verify().expect("native full verification");

    for bundle in 0..7 {
        let rel = format!("bundle-{bundle:02}.zip");
        let index = archive.entries().iter().position(|entry| entry.path == rel).unwrap();
        let (native, stats) = archive.read_member(index).expect("native ZIP-factor selective read");
        assert_eq!(native, fs::read(root.join("source").join(&rel)).unwrap());
        assert!(stats.amplification <= 8.0);
        assert!(stats.decoded_context_bytes <= 8 * 1024 * 1024);
        assert_eq!(stats.profile, "zip-framing-factor-compact-v2");
    }

    fs::remove_dir_all(root).ok();
}

#[test]
fn native_candidate_decoder_fails_closed_on_group_corruption() {
    let root = work_root("corrupt");
    let archive_path = python_fixture(&root, true);
    match zipfactor::ZipFactorArchive::open(&archive_path) {
        Ok(archive) => assert!(archive.verify().is_err(), "corrupted ZIP-factor bytes must not verify"),
        Err(_) => {}, // corruption may make the compressed group itself malformed, which is equally fail-closed.
    }
    fs::remove_dir_all(root).ok();
}
