//! Memory-safe read-only CMPCT core.
//!
//! The native slice authenticates the primary index, enumerates its logical tree, and can read
//! bounded byte ranges from direct RAW/Zstd/Deflate/Zstd-dictionary members, revision-24 fixed/CDC chunk maps, and
//! sparse extents. RAW stays genuinely range-local; compressed direct members decode one bounded
//! object, while chunked/sparse ranges decode only intersecting stored data. Virtual containers and
//! transactional recovery remain behind explicit unsupported errors until each representation has its
//! own conformance gate.

use flate2::read::DeflateDecoder;
use rmpv::Value;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::ffi::CStr;
use std::fs::File;
use std::io::{Cursor, Read, Seek, SeekFrom};
use std::os::raw::{c_char, c_int};
use std::path::Path;
use std::ptr;
use std::sync::Mutex;
use thiserror::Error;

const MAGIC: &[u8; 8] = b"CMPCT24\0";
const BLOB_MAGIC: &[u8; 4] = b"CMA4";
const VERSION: u16 = 24;
const HEADER_SIZE: usize = 68;
const BLOB_HEADER_SIZE: usize = 64;
const CODEC_RAW: u8 = 0;
const CODEC_ZSTD: u8 = 1;
const CODEC_ZSTDDICT: u8 = 3;
const CODEC_DEFLATE: u8 = 4;
const STORAGE_BLOB: u64 = 0;
const STORAGE_CHUNKS: u64 = 1;
const STORAGE_SPARSE: u64 = 3;
const STORAGE_CDC: u64 = 5;
const MAX_INDEX_BYTES: u64 = 256 * 1024 * 1024;
const MAX_DIRECT_DECODE_BYTES: u64 = 256 * 1024 * 1024;
const MAX_FILES: usize = 4_000_000;
const MAX_BLOBS: usize = 4_000_000;
const MAX_PATH_BYTES: usize = 1024 * 1024;

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
    #[error("member exceeds native direct-decode resource limit")]
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
    #[error("decoded member SHA-256 does not match its physical blob identity")]
    MemberHash,
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
    Sparse(Vec<SparseExtent>),
    Cdc(Vec<ChunkRef>),
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

impl Archive {
    /// Open only enough of the archive to authenticate and decode the primary index.
    ///
    /// Footnote: the Python reader can recover from a damaged primary index through the tail/journal
    /// chain. Native recovery will be added as a separate conformance milestone; this initial handler
    /// refuses a damaged primary rather than silently implementing a different recovery policy.
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

        let compressed_len = le_u64(&header[12..20]);
        let uncompressed_len = le_u64(&header[20..28]);
        let data_span = le_u64(&header[28..36]);
        if compressed_len > MAX_INDEX_BYTES || uncompressed_len > MAX_INDEX_BYTES {
            return Err(CmpctError::IndexLimit);
        }
        let data_base = (HEADER_SIZE as u64)
            .checked_add(compressed_len)
            .ok_or(CmpctError::IndexLimit)?;
        let data_end = data_base
            .checked_add(data_span)
            .ok_or(CmpctError::IndexLimit)?;
        if data_base > file_len || data_end > file_len {
            return Err(CmpctError::Truncated);
        }

        let mut compressed = vec![0u8; compressed_len as usize];
        file.read_exact(&mut compressed)?;
        let decoder = zstd::stream::read::Decoder::new(Cursor::new(compressed))?;
        let mut limited = decoder.take(uncompressed_len.saturating_add(1));
        let mut index_bytes = Vec::with_capacity(uncompressed_len as usize);
        limited.read_to_end(&mut index_bytes)?;
        if index_bytes.len() as u64 != uncompressed_len {
            return Err(CmpctError::IndexLength);
        }
        let expected_hash = &header[36..68];
        if Sha256::digest(&index_bytes).as_slice() != expected_hash {
            return Err(CmpctError::IndexHash);
        }

        let mut cursor = Cursor::new(index_bytes.as_slice());
        let index = rmpv::decode::read_value(&mut cursor)
            .map_err(|e| CmpctError::MessagePack(e.to_string()))?;
        if cursor.position() != index_bytes.len() as u64 {
            return Err(CmpctError::Schema(
                "trailing bytes after root index object".into(),
            ));
        }
        let blobs = parse_blobs(&index, data_span)?;
        let dict_blob = parse_dictionary_blob(&index, &blobs)?;
        let entries = parse_entries(&index, &blobs)?;
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
            .and_then(|v| v.checked_add(blob.meta_len as u64))
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
        let physical_usize = le_u64(&header[8..16]);
        let physical_csize = le_u64(&header[16..24]);
        let physical_meta_len = le_u32(&header[24..28]);
        if &header[0..4] != BLOB_MAGIC
            || physical_codec != blob.codec
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

