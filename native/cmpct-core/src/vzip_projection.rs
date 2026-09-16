//! Bounded virtual-ZIP logical-range projection over authenticated stored blobs.
//!
//! This module deliberately contains no `Archive` implementation. Keeping the pure projection executor
//! separate lets the native integration tests compile and exercise the exact production projection source
//! without pretending their test crate owns the archive core's private `Archive`/`Storage` types.

use crate::vzip::{VirtualZipError, VirtualZipRecipe};
use sha2::{Digest, Sha256};

#[derive(Debug, PartialEq, Eq)]
pub enum VirtualZipDispatchError<E> {
    Plan(VirtualZipError),
    Blob(E),
    InvalidProjection,
    LogicalHash,
}

impl<E> From<VirtualZipError> for VirtualZipDispatchError<E> {
    fn from(value: VirtualZipError) -> Self {
        Self::Plan(value)
    }
}

/// Execute one bounded virtual-ZIP range through an authenticated blob-range reader.
///
/// `read_blob_range` must preserve the archive core's normal physical framing and codec-integrity
/// checks. The executor never reads unrelated recipe segments: each callback corresponds to exactly
/// one slice emitted by `VirtualZipRecipe::plan_range`.
pub fn execute_range<E, F>(
    recipe: &VirtualZipRecipe,
    start: u64,
    out: &mut [u8],
    mut read_blob_range: F,
) -> Result<(), VirtualZipDispatchError<E>>
where
    F: FnMut(usize, u64, &mut [u8]) -> Result<(), E>,
{
    let length =
        u64::try_from(out.len()).map_err(|_| VirtualZipDispatchError::InvalidProjection)?;
    let segments = recipe.plan_range(start, length)?;
    if out.is_empty() {
        return Ok(());
    }

    let mut covered = 0usize;
    let mut expected_output_offset = 0usize;
    for segment in segments {
        let output_offset = usize::try_from(segment.output_offset)
            .map_err(|_| VirtualZipDispatchError::InvalidProjection)?;
        let segment_len = usize::try_from(segment.length)
            .map_err(|_| VirtualZipDispatchError::InvalidProjection)?;
        let output_end = output_offset
            .checked_add(segment_len)
            .ok_or(VirtualZipDispatchError::InvalidProjection)?;
        if output_offset != expected_output_offset || output_end > out.len() || segment_len == 0 {
            return Err(VirtualZipDispatchError::InvalidProjection);
        }

        // Requiring contiguous output coverage turns a malformed/buggy projection into a hard failure
        // instead of leaving caller-visible bytes uninitialized or silently duplicated.
        read_blob_range(
            segment.blob_index,
            segment.blob_offset,
            &mut out[output_offset..output_end],
        )
        .map_err(VirtualZipDispatchError::Blob)?;
        covered = covered
            .checked_add(segment_len)
            .ok_or(VirtualZipDispatchError::InvalidProjection)?;
        expected_output_offset = output_end;
    }
    if covered != out.len() || expected_output_offset != out.len() {
        return Err(VirtualZipDispatchError::InvalidProjection);
    }

    // Partial reads retain touched-blob integrity semantics. A complete logical read additionally
    // authenticates the reconstructed nested ZIP against the recipe identity frozen in the index.
    let end = start
        .checked_add(length)
        .ok_or(VirtualZipDispatchError::InvalidProjection)?;
    if start == 0
        && end == recipe.logical_size
        && Sha256::digest(&*out).as_slice() != recipe.logical_sha256
    {
        return Err(VirtualZipDispatchError::LogicalHash);
    }
    Ok(())
}
