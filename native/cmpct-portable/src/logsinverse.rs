use crate::format::{as_array, bounded_zstd_decode, digest32, parse_msgpack, safe_relpath, sha256, text, uint};
use crate::{MemberReadStats, PortableEntry, PortableError};
use flate2::read::GzDecoder;
use rmpv::Value;
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::{Cursor, Read, Seek, SeekFrom};
use std::path::Path;
use std::sync::Mutex;
use xz2::read::XzDecoder;

const MAGIC: &[u8; 8] = b"C25LG12\0";
const TAIL_MAGIC: &[u8; 8] = b"C25L12T\0";
const PROFILE: &str = "cmpct-r25-logs-inverse-v1";
const LEVEL: u64 = 12;
const MAX_META_RAW: u64 = 2 * 1024 * 1024;
const MAX_META_COMP: u64 = 2 * 1024 * 1024;
const MAX_PACKS: usize = 64;
const MAX_FILES: usize = 4096;
const MAX_DECODE_UNIT: u64 = 8 * 1024 * 1024;
const MAX_MEMBER_AMPLIFICATION: f64 = 8.0;
const HEADER_SIZE: u64 = 8 + 8 + 8 + 4 + 32;
const FOOTER_SIZE: u64 = HEADER_SIZE;
const PACK_HEADER_SIZE: u64 = 1 + 8 + 8 + 4 + 32;
const CODEC_RAW: u8 = 0;
const CODEC_ZSTD: u8 = 1;

#[derive(Debug, Clone)]
enum Storage {
    Pack { pack: usize, offset: u64, length: u64 },
    Raw { pack: usize, offset: u64, length: u64 },
    Derive { source: usize, codec: String },
}

#[derive(Debug, Clone)]
struct FileRow {
    path: String,
    size: u64,
    sha256: [u8; 32],
    storage: Storage,
}

#[derive(Debug, Clone)]
struct PackDesc {
    codec: u8,
    raw_size: u64,
    blob_size: u64,
    crc32: u32,
    sha256: [u8; 32],
    offset: u64,
}

/// Hidden pre-dispatch reader for the recoverable C25LG12 inverse-log profile.
///
/// This surface exists so Python-writer -> Rust-reader parity can be proven before the profile is admitted to
/// production format dispatch. Canonical filesystem-manifest integration and Android/ABI promotion remain
/// separate release gates.
#[derive(Debug)]
pub struct LogsInverseArchive {
    entries: Vec<PortableEntry>,
    files: Vec<FileRow>,
    packs: Vec<PackDesc>,
    recovery_route: &'static str,
    file: Mutex<File>,
}

impl LogsInverseArchive {
    pub fn open(path: &Path) -> Result<Self, PortableError> {
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        if file_len < HEADER_SIZE + FOOTER_SIZE {
            return Err(PortableError::Format("short logs-inverse archive".into()));
        }

        let (meta_raw, meta_csize, pack_count, recovery_route) =
            read_control(&mut file, file_len)?;
        let files = parse_metadata(&meta_raw)?;
        let packs = scan_packs(&mut file, file_len, meta_csize, pack_count)?;

        // All storage references are validated before any member read can allocate/decompress payload bytes.
        for (index, row) in files.iter().enumerate() {
            match &row.storage {
                Storage::Pack { pack, offset, length } | Storage::Raw { pack, offset, length } => {
                    let desc = packs.get(*pack).ok_or_else(|| {
                        PortableError::Format(format!("logs-inverse pack id out of range for member {index}"))
                    })?;
                    let end = offset
                        .checked_add(*length)
                        .ok_or_else(|| PortableError::Limit("logs-inverse slice overflow".into()))?;
                    if *length != row.size || end > desc.raw_size {
                        return Err(PortableError::Integrity(
                            "logs-inverse stored slice exceeds authenticated pack".into(),
                        ));
                    }
                    if matches!(row.storage, Storage::Raw { .. }) && desc.codec != CODEC_RAW {
                        return Err(PortableError::Integrity(
                            "logs-inverse raw storage references compressed pack".into(),
                        ));
                    }
                }
                Storage::Derive { source, codec } => {
                    if *source >= files.len() || *source == index {
                        return Err(PortableError::Format(
                            "logs-inverse dependency index is invalid".into(),
                        ));
                    }
                    if !matches!(codec.as_str(), "gzip" | "xz" | "zstd") {
                        return Err(PortableError::Format(
                            "logs-inverse dependency codec is unsupported".into(),
                        ));
                    }
                }
            }
        }

        let entries = files
            .iter()
            .map(|row| PortableEntry {
                path: row.path.clone(),
                size: row.size,
                kind: 0,
                mode: 0,
                mtime_ns: 0,
            })
            .collect();

        Ok(Self {
            entries,
            files,
            packs,
            recovery_route,
            file: Mutex::new(file),
        })
    }

