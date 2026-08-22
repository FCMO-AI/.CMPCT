use crate::format::{
    as_array, bounded_zstd_decode, digest32, parse_msgpack, safe_relpath, sha256, text, uint,
};
use crate::manifest::{FILESYSTEM_MANIFEST, FsKind, FsManifest};
use crate::{MemberReadStats, PortableEntry, PortableError};
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::Path;
use std::sync::Mutex;

const MAGIC: &[u8; 8] = b"C25LG12\0";
const TAIL_MAGIC: &[u8; 8] = b"C25L12T\0";
const PROFILE: &str = "cmpct-r25-logs-inverse-v1";
const LEVEL: u64 = 12;
const MAX_META_RAW: u64 = 2 * 1024 * 1024;
const MAX_META_COMP: u64 = 2 * 1024 * 1024;
const MAX_PACKS: u64 = 64;
const MAX_FILES: usize = 4096;
const MAX_PATH_BYTES: usize = 4096;
const MAX_DECODE_UNIT: u64 = 8 * 1024 * 1024;
const MAX_MEMBER_READ_AMP: f64 = 8.0;
const HEADER_SIZE: u64 = 8 + 8 + 8 + 4 + 32;
const FOOTER_SIZE: u64 = HEADER_SIZE;
const PACK_HEADER_SIZE: u64 = 1 + 8 + 8 + 4 + 32;
const CODEC_RAW: u8 = 0;
const CODEC_ZSTD: u8 = 1;

#[derive(Debug, Clone)]
enum Storage {
    Pack {
        compressed: bool,
        pack: usize,
        offset: u64,
        length: u64,
    },
    Derive {
        source: usize,
        codec: String,
    },
}

#[derive(Debug, Clone)]
struct LogicalFile {
    path: String,
    size: u64,
    sha256: [u8; 32],
    storage: Storage,
}

#[derive(Debug, Clone)]
struct PackDesc {
    offset: u64,
    codec: u8,
    usize: u64,
    csize: u64,
    crc32: u32,
    sha256: [u8; 32],
}

/// Hidden pre-dispatch reader for the bounded recoverable logs inverse profile.
///
/// This is public only so cross-language preparity can exercise the exact implementation. Production identity,
/// ABI and Android dispatch deliberately do not recognize this profile until every native codec, hostile-input
/// test and platform gate is complete.
#[derive(Debug)]
pub struct LogsInverseArchive {
    entries: Vec<PortableEntry>,
    identities: Vec<(u64, [u8; 32])>,
    files: Vec<LogicalFile>,
    packs: Vec<PackDesc>,
    manifest_index: usize,
    recovery_route: &'static str,
    file: Mutex<File>,
}

impl LogsInverseArchive {
    pub fn open(path: &Path) -> Result<Self, PortableError> {
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        if file_len < HEADER_SIZE + FOOTER_SIZE {
            return Err(PortableError::Format("short logs inverse archive".into()));
        }

        let (meta_raw, meta_csize, pack_count, recovery_route) =
            read_authenticated_metadata(&mut file, file_len)?;
        let files = parse_metadata(&meta_raw)?;
        let packs = scan_packs(&mut file, file_len, meta_csize, pack_count)?;

        let mut entries = Vec::with_capacity(files.len());
        let mut identities = Vec::with_capacity(files.len());
        let mut manifest_index = None;
        for (index, logical) in files.iter().enumerate() {
            if logical.path == FILESYSTEM_MANIFEST {
                manifest_index = Some(index);
            }
            entries.push(PortableEntry {
                path: logical.path.clone(),
                size: logical.size,
                kind: 0,
                mode: 0,
                mtime_ns: 0,
            });
            identities.push((logical.size, logical.sha256));
        }
        let manifest_index = manifest_index.ok_or_else(|| {
            PortableError::Integrity("logs inverse archive is missing filesystem manifest".into())
        })?;

        let archive = Self {
            entries,
            identities,
            files,
            packs,
            manifest_index,
            recovery_route,
            file: Mutex::new(file),
        };
        archive.validate_filesystem_manifest()?;
        Ok(archive)
    }

    pub fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    pub fn entry_identity(&self, index: usize) -> Result<(u64, [u8; 32]), PortableError> {
        self.identities
            .get(index)
            .copied()
            .ok_or_else(|| PortableError::Format("logs inverse member id out of range".into()))
    }