        // Footnote: compressed direct-range reads are correctness-first at this milestone. Zstd is
        // not independently seekable here, so the native handler decodes exactly one direct member,
        // caps the allocation before decoding, authenticates the complete bytes, then returns the
        // requested slice. Large files are normally chunked by the encoder and use range-local maps.
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

        // Footnote: dict_blob is authenticated index metadata, but the dictionary bytes are a second
        // archive-controlled dependency. Authenticate that blob first, then decode one bounded codec-3
        // member and authenticate its complete content before exposing even a partial range.
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

        // Footnote: revision 24 codec 4 is raw RFC 1951 Deflate, without zlib/gzip framing.
        // Decode one bounded direct member completely and authenticate its SHA-256 before any slice
        // crosses the C ABI, matching the correctness-first policy used for direct Zstd.
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
        let (payload_pos, expected_hash) = self.checked_blob_layout(blob, file)?;
        match blob.codec {
            CODEC_RAW => {
                if blob.csize != blob.usize {
                    return Err(CmpctError::BlobHeader);
                }
                let read_pos = payload_pos.checked_add(start).ok_or(CmpctError::Range)?;
                file.seek(SeekFrom::Start(read_pos))?;
                file.read_exact(out)?;
            }
            CODEC_ZSTD => {
                let decoded = self.decode_zstd_blob(blob, file, payload_pos, &expected_hash)?;
                let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
                let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
                out.copy_from_slice(&decoded[start..end]);
            }
            CODEC_ZSTDDICT => {
                let decoded =
                    self.decode_zstd_dictionary_blob(blob, file, payload_pos, &expected_hash)?;
                let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
                let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
                out.copy_from_slice(&decoded[start..end]);
            }
            CODEC_DEFLATE => {
                let decoded = self.decode_deflate_blob(blob, file, payload_pos, &expected_hash)?;
                let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
                let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
                out.copy_from_slice(&decoded[start..end]);
            }
            _ => return Err(CmpctError::Unsupported),
        }
        Ok(())
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

        // Footnote: the chunk table is authenticated index data. Walk only until the requested end,
        // and decode only chunks that overlap the caller's range. This is the revision-24 mechanism
        // that prevents a 4 KiB read from inflating a multi-gigabyte compressed member.
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

        // Footnote: holes are semantic zeros, not stored payload. Leave them zero-filled and decode
        // only physical chunks belonging to data extents that intersect the requested range. This is
        // what keeps native browsing of sparse VM/disk images proportional to touched data rather than
        // to the logical file size.
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

