//! Execution layer for revision-24 virtual-ZIP archive dispatch and complete verification.
//!
//! Pure logical-range projection lives in `vzip_projection.rs`; this module binds that executor to the
//! archive core's authenticated storage path and owns complete-member verification. The split keeps one
//! production implementation of range planning while allowing integration tests to compile that pure layer
//! without importing private `Archive`/`Storage` internals into the test crate root.

// Packaging bridge: compile the package-owned codec ABI into the same shipping cdylib. These modules
// remain private Rust implementation details; the exported contract is `cmpct_codec.h`, not a new Rust
// API. Keep archive grammar and the read-only `cmpct.h` contract separate.
#[path = "codec_abi.rs"]
mod codec_abi;
#[path = "codec_decoder_abi.rs"]
mod codec_decoder_abi;

#[path = "vzip_projection.rs"]
mod projection;
pub use projection::{execute_range, VirtualZipDispatchError};

use crate::{
    Archive, CmpctError, Storage, CODEC_WAV_FLAC, MAX_DIRECT_DECODE_BYTES, MAX_INDEX_BYTES,
};
use sha2::{Digest, Sha256};
use std::io::{Read, Seek, SeekFrom};

const VERIFY_CHUNK_BYTES: usize = 8 * 1024 * 1024;

impl Archive {
    /// Resolve the complete identity revision-24 carries for one payload-bearing file or symlink.
    ///
    /// Newer r24 representations may carry a member-level logical SHA-256 in the authenticated index, and
    /// virtual ZIP carries one in its recipe. Historical direct members predate that field: for those exact
    /// one-blob members the physical CMA4 header SHA-256 is the format's complete decoded-blob integrity value.
    /// We may use it only when the direct blob spans the whole logical member; composites without a logical
    /// identity still fail closed instead of inventing a checksum from partial storage metadata.
    fn complete_member_identity_and_crc(
        &self,
        entry_index: usize,
    ) -> Result<([u8; 32], Option<u32>), CmpctError> {
        let entry = self.entries.get(entry_index).ok_or(CmpctError::Range)?;

        if let Storage::Direct(index) = &entry.storage {
            let blob = self.blobs.get(*index).ok_or_else(|| {
                CmpctError::Schema("direct member references missing blob".into())
            })?;
            if blob.usize != entry.size {
                return Err(CmpctError::BlobHeader);
            }
            // The physical hash and CRC belong to the same checked CMA4 header.
            // Re-reading CRC after authenticating the hash duplicated header I/O
            // and could observe a different header if the source changed between reads.
            let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
            let (_payload_pos, physical_hash, physical_crc) =
                self.checked_blob_layout_with_crc(blob, &mut file)?;
            if let Some(logical_hash) = entry.logical_hash {
                if physical_hash != logical_hash {
                    return Err(CmpctError::MemberHash);
                }
            }
            return Ok((
                entry.logical_hash.unwrap_or(physical_hash),
                Some(physical_crc),
            ));
        }

        if let Some(hash) = entry.logical_hash {
            return Ok((hash, None));
        }
        match &entry.storage {
            Storage::VirtualZip(recipe) => Ok((recipe.logical_sha256, None)),
            // Chunked, sparse and packed members can compose or slice several blobs. Their
            // physical blob hashes/CRCs cannot be the concatenated member's identity.
            _ => Err(CmpctError::Schema(format!(
                "regular member {} is missing complete logical SHA-256",
                entry.path
            ))),
        }
    }

