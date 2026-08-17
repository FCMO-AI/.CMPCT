//! Memory-safe read-only CMPCT core.
//!
//! The native slice authenticates the latest committed revision-24 index, enumerates its logical tree,
//! and can read bounded byte ranges from direct RAW/Zstd/WAV-FLAC/Deflate/Zstd-dictionary members,
//! fixed/CDC chunk maps, sparse extents, micro-solid packs, and all three revision-24 virtual-ZIP
//! Deflate stream modes. The same core exposes explicit structural preflight, sequential stream handles,
//! and safe extraction so platform shells do not grow independent parsers.
//!
//! Footnote: revision 24 deliberately keeps the encoder and reader contracts separate. Native recovery
//! follows committed generation footers rather than replaying encoder heuristics. Virtual ZIP modes 0
//! and 2 have no universally required independent stream digest in the on-disk grammar, so selective
//! reads of those modes authenticate a complete bounded virtual member before returning a slice. This
//! trades some locality for exactness rather than returning an equivalent-but-byte-different ZIP.

mod deflate_physical;
mod deflate_regen;
mod msgpack_guard;
mod recovery;
mod vzip;
mod vzip_dispatch;
mod wavflac;

use flate2::read::DeflateDecoder;
use rmpv::Value;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::{HashMap, HashSet};
use std::ffi::CStr;
use std::fs::{self, File};
use std::io::{Cursor, Read, Seek, SeekFrom, Write};
use std::os::raw::{c_char, c_int};
use std::path::{Component, Path};
use std::ptr;
use std::sync::Mutex;
use thiserror::Error;

#[cfg(unix)]
use std::os::unix::fs::{symlink, PermissionsExt};
#[cfg(windows)]
use std::os::windows::fs::symlink_file;

const MAGIC: &[u8; 8] = b"CMPCT24\0";
const BLOB_MAGIC: &[u8; 4] = b"CMA4";
const VERSION: u16 = 24;
const HEADER_SIZE: usize = 68;
const BLOB_HEADER_SIZE: usize = 64;
const CODEC_RAW: u8 = 0;
const CODEC_ZSTD: u8 = 1;
const CODEC_WAV_FLAC: u8 = 2;
const CODEC_ZSTDDICT: u8 = 3;
const CODEC_DEFLATE: u8 = 4;
const STORAGE_BLOB: u64 = 0;
const STORAGE_CHUNKS: u64 = 1;
const STORAGE_VZIP: u64 = 2;
const STORAGE_SPARSE: u64 = 3;
const STORAGE_PACK: u64 = 4;
const STORAGE_CDC: u64 = 5;
const KIND_FILE: u8 = 0;
const KIND_DIR: u8 = 1;
const KIND_SYMLINK: u8 = 2;
const KIND_HARDLINK: u8 = 3;
const MAX_INDEX_BYTES: u64 = 256 * 1024 * 1024;
const MAX_BLOB_BYTES: u64 = 1024 * 1024 * 1024;
const MAX_DIRECT_DECODE_BYTES: u64 = 256 * 1024 * 1024;
const MAX_RANGE_OUTPUT_BYTES: u64 = 64 * 1024 * 1024;
const MAX_READ_WORK_BYTES: u64 = 512 * 1024 * 1024;
const MAX_FILES: usize = 4_000_000;
const MAX_BLOBS: usize = 4_000_000;
const MAX_RECIPES: usize = 1_000_000;
const MAX_PATH_BYTES: usize = 1024 * 1024;
const MAX_GENERATIONS: usize = 4096;
const MAX_MSGPACK_DEPTH: usize = 1024;
const MAX_MSGPACK_NODES: u64 = 16_000_000;
const STREAM_CHUNK_BYTES: usize = 8 * 1024 * 1024;
const MAX_EXTRACT_OUTPUT_BYTES: u64 = 64 * 1024 * 1024 * 1024;
const MAX_SYMLINK_TARGET_BYTES: u64 = 1024 * 1024;