    pub fn recovery_route(&self) -> &'static str {
        self.recovery_route
    }

    pub fn tail_authenticated(&self) -> bool {
        true
    }

    fn validate_filesystem_manifest(&self) -> Result<(), PortableError> {
        let (manifest_raw, _) = self.read_member(self.manifest_index)?;
        let manifest = FsManifest::parse(&manifest_raw, &self.entries)?;
        let mut regular = HashMap::new();
        for entry in manifest.entries() {
            if let FsKind::File { size, sha256 } = &entry.kind {
                regular.insert(entry.path.clone(), (*size, *sha256));
            }
        }
        let expected = self
            .files
            .iter()
            .enumerate()
            .filter(|(index, _)| *index != self.manifest_index)
            .map(|(_, file)| (file.path.clone(), (file.size, file.sha256)))
            .collect::<HashMap<_, _>>();
        if regular != expected {
            return Err(PortableError::Integrity(
                "logs inverse filesystem/content identity mismatch".into(),
            ));
        }
        Ok(())
    }

    fn read_pack(&self, index: usize) -> Result<Vec<u8>, PortableError> {
        let desc = self
            .packs
            .get(index)
            .ok_or_else(|| PortableError::Format("logs inverse pack id out of range".into()))?;
        let size = usize::try_from(desc.csize)
            .map_err(|_| PortableError::Limit("logs inverse pack size does not fit host".into()))?;
        let mut payload = vec![0u8; size];
        let mut file = self
            .file
            .lock()
            .map_err(|_| PortableError::IoState("logs inverse file lock poisoned".into()))?;
        file.seek(SeekFrom::Start(desc.offset))?;
        file.read_exact(&mut payload)?;
        drop(file);

        let raw = match desc.codec {
            CODEC_RAW => payload,
            CODEC_ZSTD => bounded_zstd_decode(&payload, desc.usize, MAX_DECODE_UNIT, None)?,
            _ => return Err(PortableError::Format("unknown logs inverse pack codec".into())),
        };
        if raw.len() as u64 != desc.usize
            || crc32fast::hash(&raw) != desc.crc32
            || sha256(&raw) != desc.sha256
        {
            return Err(PortableError::Integrity(
                "logs inverse pack identity mismatch".into(),
            ));
        }
        Ok(raw)
    }

    fn decode_derived(
        &self,
        codec: &str,
        source: &[u8],
        expected_size: u64,
    ) -> Result<Vec<u8>, PortableError> {
        // Zstd is deliberately the first native inverse codec because the writer's deterministic edge ranking
        // prefers it. Gzip/XZ remain fail-closed until bounded native decoders are added and tested; preparity
        // must not silently claim coverage it does not have.
        if codec != "zstd" {
            return Err(PortableError::Unsupported(format!(
                "logs inverse native codec preparity incomplete: {codec}"
            )));
        }
        bounded_zstd_decode(source, expected_size, MAX_DECODE_UNIT, None)
    }

    fn restore_member(
        &self,
        index: usize,
        cache: &mut HashMap<usize, (Vec<u8>, u64)>,
        active: &mut HashSet<usize>,
    ) -> Result<(Vec<u8>, u64), PortableError> {
        if let Some(value) = cache.get(&index) {
            return Ok(value.clone());
        }
        if index >= self.files.len() || !active.insert(index) {
            return Err(PortableError::Format(
                "logs inverse dependency cycle or member id error".into(),
            ));
        }
        let logical = &self.files[index];
        let result = match &logical.storage {
            Storage::Pack {
                compressed,
                pack,
                offset,
                length,
            } => {
                let raw = self.read_pack(*pack)?;
                let end = offset
                    .checked_add(*length)
                    .ok_or_else(|| PortableError::Limit("logs inverse slice overflow".into()))?;
                if *length != logical.size || end > raw.len() as u64 {
                    active.remove(&index);
                    return Err(PortableError::Format("logs inverse slice bounds".into()));
                }
                let start = usize::try_from(*offset).map_err(|_| {
                    PortableError::Limit("logs inverse slice offset does not fit host".into())
                })?;
                let end = usize::try_from(end).map_err(|_| {
                    PortableError::Limit("logs inverse slice end does not fit host".into())
                })?;
                let value = raw[start..end].to_vec();
                let context = if *compressed {
                    raw.len() as u64
                } else {
                    *length
                };
                (value, context)
            }
            Storage::Derive { source, codec } => {
                if *source == index {
                    active.remove(&index);
                    return Err(PortableError::Format("logs inverse self dependency".into()));
                }
                let (source_raw, source_context) = self.restore_member(*source, cache, active)?;
                let value = self.decode_derived(codec, &source_raw, logical.size)?;
                let context = source_context
                    .checked_add(value.len() as u64)
                    .ok_or_else(|| PortableError::Limit("logs inverse context overflow".into()))?;
                (value, context)
            }
        };
        if result.0.len() as u64 != logical.size || sha256(&result.0) != logical.sha256 {
            active.remove(&index);
            return Err(PortableError::Integrity(
                "logs inverse logical member identity mismatch".into(),
            ));
        }
        active.remove(&index);
        cache.insert(index, result.clone());
        Ok(result)
    }

    pub fn read_member(&self, index: usize) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let logical = self
            .files
            .get(index)
            .ok_or_else(|| PortableError::Format("logs inverse member id out of range".into()))?;
        let mut cache = HashMap::new();
        let mut active = HashSet::new();
        let (raw, context) = self.restore_member(index, &mut cache, &mut active)?;
        if context > MAX_DECODE_UNIT {
            return Err(PortableError::Limit(
                "logs inverse member decoded context exceeds policy".into(),
            ));
        }
        let amplification = context as f64 / logical.size.max(1) as f64;
        if amplification > MAX_MEMBER_READ_AMP {
            return Err(PortableError::Limit(
                "logs inverse member amplification exceeds policy".into(),
            ));
        }
        Ok((
            raw,
            MemberReadStats {
                logical_bytes: logical.size,
                decoded_context_bytes: context,
                amplification,
                profile: "logs-inverse-r25-preparity",
            },
        ))
    }

    pub fn verify(&self) -> Result<(), PortableError> {
        for index in 0..self.files.len() {
            self.read_member(index)?;
        }
        self.validate_filesystem_manifest()?;
        Ok(())
    }
}