    fn verify_direct_wav_flac(
        &self,
        entry_index: usize,
        blob_index: usize,
    ) -> Result<(), CmpctError> {
        let entry = self.entries.get(entry_index).ok_or(CmpctError::Range)?;
        let blob = self.blobs.get(blob_index).ok_or(CmpctError::BlobHeader)?;
        if blob.codec != CODEC_WAV_FLAC || blob.usize != entry.size {
            return Err(CmpctError::BlobHeader);
        }
        if blob.usize > MAX_DIRECT_DECODE_BYTES
            || blob.csize > MAX_DIRECT_DECODE_BYTES
            || u64::from(blob.meta_len) > MAX_DIRECT_DECODE_BYTES
        {
            return Err(CmpctError::MemberLimit);
        }
        let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
        let (pos, physical_sha, physical_crc) =
            self.checked_blob_layout_with_crc(blob, &mut file)?;
        if entry.logical_hash.is_some_and(|hash| hash != physical_sha) {
            return Err(CmpctError::MemberHash);
        }
        let meta_pos = pos
            .checked_sub(u64::from(blob.meta_len))
            .ok_or(CmpctError::BlobHeader)?;
        file.seek(SeekFrom::Start(meta_pos))?;
        let mut meta = vec![0u8; blob.meta_len as usize];
        file.read_exact(&mut meta)?;
        file.seek(SeekFrom::Start(pos))?;
        let (sha, crc) = crate::wavflac::digest_wav_flac_stream(
            (&mut *file).take(blob.csize),
            &meta,
            blob.usize,
            MAX_DIRECT_DECODE_BYTES,
        )?;
        if sha != physical_sha {
            return Err(CmpctError::MemberHash);
        }
        if crc != physical_crc {
            return Err(CmpctError::BlobHeader);
        }
        Ok(())
    }

    /// Refuse to certify a stale primary checkpoint as the latest archive generation.
    ///
    /// Native open/list/range currently address the primary r24 index only. The public
    /// Python Reader replays signed appended PUT/DELETE generations. Until native
    /// recovery has its own conformance court, a whole-archive SUCCESS must only
    /// cover a terminal checkpoint whose *decoded* index matches that primary.
    /// This reads the same held File, never a new pathname (the C handle can
    /// survive rename/rebinding), and bounds decompression by the r24 index cap.
    fn require_primary_generation_for_complete_verify(&self) -> Result<(), CmpctError> {
        use crate::{HEADER_SIZE, MAGIC};
        const FOOTER_SIZE: u64 = 68;
        const FOOTER_MAGIC: &[u8; 8] = b"CMPTF24\0";

        let mut file = self.file.lock().map_err(|_| CmpctError::Unsupported)?;
        let file_len = file.metadata()?.len();
        if file_len < FOOTER_SIZE {
            return Err(CmpctError::Unsupported);
        }
        file.seek(SeekFrom::Start(0))?;
        let mut header = [0u8; HEADER_SIZE];
        file.read_exact(&mut header)?;
        if &header[..8] != MAGIC {
            return Err(CmpctError::Unsupported);
        }
        let primary_uncompressed = u64::from_le_bytes(
            header[20..28]
                .try_into()
                .map_err(|_| CmpctError::Unsupported)?,
        );
        let primary_sha = &header[36..68];

        file.seek(SeekFrom::Start(file_len - FOOTER_SIZE))?;
        let mut footer = [0u8; FOOTER_SIZE as usize];
        file.read_exact(&mut footer)?;
        // 0 = complete checkpoint, 1 = delta; prev != 0 means this checkpoint
        // follows a signed history and may represent a different logical tree.
        if &footer[..8] != FOOTER_MAGIC
            || footer[8] != 0
            || footer[9] > 1
            || footer[10] != 0
            || footer[11] != 0
            || footer[28..36] != [0u8; 8]
            || &footer[36..68] != primary_sha
        {
            return Err(CmpctError::Unsupported);
        }
        let compressed_len = u64::from_le_bytes(
            footer[12..20]
                .try_into()
                .map_err(|_| CmpctError::Unsupported)?,
        );
        let uncompressed_len = u64::from_le_bytes(
            footer[20..28]
                .try_into()
                .map_err(|_| CmpctError::Unsupported)?,
        );
        if compressed_len > MAX_INDEX_BYTES
            || uncompressed_len > MAX_INDEX_BYTES
            || uncompressed_len != primary_uncompressed
            || self
                .data_end
                .checked_add(compressed_len)
                .and_then(|end| end.checked_add(FOOTER_SIZE))
                != Some(file_len)
        {
            return Err(CmpctError::Unsupported);
        }

        fn bounded_sha<R: Read>(mut source: R, limit: u64) -> Result<([u8; 32], u64), CmpctError> {
            let mut sha = Sha256::new();
            let mut count = 0u64;
            let mut chunk = [0u8; 64 * 1024];
            loop {
                let got = source.read(&mut chunk)?;
                if got == 0 {
                    break;
                }
                count = count
                    .checked_add(got as u64)
                    .ok_or(CmpctError::IndexLimit)?;
                if count > limit {
                    return Err(CmpctError::IndexLimit);
                }
                sha.update(&chunk[..got]);
            }
            Ok((sha.finalize().into(), count))
        }

        file.seek(SeekFrom::Start(self.data_end))?;
        let (tail_sha, tail_len) = match footer[9] {
            0 => bounded_sha((&mut *file).take(compressed_len), uncompressed_len)?,
            1 => {
                let decoder = zstd::stream::read::Decoder::new((&mut *file).take(compressed_len))?;
                bounded_sha(decoder, uncompressed_len)?
            }
            _ => return Err(CmpctError::Unsupported),
        };
        if tail_len != uncompressed_len || tail_sha.as_slice() != primary_sha {
            return Err(CmpctError::Unsupported);
        }
        Ok(())
    }

