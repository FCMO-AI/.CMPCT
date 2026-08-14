from __future__ import annotations

from pathlib import Path


PATH = Path("native/cmpct-core/src/lib.rs")
text = PATH.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one patch target, found {count}: {old[:80]!r}")
    text = text.replace(old, new, 1)


replace_once(
    "//! bounded byte ranges from direct RAW, ordinary Zstd, and raw Deflate members. RAW stays genuinely range-local;\n//! Zstd currently decodes and authenticates the complete direct member before slicing the requested\n//! range. Chunk maps, sparse maps, virtual containers and transactional recovery remain behind\n//! explicit unsupported errors until each representation has its own conformance gate.\n",
    "//! bounded byte ranges from direct RAW/Zstd/Deflate members and revision-24 fixed/CDC chunk maps.\n//! RAW stays genuinely range-local; compressed direct members decode one bounded object, while chunked\n//! ranges decode only intersecting chunks. Sparse maps, virtual containers and transactional recovery\n//! remain behind explicit unsupported errors until each representation has its own conformance gate.\n",
)

replace_once(
    "const STORAGE_BLOB: u64 = 0;\n",
    "const STORAGE_BLOB: u64 = 0;\nconst STORAGE_CHUNKS: u64 = 1;\nconst STORAGE_CDC: u64 = 5;\n",
)

replace_once(
    "#[derive(Debug, Clone, Copy)]\nstruct DirectBlob {\n    index: usize,\n}\n",
    "#[derive(Debug, Clone, Copy)]\nstruct ChunkRef {\n    logical_len: u64,\n    index: usize,\n}\n\n#[derive(Debug, Clone)]\nenum Storage {\n    Unsupported,\n    Direct(usize),\n    Fixed(Vec<ChunkRef>),\n    Cdc(Vec<ChunkRef>),\n}\n",
)

replace_once(
    "    #[serde(skip)]\n    direct_blob: Option<DirectBlob>,\n",
    "    #[serde(skip)]\n    storage: Storage,\n    #[serde(skip)]\n    logical_hash: Option<[u8; 32]>,\n",
)

replace_once(
    "        let entries = parse_entries(&index, blobs.len())?;\n",
    "        let entries = parse_entries(&index, &blobs)?;\n",
)

replace_once("    fn decode_direct_zstd(\n", "    fn decode_zstd_blob(\n")
replace_once("    fn decode_direct_deflate(\n", "    fn decode_deflate_blob(\n")

anchor = "    /// Read a byte range from a supported direct member.\n"
insert = r'''    fn read_blob_range(
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
                let length = usize::try_from(overlap_end - overlap_start)
                    .map_err(|_| CmpctError::Range)?;
                let dst_start = usize::try_from(overlap_start - start)
                    .map_err(|_| CmpctError::Range)?;
                let dst_end = dst_start.checked_add(length).ok_or(CmpctError::Range)?;
                self.read_blob_range(
                    chunk.index,
                    local_start,
                    &mut out[dst_start..dst_end],
                    file,
                )?;
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

'''
replace_once(anchor, insert + anchor)

old_read = r'''    /// Read a byte range from a supported direct member.
    ///
    /// RAW returns only the requested physical bytes after authenticated-index/header cross-checking.
    /// Ordinary Zstd currently decodes and verifies the complete direct member before slicing; that
    /// keeps hostile-input bounds and integrity semantics strict while the native chunk reader is built.
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
        let direct = entry.direct_blob.ok_or(CmpctError::Unsupported)?;
        let blob = self
            .blobs
            .get(direct.index)
            .ok_or_else(|| CmpctError::Schema("direct member references missing blob".into()))?;
        if blob.usize != entry.size {
            return Err(CmpctError::BlobHeader);
        }

        let mut file = self.file.lock().map_err(|_| CmpctError::BlobHeader)?;
        let (payload_pos, expected_hash) = self.checked_blob_layout(blob, &mut file)?;
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
                let decoded =
                    self.decode_direct_zstd(blob, &mut file, payload_pos, &expected_hash)?;
                let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
                let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
                out.copy_from_slice(&decoded[start..end]);
            }
            CODEC_DEFLATE => {
                let decoded =
                    self.decode_direct_deflate(blob, &mut file, payload_pos, &expected_hash)?;
                let start = usize::try_from(start).map_err(|_| CmpctError::Range)?;
                let end = start.checked_add(out.len()).ok_or(CmpctError::Range)?;
                out.copy_from_slice(&decoded[start..end]);
            }
            _ => return Err(CmpctError::Unsupported),
        }
        Ok(out.len())
    }
'''
new_read = r'''    /// Read a byte range from a supported direct or chunked member.
    ///
    /// RAW returns only requested physical bytes after authenticated-index/header cross-checking.
    /// Compressed direct members decode one bounded object; fixed/CDC maps decode only intersecting
    /// chunks. A complete chunked read also verifies the logical whole-file SHA-256 stored in the index.
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
                    if Sha256::digest(out).as_slice() != expected {
                        return Err(CmpctError::MemberHash);
                    }
                }
            }
        }
        Ok(out.len())
    }
'''
replace_once(old_read, new_read)

start = text.index("fn parse_entries(")
end = text.index("\n#[repr(C)]", start)
old_parse = text[start:end]
new_parse = r'''fn parse_hash(value: &Value, row_index: usize) -> Result<Option<[u8; 32]>, CmpctError> {
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
        return Err(CmpctError::Schema(format!("{label} references missing blob")));
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
                CmpctError::Schema(format!("file row {row_index} fixed chunks are not an array"))
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
        if matches!(storage, Storage::Fixed(_) | Storage::Cdc(_)) && logical_hash.is_none() {
            return Err(CmpctError::Schema(format!(
                "file row {i} chunked member is missing logical SHA-256"
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
'''
text = text[:start] + new_parse + text[end:]

replace_once(
    "/// Read a bounded byte range from a supported direct member.\n",
    "/// Read a bounded byte range from a supported direct or chunked member.\n",
)

PATH.write_text(text)
