#[path = "../src/vzip.rs"]
mod vzip;
#[path = "../src/vzip_dispatch.rs"]
mod vzip_dispatch;

use sha2::{Digest, Sha256};
use vzip::{ProjectionSource, StoredPayload, VirtualZipRecipe};
use vzip_dispatch::{execute_range, VirtualZipDispatchError};

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
                source: ProjectionSource::LogicalBlob,
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
fn executes_only_intersecting_source_slices() {
    let (recipe, blobs, logical) = fixture();
    let mut calls = Vec::new();
    let mut out = vec![0u8; 9];
    execute_range(&recipe, 2, &mut out, |source, index, offset, dst| {
        calls.push((source, index, offset, dst.len()));
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();

    assert_eq!(out, logical[2..11]);
    assert_eq!(
        calls,
        vec![
            (ProjectionSource::LogicalBlob, 0, 2, 2),
            (ProjectionSource::LogicalBlob, 1, 0, 7),
        ]
    );
}

#[test]
fn trailing_range_does_not_touch_payload_source() {
    let (recipe, blobs, logical) = fixture();
    let mut calls = Vec::new();
    let mut out = vec![0u8; 4];
    execute_range(&recipe, 11, &mut out, |source, index, offset, dst| {
        calls.push((source, index, offset, dst.len()));
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();

    assert_eq!(out, logical[11..15]);
    assert_eq!(calls, vec![(ProjectionSource::LogicalBlob, 0, 4, 4)]);
}

#[test]
fn typed_source_and_expected_length_are_preserved_for_deflate_payloads() {
    let (mut recipe, blobs, _logical) = fixture();
    recipe.payloads[0].source = ProjectionSource::PhysicalDeflate { expected_len: 7 };
    let mut physical_calls = Vec::new();
    let mut out = vec![0u8; 7];
    execute_range(&recipe, 4, &mut out, |source, index, offset, dst| {
        physical_calls.push((source, index, offset, dst.len()));
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();
    assert_eq!(
        physical_calls[0].0,
        ProjectionSource::PhysicalDeflate { expected_len: 7 }
    );

    recipe.payloads[0].source = ProjectionSource::RegeneratedDeflate {
        level: 6,
        expected_len: 7,
    };
    let mut regenerated_calls = Vec::new();
    execute_range(&recipe, 4, &mut out, |source, index, offset, dst| {
        regenerated_calls.push((source, index, offset, dst.len()));
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();
    assert_eq!(
        regenerated_calls[0].0,
        ProjectionSource::RegeneratedDeflate {
            level: 6,
            expected_len: 7,
        }
    );
}

#[test]
fn complete_read_enforces_recipe_logical_identity() {
    let (recipe, blobs, logical) = fixture();
    let mut out = vec![0u8; logical.len()];
    execute_range(&recipe, 0, &mut out, |_source, index, offset, dst| {
        let start = offset as usize;
        dst.copy_from_slice(&blobs[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap();
    assert_eq!(out, logical);

    let mut corrupt = blobs.clone();
    corrupt[1][0] ^= 0x01;
    let mut out = vec![0u8; logical.len()];
    let error = execute_range(&recipe, 0, &mut out, |_source, index, offset, dst| {
        let start = offset as usize;
        dst.copy_from_slice(&corrupt[index][start..start + dst.len()]);
        Ok::<(), ()>(())
    })
    .unwrap_err();
    assert_eq!(error, VirtualZipDispatchError::LogicalHash);
}

#[test]
fn source_reader_failure_is_propagated_without_touching_later_segments() {
    let (recipe, _blobs, _logical) = fixture();
    let mut calls = 0usize;
    let mut out = vec![0u8; 9];
    let error = execute_range(&recipe, 2, &mut out, |_source, _index, _offset, _dst| {
        calls += 1;
        Err::<(), _>("corrupt touched source")
    })
    .unwrap_err();

    assert_eq!(calls, 1);
    assert_eq!(error, VirtualZipDispatchError::Source("corrupt touched source"));
}