    /// Stream every regular file and symlink payload and authenticate its complete logical identity.
    ///
    /// This is deliberately stronger than treating a successful range read as verification. Direct RAW range
    /// reads are intentionally local and therefore do not hash unseen payload bytes; complete verification must
    /// hash the entire logical stream against the member/recipe identity, or the historical complete direct-blob
    /// identity when that is the only checksum the r24 grammar contains. Chunking the verifier also removes the
    /// old portable wrapper's 256 MiB materialization ceiling for large RAW/chunked/sparse members.
    pub fn verify_complete(&self) -> Result<usize, CmpctError> {
        self.require_primary_generation_for_complete_verify()?;
        let mut verified = 0usize;
        for (entry_index, entry) in self.entries.iter().enumerate() {
            // A symlink target is an archived payload too: skipping kind=2 silently certified
            // corrupt or contradictory targets as verified. Direct symlinks reuse this exact
            // bounded hash/read path; directories and hardlink aliases have no own payload.
            if entry.kind != 0 && entry.kind != 2 {
                continue;
            }
            if let Storage::Direct(idx) = &entry.storage {
                if self
                    .blobs
                    .get(*idx)
                    .is_some_and(|b| b.codec == CODEC_WAV_FLAC)
                {
                    self.verify_direct_wav_flac(entry_index, *idx)?;
                    verified = verified.checked_add(1).ok_or(CmpctError::MemberLimit)?;
                    continue;
                }
            }
            let (expected, physical_crc) = self.complete_member_identity_and_crc(entry_index)?;
            // Physical CMA4 CRC32 is a separately stored field, not superseded by SHA.
            // Only a direct member spans its own physical blob exactly: composite member
            // CRCs cannot be inferred from the concatenated logical stream.
            let mut digest = Sha256::new();
            let mut crc = physical_crc.map(|_| crc32fast::Hasher::new());
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
                if let Some(crc) = crc.as_mut() {
                    // Feed the same decoded bytes once: no second payload traversal.
                    crc.update(&buffer[..take]);
                }
                offset = offset
                    .checked_add(take as u64)
                    .ok_or(CmpctError::MemberLimit)?;
            }
            let got: [u8; 32] = digest.finalize().into();
            if got != expected {
                return Err(CmpctError::MemberHash);
            }
            if let (Some(expected_crc), Some(crc)) = (physical_crc, crc) {
                if crc.finalize() != expected_crc {
                    return Err(CmpctError::BlobHeader);
                }
            }
            verified = verified.checked_add(1).ok_or(CmpctError::MemberLimit)?;
        }
        Ok(verified)
    }
}
