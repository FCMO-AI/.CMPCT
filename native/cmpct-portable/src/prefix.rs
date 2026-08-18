use crate::format::{
    as_array, as_map, bounded_zstd_decode, digest32, field, number, optional_field, parse_msgpack,
    safe_relpath, sha256, text, tree_digest, tree_hasher_prefix, u64_le, uint, MAX_META_BYTES,
};
use crate::identity::R25Identity;
use crate::{MemberReadStats, PortableEntry, PortableError};
use rmpv::Value;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::sync::Mutex;

const HEADER_SIZE: u64 = 56;
const FOOTER_SIZE: u64 = 56;
const MAX_FILES: usize = 1024;
const MAX_FILE_BYTES: u64 = 8 * 1024 * 1024;
const MAX_MEMBER_READ_AMP: f64 = 8.0;

#[derive(Debug, Clone)]
enum PrefixKind {
    Direct,
    Prefix(usize),
}

#[derive(Debug, Clone)]
struct PrefixRecord {
    kind: PrefixKind,
    usize: u64,
    csize: u64,
    payload_sha: [u8; 32],
    logical_sha: [u8; 32],
    payload_offset: u64,
}

#[derive(Debug)]
pub(crate) struct PrefixArchive {
    identity: R25Identity,
    entries: Vec<PortableEntry>,
    records: Vec<PrefixRecord>,
    tree_sha: [u8; 32],
    tail_authenticated: bool,
    file: Mutex<File>,
}

#[derive(Debug)]
struct AuthMeta {
    value: Value,
    compressed_size: u64,
    meta_sha: [u8; 32],
    tail_offset: Option<u64>,
}

impl PrefixArchive {
    pub(crate) fn open(path: &Path, identity: R25Identity) -> Result<Self, PortableError> {
        if !matches!(
            identity,
            R25Identity::ResearchPrefix | R25Identity::CanonicalPrefix
        ) {
            return Err(PortableError::Format(
                "PrefixGraph reader received a G0-G4 profile identity".into(),
            ));
        }
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        if file_len < HEADER_SIZE + FOOTER_SIZE {
            return Err(PortableError::Format("short PrefixGraph archive".into()));
        }

        let primary = read_primary(&mut file, identity).ok();
        let tail = read_tail(&mut file, file_len, identity).ok();
        if primary.is_none() && tail.is_none() {
            return Err(PortableError::Integrity(
                "no authenticated PrefixGraph metadata copy".into(),
            ));
        }
        if let (Some(left), Some(right)) = (&primary, &tail) {
            if left.meta_sha != right.meta_sha {
                return Err(PortableError::Integrity(
                    "conflicting authenticated PrefixGraph metadata copies".into(),
                ));
            }
        }
        let chosen = primary.as_ref().or(tail.as_ref()).expect("metadata copy");
        let (entries, mut records, tree_sha) = parse_meta(&chosen.value)?;
        let payload_start = HEADER_SIZE
            .checked_add(chosen.compressed_size)
            .ok_or_else(|| PortableError::Limit("PrefixGraph payload offset overflow".into()))?;
        let mut cursor = payload_start;
        for record in &mut records {
            record.payload_offset = cursor;
            cursor = cursor
                .checked_add(record.csize)
                .ok_or_else(|| PortableError::Limit("PrefixGraph payload span overflow".into()))?;
        }
        if let Some(tail) = &tail {
            let expected = tail
                .tail_offset
                .ok_or_else(|| PortableError::Format("missing PrefixGraph tail offset".into()))?;
            if cursor != expected {
                return Err(PortableError::Integrity(
                    "PrefixGraph payload endpoint does not bind authenticated tail".into(),
                ));
            }
        } else if cursor > file_len {
            return Err(PortableError::Format(
                "PrefixGraph payload endpoint exceeds archive".into(),
            ));
        }

        // Footnote: payload hashes are checked lazily when a member is touched. The authenticated metadata
        // fixes every csize/hash and the tail binds the aggregate payload endpoint, so opening a large archive
        // remains metadata-bounded while selective reads still authenticate every context byte they consume.
        Ok(Self {
            identity,
            entries,
            records,
            tree_sha,
            tail_authenticated: tail.is_some(),
            file: Mutex::new(file),
        })
    }