    pub fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    pub fn entry_identity(&self, index: usize) -> Result<(u64, [u8; 32]), PortableError> {
        let row = self
            .files
            .get(index)
            .ok_or_else(|| PortableError::Format("logs-inverse member id out of range".into()))?;
        Ok((row.size, row.sha256))
    }

    pub fn recovery_route(&self) -> &'static str {
        self.recovery_route
    }

    fn read_pack(&self, index: usize) -> Result<Vec<u8>, PortableError> {
        let desc = self
            .packs
            .get(index)
            .ok_or_else(|| PortableError::Format("logs-inverse pack id out of range".into()))?;
        let size = usize::try_from(desc.blob_size)
            .map_err(|_| PortableError::Limit("logs-inverse pack size does not fit host".into()))?;
        let mut blob = vec![0u8; size];
        let mut file = self
            .file
            .lock()
            .map_err(|_| PortableError::IoState("logs-inverse file lock poisoned".into()))?;
        file.seek(SeekFrom::Start(desc.offset))?;
        file.read_exact(&mut blob)?;
        drop(file);

        let raw = match desc.codec {
            CODEC_RAW => {
                if blob.len() as u64 != desc.raw_size {
                    return Err(PortableError::Integrity(
                        "logs-inverse raw pack size mismatch".into(),
                    ));
                }
                blob
            }
            CODEC_ZSTD => bounded_zstd_decode(&blob, desc.raw_size, MAX_DECODE_UNIT, None)?,
            _ => return Err(PortableError::Format("logs-inverse pack codec".into())),
        };
        if crc32fast::hash(&raw) != desc.crc32 || sha256(&raw) != desc.sha256 {
            return Err(PortableError::Integrity(
                "logs-inverse pack identity mismatch".into(),
            ));
        }
        Ok(raw)
    }

    fn restore(
        &self,
        index: usize,
        cache: &mut HashMap<usize, (Vec<u8>, u64)>,
        active: &mut HashSet<usize>,
    ) -> Result<(Vec<u8>, u64), PortableError> {
        if let Some(value) = cache.get(&index) {
            return Ok(value.clone());
        }
        let row = self
            .files
            .get(index)
            .ok_or_else(|| PortableError::Format("logs-inverse member id out of range".into()))?;
        if !active.insert(index) {
            return Err(PortableError::Format(
                "logs-inverse dependency cycle detected".into(),
            ));
        }

        let (value, decoded_context) = match &row.storage {
            Storage::Pack { pack, offset, length } => {
                let raw = self.read_pack(*pack)?;
                let start = usize::try_from(*offset)
                    .map_err(|_| PortableError::Limit("logs-inverse offset does not fit host".into()))?;
                let length = usize::try_from(*length)
                    .map_err(|_| PortableError::Limit("logs-inverse length does not fit host".into()))?;
                let end = start
                    .checked_add(length)
                    .ok_or_else(|| PortableError::Limit("logs-inverse slice overflow".into()))?;
                (raw[start..end].to_vec(), raw.len() as u64)
            }
            Storage::Raw { pack, offset, length } => {
                let raw = self.read_pack(*pack)?;
                let start = usize::try_from(*offset)
                    .map_err(|_| PortableError::Limit("logs-inverse offset does not fit host".into()))?;
                let length = usize::try_from(*length)
                    .map_err(|_| PortableError::Limit("logs-inverse length does not fit host".into()))?;
                let end = start
                    .checked_add(length)
                    .ok_or_else(|| PortableError::Limit("logs-inverse slice overflow".into()))?;
                (raw[start..end].to_vec(), *length)
            }
            Storage::Derive { source, codec } => {
                let (compressed, source_context) = self.restore(*source, cache, active)?;
                let decoded = decode_inverse(codec, &compressed, row.size)?;
                let context = source_context
                    .checked_add(decoded.len() as u64)
                    .ok_or_else(|| PortableError::Limit("logs-inverse context overflow".into()))?;
                (decoded, context)
            }
        };

        active.remove(&index);
        if value.len() as u64 != row.size || sha256(&value) != row.sha256 {
            return Err(PortableError::Integrity(format!(
                "logs-inverse logical identity mismatch: {}",
                row.path
            )));
        }
        if decoded_context > MAX_DECODE_UNIT
            || decoded_context as f64 / row.size.max(1) as f64 > MAX_MEMBER_AMPLIFICATION
        {
            return Err(PortableError::Limit(format!(
                "logs-inverse locality ceiling exceeded: {}",
                row.path
            )));
        }
        cache.insert(index, (value.clone(), decoded_context));
        Ok((value, decoded_context))
    }

    pub fn read_member(&self, index: usize) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let mut cache = HashMap::new();
        let mut active = HashSet::new();
        let (raw, decoded_context) = self.restore(index, &mut cache, &mut active)?;
        let row = &self.files[index];
        Ok((
            raw,
            MemberReadStats {
                logical_bytes: row.size,
                decoded_context_bytes: decoded_context,
                amplification: decoded_context as f64 / row.size.max(1) as f64,
                profile: PROFILE,
            },
        ))
    }

    pub fn verify(&self) -> Result<(), PortableError> {
        for index in 0..self.files.len() {
            self.read_member(index)?;
        }
        Ok(())
    }
}

