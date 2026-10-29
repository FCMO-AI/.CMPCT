//! J24I30 — actual native revision-24 strong-verify coverage of symlink records.
//!
//! Expected scientific NEGATIVE: the current Archive::verify_complete skips
//! non-regular entries, including genuine symlinks. A passing test documents
//! the defect; it does not assert a safe released-product behavior.
use cmpct_core::Archive;
use std::env;
use std::path::PathBuf;

#[test]
fn j24i30_source_exact_native_symlink_verify_falsifier() {
    let root = PathBuf::from(
        env::var("J24I30_CASE_DIR").expect("J24I30_CASE_DIR must point at authenticated wire specimens"),
    );
    let cases = [
        "original",
        "present-correct",
        "present-empty",
        "present-foreign",
        "physical-wrong",
    ];
    let mut observed = Vec::new();
    for label in cases {
        let path = root.join(format!("{label}.cmpct"));
        let archive = Archive::open(&path)
            .unwrap_or_else(|e| panic!("{label}: native cannot open authentic r24 signed-index variant: {e}"));
        assert_eq!(archive.entries().len(), 1, "{label}: expected one member");
        assert_eq!(archive.entries()[0].kind, 2, "{label}: expected genuine symlink kind");
        assert_eq!(archive.entries()[0].path, "link");
        let verified = archive.verify_complete().unwrap_or_else(|e| {
            panic!("{label}: native rejected the predicted contradictory variant: {e}")
        });
        assert_eq!(verified, 0, "{label}: current native skips symlinks rather than hashing them");
        observed.push(format!("{label}:native_verify_ok=true;verified_regular_count={verified}"));
    }
    for observation in observed {
        println!("J24I30_NEGATIVE_{observation}");
    }
}
