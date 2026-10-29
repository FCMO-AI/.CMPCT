//! J24I34 product candidate court: native complete verification must authenticate symlink bytes.
//!
//! J24I30 research is frozen negative evidence for its original source. This separate
//! test expects the opposite behavior on *this* candidate, without editing historical tests.
//! Dedicated CI supplies actual Builder-origin r24 files; ordinary Cargo marks it ignored.
use cmpct_core::{Archive, CmpctError};
use std::env;
use std::path::PathBuf;

fn case_path(case: &str) -> PathBuf {
    PathBuf::from(env::var("J24I34_CASE_DIR").expect("dedicated CI must supply J24I34_CASE_DIR"))
        .join(format!("{case}.cmpct"))
}

#[test]
#[ignore = "requires physically authenticated J24I34_CASE_DIR; execute from dedicated CI"]
fn j24i34_real_symlink_and_present_correct_strongly_verified() {
    for case in ["original", "present-correct"] {
        let archive = Archive::open(&case_path(case))
            .unwrap_or_else(|e| panic!("{case}: native failed to open genuine r24 symlink: {e}"));
        assert_eq!(archive.entries().len(), 1);
        assert_eq!(archive.entries()[0].kind, 2);
        assert_eq!(archive.entries()[0].path, "link");
        let count = archive
            .verify_complete()
            .unwrap_or_else(|e| panic!("{case}: complete verification unexpectedly rejected: {e}"));
        assert_eq!(
            count, 1,
            "{case}: symlink must count as one verified payload"
        );
        println!("J24I34_GOOD_{case}:verified_payload_count={count}");
    }
}

#[test]
#[ignore = "requires physically authenticated J24I34_CASE_DIR; execute from dedicated CI"]
fn j24i34_bad_logical_or_physical_symlink_is_rejected() {
    for case in ["present-foreign", "physical-wrong"] {
        let archive = Archive::open(&case_path(case))
            .unwrap_or_else(|e| panic!("{case}: signed index should be parse-admissible: {e}"));
        match archive.verify_complete() {
            Err(CmpctError::MemberHash) => {
                println!("J24I34_REJECTED_{case}:reason=MemberHash");
            }
            Err(other) => panic!("{case}: different failure reason: {other}"),
            Ok(count) => panic!("{case}: false integrity pass after {count} verified entries"),
        }
    }
}

#[test]
#[ignore = "requires physically authenticated J24I34_CASE_DIR; execute from dedicated CI"]
fn j24i34_legacy_empty_optional_hash_parity_is_still_unresolved() {
    let error = Archive::open(&case_path("present-empty"))
        .expect_err("legacy empty row SHA remains a separate native parser obligation");
    assert!(
        error.to_string().contains("invalid logical SHA-256 length"),
        "unexpected admission error: {error}"
    );
    println!("J24I34_SEPARATE_DEBT_empty_optional_sha=native_rejected");
}