#[derive(Debug, Error)]
pub enum CmpctError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("not a CMPCT revision-24 archive")]
    Magic,
    #[error("unsupported CMPCT revision {0}")]
    Revision(u16),
    #[error("index exceeds native handler resource limit")]
    IndexLimit,
    #[error("member exceeds native operation resource limit")]
    MemberLimit,
    #[error("archive is truncated")]
    Truncated,
    #[error("primary index decompressed to an unexpected length")]
    IndexLength,
    #[error("primary index SHA-256 mismatch")]
    IndexHash,
    #[error("invalid MessagePack index: {0}")]
    MessagePack(String),
    #[error("invalid index schema: {0}")]
    Schema(String),
    #[error("unsafe or ambiguous logical path: {0}")]
    Path(String),
    #[error("member representation is not implemented by the native read-only core")]
    Unsupported,
    #[error("requested member range is outside the logical file")]
    Range,
    #[error("physical blob header does not match the authenticated index")]
    BlobHeader,
    #[error("decoded member length does not match its authenticated declaration")]
    MemberLength,
    #[error("decoded member SHA-256 does not match its authenticated identity")]
    MemberHash,
    #[error("WAV-FLAC reconstruction failed: {0}")]
    WavFlac(#[from] wavflac::WavFlacError),
    #[error("committed-generation recovery failed: {0}")]
    Recovery(#[from] recovery::RecoveryError),
    #[error("safe extraction refused archive/destination semantics: {0}")]
    Extraction(String),
}

#[derive(Debug, Clone)]
struct Blob {
    offset: u64,
    usize: u64,
    csize: u64,
    codec: u8,
    meta_len: u32,
}

#[derive(Debug, Clone, Copy)]
struct ChunkRef {
    logical_len: u64,
    index: usize,
}

#[derive(Debug, Clone)]
struct SparseExtent {
    offset: u64,
    logical_len: u64,
    chunks: Vec<ChunkRef>,
}

#[derive(Debug, Clone)]
enum Storage {
    Unsupported,
    Direct(usize),
    Fixed(Vec<ChunkRef>),
    VirtualZip(vzip::VirtualZipRecipe),
    Sparse(Vec<SparseExtent>),
    Pack {
        index: usize,
        offset: u64,
        length: u64,
    },
    Cdc(Vec<ChunkRef>),
    Hardlink(String),
}

#[derive(Debug, Clone, Serialize)]
pub struct Entry {
    pub path: String,
    pub kind: u8,
    pub mode: u32,
    pub mtime_ns: i64,
    pub size: u64,
    #[serde(skip)]
    storage: Storage,
    #[serde(skip)]
    logical_hash: Option<[u8; 32]>,
    #[serde(skip)]
    pub link_target: Option<String>,
}

#[derive(Debug)]
pub struct Archive {
    revision: u16,
    entries: Vec<Entry>,
    blobs: Vec<Blob>,
    dict_blob: Option<usize>,
    data_base: u64,
    data_end: u64,
    file: Mutex<File>,
}

fn guard_index_messagepack(bytes: &[u8]) -> Result<(), CmpctError> {
    msgpack_guard::validate(
        bytes,
        msgpack_guard::GuardLimits {
            max_string_bytes: MAX_PATH_BYTES as u64,
            max_binary_bytes: MAX_INDEX_BYTES,
            max_array_items: MAX_FILES.max(MAX_BLOBS).max(MAX_RECIPES) as u64,
            max_map_items: MAX_FILES.max(MAX_BLOBS).max(MAX_RECIPES) as u64,
            max_depth: MAX_MSGPACK_DEPTH,
            max_nodes: MAX_MSGPACK_NODES,
        },
    )
    .map_err(|error| match error {
        msgpack_guard::GuardError::Limit => CmpctError::IndexLimit,
        _ => CmpctError::Schema(format!("MessagePack declaration guard: {error}")),
    })
}

impl Archive {
    /// Open the newest valid committed revision-24 generation.
    ///
    /// The tail/footer chain is authoritative when valid. If it is missing/corrupt, the primary index
    /// remains a compatibility fallback. This ordering also lets a valid committed tail recover from
    /// a damaged primary index without trusting uncommitted bytes after the last valid footer.
    pub fn open(path: &Path) -> Result<Self, CmpctError> {
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        if file_len < HEADER_SIZE as u64 {
            return Err(CmpctError::Truncated);
        }

        let mut header = [0u8; HEADER_SIZE];
        file.read_exact(&mut header)?;
        if &header[0..8] != MAGIC {
            return Err(CmpctError::Magic);
        }
        let revision = u16::from_le_bytes([header[8], header[9]]);
        if revision != VERSION {
            return Err(CmpctError::Revision(revision));
        }
        if header[10] != 0 || header[11] != 0 {
            return Err(CmpctError::Schema(
                "revision-24 header uses unsupported flags".into(),
            ));
        }

        let compressed_len = le_u64(&header[12..20]);
        let uncompressed_len = le_u64(&header[20..28]);
        let base_data_span = le_u64(&header[28..36]);
        if compressed_len > MAX_INDEX_BYTES || uncompressed_len > MAX_INDEX_BYTES {
            return Err(CmpctError::IndexLimit);
        }
        let data_base = (HEADER_SIZE as u64)
            .checked_add(compressed_len)
            .ok_or(CmpctError::IndexLimit)?;
        let base_data_end = data_base
            .checked_add(base_data_span)
            .ok_or(CmpctError::IndexLimit)?;
        if data_base > file_len || base_data_end > file_len {
            return Err(CmpctError::Truncated);
        }

        let recovered = recovery::latest_committed_index(
            &mut file,
            file_len,
            MAX_INDEX_BYTES,
            MAX_GENERATIONS,
        )?;

        let (index, data_end) = if let Some(recovered) = recovered {
            if recovered.committed_data_end < data_base || recovered.committed_data_end > file_len {
                return Err(CmpctError::Schema(
                    "committed generation data boundary is outside the archive".into(),
                ));
            }
            (recovered.index, recovered.committed_data_end)
        } else {
            file.seek(SeekFrom::Start(HEADER_SIZE as u64))?;
            let compressed_len_usize =
                usize::try_from(compressed_len).map_err(|_| CmpctError::IndexLimit)?;
            let mut compressed = vec![0u8; compressed_len_usize];
            file.read_exact(&mut compressed)?;
            let decoder = zstd::stream::read::Decoder::new(Cursor::new(compressed))?;
            let mut limited = decoder.take(uncompressed_len.saturating_add(1));
            let mut index_bytes = Vec::with_capacity(
                usize::try_from(uncompressed_len).map_err(|_| CmpctError::IndexLimit)?,
            );
            limited.read_to_end(&mut index_bytes)?;
            if index_bytes.len() as u64 != uncompressed_len {
                return Err(CmpctError::IndexLength);
            }
            if Sha256::digest(&index_bytes).as_slice() != &header[36..68] {
                return Err(CmpctError::IndexHash);
            }
            guard_index_messagepack(&index_bytes)?;
            let mut cursor = Cursor::new(index_bytes.as_slice());
            let index = rmpv::decode::read_value(&mut cursor)
                .map_err(|error| CmpctError::MessagePack(error.to_string()))?;
            if cursor.position() != index_bytes.len() as u64 {
                return Err(CmpctError::Schema(
                    "trailing bytes after root index object".into(),
                ));
            }
            (index, base_data_end)
        };

        let span = data_end
            .checked_sub(data_base)
            .ok_or_else(|| CmpctError::Schema("negative committed data span".into()))?;
        let blobs = parse_blobs(&index, span)?;
        validate_recipes(&index, &blobs)?;
        let dict_blob = parse_dictionary_blob(&index, &blobs)?;
        let entries = parse_entries(&index, &blobs)?;
        validate_fsmeta(&index, entries.len())?;
        validate_entry_tree(&entries)?;

        Ok(Self {
            revision,
            entries,
            blobs,
            dict_blob,
            data_base,
            data_end,
            file: Mutex::new(file),
        })
    }

    pub fn revision(&self) -> u16 {
        self.revision
    }

    pub fn entries(&self) -> &[Entry] {
        &self.entries
    }

    fn checked_blob_layout(
        &self,
        blob: &Blob,
        file: &mut File,
    ) -> Result<(u64, [u8; 32]), CmpctError> {
        let blob_pos = self
            .data_base
            .checked_add(blob.offset)
            .ok_or(CmpctError::BlobHeader)?;
        let payload_pos = blob_pos
            .checked_add(BLOB_HEADER_SIZE as u64)
            .and_then(|value| value.checked_add(blob.meta_len as u64))
            .ok_or(CmpctError::BlobHeader)?;
        let payload_end = payload_pos
            .checked_add(blob.csize)
            .ok_or(CmpctError::BlobHeader)?;
        if payload_end > self.data_end {
            return Err(CmpctError::BlobHeader);
        }

        file.seek(SeekFrom::Start(blob_pos))?;
        let mut header = [0u8; BLOB_HEADER_SIZE];
        file.read_exact(&mut header)?;
        let physical_codec = header[4];
        let physical_flags = header[5];
        let physical_reserved = u16::from_le_bytes([header[6], header[7]]);
        let physical_usize = le_u64(&header[8..16]);
        let physical_csize = le_u64(&header[16..24]);
        let physical_meta_len = le_u32(&header[24..28]);
        if &header[0..4] != BLOB_MAGIC
            || physical_codec != blob.codec
            || physical_flags != 0
            || physical_reserved != 0
            || physical_usize != blob.usize
            || physical_csize != blob.csize
            || physical_meta_len != blob.meta_len
        {
            return Err(CmpctError::BlobHeader);
        }
        let mut hash = [0u8; 32];
        hash.copy_from_slice(&header[32..64]);
        Ok((payload_pos, hash))
    }

    fn decode_zstd_blob(
        &self,
        blob: &Blob,
        file: &mut File,
        payload_pos: u64,
        expected_hash: &[u8; 32],
    ) -> Result<Vec<u8>, CmpctError> {
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let compressed_len = usize::try_from(blob.csize).map_err(|_| CmpctError::MemberLimit)?;
        let decoded_len = usize::try_from(blob.usize).map_err(|_| CmpctError::MemberLimit)?;
        file.seek(SeekFrom::Start(payload_pos))?;
        let mut compressed = vec![0u8; compressed_len];
        file.read_exact(&mut compressed)?;

        // Footnote: ordinary direct Zstd is not independently seekable in revision 24. Decode one
        // bounded object, authenticate its exact logical bytes, then return a caller-selected slice.
        let decoder = zstd::stream::read::Decoder::new(Cursor::new(compressed))?;
        let mut limited = decoder.take(blob.usize.saturating_add(1));
        let mut decoded = Vec::with_capacity(decoded_len);
        limited.read_to_end(&mut decoded)?;
        if decoded.len() != decoded_len {
            return Err(CmpctError::MemberLength);
        }
        if Sha256::digest(&decoded).as_slice() != expected_hash {
            return Err(CmpctError::MemberHash);
        }
        Ok(decoded)
    }

    fn decode_wav_flac_blob(
        &self,
        blob: &Blob,
        file: &mut File,
        payload_pos: u64,
        expected_hash: &[u8; 32],
    ) -> Result<Vec<u8>, CmpctError> {
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let meta_len = usize::try_from(blob.meta_len).map_err(|_| CmpctError::MemberLimit)?;
        let compressed_len = usize::try_from(blob.csize).map_err(|_| CmpctError::MemberLimit)?;
        let meta_pos = payload_pos
            .checked_sub(blob.meta_len as u64)
            .ok_or(CmpctError::BlobHeader)?;
        file.seek(SeekFrom::Start(meta_pos))?;
        let mut meta = vec![0u8; meta_len];
        file.read_exact(&mut meta)?;
        let mut compressed = vec![0u8; compressed_len];
        file.read_exact(&mut compressed)?;

        // Footnote: codec 2 needs archive-controlled reconstruction metadata and a FLAC stream.
        // Reconstruct the complete bounded WAV and authenticate it before exposing any range.
        let decoded =
            wavflac::decode_wav_flac(&compressed, &meta, blob.usize, MAX_DIRECT_DECODE_BYTES)?;
        if Sha256::digest(&decoded).as_slice() != expected_hash {
            return Err(CmpctError::MemberHash);
        }
        Ok(decoded)
    }

    fn load_dictionary(&self, file: &mut File) -> Result<Vec<u8>, CmpctError> {
        let index = self.dict_blob.ok_or_else(|| {
            CmpctError::Schema("codec 3 member has no authenticated dict_blob".into())
        })?;
        let blob = self
            .blobs
            .get(index)
            .ok_or_else(|| CmpctError::Schema("dictionary references missing blob".into()))?;
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let (payload_pos, expected_hash) = self.checked_blob_layout(blob, file)?;
        match blob.codec {
            CODEC_RAW => {
                if blob.csize != blob.usize {
                    return Err(CmpctError::BlobHeader);
                }
                let len = usize::try_from(blob.usize).map_err(|_| CmpctError::MemberLimit)?;
                file.seek(SeekFrom::Start(payload_pos))?;
                let mut dictionary = vec![0u8; len];
                file.read_exact(&mut dictionary)?;
                if Sha256::digest(&dictionary).as_slice() != expected_hash {
                    return Err(CmpctError::MemberHash);
                }
                Ok(dictionary)
            }
            CODEC_ZSTD => self.decode_zstd_blob(blob, file, payload_pos, &expected_hash),
            CODEC_DEFLATE => self.decode_deflate_blob(blob, file, payload_pos, &expected_hash),
            _ => Err(CmpctError::Unsupported),
        }
    }

    fn decode_zstd_dictionary_blob(
        &self,
        blob: &Blob,
        file: &mut File,
        payload_pos: u64,
        expected_hash: &[u8; 32],
    ) -> Result<Vec<u8>, CmpctError> {
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let compressed_len = usize::try_from(blob.csize).map_err(|_| CmpctError::MemberLimit)?;
        let decoded_len = usize::try_from(blob.usize).map_err(|_| CmpctError::MemberLimit)?;
        let dictionary = self.load_dictionary(file)?;
        file.seek(SeekFrom::Start(payload_pos))?;
        let mut compressed = vec![0u8; compressed_len];
        file.read_exact(&mut compressed)?;
        let decoder =
            zstd::stream::read::Decoder::with_dictionary(Cursor::new(compressed), &dictionary)?;
        let mut limited = decoder.take(blob.usize.saturating_add(1));
        let mut decoded = Vec::with_capacity(decoded_len);
        limited.read_to_end(&mut decoded)?;
        if decoded.len() != decoded_len {
            return Err(CmpctError::MemberLength);
        }
        if Sha256::digest(&decoded).as_slice() != expected_hash {
            return Err(CmpctError::MemberHash);
        }
        Ok(decoded)
    }

    fn decode_deflate_blob(
        &self,
        blob: &Blob,
        file: &mut File,
        payload_pos: u64,
        expected_hash: &[u8; 32],
    ) -> Result<Vec<u8>, CmpctError> {
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let compressed_len = usize::try_from(blob.csize).map_err(|_| CmpctError::MemberLimit)?;
        let decoded_len = usize::try_from(blob.usize).map_err(|_| CmpctError::MemberLimit)?;
        file.seek(SeekFrom::Start(payload_pos))?;
        let mut compressed = vec![0u8; compressed_len];
        file.read_exact(&mut compressed)?;
        let decoder = DeflateDecoder::new(Cursor::new(compressed));
        let mut limited = decoder.take(blob.usize.saturating_add(1));
        let mut decoded = Vec::with_capacity(decoded_len);
        limited.read_to_end(&mut decoded)?;
        if decoded.len() != decoded_len {
            return Err(CmpctError::MemberLength);
        }
        if Sha256::digest(&decoded).as_slice() != expected_hash {
            return Err(CmpctError::MemberHash);
        }
        Ok(decoded)
    }

    fn read_blob_complete_authenticated(
        &self,
        blob_index: usize,
        file: &mut File,
    ) -> Result<Vec<u8>, CmpctError> {
        let blob = self
            .blobs
            .get(blob_index)
            .ok_or_else(|| CmpctError::Schema("member references missing blob".into()))?;
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let (payload_pos, expected_hash) = self.checked_blob_layout(blob, file)?;
        match blob.codec {
            CODEC_RAW => {
                if blob.csize != blob.usize {
                    return Err(CmpctError::BlobHeader);
                }
                let len = usize::try_from(blob.usize).map_err(|_| CmpctError::MemberLimit)?;
                file.seek(SeekFrom::Start(payload_pos))?;
                let mut decoded = vec![0u8; len];
                file.read_exact(&mut decoded)?;
                if Sha256::digest(&decoded).as_slice() != expected_hash {
                    return Err(CmpctError::MemberHash);
                }
                Ok(decoded)
            }
            CODEC_ZSTD => self.decode_zstd_blob(blob, file, payload_pos, &expected_hash),
            CODEC_WAV_FLAC => self.decode_wav_flac_blob(blob, file, payload_pos, &expected_hash),
            CODEC_ZSTDDICT => {
                self.decode_zstd_dictionary_blob(blob, file, payload_pos, &expected_hash)
            }
            CODEC_DEFLATE => self.decode_deflate_blob(blob, file, payload_pos, &expected_hash),
            _ => Err(CmpctError::Unsupported),
        }
    }

    fn read_blob_range(
        &self,
        blob_index: usize,
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        let blob = self
            .blobs
            .get(blob_index)
            .ok_or_else(|| CmpctError::Schema("member references missing blob".into()))?;
        let end = start
            .checked_add(out.len() as u64)
            .ok_or(CmpctError::Range)?;
        if end > blob.usize {
            return Err(CmpctError::Range);
        }
        let (payload_pos, _expected_hash) = self.checked_blob_layout(blob, file)?;
        if blob.codec == CODEC_RAW {
            if blob.csize != blob.usize {
                return Err(CmpctError::BlobHeader);
            }
            let read_pos = payload_pos.checked_add(start).ok_or(CmpctError::Range)?;
            file.seek(SeekFrom::Start(read_pos))?;
            file.read_exact(out)?;
            return Ok(());
        }

        let decoded = self.read_blob_complete_authenticated(blob_index, file)?;
        let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
        let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
        out.copy_from_slice(&decoded[start..end]);
        Ok(())
    }

    fn exact_deflate_stream_hash(
        &self,
        blob: &Blob,
        file: &mut File,
        payload_pos: u64,
    ) -> Result<Option<[u8; 32]>, CmpctError> {
        if blob.meta_len == 0 {
            return Ok(None);
        }
        let meta_pos = payload_pos
            .checked_sub(blob.meta_len as u64)
            .ok_or(CmpctError::BlobHeader)?;
        let meta_len = usize::try_from(blob.meta_len).map_err(|_| CmpctError::MemberLimit)?;
        file.seek(SeekFrom::Start(meta_pos))?;
        let mut meta = vec![0u8; meta_len];
        file.read_exact(&mut meta)?;

        // Footnote: exact-Deflate metadata is archive-controlled MessagePack just like the primary
        // index and WAV metadata. Guard declarations before `rmpv` so an authenticated tiny metadata
        // field cannot declare an absurd container/bin length and force allocation before semantics.
        msgpack_guard::validate(
            &meta,
            msgpack_guard::GuardLimits {
                max_string_bytes: 1024,
                max_binary_bytes: MAX_INDEX_BYTES,
                max_array_items: 64,
                max_map_items: 64,
                max_depth: 32,
                max_nodes: 4096,
            },
        )
        .map_err(|error| match error {
            msgpack_guard::GuardError::Limit => CmpctError::MemberLimit,
            _ => CmpctError::Schema(format!("invalid Deflate codec metadata: {error}")),
        })?;

        let mut cursor = Cursor::new(meta.as_slice());
        let value = match rmpv::decode::read_value(&mut cursor) {
            Ok(value) if cursor.position() == meta.len() as u64 => value,
            _ => return Ok(None),
        };
        let Some(row) = value.as_array() else {
            return Ok(None);
        };
        let Some(Value::Binary(bytes)) = row.first() else {
            return Ok(None);
        };
        if bytes.len() != 32 {
            return Ok(None);
        }
        let mut hash = [0u8; 32];
        hash.copy_from_slice(bytes);
        Ok(Some(hash))
    }

    fn read_physical_deflate_range(
        &self,
        blob_index: usize,
        expected_stream_len: u64,
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        let blob = self.blobs.get(blob_index).ok_or_else(|| {
            CmpctError::Schema("virtual ZIP references missing Deflate blob".into())
        })?;
        if blob.codec != CODEC_DEFLATE || blob.csize != expected_stream_len {
            return Err(CmpctError::Schema(
                "virtual-ZIP mode-0 stream length/codec disagrees with physical blob".into(),
            ));
        }
        if blob.usize > MAX_DIRECT_DECODE_BYTES || blob.csize > MAX_DIRECT_DECODE_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let (payload_pos, expected_logical_hash) = self.checked_blob_layout(blob, file)?;
        let compressed_len = usize::try_from(blob.csize).map_err(|_| CmpctError::MemberLimit)?;
        file.seek(SeekFrom::Start(payload_pos))?;
        let mut compressed = vec![0u8; compressed_len];
        file.read_exact(&mut compressed)?;

        // Some revision-24 encoders record the exact RFC-1951 stream SHA-256 as codec metadata. Use
        // that stronger proof when present, but do not require it: the independent canonical mode-0
        // oracle intentionally has meta_len=0. The surrounding virtual-member SHA authenticates exact
        // stream bytes for complete reads and for the full-verify selective path below.
        if let Some(exact_hash) = self.exact_deflate_stream_hash(blob, file, payload_pos)? {
            if Sha256::digest(&compressed).as_slice() != exact_hash {
                return Err(CmpctError::MemberHash);
            }
        }

        deflate_physical::authenticated_range(
            &compressed,
            blob.usize,
            &expected_logical_hash,
            start,
            out,
            MAX_DIRECT_DECODE_BYTES,
        )
        .map_err(|error| match error {
            deflate_physical::PhysicalDeflateError::ResourceLimit => CmpctError::MemberLimit,
            deflate_physical::PhysicalDeflateError::Range => CmpctError::Range,
            deflate_physical::PhysicalDeflateError::Decode
            | deflate_physical::PhysicalDeflateError::LogicalLength
            | deflate_physical::PhysicalDeflateError::LogicalHash => CmpctError::MemberHash,
        })
    }

    fn read_regenerated_deflate_range(
        &self,
        blob_index: usize,
        level: u8,
        expected_stream_len: u64,
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        let raw = self.read_blob_complete_authenticated(blob_index, file)?;
        deflate_regen::exact_range(
            &raw,
            level,
            expected_stream_len,
            start,
            out,
            MAX_DIRECT_DECODE_BYTES,
        )
        .map_err(|error| match error {
            deflate_regen::DeflateRegenError::Unavailable => CmpctError::Unsupported,
            deflate_regen::DeflateRegenError::ResourceLimit => CmpctError::MemberLimit,
            deflate_regen::DeflateRegenError::Range => CmpctError::Range,
            deflate_regen::DeflateRegenError::Level
            | deflate_regen::DeflateRegenError::Encode
            | deflate_regen::DeflateRegenError::StreamLength => {
                CmpctError::Schema(format!("virtual-ZIP mode-2 regeneration failed: {error}"))
            }
        })
    }

    fn read_chunked_range(
        &self,
        chunks: &[ChunkRef],
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        let request_end = start
            .checked_add(out.len() as u64)
            .ok_or(CmpctError::Range)?;
        let mut logical_pos = 0u64;
        let mut copied = 0usize;
        for chunk in chunks {
            let chunk_end = logical_pos
                .checked_add(chunk.logical_len)
                .ok_or_else(|| CmpctError::Schema("chunk map overflows logical offsets".into()))?;
            if chunk_end > start && logical_pos < request_end {
                let overlap_start = start.max(logical_pos);
                let overlap_end = request_end.min(chunk_end);
                let local_start = overlap_start - logical_pos;
                let length =
                    usize::try_from(overlap_end - overlap_start).map_err(|_| CmpctError::Range)?;
                let dst_start =
                    usize::try_from(overlap_start - start).map_err(|_| CmpctError::Range)?;
                let dst_end = dst_start.checked_add(length).ok_or(CmpctError::Range)?;
                self.read_blob_range(chunk.index, local_start, &mut out[dst_start..dst_end], file)?;
                copied = copied.checked_add(length).ok_or(CmpctError::Range)?;
            }
            logical_pos = chunk_end;
            if logical_pos >= request_end {
                break;
            }
        }
        if copied != out.len() {
            return Err(CmpctError::Schema(
                "chunk map did not cover requested logical range".into(),
            ));
        }
        Ok(())
    }

    fn read_sparse_range(
        &self,
        extents: &[SparseExtent],
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        let request_end = start
            .checked_add(out.len() as u64)
            .ok_or(CmpctError::Range)?;
        out.fill(0);
        for extent in extents {
            let extent_end = extent
                .offset
                .checked_add(extent.logical_len)
                .ok_or_else(|| {
                    CmpctError::Schema("sparse extent overflows logical offsets".into())
                })?;
            if extent_end <= start {
                continue;
            }
            if extent.offset >= request_end {
                break;
            }
            let overlap_start = start.max(extent.offset);
            let overlap_end = request_end.min(extent_end);
            let local_start = overlap_start - extent.offset;
            let length =
                usize::try_from(overlap_end - overlap_start).map_err(|_| CmpctError::Range)?;
            let dst_start =
                usize::try_from(overlap_start - start).map_err(|_| CmpctError::Range)?;
            let dst_end = dst_start.checked_add(length).ok_or(CmpctError::Range)?;
            self.read_chunked_range(
                &extent.chunks,
                local_start,
                &mut out[dst_start..dst_end],
                file,
            )?;
        }
        Ok(())
    }

    fn execute_virtual_zip_projection(
        &self,
        recipe: &vzip::VirtualZipRecipe,
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        vzip_dispatch::execute_range(
            recipe,
            start,
            out,
            |source, blob_index, blob_offset, target| match source {
                vzip::ProjectionSource::LogicalBlob => {
                    self.read_blob_range(blob_index, blob_offset, target, file)
                }
                vzip::ProjectionSource::PhysicalDeflate { expected_len } => self
                    .read_physical_deflate_range(
                        blob_index,
                        expected_len,
                        blob_offset,
                        target,
                        file,
                    ),
                vzip::ProjectionSource::RegeneratedDeflate {
                    level,
                    expected_len,
                } => self.read_regenerated_deflate_range(
                    blob_index,
                    level,
                    expected_len,
                    blob_offset,
                    target,
                    file,
                ),
            },
        )
        .map_err(|error| match error {
            vzip_dispatch::VirtualZipDispatchError::Plan(vzip::VirtualZipError::Range) => {
                CmpctError::Range
            }
            vzip_dispatch::VirtualZipDispatchError::Plan(
                vzip::VirtualZipError::UnsupportedPayload,
            ) => CmpctError::Unsupported,
            vzip_dispatch::VirtualZipDispatchError::Plan(vzip::VirtualZipError::Schema(
                message,
            )) => CmpctError::Schema(message),
            vzip_dispatch::VirtualZipDispatchError::Source(error) => error,
            vzip_dispatch::VirtualZipDispatchError::InvalidProjection => CmpctError::Schema(
                "virtual-ZIP projection did not cover the requested range exactly".into(),
            ),
            vzip_dispatch::VirtualZipDispatchError::LogicalHash => CmpctError::MemberHash,
        })
    }

    fn read_virtual_zip_range(
        &self,
        recipe: &vzip::VirtualZipRecipe,
        start: u64,
        out: &mut [u8],
        file: &mut File,
    ) -> Result<(), CmpctError> {
        let request_end = start
            .checked_add(out.len() as u64)
            .ok_or(CmpctError::Range)?;
        let needs_complete_identity = recipe.payloads.iter().any(|payload| {
            matches!(
                payload.source,
                vzip::ProjectionSource::PhysicalDeflate { .. }
                    | vzip::ProjectionSource::RegeneratedDeflate { .. }
            )
        });

        if needs_complete_identity && (start != 0 || request_end != recipe.logical_size) {
            if recipe.logical_size > MAX_DIRECT_DECODE_BYTES {
                return Err(CmpctError::MemberLimit);
            }
            let whole_len =
                usize::try_from(recipe.logical_size).map_err(|_| CmpctError::MemberLimit)?;
            let mut whole = vec![0u8; whole_len];
            self.execute_virtual_zip_projection(recipe, 0, &mut whole, file)?;
            let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
            let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
            out.copy_from_slice(&whole[start..end]);
            return Ok(());
        }

        self.execute_virtual_zip_projection(recipe, start, out, file)
    }

    fn blob_work(
        &self,
        blob_index: usize,
        requested: u64,
        full_auth: bool,
    ) -> Result<u64, CmpctError> {
        let blob = self
            .blobs
            .get(blob_index)
            .ok_or_else(|| CmpctError::Schema("work estimate references missing blob".into()))?;
        if blob.codec == CODEC_RAW && !full_auth {
            return Ok(requested);
        }
        blob.usize
            .checked_add(blob.csize)
            .ok_or(CmpctError::MemberLimit)
    }

    fn chunked_work(
        &self,
        chunks: &[ChunkRef],
        start: u64,
        length: u64,
    ) -> Result<u64, CmpctError> {
        let request_end = start.checked_add(length).ok_or(CmpctError::Range)?;
        let mut logical_pos = 0u64;
        let mut work = 0u64;
        for chunk in chunks {
            let chunk_end = logical_pos
                .checked_add(chunk.logical_len)
                .ok_or(CmpctError::MemberLimit)?;
            if chunk_end > start && logical_pos < request_end {
                let overlap = request_end.min(chunk_end) - start.max(logical_pos);
                work = work
                    .checked_add(self.blob_work(chunk.index, overlap, false)?)
                    .ok_or(CmpctError::MemberLimit)?;
            }
            logical_pos = chunk_end;
            if logical_pos >= request_end {
                break;
            }
        }
        Ok(work)
    }

    fn storage_work(&self, storage: &Storage, start: u64, length: u64) -> Result<u64, CmpctError> {
        match storage {
            Storage::Unsupported => Err(CmpctError::Unsupported),
            Storage::Direct(index) => self.blob_work(*index, length, false),
            Storage::Pack { index, .. } => self.blob_work(*index, length, true),
            Storage::Fixed(chunks) | Storage::Cdc(chunks) => {
                self.chunked_work(chunks, start, length)
            }
            Storage::Sparse(extents) => {
                let request_end = start.checked_add(length).ok_or(CmpctError::Range)?;
                let mut work = 0u64;
                for extent in extents {
                    let extent_end = extent
                        .offset
                        .checked_add(extent.logical_len)
                        .ok_or(CmpctError::MemberLimit)?;
                    if extent_end <= start {
                        continue;
                    }
                    if extent.offset >= request_end {
                        break;
                    }
                    let overlap_start = start.max(extent.offset);
                    let overlap_end = request_end.min(extent_end);
                    work = work
                        .checked_add(self.chunked_work(
                            &extent.chunks,
                            overlap_start - extent.offset,
                            overlap_end - overlap_start,
                        )?)
                        .ok_or(CmpctError::MemberLimit)?;
                }
                Ok(work)
            }
            Storage::VirtualZip(recipe) => {
                let segments = recipe
                    .plan_range(start, length)
                    .map_err(|error| match error {
                        vzip::VirtualZipError::Range => CmpctError::Range,
                        vzip::VirtualZipError::UnsupportedPayload => CmpctError::Unsupported,
                        vzip::VirtualZipError::Schema(message) => CmpctError::Schema(message),
                    })?;
                let partial_exact_stream = recipe.payloads.iter().any(|payload| {
                    matches!(
                        payload.source,
                        vzip::ProjectionSource::PhysicalDeflate { .. }
                            | vzip::ProjectionSource::RegeneratedDeflate { .. }
                    )
                }) && (start != 0 || length != recipe.logical_size);
                if partial_exact_stream {
                    return recipe
                        .logical_size
                        .checked_mul(2)
                        .ok_or(CmpctError::MemberLimit);
                }
                let mut work = 0u64;
                for segment in segments {
                    let cost = match segment.source {
                        vzip::ProjectionSource::LogicalBlob => {
                            self.blob_work(segment.blob_index, segment.length, false)?
                        }
                        vzip::ProjectionSource::PhysicalDeflate { expected_len } => {
                            let blob = self.blobs.get(segment.blob_index).ok_or_else(|| {
                                CmpctError::Schema("virtual ZIP references missing blob".into())
                            })?;
                            if blob.csize != expected_len {
                                return Err(CmpctError::Schema(
                                    "virtual ZIP physical stream length mismatch".into(),
                                ));
                            }
                            blob.usize
                                .checked_add(blob.csize)
                                .ok_or(CmpctError::MemberLimit)?
                        }
                        vzip::ProjectionSource::RegeneratedDeflate { expected_len, .. } => {
                            let blob = self.blobs.get(segment.blob_index).ok_or_else(|| {
                                CmpctError::Schema("virtual ZIP references missing blob".into())
                            })?;
                            self.blob_work(segment.blob_index, blob.usize, true)?
                                .checked_add(expected_len)
                                .ok_or(CmpctError::MemberLimit)?
                        }
                    };
                    work = work.checked_add(cost).ok_or(CmpctError::MemberLimit)?;
                }
                Ok(work)
            }
            Storage::Hardlink(_) => Err(CmpctError::Schema(
                "hardlink work must be estimated after target resolution".into(),
            )),
        }
    }

    fn resolve_entry_index(&self, mut index: usize) -> Result<usize, CmpctError> {
        let mut seen = HashSet::new();
        while let Storage::Hardlink(target) =
            &self.entries.get(index).ok_or(CmpctError::Range)?.storage
        {
            if !seen.insert(index) {
                return Err(CmpctError::Schema("hardlink cycle".into()));
            }
            index = self
                .entries
                .iter()
                .position(|entry| entry.path == *target)
                .ok_or_else(|| CmpctError::Schema("hardlink target is missing".into()))?;
        }
        Ok(index)
    }

    fn expected_entry_hash(&self, entry_index: usize) -> Result<Option<[u8; 32]>, CmpctError> {
        let resolved_index = self.resolve_entry_index(entry_index)?;
        let entry = self.entries.get(resolved_index).ok_or(CmpctError::Range)?;
        if let Some(hash) = entry.logical_hash {
            return Ok(Some(hash));
        }
        match &entry.storage {
            Storage::Direct(index) => {
                let blob = self.blobs.get(*index).ok_or_else(|| {
                    CmpctError::Schema("direct member references missing blob".into())
                })?;
                let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
                let (_, hash) = self.checked_blob_layout(blob, &mut file)?;
                Ok(Some(hash))
            }
            Storage::VirtualZip(recipe) => Ok(Some(recipe.logical_sha256)),
            // S_PACK has authenticated slice metadata but revision-24 pack rows commonly omit an
            // independent member hash. Each range authenticates the complete shared pack blob instead.
            Storage::Pack { .. } => Ok(None),
            Storage::Fixed(_) | Storage::Sparse(_) | Storage::Cdc(_) => Err(CmpctError::Schema(
                "mapped member is missing required logical SHA-256".into(),
            )),
            Storage::Hardlink(_) => unreachable!("hardlinks are resolved above"),
            Storage::Unsupported => Err(CmpctError::Unsupported),
        }
    }

    /// Read one bounded logical range with a per-operation output and decode-work budget.
    pub fn read_range(
        &self,
        entry_index: usize,
        start: u64,
        out: &mut [u8],
    ) -> Result<usize, CmpctError> {
        if out.len() as u64 > MAX_RANGE_OUTPUT_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let requested_entry = self.entries.get(entry_index).ok_or(CmpctError::Range)?;
        let end = start
            .checked_add(out.len() as u64)
            .ok_or(CmpctError::Range)?;
        if end > requested_entry.size {
            return Err(CmpctError::Range);
        }
        if out.is_empty() {
            return Ok(0);
        }
        let resolved_index = self.resolve_entry_index(entry_index)?;
        let entry = self.entries.get(resolved_index).ok_or(CmpctError::Range)?;
        if entry.kind == KIND_DIR {
            return Err(CmpctError::Unsupported);
        }
        if end > entry.size {
            return Err(CmpctError::Range);
        }
        let work = self.storage_work(&entry.storage, start, out.len() as u64)?;
        if work > MAX_READ_WORK_BYTES {
            return Err(CmpctError::MemberLimit);
        }

        let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
        match &entry.storage {
            Storage::Unsupported => return Err(CmpctError::Unsupported),
            Storage::Direct(index) => {
                let blob = self.blobs.get(*index).ok_or_else(|| {
                    CmpctError::Schema("direct member references missing blob".into())
                })?;
                if blob.usize != entry.size {
                    return Err(CmpctError::BlobHeader);
                }
                self.read_blob_range(*index, start, out, &mut file)?;
                if blob.codec == CODEC_RAW && start == 0 && end == entry.size {
                    let (_, expected_hash) = self.checked_blob_layout(blob, &mut file)?;
                    if Sha256::digest(&*out).as_slice() != expected_hash {
                        return Err(CmpctError::MemberHash);
                    }
                }
            }
            Storage::Fixed(chunks) | Storage::Cdc(chunks) => {
                self.read_chunked_range(chunks, start, out, &mut file)?;
                if start == 0 && end == entry.size {
                    let expected = entry.logical_hash.ok_or_else(|| {
                        CmpctError::Schema("chunked member is missing logical SHA-256".into())
                    })?;
                    if Sha256::digest(&*out).as_slice() != expected {
                        return Err(CmpctError::MemberHash);
                    }
                }
            }
            Storage::VirtualZip(recipe) => {
                self.read_virtual_zip_range(recipe, start, out, &mut file)?;
            }
            Storage::Pack {
                index,
                offset,
                length,
            } => {
                if *length != entry.size {
                    return Err(CmpctError::BlobHeader);
                }
                // Footnote: packed file rows normally omit an independent file SHA. Authenticate the
                // complete shared pack blob—even when it is RAW—then expose only this member's bounded
                // slice. A corrupted sibling can therefore never cross the public ABI as trusted pack
                // content merely because the requested slice itself happened to look plausible.
                let decoded = self.read_blob_complete_authenticated(*index, &mut file)?;
                let source_start_u64 = offset.checked_add(start).ok_or(CmpctError::Range)?;
                let source_start =
                    usize::try_from(source_start_u64).map_err(|_| CmpctError::Range)?;
                let source_end = source_start
                    .checked_add(out.len())
                    .ok_or(CmpctError::Range)?;
                if source_end > decoded.len() {
                    return Err(CmpctError::Range);
                }
                out.copy_from_slice(&decoded[source_start..source_end]);
                if start == 0 && end == entry.size {
                    if let Some(expected) = entry.logical_hash {
                        if Sha256::digest(&*out).as_slice() != expected {
                            return Err(CmpctError::MemberHash);
                        }
                    }
                }
            }
            Storage::Sparse(extents) => {
                self.read_sparse_range(extents, start, out, &mut file)?;
                if start == 0 && end == entry.size {
                    let expected = entry.logical_hash.ok_or_else(|| {
                        CmpctError::Schema("sparse member is missing logical SHA-256".into())
                    })?;
                    if Sha256::digest(&*out).as_slice() != expected {
                        return Err(CmpctError::MemberHash);
                    }
                }
            }
            Storage::Hardlink(_) => unreachable!("hardlinks are resolved before reading"),
        }
        Ok(out.len())
    }

    /// Validate all physical blob framing plus already-parsed logical relationships without decoding
    /// every payload. This is the native structural-preflight boundary used before extraction.
    pub fn preflight(&self) -> Result<(), CmpctError> {
        let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
        for blob in &self.blobs {
            self.checked_blob_layout(blob, &mut file)?;
        }
        for entry in &self.entries {
            if entry.kind != KIND_DIR && matches!(entry.storage, Storage::Unsupported) {
                return Err(CmpctError::Unsupported);
            }
        }
        Ok(())
    }

    /// Copy one logical entry sequentially without requiring the caller to allocate its whole size.
    /// A complete stream is SHA-checked at EOF whenever revision 24 provides a member identity.
    pub fn copy_entry_to<W: Write>(
        &self,
        entry_index: usize,
        writer: &mut W,
    ) -> Result<u64, CmpctError> {
        let entry = self.entries.get(entry_index).ok_or(CmpctError::Range)?;
        if entry.kind != KIND_FILE && entry.kind != KIND_SYMLINK && entry.kind != KIND_HARDLINK {
            return Err(CmpctError::Unsupported);
        }
        let expected_hash = self.expected_entry_hash(entry_index)?;
        let mut hasher = Sha256::new();
        let mut offset = 0u64;
        let mut buffer = vec![0u8; STREAM_CHUNK_BYTES];
        while offset < entry.size {
            let length = usize::try_from((entry.size - offset).min(STREAM_CHUNK_BYTES as u64))
                .map_err(|_| CmpctError::MemberLimit)?;
            self.read_range(entry_index, offset, &mut buffer[..length])?;
            hasher.update(&buffer[..length]);
            writer.write_all(&buffer[..length])?;
            offset += length as u64;
        }
        if let Some(expected) = expected_hash {
            if hasher.finalize().as_slice() != expected {
                return Err(CmpctError::MemberHash);
            }
        }
        Ok(offset)
    }

    fn extraction_materialized_bytes(&self) -> Result<u64, CmpctError> {
        self.entries.iter().try_fold(0u64, |total, entry| {
            // Hardlinks reuse already-materialized file bytes and directories carry no payload.
            // Symlink targets still count because archive-controlled bytes are materialized on disk.
            let bytes = match entry.kind {
                KIND_FILE | KIND_SYMLINK => entry.size,
                KIND_DIR | KIND_HARDLINK => 0,
                _ => return Err(CmpctError::Unsupported),
            };
            total.checked_add(bytes).ok_or(CmpctError::MemberLimit)
        })
    }

    /// Extract the complete tree with an explicit archive-wide materialization budget.
    pub fn extract_all_bounded(
        &self,
        destination: &Path,
        max_materialized_bytes: u64,
    ) -> Result<(), CmpctError> {
        self.preflight()?;
        if self.extraction_materialized_bytes()? > max_materialized_bytes {
            return Err(CmpctError::MemberLimit);
        }

        if destination.exists() {
            if !destination.is_dir() {
                return Err(CmpctError::Extraction(
                    "destination exists and is not a directory".into(),
                ));
            }
            if fs::read_dir(destination)?.next().is_some() {
                return Err(CmpctError::Extraction(
                    "destination must be empty to preserve no-follow extraction safety".into(),
                ));
            }
        } else {
            fs::create_dir_all(destination)?;
        }

        // Build directory topology before restoring archived permissions. Restrictive modes such as
        // 0500 or 0000 must not make a parent unwritable before its descendants are populated.
        for entry in &self.entries {
            if entry.kind == KIND_DIR {
                fs::create_dir_all(destination.join(&entry.path))?;
            }
        }

        for (index, entry) in self.entries.iter().enumerate() {
            let output = destination.join(&entry.path);
            match entry.kind {
                KIND_FILE => {
                    if let Some(parent) = output.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    let mut target = File::create(&output)?;
                    self.copy_entry_to(index, &mut target)?;
                    target.sync_all()?;
                    apply_mode(&output, entry.mode)?;
                }
                KIND_SYMLINK => {
                    if entry.size > MAX_SYMLINK_TARGET_BYTES {
                        return Err(CmpctError::MemberLimit);
                    }
                    let len = usize::try_from(entry.size).map_err(|_| CmpctError::MemberLimit)?;
                    let mut bytes = vec![0u8; len];
                    self.read_range(index, 0, &mut bytes)?;
                    if let Some(expected) = self.expected_entry_hash(index)? {
                        if Sha256::digest(&bytes).as_slice() != expected {
                            return Err(CmpctError::MemberHash);
                        }
                    }
                    let target = String::from_utf8(bytes).map_err(|_| {
                        CmpctError::Extraction(format!(
                            "symlink target for {} is not UTF-8",
                            entry.path
                        ))
                    })?;
                    validate_symlink_target(&entry.path, &target)?;
                    if let Some(parent) = output.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    create_symlink(&target, &output)?;
                }
                KIND_DIR | KIND_HARDLINK => {}
                _ => return Err(CmpctError::Unsupported),
            }
        }

        for (index, entry) in self.entries.iter().enumerate() {
            if entry.kind != KIND_HARDLINK {
                continue;
            }
            let resolved = self.resolve_entry_index(index)?;
            let target_entry = self.entries.get(resolved).ok_or(CmpctError::Range)?;
            if target_entry.kind != KIND_FILE {
                return Err(CmpctError::Extraction(
                    "hardlink does not resolve to a regular file".into(),
                ));
            }
            let source = destination.join(&target_entry.path);
            let output = destination.join(&entry.path);
            if let Some(parent) = output.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::hard_link(source, output)?;
        }

        // Restore restrictive directory modes only after every descendant exists, deepest first.
        let mut directories: Vec<&Entry> = self
            .entries
            .iter()
            .filter(|entry| entry.kind == KIND_DIR)
            .collect();
        directories.sort_by_key(|entry| std::cmp::Reverse(entry.path.matches('/').count()));
        for entry in directories {
            apply_mode(&destination.join(&entry.path), entry.mode)?;
        }
        Ok(())
    }

    /// Extract using the native handler's conservative default ceiling. Callers that deliberately
    /// materialize larger trees can opt into a larger explicit budget through the bounded ABI.
    pub fn extract_all(&self, destination: &Path) -> Result<(), CmpctError> {
        self.extract_all_bounded(destination, MAX_EXTRACT_OUTPUT_BYTES)
    }
}

fn le_u32(bytes: &[u8]) -> u32 {
    u32::from_le_bytes(bytes.try_into().expect("fixed-width header slice"))
}

fn le_u64(bytes: &[u8]) -> u64 {
    u64::from_le_bytes(bytes.try_into().expect("fixed-width header slice"))
}

fn map_field<'a>(value: &'a Value, key: &str) -> Result<&'a Value, CmpctError> {
    let map = value
        .as_map()
        .ok_or_else(|| CmpctError::Schema("root index is not a map".into()))?;
    map.iter()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
        .ok_or_else(|| CmpctError::Schema(format!("missing root field {key}")))
}