fn read_authenticated_metadata(
    file: &mut File,
    file_len: u64,
) -> Result<(Vec<u8>, u64, u64, &'static str), PortableError> {
    let primary_error = match read_primary_metadata(file) {
        Ok((meta, csize, packs)) => return Ok((meta, csize, packs, "primary")),
        Err(error) => error,
    };
    match read_tail_metadata(file, file_len) {
        Ok((meta, csize, packs)) => Ok((meta, csize, packs, "tail")),
        Err(tail_error) => Err(PortableError::Integrity(format!(
            "no authenticated logs inverse metadata: primary={primary_error}; tail={tail_error}"
        ))),
    }
}

fn read_primary_metadata(file: &mut File) -> Result<(Vec<u8>, u64, u64), PortableError> {
    file.seek(SeekFrom::Start(0))?;
    let mut header = [0u8; HEADER_SIZE as usize];
    file.read_exact(&mut header)?;
    if &header[..8] != MAGIC {
        return Err(PortableError::Format(
            "bad logs inverse primary magic".into(),
        ));
    }
    let csize = le_u64(&header[8..16])?;
    let raw_size = le_u64(&header[16..24])?;
    let pack_count = u32::from_le_bytes(header[24..28].try_into().expect("fixed header")) as u64;
    let expected_sha: [u8; 32] = header[28..60].try_into().expect("fixed header");
    read_metadata_body(file, csize, raw_size, pack_count, expected_sha)
}

fn read_tail_metadata(
    file: &mut File,
    file_len: u64,
) -> Result<(Vec<u8>, u64, u64), PortableError> {
    file.seek(SeekFrom::Start(file_len - FOOTER_SIZE))?;
    let mut footer = [0u8; FOOTER_SIZE as usize];
    file.read_exact(&mut footer)?;
    if &footer[..8] != TAIL_MAGIC {
        return Err(PortableError::Format("bad logs inverse tail magic".into()));
    }
    let csize = le_u64(&footer[8..16])?;
    let raw_size = le_u64(&footer[16..24])?;
    let pack_count = u32::from_le_bytes(footer[24..28].try_into().expect("fixed footer")) as u64;
    let expected_sha: [u8; 32] = footer[28..60].try_into().expect("fixed footer");
    if csize > MAX_META_COMP || raw_size > MAX_META_RAW || pack_count > MAX_PACKS {
        return Err(PortableError::Limit(
            "logs inverse tail metadata bounds".into(),
        ));
    }
    let offset = file_len
        .checked_sub(FOOTER_SIZE + csize)
        .ok_or_else(|| PortableError::Format("logs inverse tail metadata overlap".into()))?;
    if offset < HEADER_SIZE + csize {
        return Err(PortableError::Format(
            "logs inverse tail metadata overlaps primary".into(),
        ));
    }
    file.seek(SeekFrom::Start(offset))?;
    let size = usize::try_from(csize)
        .map_err(|_| PortableError::Limit("logs inverse metadata size does not fit host".into()))?;
    let mut comp = vec![0u8; size];
    file.read_exact(&mut comp)?;
    let raw = bounded_zstd_decode(&comp, raw_size, MAX_META_RAW, None)?;
    if sha256(&raw) != expected_sha {
        return Err(PortableError::Integrity(
            "logs inverse tail metadata SHA-256 mismatch".into(),
        ));
    }
    Ok((raw, csize, pack_count))
}

