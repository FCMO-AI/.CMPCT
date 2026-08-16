#[path = "../src/deflate_physical.rs"]
mod deflate_physical;

use deflate_physical::{authenticated_range, PhysicalDeflateError};
use flate2::write::DeflateEncoder;
use flate2::Compression;
use sha2::{Digest, Sha256};
use std::io::Write;

const MAX_OBJECT: u64 = 256 * 1024 * 1024;

#[test]
fn mode0_exact_stream_range_is_returned_only_after_logical_authentication() {
    // Builder-independent v24-virtual-zip-deflate-mode0.json oracle.
    let compressed = hex_bytes("cb48cdc9c9d74dce2d482ee10200");
    let logical = b"hello-cmpct\n";
    assert_eq!(
        format!("{:x}", Sha256::digest(logical)),
        "ebf39a39099f6b93686b3ff4438afa3d6b3c41f3bde5cce7b25f5034e81c386a"
    );
    let expected_hash: [u8; 32] = Sha256::digest(logical).into();

    let mut out = [0u8; 7];
    authenticated_range(
        &compressed,
        logical.len() as u64,
        &expected_hash,
        3,
        &mut out,
        MAX_OBJECT,
    )
    .unwrap();
    assert_eq!(&out, &compressed[3..10]);
}

#[test]
fn mode0_streaming_auth_handles_logical_objects_larger_than_the_auth_buffer() {
    // Exercise many authentication-buffer turns. A highly compressible payload is intentional here:
    // the assertion targets decoded-work memory, not compression ratio or compressor throughput.
    let logical = vec![b'A'; 2 * 1024 * 1024];
    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::new(6));
    encoder.write_all(&logical).unwrap();
    let compressed = encoder.finish().unwrap();
    let expected_hash: [u8; 32] = Sha256::digest(&logical).into();

    let start = compressed.len() / 3;
    let length = 17usize.min(compressed.len() - start);
    let mut out = vec![0u8; length];
    authenticated_range(
        &compressed,
        logical.len() as u64,
        &expected_hash,
        start as u64,
        &mut out,
        MAX_OBJECT,
    )
    .unwrap();
    assert_eq!(out, compressed[start..start + length]);
}

#[test]
fn mode0_corruption_and_wrong_identity_fail_closed() {
    let mut compressed = hex_bytes("cb48cdc9c9d74dce2d482ee10200");
    let logical = b"hello-cmpct\n";
    let expected_hash: [u8; 32] = Sha256::digest(logical).into();
    compressed[5] ^= 1;

    let mut out = [0u8; 4];
    let error = authenticated_range(
        &compressed,
        logical.len() as u64,
        &expected_hash,
        0,
        &mut out,
        MAX_OBJECT,
    )
    .unwrap_err();
    assert!(matches!(
        error,
        PhysicalDeflateError::Decode
            | PhysicalDeflateError::LogicalLength
            | PhysicalDeflateError::LogicalHash
    ));

    let compressed = hex_bytes("cb48cdc9c9d74dce2d482ee10200");
    let wrong_hash = [0u8; 32];
    assert_eq!(
        authenticated_range(
            &compressed,
            logical.len() as u64,
            &wrong_hash,
            0,
            &mut out,
            MAX_OBJECT,
        ),
        Err(PhysicalDeflateError::LogicalHash)
    );
}

#[test]
fn mode0_range_and_work_limits_are_explicit() {
    let compressed = hex_bytes("cb48cdc9c9d74dce2d482ee10200");
    let logical = b"hello-cmpct\n";
    let expected_hash: [u8; 32] = Sha256::digest(logical).into();

    let mut out = [0u8; 2];
    assert_eq!(
        authenticated_range(
            &compressed,
            logical.len() as u64,
            &expected_hash,
            compressed.len() as u64 - 1,
            &mut out,
            MAX_OBJECT,
        ),
        Err(PhysicalDeflateError::Range)
    );
    assert_eq!(
        authenticated_range(
            &compressed,
            logical.len() as u64,
            &expected_hash,
            0,
            &mut out,
            8,
        ),
        Err(PhysicalDeflateError::ResourceLimit)
    );
}

fn hex_bytes(value: &str) -> Vec<u8> {
    assert_eq!(value.len() % 2, 0);
    (0..value.len())
        .step_by(2)
        .map(|index| u8::from_str_radix(&value[index..index + 2], 16).unwrap())
        .collect()
}