fn canonical_path(raw: &str) -> Result<String, CmpctError> {
    if raw.is_empty() || raw.len() > MAX_PATH_BYTES || raw.contains('\0') {
        return Err(CmpctError::Path(raw.into()));
    }
    if raw.starts_with('/') || raw.starts_with('\\') {
        return Err(CmpctError::Path(raw.into()));
    }
    let normalized = raw.replace('\\', "/");
    let mut parts = Vec::new();
    for part in normalized.split('/') {
        if part.is_empty() || part == "." || part == ".." {
            return Err(CmpctError::Path(raw.into()));
        }
        parts.push(part);
    }
    Ok(parts.join("/"))
}

fn parse_blobs(index: &Value, data_span: u64) -> Result<Vec<Blob>, CmpctError> {
    let rows = map_field(index, "blobs")?
        .as_array()
        .ok_or_else(|| CmpctError::Schema("blobs is not an array".into()))?;
    if rows.len() > MAX_BLOBS {
        return Err(CmpctError::Schema(
            "blob count exceeds native handler limit".into(),
        ));
    }
    let mut blobs = Vec::with_capacity(rows.len());
    let mut intervals = Vec::with_capacity(rows.len());
    for (index, value) in rows.iter().enumerate() {
        let row = value
            .as_array()
            .ok_or_else(|| CmpctError::Schema(format!("blob row {index} is not an array")))?;
        if row.len() != 5 {
            return Err(CmpctError::Schema(format!(
                "blob row {index} must contain five fields"
            )));
        }
        let offset = row[0]
            .as_u64()
            .ok_or_else(|| CmpctError::Schema(format!("blob row {index} has invalid offset")))?;
        let usize = row[1]
            .as_u64()
            .ok_or_else(|| CmpctError::Schema(format!("blob row {index} has invalid size")))?;
        let csize = row[2].as_u64().ok_or_else(|| {
            CmpctError::Schema(format!("blob row {index} has invalid compressed size"))
        })?;
        if usize > MAX_BLOB_BYTES || csize > MAX_BLOB_BYTES {
            return Err(CmpctError::MemberLimit);
        }
        let codec = row[3]
            .as_u64()
            .filter(|value| *value <= CODEC_DEFLATE as u64)
            .ok_or_else(|| CmpctError::Schema(format!("blob row {index} has unknown codec")))?
            as u8;
        let meta_len = row[4]
            .as_u64()
            .filter(|value| *value <= u32::MAX as u64 && *value <= MAX_INDEX_BYTES)
            .ok_or_else(|| {
                CmpctError::Schema(format!("blob row {index} has invalid metadata length"))
            })? as u32;
        let end = offset
            .checked_add(BLOB_HEADER_SIZE as u64)
            .and_then(|value| value.checked_add(meta_len as u64))
            .and_then(|value| value.checked_add(csize))
            .ok_or_else(|| CmpctError::Schema(format!("blob row {index} overflows offsets")))?;
        if end > data_span {
            return Err(CmpctError::Schema(format!(
                "blob row {index} extends past committed data boundary"
            )));
        }
        intervals.push((offset, end, index));
        blobs.push(Blob {
            offset,
            usize,
            csize,
            codec,
            meta_len,
        });
    }
    intervals.sort_unstable_by_key(|interval| interval.0);
    for pair in intervals.windows(2) {
        if pair[0].1 > pair[1].0 {
            return Err(CmpctError::Schema(format!(
                "blob rows {} and {} overlap physically",
                pair[0].2, pair[1].2
            )));
        }
    }
    Ok(blobs)
}