fn read_control(
    file: &mut File,
    file_len: u64,
) -> Result<(Vec<u8>, u64, usize, &'static str), PortableError> {
    let primary = (|| {
        file.seek(SeekFrom::Start(0))?;
        let magic = read_exact_array::<8>(file)?;
        let csize = read_u64(file)?;
        let usize_ = read_u64(file)?;
        let pack_count = read_u32(file)? as usize;
        let expected_sha = read_exact_array::<32>(file)?;
        if &magic != MAGIC
            || csize > MAX_META_COMP
            || usize_ > MAX_META_RAW
            || pack_count > MAX_PACKS
        {
            return Err(PortableError::Format(
                "logs-inverse primary control bounds".into(),
            ));
        }
        let mut comp = vec![0u8; csize as usize];
        file.read_exact(&mut comp)?;
        let raw = bounded_zstd_decode(&comp, usize_, MAX_META_RAW, None)?;
        if sha256(&raw) != expected_sha {
            return Err(PortableError::Integrity(
                "logs-inverse primary metadata authentication".into(),
            ));
        }
        Ok((raw, csize, pack_count))
    })();
    if let Ok((raw, csize, pack_count)) = primary {
        return Ok((raw, csize, pack_count, "primary"));
    }

    file.seek(SeekFrom::Start(file_len - FOOTER_SIZE))?;
    let magic = read_exact_array::<8>(file)?;
    let csize = read_u64(file)?;
    let usize_ = read_u64(file)?;
    let pack_count = read_u32(file)? as usize;
    let expected_sha = read_exact_array::<32>(file)?;
    if &magic != TAIL_MAGIC
        || csize > MAX_META_COMP
        || usize_ > MAX_META_RAW
        || pack_count > MAX_PACKS
    {
        return Err(PortableError::Format(
            "logs-inverse tail control bounds".into(),
        ));
    }
    let meta_offset = file_len
        .checked_sub(FOOTER_SIZE + csize)
        .ok_or_else(|| PortableError::Format("logs-inverse tail metadata offset".into()))?;
    if meta_offset < HEADER_SIZE + csize {
        return Err(PortableError::Format(
            "logs-inverse tail metadata overlaps primary control".into(),
        ));
    }
    file.seek(SeekFrom::Start(meta_offset))?;
    let mut comp = vec![0u8; csize as usize];
    file.read_exact(&mut comp)?;
    let raw = bounded_zstd_decode(&comp, usize_, MAX_META_RAW, None)?;
    if sha256(&raw) != expected_sha {
        return Err(PortableError::Integrity(
            "logs-inverse tail metadata authentication".into(),
        ));
    }
    Ok((raw, csize, pack_count, "tail"))
}

