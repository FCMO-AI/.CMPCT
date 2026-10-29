//! J24I33a scientific falsifier: final serialized directory SHA sentinel.
//! Dedicated installed CI only. Green means authentic current Builder trees work;
//! it also records the separate artificial b'' reader-parity negative.
//! Do not replace/falsify J24I30 frozen historical research tests.
use cmpct_core::Archive;
use std::env;
use std::path::PathBuf;

fn specimen(name: &str) -> PathBuf {
    let root = PathBuf::from(
        env::var("J24I33_CASE_DIR").expect("dedicated CI must supply J24I33_CASE_DIR"),
    );
    root.join(format!("{name}.cmpct"))
}

#[test]
#[ignore = "requires authentic J24I33 source specimens; execute by dedicated CI"]
fn j24i33a_authentic_nested_and_flat_files_open_and_verify() {
    let real = Archive::open(&specimen("real-nested"))
        .expect("authentic Builder nested directory tree must open in native");
    assert_eq!(
        real.entries().len(),
        3,
        "expected two directories and a regular file"
    );
    assert_eq!(
        real.entries().iter().map(|e| e.kind).collect::<Vec<_>>(),
        vec![1, 1, 0],
        "actual persisted Builder entry topology differs from preregistered source"
    );
    assert_eq!(real.entries()[2].path, "nested/payload.bin");
    assert_eq!(
        real.verify_complete()
            .expect("native must verify regular payload"),
        1
    );
    println!("J24I33_AUTHENTIC_NATIVE_nested=true;verified_regular=1");

    let flat =
        Archive::open(&specimen("flat")).expect("flat same-payload Builder control must open");
    assert_eq!(flat.entries().len(), 1);
    assert_eq!(flat.entries()[0].kind, 0);
    assert_eq!(flat.entries()[0].path, "payload.bin");
    assert_eq!(
        flat.verify_complete()
            .expect("native must verify flat payload"),
        1
    );
    println!("J24I33_AUTHENTIC_NATIVE_flat=true;verified_regular=1");
}

#[test]
#[ignore = "requires J24I33 derived signed-index specimens; execute by dedicated CI"]
fn j24i33a_only_optional_empty_sentinel_has_native_python_gap() {
    for label in ["inserted-empty", "invalid-one-byte"] {
        let err = Archive::open(&specimen(label)).expect_err(
            "unmodified strict native parser should refuse malformed-length binary digest",
        );
        let why = err.to_string();
        assert!(
            why.contains("invalid logical SHA-256 length"),
            "{label}: unexpected native reason {why}"
        );
        println!("J24I33_NATIVE_REFUSAL_{label}={why}");
    }
}