fn validate_recipes(index: &Value, blobs: &[Blob]) -> Result<(), CmpctError> {
    let recipes = map_field(index, "recipes")?
        .as_array()
        .ok_or_else(|| CmpctError::Schema("recipes is not an array".into()))?;
    if recipes.len() > MAX_RECIPES {
        return Err(CmpctError::IndexLimit);
    }
    let blob_sizes: Vec<u64> = blobs.iter().map(|blob| blob.usize).collect();
    for (recipe_index, recipe) in recipes.iter().enumerate() {
        let row = recipe
            .as_array()
            .ok_or_else(|| CmpctError::Schema(format!("recipe {recipe_index} is not an array")))?;
        let logical_size = row.get(4).and_then(Value::as_u64).ok_or_else(|| {
            CmpctError::Schema(format!("recipe {recipe_index} has invalid logical size"))
        })?;
        vzip::parse_recipe(recipe, &blob_sizes, logical_size).map_err(|error| match error {
            vzip::VirtualZipError::UnsupportedPayload => CmpctError::Unsupported,
            vzip::VirtualZipError::Schema(message) => {
                CmpctError::Schema(format!("recipe {recipe_index}: {message}"))
            }
            vzip::VirtualZipError::Range => CmpctError::Schema(format!(
                "recipe {recipe_index} has invalid range accounting"
            )),
        })?;
    }
    Ok(())
}