    pub(crate) fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    pub(crate) fn entry_identity(&self, index: usize) -> Result<(u64, [u8; 32]), PortableError> {
        let record = self
            .records
            .get(index)
            .ok_or_else(|| PortableError::Format("PrefixGraph member id out of range".into()))?;
        Ok((record.usize, record.logical_sha))
    }

    pub(crate) fn tail_authenticated(&self) -> bool {
        self.tail_authenticated
    }

    fn payload(&self, index: usize) -> Result<Vec<u8>, PortableError> {
        let record = self
            .records
            .get(index)
            .ok_or_else(|| PortableError::Format("PrefixGraph record id out of range".into()))?;
        let len = usize::try_from(record.csize)
            .map_err(|_| PortableError::Limit("PrefixGraph payload does not fit host".into()))?;
        let mut payload = vec![0u8; len];
        let mut file = self
            .file
            .lock()
            .map_err(|_| PortableError::IoState("PrefixGraph file lock poisoned".into()))?;
        file.seek(SeekFrom::Start(record.payload_offset))?;
        file.read_exact(&mut payload)?;
        if sha256(&payload) != record.payload_sha {
            return Err(PortableError::Integrity(
                "PrefixGraph payload SHA-256 mismatch".into(),
            ));
        }
        Ok(payload)
    }

    fn decode(&self, index: usize) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let record = self
            .records
            .get(index)
            .ok_or_else(|| PortableError::Format("PrefixGraph member id out of range".into()))?;
        let payload = self.payload(index)?;
        let mut decoded_context = record.usize;
        let raw = match record.kind {
            PrefixKind::Direct => bounded_zstd_decode(&payload, record.usize, MAX_FILE_BYTES, None)?,
            PrefixKind::Prefix(base) => {
                let base_record = self.records.get(base).ok_or_else(|| {
                    PortableError::Format("PrefixGraph base id out of range".into())
                })?;
                if !matches!(base_record.kind, PrefixKind::Direct) {
                    return Err(PortableError::Format(
                        "PrefixGraph dependency depth exceeds one".into(),
                    ));
                }
                let base_payload = self.payload(base)?;
                let anchor = bounded_zstd_decode(
                    &base_payload,
                    base_record.usize,
                    MAX_FILE_BYTES,
                    None,
                )?;
                if sha256(&anchor) != base_record.logical_sha {
                    return Err(PortableError::Integrity(
                        "PrefixGraph anchor logical SHA-256 mismatch".into(),
                    ));
                }
                decoded_context = decoded_context
                    .checked_add(base_record.usize)
                    .ok_or_else(|| PortableError::Limit("PrefixGraph context counter overflow".into()))?;
                bounded_zstd_decode(
                    &payload,
                    record.usize,
                    MAX_FILE_BYTES,
                    Some(&anchor),
                )?
            }
        };
        if sha256(&raw) != record.logical_sha {
            return Err(PortableError::Integrity(
                "PrefixGraph logical SHA-256 mismatch".into(),
            ));
        }
        let amplification = decoded_context as f64 / (record.usize.max(1) as f64);
        if amplification > MAX_MEMBER_READ_AMP {
            return Err(PortableError::Limit(format!(
                "PrefixGraph member read amplification {amplification:.3} exceeds {MAX_MEMBER_READ_AMP}x"
            )));
        }
        Ok((
            raw,
            MemberReadStats {
                logical_bytes: record.usize,
                decoded_context_bytes: decoded_context,
                amplification,
                profile: self.identity.profile_name(),
            },
        ))
    }

    pub(crate) fn read_member(
        &self,
        index: usize,
    ) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        self.decode(index)
    }

    pub(crate) fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        let (raw, stats) = self.decode(index)?;
        output.write_all(&raw)?;
        Ok(stats)
    }

    pub(crate) fn verify(&self) -> Result<(), PortableError> {
        let mut order: Vec<usize> = (0..self.entries.len()).collect();
        order.sort_by(|left, right| self.entries[*left].path.cmp(&self.entries[*right].path));
        let mut tree = Sha256::new();
        for index in order {
            let entry = &self.entries[index];
            tree_hasher_prefix(&mut tree, &entry.path, entry.size);
            let (raw, _) = self.decode(index)?;
            tree.update(&raw);
        }
        let got: [u8; 32] = tree.finalize().into();
        if got != self.tree_sha {
            return Err(PortableError::Integrity(
                "PrefixGraph streamed tree SHA-256 mismatch".into(),
            ));
        }
        Ok(())
    }
}