    /// Read a byte range from a supported direct, chunked, or sparse member.
    ///
    /// RAW returns only requested physical bytes after authenticated-index/header cross-checking.
    /// Compressed direct members decode one bounded object; fixed/CDC and sparse maps decode only
    /// intersecting stored chunks. A complete logical-map read also verifies the whole-file SHA-256.
    pub fn read_range(
        &self,
        entry_index: usize,
        start: u64,
        out: &mut [u8],
    ) -> Result<usize, CmpctError> {
        let entry = self.entries.get(entry_index).ok_or(CmpctError::Range)?;
        let end = start
            .checked_add(out.len() as u64)
            .ok_or(CmpctError::Range)?;
        if end > entry.size {
            return Err(CmpctError::Range);
        }
        if out.is_empty() {
            return Ok(0);
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
        }
        Ok(out.len())
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
        .find_map(|(k, v)| (k.as_str() == Some(key)).then_some(v))
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
    for (i, value) in rows.iter().enumerate() {
        let row = value
            .as_array()
            .ok_or_else(|| CmpctError::Schema(format!("blob row {i} is not an array")))?;
        if row.len() < 5 {
            return Err(CmpctError::Schema(format!("blob row {i} is too short")));
        }
        let offset = row[0]
            .as_u64()
            .ok_or_else(|| CmpctError::Schema(format!("blob row {i} has invalid offset")))?;
        let usize = row[1]
            .as_u64()
            .ok_or_else(|| CmpctError::Schema(format!("blob row {i} has invalid size")))?;
        let csize = row[2].as_u64().ok_or_else(|| {
            CmpctError::Schema(format!("blob row {i} has invalid compressed size"))
        })?;
        let codec = row[3]
            .as_u64()
            .filter(|v| *v <= u8::MAX as u64)
            .ok_or_else(|| CmpctError::Schema(format!("blob row {i} has invalid codec")))?
            as u8;
        let meta_len = row[4]
            .as_u64()
            .filter(|v| *v <= u32::MAX as u64)
            .ok_or_else(|| {
                CmpctError::Schema(format!("blob row {i} has invalid metadata length"))
            })? as u32;
        let end = offset
            .checked_add(BLOB_HEADER_SIZE as u64)
            .and_then(|v| v.checked_add(meta_len as u64))
            .and_then(|v| v.checked_add(csize))
            .ok_or_else(|| CmpctError::Schema(format!("blob row {i} overflows archive offsets")))?;
        if end > data_span {
            return Err(CmpctError::Schema(format!(
                "blob row {i} extends past base data span"
            )));
        }
        blobs.push(Blob {
            offset,
            usize,
            csize,
            codec,
            meta_len,
        });
    }
    Ok(blobs)
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
    let index = storage_blob_index(value, blobs.len(), "dictionary blob")?;
    Ok(Some(index))
}

fn parse_hash(value: &Value, row_index: usize) -> Result<Option<[u8; 32]>, CmpctError> {
    match value {
        Value::Nil => Ok(None),
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

fn parse_storage(
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
            if storage.len() < 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} direct storage is too short"
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
            if storage.len() < 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} fixed chunk storage is too short"
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
        STORAGE_SPARSE => {
            if storage.len() < 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} sparse storage is too short"
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
                let logical_len = extent[1].as_u64().filter(|v| *v > 0).ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} has invalid length"
                    ))
                })?;
                let extent_end = offset.checked_add(logical_len).ok_or_else(|| {
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse extent {extent_index} overflows logical offsets"
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
                    CmpctError::Schema(format!(
                        "file row {row_index} sparse blob-reference count overflows"
                    ))
                })?;
                if total_refs > MAX_BLOBS {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} sparse blob-reference count exceeds native limit"
                    )));
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
                        CmpctError::Schema(format!(
                            "file row {row_index} sparse extent {extent_index} stored bytes overflow"
                        ))
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
        STORAGE_CDC => {
            if storage.len() < 2 {
                return Err(CmpctError::Schema(format!(
                    "file row {row_index} CDC storage is too short"
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
                if pair.len() < 2 {
                    return Err(CmpctError::Schema(format!(
                        "file row {row_index} CDC chunk {chunk_index} is too short"
                    )));
                }
                let logical_len = pair[0].as_u64().ok_or_else(|| {
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
    for (i, value) in files.iter().enumerate() {
        let row = value
            .as_array()
            .ok_or_else(|| CmpctError::Schema(format!("file row {i} is not an array")))?;
        if row.len() < 7 {
            return Err(CmpctError::Schema(format!("file row {i} is too short")));
        }
        let path = row[0]
            .as_str()
            .ok_or_else(|| CmpctError::Schema(format!("file row {i} path is not UTF-8 text")))?;
        let key = canonical_path(path)?;
        if !seen.insert(key) {
            return Err(CmpctError::Path(path.into()));
        }
        let kind = row[1]
            .as_u64()
            .filter(|v| *v <= 3)
            .ok_or_else(|| CmpctError::Schema(format!("file row {i} has invalid kind")))?
            as u8;
        let mode = row[2]
            .as_u64()
            .filter(|v| *v <= u32::MAX as u64)
            .ok_or_else(|| CmpctError::Schema(format!("file row {i} has invalid mode")))?
            as u32;
        let mtime_ns = row[3]
            .as_i64()
            .ok_or_else(|| CmpctError::Schema(format!("file row {i} has invalid mtime")))?;
        let size = row[4]
            .as_u64()
            .ok_or_else(|| CmpctError::Schema(format!("file row {i} has invalid size")))?;
        let logical_hash = parse_hash(&row[5], i)?;
        let storage = parse_storage(&row[6], size, blobs, i)?;
        if matches!(
            storage,
            Storage::Fixed(_) | Storage::Sparse(_) | Storage::Cdc(_)
        ) && logical_hash.is_none()
        {
            return Err(CmpctError::Schema(format!(
                "file row {i} logical-map member is missing SHA-256"
            )));
        }
        entries.push(Entry {
            path: path.to_owned(),
            kind,
            mode,
            mtime_ns,
            size,
            storage,
            logical_hash,
        });
    }
    Ok(entries)
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

fn error_status(error: &CmpctError) -> CmpctStatus {
    match error {
        CmpctError::Io(_) | CmpctError::Truncated => CmpctStatus::Io,
        CmpctError::IndexLimit | CmpctError::MemberLimit => CmpctStatus::Limit,
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
        Archive::open(Path::new(path)).map_err(|e| error_status(&e))
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
    archive.as_ref().map_or(0, |a| a.entries.len())
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

/// Copy an entry path as UTF-8. `out_len` receives the byte length excluding the trailing NUL.
///
/// Passing a null `buffer` with capacity zero is a supported size-query operation.
///
/// # Safety
/// pointers must be valid according to their documented roles for the duration of this call.
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

/// Read a bounded byte range from a supported direct, chunked, or sparse member.
///
/// `out_read` receives the number of bytes copied. A zero-length read may pass a null buffer.
/// Representations not yet implemented by the native core return `CmpctStatus::Unsupported`.
///
/// # Safety
/// `archive` must be live; `buffer` must be writable for `length` bytes when `length > 0`; and
/// `out_read` must be writable for one `usize`.
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
        Ok(n) => {
            *out_read = n;
            CmpctStatus::Ok as c_int
        }
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
}