fn parse_dictionary_blob(index: &Value, blobs: &[Blob]) -> Result<Option<usize>, CmpctError> {
    let map = index
        .as_map()
        .ok_or_else(|| CmpctError::Schema("root index is not a map".into()))?;
    let Some(value) = map
        .iter()
        .find_map(|(key, value)| (key.as_str() == Some("dict_blob")).then_some(value))
    else {
        return Ok(None);
    };
    if matches!(value, Value::Nil) {
        return Ok(None);
    }
    Ok(Some(storage_blob_index(
        value,
        blobs.len(),
        "dictionary blob",
    )?))
}

fn parse_hash(value: &Value, row_index: usize) -> Result<Option<[u8; 32]>, CmpctError> {
    match value {
        Value::Nil => Ok(None),
        Value::Binary(bytes) if bytes.is_empty() => Ok(None),
        Value::Binary(bytes) => {
            if bytes.len() != 32 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} has invalid logical SHA-256 length"
                )));
            }
            let mut hash = [0u8; 32];
            hash.copy_from_slice(bytes);
            Ok(Some(hash))
        }
        _ => Err(CmpctError::Schema(format!(
            "file row {row_index} has invalid logical SHA-256"
        ))),
    }
}

fn storage_blob_index(value: &Value, blob_count: usize, label: &str) -> Result<usize, CmpctError> {
    let raw = value
        .as_u64()
        .ok_or_else(|| CmpctError::Schema(format!("{label} is not a blob index")))?;
    let index = usize::try_from(raw)
        .map_err(|_| CmpctError::Schema(format!("{label} exceeds native index width")))?;
    if index >= blob_count {
        return Err(CmpctError::Schema(format!(
            "{label} references missing blob"
        )));
    }
    Ok(index)
}