fn read_primary(file: &mut File, identity: R25Identity) -> Result<AuthMeta, PortableError> {
    file.seek(SeekFrom::Start(0))?;
    let mut header = [0u8; HEADER_SIZE as usize];
    file.read_exact(&mut header)?;
    if &header[0..8] != identity.magic() {
        return Err(PortableError::Format("PrefixGraph profile magic mismatch".into()));
    }
    let compressed_size = u64_le(&header[8..16])?;
    let raw_size = u64_le(&header[16..24])?;
    if compressed_size > MAX_META_BYTES || raw_size > MAX_META_BYTES {
        return Err(PortableError::Limit(
            "PrefixGraph metadata declaration exceeds policy".into(),
        ));
    }
    let expected: [u8; 32] = header[24..56]
        .try_into()
        .map_err(|_| PortableError::Format("PrefixGraph metadata SHA field".into()))?;
    let mut compressed = vec![0u8; compressed_size as usize];
    file.read_exact(&mut compressed)?;
    let raw = bounded_zstd_decode(&compressed, raw_size, MAX_META_BYTES, None)?;
    if sha256(&raw) != expected {
        return Err(PortableError::Integrity(
            "PrefixGraph primary metadata authentication".into(),
        ));
    }
    Ok(AuthMeta {
        value: parse_msgpack(&raw)?,
        compressed_size,
        meta_sha: expected,
        tail_offset: None,
    })
}

fn read_tail(
    file: &mut File,
    file_len: u64,
    identity: R25Identity,
) -> Result<AuthMeta, PortableError> {
    if file_len < FOOTER_SIZE {
        return Err(PortableError::Format("short PrefixGraph tail".into()));
    }
    file.seek(SeekFrom::Start(file_len - FOOTER_SIZE))?;
    let mut footer = [0u8; FOOTER_SIZE as usize];
    file.read_exact(&mut footer)?;
    if &footer[0..8] != identity.tail() {
        return Err(PortableError::Format("PrefixGraph tail magic".into()));
    }
    let compressed_size = u64_le(&footer[8..16])?;
    let raw_size = u64_le(&footer[16..24])?;
    if compressed_size > MAX_META_BYTES || raw_size > MAX_META_BYTES {
        return Err(PortableError::Limit(
            "PrefixGraph tail metadata declaration exceeds policy".into(),
        ));
    }
    let expected: [u8; 32] = footer[24..56]
        .try_into()
        .map_err(|_| PortableError::Format("PrefixGraph tail SHA field".into()))?;
    let tail_offset = file_len
        .checked_sub(FOOTER_SIZE)
        .and_then(|value| value.checked_sub(compressed_size))
        .ok_or_else(|| PortableError::Format("PrefixGraph tail metadata offset".into()))?;
    if tail_offset < HEADER_SIZE {
        return Err(PortableError::Format("PrefixGraph tail overlaps header".into()));
    }
    file.seek(SeekFrom::Start(tail_offset))?;
    let mut compressed = vec![0u8; compressed_size as usize];
    file.read_exact(&mut compressed)?;
    let raw = bounded_zstd_decode(&compressed, raw_size, MAX_META_BYTES, None)?;
    if sha256(&raw) != expected {
        return Err(PortableError::Integrity(
            "PrefixGraph tail metadata authentication".into(),
        ));
    }
    Ok(AuthMeta {
        value: parse_msgpack(&raw)?,
        compressed_size,
        meta_sha: expected,
        tail_offset: Some(tail_offset),
    })
}