fn parse_metadata(raw: &[u8]) -> Result<Vec<FileRow>, PortableError> {
    let value = parse_msgpack(raw)?;
    let head = as_array(&value, "logs-inverse metadata")?;
    if head.len() != 3
        || text(&head[0], "logs-inverse profile")? != PROFILE
        || uint(&head[1], "logs-inverse level", LEVEL)? != LEVEL
    {
        return Err(PortableError::Format(
            "unsupported logs-inverse metadata identity".into(),
        ));
    }
    let rows = as_array(&head[2], "logs-inverse file table")?;
    if rows.is_empty() || rows.len() > MAX_FILES {
        return Err(PortableError::Limit(
            "logs-inverse file count exceeds policy".into(),
        ));
    }

    let mut previous = String::new();
    let mut seen = HashSet::new();
    let mut files = Vec::with_capacity(rows.len());
    for (index, value) in rows.iter().enumerate() {
        let row = as_array(value, "logs-inverse file row")?;
        if row.len() != 5 {
            return Err(PortableError::Format(
                "malformed logs-inverse file row".into(),
            ));
        }
        let prefix = uint(&row[0], "logs-inverse path prefix", previous.chars().count() as u64)?
            as usize;
        let suffix = text(&row[1], "logs-inverse path suffix")?;
        let path = previous.chars().take(prefix).collect::<String>() + suffix;
        safe_relpath(&path)?;
        if !seen.insert(path.clone()) {
            return Err(PortableError::Format(
                "duplicate logs-inverse logical path".into(),
            ));
        }
        let size = uint(&row[2], "logs-inverse logical size", MAX_DECODE_UNIT)?;
        let digest = digest32(&row[3], "logs-inverse logical SHA-256")?;
        let storage_row = as_array(&row[4], "logs-inverse storage")?;
        if storage_row.is_empty() {
            return Err(PortableError::Format("empty logs-inverse storage".into()));
        }
        let kind = text(&storage_row[0], "logs-inverse storage kind")?;
        let storage = match kind {
            "pack" | "raw" => {
                if storage_row.len() != 4 {
                    return Err(PortableError::Format(
                        "malformed logs-inverse pack storage".into(),
                    ));
                }
                let pack = uint(&storage_row[1], "logs-inverse pack id", MAX_PACKS as u64)? as usize;
                let offset = uint(&storage_row[2], "logs-inverse pack offset", MAX_DECODE_UNIT)?;
                let length = uint(&storage_row[3], "logs-inverse pack length", MAX_DECODE_UNIT)?;
                if kind == "pack" {
                    Storage::Pack { pack, offset, length }
                } else {
                    Storage::Raw { pack, offset, length }
                }
            }
            "derive" => {
                if storage_row.len() != 3 {
                    return Err(PortableError::Format(
                        "malformed logs-inverse derive storage".into(),
                    ));
                }
                let source = uint(&storage_row[1], "logs-inverse derive source", MAX_FILES as u64)?
                    as usize;
                let codec = text(&storage_row[2], "logs-inverse derive codec")?.to_owned();
                Storage::Derive { source, codec }
            }
            _ => {
                return Err(PortableError::Format(format!(
                    "unknown logs-inverse storage kind at member {index}"
                )))
            }
        };
        files.push(FileRow {
            path: path.clone(),
            size,
            sha256: digest,
            storage,
        });
        previous = path;
    }
    Ok(files)
}