fn parse_virtual_zip_storage(
    index: &Value,
    storage: &[Value],
    logical_size: u64,
    blobs: &[Blob],
    row_index: usize,
) -> Result<Storage, CmpctError> {
    if storage.len() != 2 {
        return Err(CmpctError::Schema(format!(
            "file row {row_index} virtual-ZIP storage must contain two fields"
        )));
    }
    let recipe_index = storage[1].as_u64().ok_or_else(|| {
        CmpctError::Schema(format!(
            "file row {row_index} virtual-ZIP recipe index is invalid"
        ))
    })?;
    let recipe_index = usize::try_from(recipe_index).map_err(|_| {
        CmpctError::Schema(format!(
            "file row {row_index} virtual-ZIP recipe index exceeds native width"
        ))
    })?;
    let recipes = map_field(index, "recipes")?
        .as_array()
        .ok_or_else(|| CmpctError::Schema("recipes is not an array".into()))?;
    let recipe_value = recipes.get(recipe_index).ok_or_else(|| {
        CmpctError::Schema(format!(
            "file row {row_index} virtual-ZIP references missing recipe"
        ))
    })?;
    let blob_sizes: Vec<u64> = blobs.iter().map(|blob| blob.usize).collect();
    match vzip::parse_recipe(recipe_value, &blob_sizes, logical_size) {
        Ok(recipe) => Ok(Storage::VirtualZip(recipe)),
        Err(vzip::VirtualZipError::UnsupportedPayload) => Ok(Storage::Unsupported),
        Err(vzip::VirtualZipError::Schema(message)) => Err(CmpctError::Schema(format!(
            "file row {row_index} virtual-ZIP recipe: {message}"
        ))),
        Err(vzip::VirtualZipError::Range) => Err(CmpctError::Schema(format!(
            "file row {row_index} virtual-ZIP recipe has invalid range accounting"
        ))),
    }
}

fn parse_hardlink_storage(value: &Value, row_index: usize) -> Result<Storage, CmpctError> {
    let row = value.as_array().ok_or_else(|| {
        CmpctError::Schema(format!("hardlink row {row_index} storage is not an array"))
    })?;
    if row.len() != 1 {
        return Err(CmpctError::Schema(format!(
            "hardlink row {row_index} storage must contain one target path"
        )));
    }
    let target = row[0].as_str().ok_or_else(|| {
        CmpctError::Schema(format!("hardlink row {row_index} target is not UTF-8"))
    })?;
    Ok(Storage::Hardlink(canonical_path(target)?))
}

fn parse_storage(
    index: &Value,
    value: &Value,
    logical_size: u64,
    blobs: &[Blob],
    row_index: usize,
) -> Result<Storage, CmpctError> {
    let Some(storage) = value.as_array() else {
        return Ok(Storage::Unsupported);
    };
    let Some(kind) = storage.first().and_then(Value::as_u64) else {
        return Ok(Storage::Unsupported);
    };
    match kind {
        STORAGE_BLOB => {
            if storage.len() != 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} direct storage must contain two fields"
                )));
            }
            let index = storage_blob_index(
                &storage[1],
                blobs.len(),
                &format!("file row {row_index} direct blob"),
            )?;
            if blobs[index].usize != logical_size {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} direct blob length disagrees with logical size"
                )));
            }
            Ok(Storage::Direct(index))
        }
        STORAGE_CHUNKS => {
            if storage.len() != 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} fixed chunk storage must contain two fields"
                )));
            }
            let ids = storage[1].as_array().ok_or_else(|| {
                CmpctError::Schema(format!(
                    "file row {row_index} fixed chunks are not an array"
                ))
            })?;
            if ids.len() > MAX_BLOBS {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} fixed chunk count exceeds native limit"
                )));
            }
            let mut total = 0u64;
            let mut chunks = Vec::with_capacity(ids.len());
            for (chunk_index, value) in ids.iter().enumerate() {
                let index = storage_blob_index(
                    value,
                    blobs.len(),
                    &format!("file row {row_index} fixed chunk {chunk_index}"),
                )?;
                let logical_len = blobs[index].usize;
                total = total.checked_add(logical_len).ok_or_else(|| {
                    CmpctError::Schema(format!("file row {row_index} fixed chunks overflow"))
                })?;
                chunks.push(ChunkRef { logical_len, index });
            }
            if total != logical_size {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} fixed chunk lengths do not equal logical size"
                )));
            }
            Ok(Storage::Fixed(chunks))
        }
        STORAGE_VZIP => parse_virtual_zip_storage(index, storage, logical_size, blobs, row_index),
        STORAGE_SPARSE => {
            if storage.len() != 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} sparse storage must contain two fields"
                )));
            }
            let rows = storage[1].as_array().ok_or_else(|| {
                CmpctError::Schema(format!(
                    "file row {row_index} sparse extents are not an array"
                ))
            })?;
            if rows.len() > MAX_BLOBS {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} sparse extent count exceeds native limit"
                )));
            }
            let mut previous_end = 0u64;
            let mut total_refs = 0usize;
            let mut extents = Vec::with_capacity(rows.len());
            for (extent_index, value) in rows.iter().enumerate() {
                let extent = value.as_array().ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} is not an array"
                    ))
                })?;
                if extent.len() != 3 {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} has invalid shape"
                    )));
                }
                let offset = extent[0].as_u64().ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} has invalid offset"
                    ))
                })?;
                let logical_len =
                    extent[1]
                        .as_u64()
                        .filter(|value| *value > 0)
                        .ok_or_else(|| {
                            CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} has invalid length"
                    ))
                        })?;
                let extent_end = offset.checked_add(logical_len).ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} overflows"
                    ))
                })?;
                if offset < previous_end || extent_end > logical_size {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} overlaps or exceeds file"
                    )));
                }
                let ids = extent[2].as_array().ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} chunks are not an array"
                    ))
                })?;
                total_refs = total_refs.checked_add(ids.len()).ok_or_else(|| {
                    CmpctError::Schema("sparse blob-reference count overflows".into())
                })?;
                if total_refs > MAX_BLOBS {
                    return Err(CmpctError::Schema(
                        "sparse blob-reference count exceeds native limit".into(),
                    ));
                }
                let mut stored = 0u64;
                let mut chunks = Vec::with_capacity(ids.len());
                for (chunk_index, value) in ids.iter().enumerate() {
                    let index = storage_blob_index(
                        value,
                        blobs.len(),
                        &format!(
                            "file row {row_index} sparse extent {extent_index} chunk {chunk_index}"
                        ),
                    )?;
                    let chunk_len = blobs[index].usize;
                    stored = stored.checked_add(chunk_len).ok_or_else(|| {
                        CmpctError::Schema("sparse extent stored length overflows".into())
                    })?;
                    chunks.push(ChunkRef {
                        logical_len: chunk_len,
                        index,
                    });
                }
                if stored != logical_len {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} length mismatch"
                    )));
                }
                extents.push(SparseExtent {
                    offset,
                    logical_len,
                    chunks,
                });
                previous_end = extent_end;
            }
            Ok(Storage::Sparse(extents))
        }
        STORAGE_PACK => {
            if storage.len() != 4 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} pack storage has invalid shape"
                )));
            }
            let index = storage_blob_index(
                &storage[1],
                blobs.len(),
                &format!("file row {row_index} pack blob"),
            )?;
            let offset = storage[2].as_u64().ok_or_else(|| {
                CmpctError::Schema(format!("file row {row_index} pack offset is invalid"))
            })?;
            let length = storage[3].as_u64().ok_or_else(|| {
                CmpctError::Schema(format!("file row {row_index} pack length is invalid"))
            })?;
            let pack_end = offset.checked_add(length).ok_or_else(|| {
                CmpctError::Schema(format!("file row {row_index} pack range overflows"))
            })?;
            if length != logical_size || pack_end > blobs[index].usize {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} pack range disagrees with logical/blob size"
                )));
            }
            Ok(Storage::Pack {
                index,
                offset,
                length,
            })
        }
        STORAGE_CDC => {
            if storage.len() != 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} CDC storage must contain two fields"
                )));
            }
            let rows = storage[1].as_array().ok_or_else(|| {
                CmpctError::Schema(format!("file row {row_index} CDC chunks are not an array"))
            })?;
            if rows.len() > MAX_BLOBS {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} CDC chunk count exceeds native limit"
                )));
            }
            let mut total = 0u64;
            let mut chunks = Vec::with_capacity(rows.len());
            for (chunk_index, value) in rows.iter().enumerate() {
                let pair = value.as_array().ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} CDC chunk {chunk_index} is not an array"
                    ))
                })?;
                if pair.len() != 2 {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} CDC chunk {chunk_index} has invalid shape"
                    )));
                }
                let logical_len = pair[0].as_u64().filter(|value| *value > 0).ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} CDC chunk {chunk_index} has invalid length"
                    ))
                })?;
                let index = storage_blob_index(
                    &pair[1],
                    blobs.len(),
                    &format!("file row {row_index} CDC chunk {chunk_index}"),
                )?;
                if blobs[index].usize != logical_len {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} CDC chunk {chunk_index} length disagrees with blob"
                    )));
                }
                total = total.checked_add(logical_len).ok_or_else(|| {
                    CmpctError::Schema(format!("file row {row_index} CDC chunks overflow"))
                })?;
                chunks.push(ChunkRef { logical_len, index });
            }
            if total != logical_size {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} CDC chunk lengths do not equal logical size"
                )));
            }
            Ok(Storage::Cdc(chunks))
        }
        _ => Ok(Storage::Unsupported),
    }
}

