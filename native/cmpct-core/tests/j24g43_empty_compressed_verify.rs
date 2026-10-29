//! J24G43: zero-logical-byte compressed physical payload never visited by native verify_complete.
//! Research-only expected negative; ignored unless hosted authentic-to-derived specimens exist.
//! Success here means an integrity gap was reproduced, NOT that the product is safe.
use cmpct_core::Archive;
use std::env;
use std::path::PathBuf;

fn specimen(stem: &str) -> PathBuf {
    PathBuf::from(env::var("J24G43_CASE_DIR").expect("source-exact research fixture required"))
        .join(format!("{stem}.cmpct"))
}

#[test]
#[ignore = "requires genuine Builder-derived zero-sized r24 Zstd physical archive"]
fn j24g43_zero_logical_size_does_not_verify_corrupt_encoded_payload() {
    let source = Archive::open(&specimen("source-raw")).expect("first-party empty RAW source");
    assert_eq!(source.entries().len(), 1);
    assert_eq!(source.entries()[0].size, 0);
    assert_eq!(
        source.verify_complete().expect("authentic empty source strong verify"),
        1
    );
    println!("J24G43_ORIGINAL_RAW:verified_count=1");

    let valid = Archive::open(&specimen("valid-zstd-empty")).expect("derived valid Zstd empty");
    assert_eq!(valid.entries().len(), 1);
    assert_eq!(valid.entries()[0].size, 0);
    assert_eq!(
        valid.verify_complete().expect("valid compressed empty member"),
        1
    );
    println!("J24G43_VALID_ZSTD_EMPTY:verified_count=1");

    let corrupt = Archive::open(&specimen("corrupt-zstd-empty"))
        .expect("re-signed index and coherent CMA4 header must remain parseable");
    assert_eq!(corrupt.entries().len(), 1);
    assert_eq!(corrupt.entries()[0].size, 0);
    // Prospective prediction: while offset < entry.size never executes, so even an
    // invalid compressed frame is certified as a verified logical member.
    match corrupt.verify_complete() {
        Ok(1) => println!("J24G43_NATIVE_CORRUPT_ZSTD_ZERO_ACCEPTED:verified_count=1"),
        Ok(count) => panic!("prediction falsified by unexpected payload count: {count}"),
        Err(error) => panic!("prediction falsified: native rejected invalid Zstd: {error}"),
    }
}
