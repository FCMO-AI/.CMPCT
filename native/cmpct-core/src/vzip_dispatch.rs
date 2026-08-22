//! Execution layer for revision-24 virtual-ZIP archive dispatch and complete verification.
//!
//! Pure logical-range projection lives in `vzip_projection.rs`; this module binds that executor to the
//! archive core's authenticated storage path and owns complete-member verification. The split keeps one
//! production implementation of range planning while allowing integration tests to compile that pure layer
//! without importing private `Archive`/`Storage` internals into the test crate root.

#[path = "vzip_projection.rs"]
mod projection;
pub use projection::{execute_range, VirtualZipDispatchError};

use crate::{Archive, CmpctError, Storage};
use sha2::{Digest, Sha256};

const VERIFY_CHUNK_BYTES: usize = 8 * 1024 * 1024;

impl Archive {
    /// Resolve the complete identity that revision-24 actually carries for one regular member.
    ///
    /// Newer r24 representations may carry a member-level logical SHA-256 in the authenticated index, and
    /// virtual ZIP carries one in its recipe. Historical direct members predate that field: for those exact
    /// one-blob members the physical CMA4 header SHA-256 is the format's complete decoded-blob integrity value.
    /// We may use it only when the direct blob spans the whole logical member; composites without a logical
    /// identity still fail closed instead of inventing a checksum from partial storage metadata.
    fn complete_member_identity(&self, entry_index: usize) -> Result<[u8; 32], CmpctError> {
        let entry = self.entries.get(entry_index).ok_or(CmpctError::Range)?;
        if let Some(hash) = entry.logical_hash {
            return Ok(hash);
        }
        match &entry.storage {
            Storage::VirtualZip(recipe) => Ok(recipe.logical_sha256),
            Storage::Direct(index) => {
                let blob = self.blobs.get(*index).ok_or_else(|| {
                    CmpctError::Schema("direct member references missing blob".into())
                })?;
                if blob.usize != entry.size {
                    return Err(CmpctError::BlobHeader);
                }
                let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
                let (_payload_pos, hash) = self.checked_blob_layout(blob, &mut file)?;
                Ok(hash)
            }
            // Chunked, sparse and packed members can compose or slice several blobs. Their physical
            // blob hashes therefore cannot stand in for one logical member hash; accepting them here would turn
            // a compatibility fix into a false strong-verification claim.
            _ => Err(CmpctError::Schema(format!(
                "regular member {} is missing complete logical SHA-256",
                entry.path
            ))),
        }
    }

    /// Stream every regular revision-24 member and authenticate its complete logical identity.
    ///
    /// This is deliberately stronger than treating a successful range read as verification. Direct RAW range
    /// reads are intentionally local and therefore do not hash unseen payload bytes; complete verification must
    /// hash the entire logical stream against the member/recipe identity, or the historical complete direct-blob
    /// identity when that is the only checksum the r24 grammar contains. Chunking the verifier also removes the
    /// old portable wrapper's 256 MiB materialization ceiling for large RAW/chunked/sparse members.
    pub fn verify_complete(&self) -> Result<usize, CmpctError> {
        let mut verified = 0usize;
        for (entry_index, entry) in self.entries.iter().enumerate() {
            if entry.kind != 0 {
                continue;
            }
            let expected = self.complete_member_identity(entry_index)?;

            let mut digest = Sha256::new();
            let mut offset = 0u64;
            let mut buffer = vec![
                0u8;
                VERIFY_CHUNK_BYTES.min(
                    usize::try_from(entry.size.max(1)).unwrap_or(VERIFY_CHUNK_BYTES),
                )
            ];
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
            verified = verified.checked_add(1).ok_or(CmpctError::MemberLimit)?;
        }
        Ok(verified)
    }
}