fn parse_entries(index: &Value, blobs: &[Blob]) -> Result<Vec<Entry>, CmpctError> {
    let index_revision = map_field(index, "v")?
        .as_u64()
        .ok_or_else(|| CmpctError::Schema("index revision is not an unsigned integer".into()))?;
    if index_revision != VERSION as u64 {
        return Err(CmpctError::Revision(
            index_revision.min(u16::MAX as u64) as u16
        ));
    }
    let files = map_field(index, "files")?
        .as_array()
        .ok_or_else(|| CmpctError::Schema("files is not an array".into()))?;
    if files.len() > MAX_FILES {
        return Err(CmpctError::Schema(
            "file count exceeds native handler limit".into(),
        ));
    }

    let mut seen = HashSet::with_capacity(files.len().min(65_536));
    let mut entries = Vec::with_capacity(files.len());
    for (row_index, value) in files.iter().enumerate() {
        let row = value
            .as_array()
            .ok_or_else(|| CmpctError::Schema(format!("file row {row_index} is not an array")))?;
        if row.len() != 7 {
            return Err(CmpctError::Schema(format!(
                "file row {row_index} must contain seven fields"
            )));
        }
        let path = row[0]
            .as_str()
            .ok_or_else(|| CmpctError::Schema(format!("file row {row_index} path is not UTF-8")))?;
        let key = canonical_path(path)?;
        if !seen.insert(key) {
            return Err(CmpctError::Path(path.into()));
        }
        let kind = row[1]
            .as_u64()
            .filter(|value| *value <= KIND_HARDLINK as u64)
            .ok_or_else(|| CmpctError::Schema(format!("file row {row_index} has invalid kind")))?
            as u8;
        let mode = row[2]
            .as_u64()
            .filter(|value| *value <= u32::MAX as u64)
            .ok_or_else(|| CmpctError::Schema(format!("file row {row_index} has invalid mode")))?
            as u32;
        let mtime_ns = row[3]
            .as_i64()
            .ok_or_else(|| CmpctError::Schema(format!("file row {row_index} has invalid mtime")))?;
        let size = row[4]
            .as_u64()
            .ok_or_else(|| CmpctError::Schema(format!("file row {row_index} has invalid size")))?;
        let logical_hash = parse_hash(&row[5], row_index)?;
        let storage = if kind == KIND_HARDLINK {
            parse_hardlink_storage(&row[6], row_index)?
        } else if kind == KIND_DIR {
            if !matches!(&row[6], Value::Nil) {
                return Err(CmpctError::Schema(format!(
                    "directory row {row_index} must not carry storage"
                )));
            }
            Storage::Unsupported
        } else {
            parse_storage(index, &row[6], size, blobs, row_index)?
        };

        if kind == KIND_SYMLINK && !matches!(&storage, Storage::Direct(_)) {
            return Err(CmpctError::Schema(format!(
                "symlink row {row_index} must use direct blob storage"
            )));
        }
        if matches!(
            storage,
            Storage::Fixed(_) | Storage::Sparse(_) | Storage::Cdc(_)
        ) && logical_hash.is_none()
        {
            return Err(CmpctError::Schema(format!(
                "file row {row_index} mapped member is missing SHA-256"
            )));
        }
        if let Storage::VirtualZip(recipe) = &storage {
            if let Some(hash) = logical_hash {
                if hash != recipe.logical_sha256 {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} virtual-ZIP hash disagrees with recipe identity"
                    )));
                }
            }
        }
        if (kind == KIND_FILE || kind == KIND_SYMLINK) && matches!(storage, Storage::Unsupported) {
            return Err(CmpctError::Unsupported);
        }
        let link_target = match &storage {
            Storage::Hardlink(target) => Some(target.clone()),
            _ => None,
        };
        entries.push(Entry {
            path: path.to_owned(),
            kind,
            mode,
            mtime_ns,
            size,
            storage,
            logical_hash,
            link_target,
        });
    }
    Ok(entries)
}

fn validate_entry_tree(entries: &[Entry]) -> Result<(), CmpctError> {
    let by_path: HashMap<&str, usize> = entries
        .iter()
        .enumerate()
        .map(|(index, entry)| (entry.path.as_str(), index))
        .collect();

    for entry in entries {
        let parts: Vec<&str> = entry.path.split('/').collect();
        let mut prefix = String::new();
        for part in parts.iter().take(parts.len().saturating_sub(1)) {
            if !prefix.is_empty() {
                prefix.push('/');
            }
            prefix.push_str(part);
            if let Some(index) = by_path.get(prefix.as_str()) {
                if entries[*index].kind != KIND_DIR {
                    return Err(CmpctError::Path(format!(
                        "non-directory {} is an ancestor of {}",
                        prefix, entry.path
                    )));
                }
            }
        }
    }

    for (start_index, entry) in entries.iter().enumerate() {
        if entry.kind != KIND_HARDLINK {
            continue;
        }
        let mut index = start_index;
        let mut seen = HashSet::new();
        loop {
            if !seen.insert(index) {
                return Err(CmpctError::Schema(format!(
                    "hardlink cycle includes {}",
                    entry.path
                )));
            }
            let current = &entries[index];
            match &current.storage {
                Storage::Hardlink(target) => {
                    index = *by_path.get(target.as_str()).ok_or_else(|| {
                        CmpctError::Schema(format!("hardlink target {target} is missing"))
                    })?;
                    if entries[index].size != entry.size {
                        return Err(CmpctError::Schema(format!(
                            "hardlink {} size disagrees with target",
                            entry.path
                        )));
                    }
                }
                _ if current.kind == KIND_FILE => break,
                _ => {
                    return Err(CmpctError::Schema(format!(
                        "hardlink {} does not resolve to a regular file",
                        entry.path
                    )))
                }
            }
        }
    }
    Ok(())
}

fn validate_fsmeta(index: &Value, file_count: usize) -> Result<(), CmpctError> {
    let map = index
        .as_map()
        .ok_or_else(|| CmpctError::Schema("root index is not a map".into()))?;
    let Some(fsmeta) = map
        .iter()
        .find_map(|(key, value)| (key.as_str() == Some("fsmeta")).then_some(value))
    else {
        return Ok(());
    };
    let fsmeta = fsmeta
        .as_map()
        .ok_or_else(|| CmpctError::Schema("fsmeta is not a map".into()))?;
    let get = |name: &str| {
        fsmeta
            .iter()
            .find_map(|(key, value)| (key.as_str() == Some(name)).then_some(value))
    };
    if let Some(owner) = get("owner") {
        let owner = owner
            .as_array()
            .filter(|row| row.len() == 2)
            .ok_or_else(|| CmpctError::Schema("fsmeta owner has invalid shape".into()))?;
        if owner.iter().any(|value| value.as_u64().is_none()) {
            return Err(CmpctError::Schema("fsmeta owner must be unsigned".into()));
        }
    }
    if let Some(overrides) = get("owner_overrides") {
        for row in overrides
            .as_array()
            .ok_or_else(|| CmpctError::Schema("owner_overrides is not an array".into()))?
        {
            let row = row
                .as_array()
                .filter(|row| row.len() == 3)
                .ok_or_else(|| CmpctError::Schema("owner override has invalid shape".into()))?;
            let file_index = row[0]
                .as_u64()
                .and_then(|value| usize::try_from(value).ok())
                .filter(|index| *index < file_count)
                .ok_or_else(|| {
                    CmpctError::Schema("owner override references missing file".into())
                })?;
            let _ = file_index;
            if row[1].as_u64().is_none() || row[2].as_u64().is_none() {
                return Err(CmpctError::Schema(
                    "owner override uid/gid is invalid".into(),
                ));
            }
        }
    }
    if let Some(xattrs) = get("xattrs") {
        for row in xattrs
            .as_array()
            .ok_or_else(|| CmpctError::Schema("xattrs is not an array".into()))?
        {
            let row = row
                .as_array()
                .filter(|row| row.len() == 2)
                .ok_or_else(|| CmpctError::Schema("xattr row has invalid shape".into()))?;
            let file_index = row[0]
                .as_u64()
                .and_then(|value| usize::try_from(value).ok())
                .filter(|index| *index < file_count)
                .ok_or_else(|| CmpctError::Schema("xattr row references missing file".into()))?;
            let _ = file_index;
            for pair in row[1]
                .as_array()
                .ok_or_else(|| CmpctError::Schema("xattr pairs are not an array".into()))?
            {
                let pair = pair
                    .as_array()
                    .filter(|pair| pair.len() == 2)
                    .ok_or_else(|| CmpctError::Schema("xattr pair has invalid shape".into()))?;
                if pair[0].as_str().is_none() || !matches!(&pair[1], Value::Binary(_)) {
                    return Err(CmpctError::Schema(
                        "xattr name/value has invalid type".into(),
                    ));
                }
            }
        }
    }
    Ok(())
}

fn validate_symlink_target(link_path: &str, target: &str) -> Result<(), CmpctError> {
    if target.is_empty() || target.contains('\0') {
        return Err(CmpctError::Extraction(format!(
            "symlink {link_path} has an empty/NUL target"
        )));
    }
    let target_path = Path::new(target);
    if target_path.is_absolute() {
        return Err(CmpctError::Extraction(format!(
            "symlink {link_path} has an absolute target"
        )));
    }
    let mut depth = link_path.split('/').count().saturating_sub(1) as isize;
    for component in target_path.components() {
        match component {
            Component::CurDir => {}
            Component::Normal(_) => depth += 1,
            Component::ParentDir => {
                depth -= 1;
                if depth < 0 {
                    return Err(CmpctError::Extraction(format!(
                        "symlink {link_path} escapes extraction root"
                    )));
                }
            }
            Component::RootDir | Component::Prefix(_) => {
                return Err(CmpctError::Extraction(format!(
                    "symlink {link_path} has a rooted target"
                )))
            }
        }
    }
    Ok(())
}

#[cfg(unix)]
fn create_symlink(target: &str, output: &Path) -> Result<(), CmpctError> {
    symlink(target, output)?;
    Ok(())
}

#[cfg(windows)]
fn create_symlink(target: &str, output: &Path) -> Result<(), CmpctError> {
    symlink_file(target, output)?;
    Ok(())
}

#[cfg(not(any(unix, windows)))]
fn create_symlink(_target: &str, _output: &Path) -> Result<(), CmpctError> {
    Err(CmpctError::Unsupported)
}

#[cfg(unix)]
fn apply_mode(path: &Path, mode: u32) -> Result<(), CmpctError> {
    fs::set_permissions(path, fs::Permissions::from_mode(mode & 0o7777))?;
    Ok(())
}

#[cfg(not(unix))]
fn apply_mode(_path: &Path, _mode: u32) -> Result<(), CmpctError> {
    Ok(())
}

#[repr(C)]
#[derive(Debug, Copy, Clone, Eq, PartialEq)]
pub enum CmpctStatus {
    Ok = 0,
    Null = -1,
    Io = -2,
    Format = -3,
    Limit = -4,
    Utf8 = -5,
    Range = -6,
    Unsupported = -7,
    Panic = -127,
}