fn read_metadata_body(
    file: &mut File,
    csize: u64,
    raw_size: u64,
    pack_count: u64,
    expected_sha: [u8; 32],
) -> Result<(Vec<u8>, u64, u64), PortableError> {
    if csize > MAX_META_COMP || raw_size > MAX_META_RAW || pack_count > MAX_PACKS {
        return Err(PortableError::Limit(
            "logs inverse primary metadata bounds".into(),
        ));
    }
    let size = usize::try_from(csize)
        .map_err(|_| PortableError::Limit("logs inverse metadata size does not fit host".into()))?;
    let mut comp = vec![0u8; size];
    file.read_exact(&mut comp)?;
    let raw = bounded_zstd_decode(&comp, raw_size, MAX_META_RAW, None)?;
    if sha256(&raw) != expected_sha {
        return Err(PortableError::Integrity(
            "logs inverse primary metadata SHA-256 mismatch".into(),
        ));
    }
    Ok((raw, csize, pack_count))
}

fn parse_metadata(raw: &[u8]) -> Result<Vec<LogicalFile>, PortableError> {
    let value = parse_msgpack(raw)?;
    let head = as_array(&value, "logs inverse metadata")?;
    if head.len() != 3
        || text(&head[0], "logs inverse profile")? != PROFILE
        || uint(&head[1], "logs inverse level", LEVEL)? != LEVEL
    {
        return Err(PortableError::Format(
            "unsupported logs inverse metadata identity".into(),
        ));
    }
    let rows = as_array(&head[2], "logs inverse file table")?;
    if rows.is_empty() || rows.len() > MAX_FILES {
        return Err(PortableError::Limit(
            "logs inverse file count exceeds policy".into(),
        ));
    }
    let mut out = Vec::with_capacity(rows.len());
    let mut previous = String::new();
    let mut seen = HashSet::with_capacity(rows.len());
    for row_value in rows {
        let row = as_array(row_value, "logs inverse file row")?;
        if row.len() != 5 {
            return Err(PortableError::Format(
                "malformed logs inverse file row".into(),
            ));
        }
        let prefix = usize::try_from(uint(
            &row[0],
            "logs inverse path prefix",
            MAX_PATH_BYTES as u64,
        )?)
        .map_err(|_| PortableError::Limit("logs inverse path prefix does not fit host".into()))?;
        let suffix = text(&row[1], "logs inverse path suffix")?;
        if prefix > previous.len() || !previous.is_char_boundary(prefix) {
            return Err(PortableError::Format(
                "logs inverse path prefix exceeds UTF-8 byte boundary".into(),
            ));
        }
        let mut path = previous[..prefix].to_owned();
        path.push_str(suffix);
        if path.len() > MAX_PATH_BYTES || !seen.insert(path.clone()) {
            return Err(PortableError::Format(
                "duplicate/oversized logs inverse path".into(),
            ));
        }
        safe_relpath(&path)?;
        let size = uint(&row[2], "logs inverse logical size", MAX_DECODE_UNIT)?;
        let expected_sha = digest32(&row[3], "logs inverse logical SHA-256")?;
        let storage_row = as_array(&row[4], "logs inverse storage")?;
        if storage_row.is_empty() {
            return Err(PortableError::Format(
                "empty logs inverse storage".into(),
            ));
        }
        let kind = text(&storage_row[0], "logs inverse storage kind")?;
        let storage = match kind {
            "pack" | "raw" => {
                if storage_row.len() != 4 {
                    return Err(PortableError::Format(
                        "malformed logs inverse pack storage".into(),
                    ));
                }
                Storage::Pack {
                    compressed: kind == "pack",
                    pack: usize::try_from(uint(
                        &storage_row[1],
                        "logs inverse pack id",
                        MAX_PACKS - 1,
                    )?)
                    .map_err(|_| {
                        PortableError::Limit("logs inverse pack id does not fit host".into())
                    })?,
                    offset: uint(
                        &storage_row[2],
                        "logs inverse pack offset",
                        MAX_DECODE_UNIT,
                    )?,
                    length: uint(
                        &storage_row[3],
                        "logs inverse pack length",
                        MAX_DECODE_UNIT,
                    )?,
                }
            }
            "derive" => {
                if storage_row.len() != 3 {
                    return Err(PortableError::Format(
                        "malformed logs inverse derive storage".into(),
                    ));
                }
                Storage::Derive {
                    source: usize::try_from(uint(
                        &storage_row[1],
                        "logs inverse source id",
                        (MAX_FILES - 1) as u64,
                    )?)
                    .map_err(|_| {
                        PortableError::Limit("logs inverse source id does not fit host".into())
                    })?,
                    codec: text(&storage_row[2], "logs inverse derive codec")?.to_owned(),
                }
            }
            _ => {
                return Err(PortableError::Format(
                    "unknown logs inverse storage kind".into(),
                ));
            }
        };
        out.push(LogicalFile {
            path: path.clone(),
            size,
            sha256: expected_sha,
            storage,
        });
        previous = path;
    }
    Ok(out)
}

