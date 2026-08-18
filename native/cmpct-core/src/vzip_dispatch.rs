//! Execution layer for revision-24 virtual-ZIP range projections and complete archive verification.
//!
//! The recipe planner decides which logical blob slices intersect a request. This layer performs
//! exactly those reads through a caller-supplied authenticated blob-range callback and verifies the
//! recipe's logical SHA-256 when the caller asks for the complete virtual member. Keeping physical
//! blob I/O behind the callback lets archive dispatch reuse the existing framing/codec integrity path.

use crate::vzip::{VirtualZipError, VirtualZipRecipe};
use crate::{Archive, CmpctError, Storage};
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

        // Footnote: requiring contiguous output coverage turns a malformed/buggy projection into a
        // hard failure instead of leaving caller-visible bytes uninitialized or silently duplicated.
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

const VERIFY_CHUNK_BYTES: usize = 8 * 1024 * 1024;

impl Archive {
    /// Stream every regular revision-24 member and authenticate its complete logical identity.
    ///
    /// This is deliberately stronger than treating a successful range read as verification. Direct RAW range
    /// reads are intentionally local and therefore do not hash unseen payload bytes; complete verification must
    /// hash the entire logical stream against the authenticated index/recipe identity. Chunking the verifier also
    /// removes the old portable wrapper's 256 MiB materialization ceiling for large RAW/chunked/sparse members.
    pub fn verify_complete(&self) -> Result<usize, CmpctError> {
        let mut verified = 0usize;
        for (entry_index, entry) in self.entries.iter().enumerate() {
            if entry.kind != 0 {
                continue;
            }
            let expected = match (&entry.storage, entry.logical_hash) {
                (_, Some(hash)) => hash,
                (Storage::VirtualZip(recipe), None) => recipe.logical_sha256,
                // A regular member without any authenticated logical identity cannot satisfy a strong verify
                // contract. Failing closed is preferable to returning success from touched-byte checks only.
                _ => {
                    return Err(CmpctError::Schema(format!(
                        "regular member {} is missing complete logical SHA-256",
                        entry.path
                    )))
                }
            };

            let mut digest = Sha256::new();
            let mut offset = 0u64;
            let mut buffer = vec![0u8; VERIFY_CHUNK_BYTES.min(
                usize::try_from(entry.size.max(1)).unwrap_or(VERIFY_CHUNK_BYTES),
            )];
            while offset < entry.size {
                let remaining = entry.size - offset;
                let take = usize::try_from(remaining.min(buffer.len() as u64))
                    .map_err(|_| CmpctError::MemberLimit)?;
                self.read_range(entry_index, offset, &mut buffer[..take])?;
                digest.update(&buffer[..take]);
                offset = offset
                    .checked_add(take as u64)
                    .ok_or(CmpctError::MemberLimit)?;
            }
            let got: [u8; 32] = digest.finalize().into();
            if got != expected {
                return Err(CmpctError::MemberHash);
            }
            verified = verified
                .checked_add(1)
                .ok_or(CmpctError::MemberLimit)?;
        }
        Ok(verified)
    }
}