fn parse_meta(value: &Value) -> Result<(Vec<PortableEntry>, Vec<PrefixRecord>, [u8; 32]), PortableError> {
    let map = as_map(value, "PrefixGraph metadata")?;
    if uint(field(map, "v")?, "PrefixGraph metadata revision", 1)? != 1
        || text(field(map, "engine")?, "PrefixGraph engine")? != "PrefixGraph-depth1-v1"
    {
        return Err(PortableError::Format(
            "unsupported PrefixGraph metadata".into(),
        ));
    }
    let tree_sha = tree_digest(text(field(map, "tree_sha256")?, "PrefixGraph tree SHA")?)?;
    let files = as_array(field(map, "files")?, "PrefixGraph files")?;
    let rows = as_array(field(map, "records")?, "PrefixGraph records")?;
    if files.is_empty() || files.len() > MAX_FILES || files.len() != rows.len() {
        return Err(PortableError::Format(
            "PrefixGraph file/record count declaration".into(),
        ));
    }
    let max_depth = optional_field(map, "max_dependency_depth")
        .map(|value| uint(value, "PrefixGraph dependency depth", 1))
        .transpose()?
        .unwrap_or(1);
    if max_depth > 1 {
        return Err(PortableError::Limit(
            "PrefixGraph dependency depth exceeds one".into(),
        ));
    }
    if let Some(value) = optional_field(map, "max_file_bytes") {
        if uint(value, "PrefixGraph max_file_bytes", MAX_FILE_BYTES)? > MAX_FILE_BYTES {
            return Err(PortableError::Limit(
                "PrefixGraph file-size declaration exceeds policy".into(),
            ));
        }
    }
    if let Some(value) = optional_field(map, "max_member_read_amplification") {
        if number(value, "PrefixGraph read amplification")? > MAX_MEMBER_READ_AMP {
            return Err(PortableError::Limit(
                "PrefixGraph read-amplification declaration exceeds policy".into(),
            ));
        }
    }

    let mut seen = HashSet::with_capacity(files.len());
    let mut entries = Vec::with_capacity(files.len());
    let mut records = Vec::with_capacity(rows.len());
    for (index, (file_value, row_value)) in files.iter().zip(rows).enumerate() {
        let rel = text(file_value, "PrefixGraph path")?;
        safe_relpath(rel)?;
        if !seen.insert(rel.to_owned()) {
            return Err(PortableError::Format(
                "duplicate PrefixGraph logical path".into(),
            ));
        }
        let row = as_array(row_value, "PrefixGraph record")?;
        if row.len() != 6 {
            return Err(PortableError::Format("malformed PrefixGraph record".into()));
        }
        let kind = text(&row[0], "PrefixGraph record kind")?;
        let base = row[1]
            .as_i64()
            .ok_or_else(|| PortableError::Format("PrefixGraph base id".into()))?;
        let usize = uint(&row[2], "PrefixGraph logical size", MAX_FILE_BYTES)?;
        let csize = uint(
            &row[3],
            "PrefixGraph payload size",
            MAX_FILE_BYTES + 1024 * 1024,
        )?;
        let payload_sha = digest32(&row[4], "PrefixGraph payload digest")?;
        let logical_sha = digest32(&row[5], "PrefixGraph logical digest")?;
        let kind = match kind {
            "direct" if base == -1 => PrefixKind::Direct,
            "prefix" if base >= 0 => {
                let base = usize::try_from(base)
                    .map_err(|_| PortableError::Format("PrefixGraph base id".into()))?;
                if base >= rows.len() || base == index {
                    return Err(PortableError::Format(
                        "PrefixGraph base id out of range".into(),
                    ));
                }
                PrefixKind::Prefix(base)
            }
            _ => {
                return Err(PortableError::Format(
                    "unknown PrefixGraph record kind/base shape".into(),
                ));
            }
        };
        entries.push(PortableEntry {
            path: rel.to_owned(),
            size: usize,
            kind: 0,
            mode: 0o644,
            mtime_ns: 0,
        });
        records.push(PrefixRecord {
            kind,
            usize,
            csize,
            payload_sha,
            logical_sha,
            payload_offset: 0,
        });
    }

    for (index, record) in records.iter().enumerate() {
        if let PrefixKind::Prefix(base) = record.kind {
            let anchor = &records[base];
            if !matches!(anchor.kind, PrefixKind::Direct) {
                return Err(PortableError::Format(
                    "PrefixGraph dependency depth exceeds one".into(),
                ));
            }
            let amp = (record.usize + anchor.usize) as f64 / record.usize.max(1) as f64;
            if amp > MAX_MEMBER_READ_AMP {
                return Err(PortableError::Limit(format!(
                    "PrefixGraph record {index} amplification {amp:.3} exceeds {MAX_MEMBER_READ_AMP}x"
                )));
            }
        }
    }
    Ok((entries, records, tree_sha))
}