fn scan_packs(
    file: &mut File,
    file_len: u64,
    meta_csize: u64,
    pack_count: usize,
) -> Result<Vec<PackDesc>, PortableError> {
    file.seek(SeekFrom::Start(HEADER_SIZE + meta_csize))?;
    let mut packs = Vec::with_capacity(pack_count);
    for _ in 0..pack_count {
        let codec = read_exact_array::<1>(file)?[0];
        let raw_size = read_u64(file)?;
        let blob_size = read_u64(file)?;
        let crc32 = read_u32(file)?;
        let digest = read_exact_array::<32>(file)?;
        if !matches!(codec, CODEC_RAW | CODEC_ZSTD)
            || raw_size > MAX_DECODE_UNIT
            || blob_size > MAX_DECODE_UNIT
        {
            return Err(PortableError::Limit(
                "logs-inverse pack declaration exceeds policy".into(),
            ));
        }
        let offset = file.stream_position()?;
        let end = offset
            .checked_add(blob_size)
            .ok_or_else(|| PortableError::Limit("logs-inverse pack offset overflow".into()))?;
        if end > file_len {
            return Err(PortableError::Format("truncated logs-inverse pack".into()));
        }
        file.seek(SeekFrom::Start(end))?;
        packs.push(PackDesc {
            codec,
            raw_size,
            blob_size,
            crc32,
            sha256: digest,
            offset,
        });
    }
    let expected_tail = file_len
        .checked_sub(FOOTER_SIZE + meta_csize)
        .ok_or_else(|| PortableError::Format("logs-inverse tail boundary".into()))?;
    if file.stream_position()? != expected_tail {
        return Err(PortableError::Format(
            "logs-inverse pack table/tail boundary mismatch".into(),
        ));
    }
    Ok(packs)
}

fn decode_inverse(codec: &str, compressed: &[u8], expected_size: u64) -> Result<Vec<u8>, PortableError> {
    if expected_size > MAX_DECODE_UNIT {
        return Err(PortableError::Limit(
            "logs-inverse derived output exceeds policy".into(),
        ));
    }
    let mut out = Vec::with_capacity(expected_size as usize);
    match codec {
        "gzip" => {
            let decoder = GzDecoder::new(Cursor::new(compressed));
            decoder
                .take(expected_size + 1)
                .read_to_end(&mut out)
                .map_err(|error| PortableError::Format(format!("gzip inverse decode: {error}")))?;
        }
        "xz" => {
            let decoder = XzDecoder::new(Cursor::new(compressed));
            decoder
                .take(expected_size + 1)
                .read_to_end(&mut out)
                .map_err(|error| PortableError::Format(format!("xz inverse decode: {error}")))?;
        }
        "zstd" => {
            return bounded_zstd_decode(compressed, expected_size, MAX_DECODE_UNIT, None);
        }
        _ => return Err(PortableError::Format("unknown inverse codec".into())),
    }
    if out.len() as u64 != expected_size {
        return Err(PortableError::Integrity(
            "logs-inverse derived size mismatch".into(),
        ));
    }
    Ok(out)
}

fn read_u32<R: Read>(reader: &mut R) -> Result<u32, PortableError> {
    Ok(u32::from_le_bytes(read_exact_array::<4>(reader)?))
}

fn read_u64<R: Read>(reader: &mut R) -> Result<u64, PortableError> {
    Ok(u64::from_le_bytes(read_exact_array::<8>(reader)?))
}

fn read_exact_array<const N: usize, R: Read>(reader: &mut R) -> Result<[u8; N], PortableError> {
    let mut raw = [0u8; N];
    reader.read_exact(&mut raw)?;
    Ok(raw)
}