#[repr(C)]
pub struct CmpctEntryInfo {
    pub kind: u8,
    pub _reserved: [u8; 3],
    pub mode: u32,
    pub size: u64,
    pub mtime_ns: i64,
}

#[repr(C)]
pub struct CmpctStream {
    archive: *const Archive,
    entry_index: usize,
    offset: u64,
    hasher: Sha256,
    expected_hash: Option<[u8; 32]>,
    verified: bool,
}

fn error_status(error: &CmpctError) -> CmpctStatus {
    match error {
        CmpctError::Io(_) | CmpctError::Truncated => CmpctStatus::Io,
        CmpctError::IndexLimit | CmpctError::MemberLimit => CmpctStatus::Limit,
        CmpctError::WavFlac(wavflac::WavFlacError::Limit) => CmpctStatus::Limit,
        CmpctError::Recovery(recovery::RecoveryError::Io(_)) => CmpctStatus::Io,
        CmpctError::Recovery(recovery::RecoveryError::Limit) => CmpctStatus::Limit,
        CmpctError::Range => CmpctStatus::Range,
        CmpctError::Unsupported => CmpctStatus::Unsupported,
        _ => CmpctStatus::Format,
    }
}

/// Open an archive through the stable C-facing ownership boundary.
///
/// # Safety
/// `path` must point to a valid NUL-terminated UTF-8 string and `out` must be writable.
#[no_mangle]
pub unsafe extern "C" fn cmpct_open(path: *const c_char, out: *mut *mut Archive) -> c_int {
    if path.is_null() || out.is_null() {
        return CmpctStatus::Null as c_int;
    }
    *out = ptr::null_mut();
    let result = std::panic::catch_unwind(|| {
        let path = CStr::from_ptr(path)
            .to_str()
            .map_err(|_| CmpctStatus::Utf8)?;
        Archive::open(Path::new(path)).map_err(|error| error_status(&error))
    });
    match result {
        Ok(Ok(archive)) => {
            *out = Box::into_raw(Box::new(archive));
            CmpctStatus::Ok as c_int
        }
        Ok(Err(status)) => status as c_int,
        Err(_) => CmpctStatus::Panic as c_int,
    }
}

/// # Safety
/// `archive` must be a pointer returned by `cmpct_open` and must be closed exactly once.
#[no_mangle]
pub unsafe extern "C" fn cmpct_close(archive: *mut Archive) {
    if !archive.is_null() {
        drop(Box::from_raw(archive));
    }
}

/// # Safety
/// `archive` must be a live pointer returned by `cmpct_open`.
#[no_mangle]
pub unsafe extern "C" fn cmpct_revision(archive: *const Archive) -> u16 {
    archive.as_ref().map_or(0, Archive::revision)
}

/// # Safety
/// `archive` must be a live pointer returned by `cmpct_open`.
#[no_mangle]
pub unsafe extern "C" fn cmpct_entry_count(archive: *const Archive) -> usize {
    archive.as_ref().map_or(0, |archive| archive.entries.len())
}

/// # Safety
/// pointers must be valid for the duration of this call.
#[no_mangle]
pub unsafe extern "C" fn cmpct_entry_info(
    archive: *const Archive,
    index: usize,
    out: *mut CmpctEntryInfo,
) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(out) = out.as_mut() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(entry) = archive.entries.get(index) else {
        return CmpctStatus::Range as c_int;
    };
    *out = CmpctEntryInfo {
        kind: entry.kind,
        _reserved: [0; 3],
        mode: entry.mode,
        size: entry.size,
        mtime_ns: entry.mtime_ns,
    };
    CmpctStatus::Ok as c_int
}

/// Copy an entry path as UTF-8. Passing a null buffer with capacity zero is a size query.
#[no_mangle]
pub unsafe extern "C" fn cmpct_entry_path(
    archive: *const Archive,
    index: usize,
    buffer: *mut c_char,
    capacity: usize,
    out_len: *mut usize,
) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(out_len) = out_len.as_mut() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(entry) = archive.entries.get(index) else {
        return CmpctStatus::Range as c_int;
    };
    let bytes = entry.path.as_bytes();
    *out_len = bytes.len();
    if buffer.is_null() {
        return if capacity == 0 {
            CmpctStatus::Ok as c_int
        } else {
            CmpctStatus::Null as c_int
        };
    }
    if capacity < bytes.len().saturating_add(1) {
        return CmpctStatus::Range as c_int;
    }
    ptr::copy_nonoverlapping(bytes.as_ptr(), buffer.cast::<u8>(), bytes.len());
    *buffer.add(bytes.len()) = 0;
    CmpctStatus::Ok as c_int
}

/// Run complete native structural preflight without extracting payloads.
#[no_mangle]
pub unsafe extern "C" fn cmpct_preflight(archive: *const Archive) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    match archive.preflight() {
        Ok(()) => CmpctStatus::Ok as c_int,
        Err(error) => error_status(&error) as c_int,
    }
}

/// Read one bounded logical range. `out_read` is zero on every failure.
#[no_mangle]
pub unsafe extern "C" fn cmpct_entry_read_range(
    archive: *const Archive,
    index: usize,
    offset: u64,
    buffer: *mut u8,
    length: usize,
    out_read: *mut usize,
) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(out_read) = out_read.as_mut() else {
        return CmpctStatus::Null as c_int;
    };
    *out_read = 0;
    if length > 0 && buffer.is_null() {
        return CmpctStatus::Null as c_int;
    }
    let out = if length == 0 {
        &mut []
    } else {
        std::slice::from_raw_parts_mut(buffer, length)
    };
    match archive.read_range(index, offset, out) {
        Ok(count) => {
            *out_read = count;
            CmpctStatus::Ok as c_int
        }
        Err(error) => error_status(&error) as c_int,
    }
}

/// Open a sequential logical stream. The archive handle must outlive the stream.
#[no_mangle]
pub unsafe extern "C" fn cmpct_entry_stream_open(
    archive: *const Archive,
    index: usize,
    out: *mut *mut CmpctStream,
) -> c_int {
    let Some(archive_ref) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(out) = out.as_mut() else {
        return CmpctStatus::Null as c_int;
    };
    *out = ptr::null_mut();
    let Some(entry) = archive_ref.entries.get(index) else {
        return CmpctStatus::Range as c_int;
    };
    if entry.kind == KIND_DIR {
        return CmpctStatus::Unsupported as c_int;
    }
    let expected_hash = match archive_ref.expected_entry_hash(index) {
        Ok(hash) => hash,
        Err(error) => return error_status(&error) as c_int,
    };
    *out = Box::into_raw(Box::new(CmpctStream {
        archive,
        entry_index: index,
        offset: 0,
        hasher: Sha256::new(),
        expected_hash,
        verified: false,
    }));
    CmpctStatus::Ok as c_int
}

/// Read the next sequential stream bytes; EOF is `CMPCT_OK` with `out_read == 0`.
#[no_mangle]
pub unsafe extern "C" fn cmpct_stream_read(
    stream: *mut CmpctStream,
    buffer: *mut u8,
    capacity: usize,
    out_read: *mut usize,
) -> c_int {
    let Some(stream) = stream.as_mut() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(out_read) = out_read.as_mut() else {
        return CmpctStatus::Null as c_int;
    };
    *out_read = 0;
    if capacity > 0 && buffer.is_null() {
        return CmpctStatus::Null as c_int;
    }
    let Some(archive) = stream.archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    let Some(entry) = archive.entries.get(stream.entry_index) else {
        return CmpctStatus::Range as c_int;
    };
    if stream.offset >= entry.size {
        if !stream.verified {
            if let Some(expected) = stream.expected_hash {
                if stream.hasher.clone().finalize().as_slice() != expected {
                    return CmpctStatus::Format as c_int;
                }
            }
            stream.verified = true;
        }
        return CmpctStatus::Ok as c_int;
    }
    if capacity == 0 {
        return CmpctStatus::Ok as c_int;
    }
    let length = capacity
        .min(MAX_RANGE_OUTPUT_BYTES as usize)
        .min(usize::try_from(entry.size - stream.offset).unwrap_or(usize::MAX));
    let out = std::slice::from_raw_parts_mut(buffer, length);
    match archive.read_range(stream.entry_index, stream.offset, out) {
        Ok(count) => {
            stream.hasher.update(&out[..count]);
            stream.offset += count as u64;
            if stream.offset == entry.size {
                if let Some(expected) = stream.expected_hash {
                    if stream.hasher.clone().finalize().as_slice() != expected {
                        return CmpctStatus::Format as c_int;
                    }
                }
                stream.verified = true;
            }
            *out_read = count;
            CmpctStatus::Ok as c_int
        }
        Err(error) => error_status(&error) as c_int,
    }
}

#[no_mangle]
pub unsafe extern "C" fn cmpct_stream_close(stream: *mut CmpctStream) {
    if !stream.is_null() {
        drop(Box::from_raw(stream));
    }
}

/// Extract with an explicit archive-wide payload-materialization ceiling.
///
/// # Safety
/// `archive` must be live and `destination` must point to a valid NUL-terminated UTF-8 string.
#[no_mangle]
pub unsafe extern "C" fn cmpct_extract_all_bounded(
    archive: *const Archive,
    destination: *const c_char,
    max_materialized_bytes: u64,
) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    if destination.is_null() {
        return CmpctStatus::Null as c_int;
    }
    let destination = match CStr::from_ptr(destination).to_str() {
        Ok(destination) => destination,
        Err(_) => return CmpctStatus::Utf8 as c_int,
    };
    match archive.extract_all_bounded(Path::new(destination), max_materialized_bytes) {
        Ok(()) => CmpctStatus::Ok as c_int,
        Err(error) => error_status(&error) as c_int,
    }
}

/// Extract the complete archive into an absent or empty UTF-8 destination directory.
///
/// # Safety
/// `archive` must be live and `destination` must point to a valid NUL-terminated UTF-8 string.
#[no_mangle]
pub unsafe extern "C" fn cmpct_extract_all(
    archive: *const Archive,
    destination: *const c_char,
) -> c_int {
    let Some(archive) = archive.as_ref() else {
        return CmpctStatus::Null as c_int;
    };
    if destination.is_null() {
        return CmpctStatus::Null as c_int;
    }
    let destination = match CStr::from_ptr(destination).to_str() {
        Ok(destination) => destination,
        Err(_) => return CmpctStatus::Utf8 as c_int,
    };
    match archive.extract_all(Path::new(destination)) {
        Ok(()) => CmpctStatus::Ok as c_int,
        Err(error) => error_status(&error) as c_int,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_path_rejects_aliases_and_traversal() {
        assert_eq!(canonical_path("a\\b").unwrap(), "a/b");
        assert!(canonical_path("../escape").is_err());
        assert!(canonical_path("a//b").is_err());
        assert!(canonical_path("/absolute").is_err());
    }

    #[test]
    fn symlink_target_may_walk_inside_root_but_not_escape_it() {
        assert!(validate_symlink_target("dir/link", "../target").is_ok());
        assert!(validate_symlink_target("link", "../escape").is_err());
        assert!(validate_symlink_target("dir/link", "/absolute").is_err());
    }
}
