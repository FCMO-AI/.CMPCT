//! Execution layer for revision-24 virtual-ZIP range projections.
//!
//! The recipe planner decides which typed source slices intersect a request. This layer performs
//! exactly those reads through a caller-supplied authenticated source callback and verifies the
//! recipe's logical SHA-256 when the caller asks for the complete virtual member. Keeping physical
//! archive I/O behind the callback lets the core select logical-blob, physical-Deflate, or regenerated
//! Deflate semantics without duplicating recipe traversal in every platform binding.

use crate::vzip::{ProjectionSource, VirtualZipError, VirtualZipRecipe};
use sha2::{Digest, Sha256};

#[derive(Debug, PartialEq, Eq)]
pub enum VirtualZipDispatchError<E> {
    Plan(VirtualZipError),
    Source(E),
    InvalidProjection,
    LogicalHash,
}

impl<E> From<VirtualZipError> for VirtualZipDispatchError<E> {
    fn from(value: VirtualZipError) -> Self {
        Self::Plan(value)
    }
}

/// Execute one bounded virtual-ZIP range through an authenticated typed-source reader.
///
/// `read_source_range` receives the explicit source kind selected by the recipe planner. The archive
/// core is responsible for mapping that source to its integrity-preserving primitive:
///
/// - `LogicalBlob` -> normal decoded/authenticated blob range;
/// - `PhysicalDeflate` -> authenticated exact physical codec-4 RFC-1951 bytes;
/// - `RegeneratedDeflate` -> authenticated logical content followed by exact zlib-compatible
///   regeneration at the recorded level.
///
/// Footnote: this callback boundary is intentionally more explicit than overloading blob offsets with
/// sentinel bits. The format already distinguishes the semantics; the native API should do the same.
pub fn execute_range<E, F>(
    recipe: &VirtualZipRecipe,
    start: u64,
    out: &mut [u8],
    mut read_source_range: F,
) -> Result<(), VirtualZipDispatchError<E>>
where
    F: FnMut(ProjectionSource, usize, u64, &mut [u8]) -> Result<(), E>,
{
    let length = u64::try_from(out.len()).map_err(|_| VirtualZipDispatchError::InvalidProjection)?;
    let segments = recipe.plan_range(start, length)?;
    if out.is_empty() {
        return Ok(());
    }

    let mut covered = 0usize;
    let mut expected_output_offset = 0usize;
    for segment in segments {
        let output_offset = usize::try_from(segment.output_offset)
            .map_err(|_| VirtualZipDispatchError::InvalidProjection)?;
        let segment_len =
            usize::try_from(segment.length).map_err(|_| VirtualZipDispatchError::InvalidProjection)?;
        let output_end = output_offset
            .checked_add(segment_len)
            .ok_or(VirtualZipDispatchError::InvalidProjection)?;
        if output_offset != expected_output_offset || output_end > out.len() || segment_len == 0 {
            return Err(VirtualZipDispatchError::InvalidProjection);
        }

        // Footnote: requiring contiguous output coverage turns a malformed/buggy projection into a
        // hard failure instead of leaving caller-visible bytes uninitialized or silently duplicated.
        read_source_range(
            segment.source,
            segment.blob_index,
            segment.blob_offset,
            &mut out[output_offset..output_end],
        )
        .map_err(VirtualZipDispatchError::Source)?;
        covered = covered
            .checked_add(segment_len)
            .ok_or(VirtualZipDispatchError::InvalidProjection)?;
        expected_output_offset = output_end;
    }
    if covered != out.len() || expected_output_offset != out.len() {
        return Err(VirtualZipDispatchError::InvalidProjection);
    }

    // Partial reads retain the integrity semantics of each touched source. A complete logical read
    // additionally authenticates the reconstructed nested ZIP against the recipe identity frozen in
    // the authenticated index, catching any source-level bug that still produced the expected length.
    let end = start
        .checked_add(length)
        .ok_or(VirtualZipDispatchError::InvalidProjection)?;
    if start == 0 && end == recipe.logical_size {
        if Sha256::digest(&*out).as_slice() != recipe.logical_sha256 {
            return Err(VirtualZipDispatchError::LogicalHash);
        }
    }
    Ok(())
}