fn scan_packs(
    file: &mut File,
    file_len: u64,
    meta_csize: u64,
    pack_count: u64,
) -> Result<Vec<PackDesc>, PortableError> {
    file.seek(SeekFrom::Start(HEADER_SIZE + meta_csize))?;
    let mut packs = Vec::with_capacity(pack_count as usize);
    for _ in 0..pack_count {
        let mut header = [0u8; PACK_HEADER_SIZE as usize];
        file.read_exact(&mut header)?;
        let codec = header[0];
        let raw_size = le_u64(&header[1..9])?;
        let csize = le_u64(&header[9..17])?;
        let crc32 = u32::from_le_bytes(header[17..21].try_into().expect("fixed pack header"));
        let expected_sha: [u8; 32] = header[21..53].try_into().expect("fixed pack header");
        if !matches!(codec, CODEC_RAW | CODEC_ZSTD)
            || raw_size > MAX_DECODE_UNIT
            || csize > MAX_DECODE_UNIT
        {
            return Err(PortableError::Limit(
                "logs inverse pack declaration exceeds policy".into(),
            ));
        }
        let offset = file.stream_position()?;
        let end = offset
            .checked_add(csize)
            .ok_or_else(|| PortableError::Limit("logs inverse pack extent overflow".into()))?;
        let tail_meta_offset = file_len
            .checked_sub(FOOTER_SIZE + meta_csize)
            .ok_or_else(|| PortableError::Format("logs inverse tail metadata overlap".into()))?;
        if end > tail_meta_offset {
            return Err(PortableError::Format(
                "logs inverse pack overlaps tail metadata".into(),
            ));
        }
        file.seek(SeekFrom::Start(end))?;
        packs.push(PackDesc {
            offset,
            codec,
            usize: raw_size,
            csize,
            crc32,
            sha256: expected_sha,
        });
    }
    let expected_tail = file_len
        .checked_sub(FOOTER_SIZE + meta_csize)
        .ok_or_else(|| PortableError::Format("logs inverse tail metadata overlap".into()))?;
    if file.stream_position()? != expected_tail {
        return Err(PortableError::Format(
            "logs inverse pack table/tail boundary mismatch".into(),
        ));
    }
    Ok(packs)
}

fn le_u64(bytes: &[u8]) -> Result<u64, PortableError> {
    let raw: [u8; 8] = bytes
        .try_into()
        .map_err(|_| PortableError::Format("short logs inverse little-endian u64".into()))?;
    Ok(u64::from_le_bytes(raw))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn metadata_identity_constants_match_python_profile() {
        assert_eq!(MAGIC, b"C25LG12\0");
        assert_eq!(TAIL_MAGIC, b"C25L12T\0");
        assert_eq!(LEVEL, 12);
        assert_eq!(MAX_DECODE_UNIT, 8 * 1024 * 1024);
        assert_eq!(MAX_MEMBER_READ_AMP, 8.0);
    }
}
