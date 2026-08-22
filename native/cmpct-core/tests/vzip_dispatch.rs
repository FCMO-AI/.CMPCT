#[allow(dead_code)]
#[path = "../src/vzip.rs"]
mod vzip;
#[path = "../src/vzip_projection.rs"]
mod vzip_projection;

use sha2::{Digest, Sha256};
use vzip::{StoredPayload, VirtualZipRecipe};
use vzip_projection::{execute_range, VirtualZipDispatchError};

fn fixture() -> (VirtualZipRecipe, Vec<Vec<u8>>, Vec<u8>) {
    let skeleton = b"HEADTAIL".to_vec();
    let payload = b"payload".to_vec();
    let logical = b"HEADpayloadTAIL".to_vec();
    let mut hash = [0u8; 32];
    hash.copy_from_slice(Sha256::digest(&logical).as_slice());
    (
        VirtualZipRecipe {
            skeleton_blob: 0,
            literal_lengths: vec![4, 4],
            payloads: vec![StoredPayload {
                blob_index: 1,
                logical_len: payload.len() as u64,
            }],
            logical_sha256: hash,
            logical_size: logical.len() as u64,
            logical_crc32: 0,
        },
        vec![skeleton, payload],
        logical,
    )
}

#[test]
fn executes_only_intersecting_blob_slices() {
    let (recipe, blobs, logical) = fixture();
    let mut calls = Vec::new();
    let mut out = vec![0u8; 9];
    execute_range(&recipe, 2, &mut out, |index, offset, dst| {
        calls.push((index, offset, dst.len()));
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();

    assert_eq!(out, logical[2..11]);
    assert_eq!(calls, vec![(0, 2, 2), (1, 0, 7)]);
}

#[test]
fn trailing_range_does_not_touch_payload_blob() {
    let (recipe, blobs, logical) = fixture();
    let mut calls = Vec::new();
    let mut out = vec![0u8; 4];
    execute_range(&recipe, 11, &mut out, |index, offset, dst| {
        calls.push((index, offset, dst.len()));
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();

    assert_eq!(out, logical[11..15]);
    assert_eq!(calls, vec![(0, 4, 4)]);
}

#[test]
fn complete_read_enforces_recipe_logical_identity() {
    let (recipe, blobs, logical) = fixture();
    let mut out = vec![0u8; logical.len()];
    execute_range(&recipe, 0, &mut out, |index, offset, dst| {
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();
    assert_eq!(out, logical);

    let mut corrupt = blobs.clone();
    corrupt[1][0] ^= 0x01;
    let mut out = vec![0u8; logical.len()];
    let error = execute_range(&recipe, 0, &mut out, |index, offset, dst| {
        let start = offset as usize;
        dst.copy_from_slice(&corrupt[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap_err();
    assert_eq!(error, VirtualZipDispatchError::LogicalHash);
}

#[test]
fn blob_reader_failure_is_propagated_without_touching_later_segments() {
    let (recipe, _blobs, _logical) = fixture();
    let mut calls = 0usize;
    let mut out = vec![0u8; 9];
    let error = execute_range(&recipe, 2, &mut out, |_index, _offset, _dst| {
        calls += 1;
        Err::<(), _>("corrupt touched blob")
    })
    .unwrap_err();

    assert_eq!(calls, 1);
    assert_eq!(error, VirtualZipDispatchError::Blob("corrupt touched blob"));
}

// Footnote: this integration test includes the exact production projection source. Archive-wide verification
// remains compiled through the library crate, where its private `Archive`/`Storage` types actually exist.
