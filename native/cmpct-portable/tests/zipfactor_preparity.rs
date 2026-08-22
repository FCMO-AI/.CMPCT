use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

use cmpct_portable::zipfactor::ZipFactorArchive;
use sha2::{Digest, Sha256};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("cmpct-portable must live under <repo>/native/")
        .to_path_buf()
}

fn python_fixture(root: &Path) {
    let script = r#"
import sys
from pathlib import Path
from experiments import entropygraph_v030_zipfactor_fused as ZFF
from tests import test_v030_zip_framing_factor_admission as ADMIT

root=Path(sys.argv[1])
src=root/'src'
src.mkdir(parents=True)
ADMIT._make_family(src, archives=5, members=3)
product=ZFF._fused_scan(src)
payload, stats=ZFF._build_archive(product, level=3)
(root/'candidate.cmpct').write_bytes(payload)
(root/'expected.tsv').write_text(''.join(
    f"{entry.rel}\t{entry.sha256}\t{entry.size}\n" for entry in product.entries
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
        .expect("python fixture builder must start");
    assert!(status.success(), "python ZIP-factor fixture builder failed");
}

fn expected_rows(path: &Path) -> Vec<(String, String, u64)> {
    fs::read_to_string(path)
        .unwrap()
        .lines()
        .map(|line| {
            let mut fields = line.split('\t');
            (
                fields.next().unwrap().to_string(),
                fields.next().unwrap().to_string(),
                fields.next().unwrap().parse().unwrap(),
            )
        })
        .collect()
}

fn digest_hex(digest: [u8; 32]) -> String {
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[test]
fn python_writer_rust_reader_reconstructs_exact_zip_family() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let archive =
        ZipFactorArchive::open(&archive_path).expect("Rust must open Python writer output");
    let expected = expected_rows(&temp.path().join("expected.tsv"));

    // The production reader exposes the authenticated filesystem manifest as member zero.
    assert_eq!(archive.entries().len(), expected.len() + 1);
    assert!(archive.declared_amplification() <= 8.0);
    assert!(
        !archive.tail_authenticated(),
        "CMP25Z2 remains preparity-only until its recovery envelope is wired into native production dispatch"
    );
    archive.verify().expect("Rust strong ZIP-factor verification");

    let mut max_decode_unit = 0u64;
    for (rel, sha, size) in &expected {
        let index = archive
            .entries()
            .iter()
            .position(|entry| &entry.path == rel)
            .expect("Python writer path must exist in Rust logical table");
        let entry = &archive.entries()[index];
        assert_eq!(entry.size, *size);
        let (identity_size, identity_sha) = archive.entry_identity(index).unwrap();
        assert_eq!(identity_size, *size);
        assert_eq!(digest_hex(identity_sha), *sha);

        let (raw, stats) = archive.read_member(index).unwrap();
        assert_eq!(raw.len() as u64, *size);
        assert!(stats.amplification <= 8.0);
        max_decode_unit = max_decode_unit.max(stats.decoded_context_bytes);
        let got = Sha256::digest(&raw);
        assert_eq!(format!("{got:x}"), *sha);
    }
    assert!(max_decode_unit <= 8 * 1024 * 1024);
}

#[test]
fn zipfactor_preparity_rejects_corruption_and_remains_outside_production_dispatch() {
    let temp = tempfile::tempdir().unwrap();
    python_fixture(temp.path());
    let archive_path = temp.path().join("candidate.cmpct");
    let parsed = ZipFactorArchive::open(&archive_path).unwrap();
    let (_, stats) = parsed.read_member(1).unwrap();
    assert!(stats.amplification <= 8.0);
    assert!(!parsed.tail_authenticated());
    drop(parsed);

    let mut raw = fs::read(&archive_path).unwrap();
    let middle = raw.len() / 2;
    raw[middle] ^= 0x5a;
    let corrupted_path = temp.path().join("corrupted.cmpct");
    fs::write(&corrupted_path, raw).unwrap();
    assert!(
        ZipFactorArchive::open(&corrupted_path)
            .and_then(|archive| archive.verify().map(|_| archive))
            .is_err()
    );

    let production = cmpct_portable::PortableArchive::open(&archive_path);
    assert!(
        production.is_err(),
        "CMP25Z2 must remain outside production dispatch until recovery/native promotion is complete"
    );
}
