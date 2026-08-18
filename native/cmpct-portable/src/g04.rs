use crate::format::{
    as_array, as_map, bounded_zstd_decode, digest32, field, merkle_root, number, optional_field,
    parse_msgpack, safe_relpath, sha256, text, tree_digest, tree_hasher_prefix, u32_le, u64_le, uint,
    MAX_META_BYTES,
};
use crate::{MemberReadStats, PortableEntry, PortableError};
use crc32fast::Hasher as Crc32;
use preflate_container::{PreflateContainerConfig, ProcessBuffer, RecreateContainerProcessor};
use rmpv::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::File;
use std::io::{Cursor, Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::sync::{Arc, Mutex};

const MAGIC: &[u8; 8] = b"CMPNXG4\0";
const TAIL: &[u8; 8] = b"CNG4T\0\0\0";
const ENGINE: &str = "EntropyGraph-II-v030-G04Overlay-v1";
const HEADER_SIZE: u64 = 108;
const FOOTER_SIZE: u64 = 88;
const PHYSICAL_HEADER_SIZE: u64 = 53;
const CODEC_RAW: u8 = 0;
const CODEC_ZSTD: u8 = 1;
const CODEC_PREFLATE: u8 = 2;
const MAX_FILES: usize = 65_536;
const MAX_NODES: usize = 262_144;
const MAX_CHUNK: u64 = 512 * 1024;
const MAX_DECODE_UNIT: u64 = 8 * 1024 * 1024;
const MAX_DECODER_MEMORY: u64 = 96 * 1024 * 1024;
const MAX_MOSAIC_BASES: usize = 4;
const MAX_MOSAIC_SOURCE_INDEX: u64 = 8 * 1024 * 1024;
const MAX_RESIDUAL_PACK: u64 = 256 * 1024;
const MAX_ADDITIONAL_RECIPE_AMP: f64 = 2.0;
const MAX_MEMBER_READ_AMP: f64 = 8.0;
const MAX_RECORD_CACHE_BYTES: usize = 64 * 1024 * 1024;
const MAX_NODE_CACHE_BYTES: usize = 32 * 1024 * 1024;
const MAX_MATERIALIZED_MEMBER: u64 = 64 * 1024 * 1024;
const MAX_DECLARED_LOGICAL_BYTES: u64 = 8 * 1024 * 1024 * 1024 * 1024;
const LANE_WIDTHS: &[u64] = &[2, 4, 8, 16];
const MAX_OVERLAY_RECORD: u64 = 2 * 1024 * 1024;
const MAX_DELIMITER_SEGMENTS: u64 = 65_536;
const MAX_DELIMITER_CELL_SCANS: u64 = 8 * MAX_OVERLAY_RECORD;
const HG_MAX_ROWS: u64 = 65_536;
const HG_MAX_FIELDS_PER_ROW: u64 = 256;
const HG_MAX_FIELD_DESCRIPTORS: u64 = 131_072;
const HG_MAX_CELL_SCANS: u64 = 8 * MAX_CHUNK;
const HG_MAX_EXACT_FINALISTS: u64 = 3;
const HG_SCREEN_LEVEL: u64 = 6;
const HG_EXACT_LEVEL: u64 = 19;
const HG_MAGIC_PLAIN: &[u8; 4] = b"HGT2";
const HG_MAGIC_PREFIX: &[u8; 4] = b"HGP2";

#[derive(Debug, Clone)]
enum Transform {
    None,
    Lane { width: usize, logical_size: usize },
    Delimiter { delimiter: u8, logical_size: usize },
    Hierarchical {
        primary: u8,
        secondary: u8,
        prefix_planes: bool,
        logical_size: usize,
    },
}

#[derive(Debug, Clone)]
struct Record {
    offset: u64,
    codec: u8,
    usize: u64,
    csize: u64,
    crc32: u32,
    logical_sha: [u8; 32],
    payload_sha: [u8; 32],
    transform: Transform,
}

#[derive(Debug, Clone)]
enum Node {
    Direct {
        record: usize,
        offset: usize,
        length: usize,
        sha: [u8; 32],
    },
    Delta {
        base: usize,
        record: usize,
        length: usize,
        sha: [u8; 32],
    },
    DeltaPack {
        base: usize,
        record: usize,
        recipe_offset: usize,
        recipe_len: usize,
        length: usize,
        sha: [u8; 32],
    },
    Mosaic {
        bases: Vec<usize>,
        record: usize,
        length: usize,
        sha: [u8; 32],
    },
    PackMosaic {
        record: usize,
        offset: usize,
        recipe_len: usize,
        bases: Vec<usize>,
        length: usize,
        sha: [u8; 32],
    },
}

impl Node {
    fn is_direct(&self) -> bool {
        matches!(self, Self::Direct { .. })
    }

    fn logical_len(&self) -> usize {
        match self {
            Self::Direct { length, .. }
            | Self::Delta { length, .. }
            | Self::DeltaPack { length, .. }
            | Self::Mosaic { length, .. }
            | Self::PackMosaic { length, .. } => *length,
        }
    }
}

#[derive(Debug, Clone)]
enum GFile {
    Preflate {
        record: usize,
        size: u64,
        sha: [u8; 32],
    },
    Nodes {
        nodes: Vec<usize>,
        size: u64,
        sha: [u8; 32],
    },
}

#[derive(Debug)]
pub(crate) struct G04Archive {
    entries: Vec<PortableEntry>,
    files: BTreeMap<String, GFile>,
    nodes: Vec<Node>,
    records: Vec<Record>,
    tree_sha: [u8; 32],
    declared_amplification: f64,
    tail_authenticated: bool,
    file: Mutex<File>,
}

#[derive(Debug)]
struct ParsedMeta {
    files: BTreeMap<String, GFile>,
    nodes: Vec<Node>,
    offsets: Vec<u64>,
    leaves: Vec<[u8; 32]>,
    transforms: Vec<Transform>,
    tree_sha: [u8; 32],
    declared_amplification: f64,
}

#[derive(Debug)]
struct AuthMeta {
    value: Value,
    compressed_size: u64,
    meta_sha: [u8; 32],
    merkle: [u8; 32],
    expected_count: Option<usize>,
    tail_offset: Option<u64>,
}

impl G04Archive {
    pub(crate) fn open(path: &Path) -> Result<Self, PortableError> {
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        if file_len < HEADER_SIZE + FOOTER_SIZE {
            return Err(PortableError::Format("short G0-G4 archive".into()));
        }
        let primary = read_primary(&mut file).ok();
        let tail = read_tail(&mut file, file_len).ok();
        if primary.is_none() && tail.is_none() {
            return Err(PortableError::Integrity(
                "no authenticated G0-G4 metadata copy".into(),
            ));
        }
        if let (Some(left), Some(right)) = (&primary, &tail) {
            if left.meta_sha != right.meta_sha || left.merkle != right.merkle {
                return Err(PortableError::Integrity(
                    "conflicting authenticated G0-G4 metadata copies".into(),
                ));
            }
        }
        let chosen = primary.as_ref().or(tail.as_ref()).expect("metadata copy");
        let parsed = parse_meta(&chosen.value, chosen.expected_count)?;
        if merkle_root(&parsed.leaves) != chosen.merkle {
            return Err(PortableError::Integrity(
                "G0-G4 metadata leaf table does not match authenticated Merkle root".into(),
            ));
        }

        let record_start = HEADER_SIZE
            .checked_add(chosen.compressed_size)
            .ok_or_else(|| PortableError::Limit("G0-G4 record offset overflow".into()))?;
        let mut expected_rel = 0u64;
        let mut records = Vec::with_capacity(parsed.offsets.len());
        for (record_id, rel) in parsed.offsets.iter().copied().enumerate() {
            if rel != expected_rel {
                return Err(PortableError::Format(
                    "G0-G4 physical record table contains gap/overlap".into(),
                ));
            }
            let absolute = record_start
                .checked_add(rel)
                .ok_or_else(|| PortableError::Limit("G0-G4 record absolute offset overflow".into()))?;
            file.seek(SeekFrom::Start(absolute))?;
            let mut header = [0u8; PHYSICAL_HEADER_SIZE as usize];
            file.read_exact(&mut header)?;
            let codec = header[0];
            if !matches!(codec, CODEC_RAW | CODEC_ZSTD | CODEC_PREFLATE) {
                return Err(PortableError::Format("unknown G0-G4 physical codec".into()));
            }
            let usize = u64_le(&header[1..9])?;
            let csize = u64_le(&header[9..17])?;
            let crc32 = u32_le(&header[17..21])?;
            let logical_sha: [u8; 32] = header[21..53]
                .try_into()
                .map_err(|_| PortableError::Format("G0-G4 physical SHA field".into()))?;
            if usize > MAX_DECODE_UNIT || csize > MAX_DECODE_UNIT + 1024 * 1024 {
                return Err(PortableError::Limit(
                    "G0-G4 physical record declaration exceeds policy".into(),
                ));
            }
            expected_rel = expected_rel
                .checked_add(PHYSICAL_HEADER_SIZE)
                .and_then(|value| value.checked_add(csize))
                .ok_or_else(|| PortableError::Limit("G0-G4 physical table overflow".into()))?;
            records.push(Record {
                offset: absolute,
                codec,
                usize,
                csize,
                crc32,
                logical_sha,
                payload_sha: parsed.leaves[record_id],
                transform: parsed.transforms[record_id].clone(),
            });
        }
        let physical_end = record_start
            .checked_add(expected_rel)
            .ok_or_else(|| PortableError::Limit("G0-G4 physical endpoint overflow".into()))?;
        if let Some(tail) = &tail {
            let tail_offset = tail
                .tail_offset
                .ok_or_else(|| PortableError::Format("missing G0-G4 tail offset".into()))?;
            if physical_end != tail_offset {
                return Err(PortableError::Integrity(
                    "G0-G4 physical endpoint does not bind authenticated tail".into(),
                ));
            }
        } else if physical_end > file_len {
            return Err(PortableError::Format(
                "G0-G4 physical endpoint exceeds archive".into(),
            ));
        }

        let entries = parsed
            .files
            .iter()
            .map(|(path, file)| PortableEntry {
                path: path.clone(),
                size: match file {
                    GFile::Preflate { size, .. } | GFile::Nodes { size, .. } => *size,
                },
                kind: 0,
                mode: 0o644,
                mtime_ns: 0,
            })
            .collect();

        Ok(Self {
            entries,
            files: parsed.files,
            nodes: parsed.nodes,
            records,
            tree_sha: parsed.tree_sha,
            declared_amplification: parsed.declared_amplification,
            tail_authenticated: tail.is_some(),
            file: Mutex::new(file),
        })
    }

    pub(crate) fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    pub(crate) fn tail_authenticated(&self) -> bool {
        self.tail_authenticated
    }

    pub(crate) fn declared_amplification(&self) -> f64 {
        self.declared_amplification
    }

    fn file_at(&self, index: usize) -> Result<(&str, &GFile), PortableError> {
        let entry = self
            .entries
            .get(index)
            .ok_or_else(|| PortableError::Format("G0-G4 member id out of range".into()))?;
        let file = self.files.get(&entry.path).ok_or_else(|| {
            PortableError::Format("G0-G4 entry/file table disagreement".into())
        })?;
        Ok((&entry.path, file))
    }

    pub(crate) fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        let (_, file) = self.file_at(index)?;
        let mut context = DecodeContext::new(self);
        let (expected_size, expected_sha) = match file {
            GFile::Preflate { size, sha, .. } | GFile::Nodes { size, sha, .. } => (*size, *sha),
        };
        let mut logical = 0u64;
        let mut digest = Sha256::new();
        match file {
            GFile::Preflate { record, .. } => {
                let raw = context.record(*record)?;
                logical = raw.len() as u64;
                digest.update(raw.as_slice());
                output.write_all(raw.as_slice())?;
            }
            GFile::Nodes { nodes, .. } => {
                for node_id in nodes {
                    let raw = context.node(*node_id)?;
                    logical = logical
                        .checked_add(raw.len() as u64)
                        .ok_or_else(|| PortableError::Limit("G0-G4 member length overflow".into()))?;
                    if logical > expected_size {
                        return Err(PortableError::Integrity(
                            "G0-G4 streamed member exceeds declaration".into(),
                        ));
                    }
                    digest.update(raw.as_slice());
                    output.write_all(raw.as_slice())?;
                }
            }
        }
        let got: [u8; 32] = digest.finalize().into();
        if logical != expected_size || got != expected_sha {
            return Err(PortableError::Integrity(
                "G0-G4 streamed member logical identity mismatch".into(),
            ));
        }
        let decoded_context_bytes = context.decoded_context_bytes()?;
        let amplification = decoded_context_bytes as f64 / expected_size.max(1) as f64;
        if amplification > MAX_MEMBER_READ_AMP {
            return Err(PortableError::Limit(format!(
                "G0-G4 member read amplification {amplification:.3} exceeds {MAX_MEMBER_READ_AMP}x"
            )));
        }
        Ok(MemberReadStats {
            logical_bytes: expected_size,
            decoded_context_bytes,
            amplification,
            profile: "g04-r25",
        })
    }

    pub(crate) fn read_member(
        &self,
        index: usize,
    ) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let size = self
            .entries
            .get(index)
            .ok_or_else(|| PortableError::Format("G0-G4 member id out of range".into()))?
            .size;
        if size > MAX_MATERIALIZED_MEMBER {
            return Err(PortableError::Limit(format!(
                "G0-G4 member is {size} bytes; use streaming extraction instead of materializing above {MAX_MATERIALIZED_MEMBER}"
            )));
        }
        let mut out = Vec::with_capacity(size as usize);
        let stats = self.stream_member(index, &mut out)?;
        Ok((out, stats))
    }

    pub(crate) fn verify(&self) -> Result<(), PortableError> {
        let mut tree = Sha256::new();
        for (index, entry) in self.entries.iter().enumerate() {
            tree_hasher_prefix(&mut tree, &entry.path, entry.size);
            let mut sink = DigestWriter(&mut tree);
            self.stream_member(index, &mut sink)?;
        }
        let got: [u8; 32] = tree.finalize().into();
        if got != self.tree_sha {
            return Err(PortableError::Integrity(
                "G0-G4 streamed tree SHA-256 mismatch".into(),
            ));
        }
        Ok(())
    }
}

struct DigestWriter<'a>(&'a mut Sha256);

impl Write for DigestWriter<'_> {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        self.0.update(buf);
        Ok(buf.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

struct DecodeContext<'a> {
    archive: &'a G04Archive,
    record_cache: HashMap<usize, Arc<Vec<u8>>>,
    record_cache_bytes: usize,
    node_cache: HashMap<usize, Arc<Vec<u8>>>,
    node_cache_bytes: usize,
    touched_records: HashMap<usize, u64>,
}

impl<'a> DecodeContext<'a> {
    fn new(archive: &'a G04Archive) -> Self {
        Self {
            archive,
            record_cache: HashMap::new(),
            record_cache_bytes: 0,
            node_cache: HashMap::new(),
            node_cache_bytes: 0,
            touched_records: HashMap::new(),
        }
    }

    fn decoded_context_bytes(&self) -> Result<u64, PortableError> {
        self.touched_records.values().try_fold(0u64, |total, value| {
            total
                .checked_add(*value)
                .ok_or_else(|| PortableError::Limit("G0-G4 context byte counter overflow".into()))
        })
    }

    fn record(&mut self, record_id: usize) -> Result<Arc<Vec<u8>>, PortableError> {
        if let Some(value) = self.record_cache.get(&record_id) {
            return Ok(Arc::clone(value));
        }
        let record = self.archive.records.get(record_id).ok_or_else(|| {
            PortableError::Format("G0-G4 record reference out of range".into())
        })?;
        let mut file = self
            .archive
            .file
            .lock()
            .map_err(|_| PortableError::IoState("G0-G4 file lock poisoned".into()))?;
        file.seek(SeekFrom::Start(record.offset))?;
        let mut header = [0u8; PHYSICAL_HEADER_SIZE as usize];
        file.read_exact(&mut header)?;
        if header[0] != record.codec
            || u64_le(&header[1..9])? != record.usize
            || u64_le(&header[9..17])? != record.csize
            || u32_le(&header[17..21])? != record.crc32
            || header[21..53] != record.logical_sha
        {
            return Err(PortableError::Integrity(
                "G0-G4 physical header changed after authenticated preflight".into(),
            ));
        }
        let mut payload = vec![0u8; record.csize as usize];
        file.read_exact(&mut payload)?;
        drop(file);
        if sha256(&payload) != record.payload_sha {
            return Err(PortableError::Integrity(
                "G0-G4 payload SHA-256 mismatch".into(),
            ));
        }
        let physical = match record.codec {
            CODEC_RAW => {
                if payload.len() as u64 != record.usize {
                    return Err(PortableError::Integrity(
                        "G0-G4 RAW physical length mismatch".into(),
                    ));
                }
                payload
            }
            CODEC_ZSTD => bounded_zstd_decode(&payload, record.usize, MAX_DECODE_UNIT, None)?,
            CODEC_PREFLATE => preflate_unpack(&payload, record.usize)?,
            _ => return Err(PortableError::Format("unknown G0-G4 physical codec".into())),
        };
        let original = match &record.transform {
            Transform::None => physical,
            Transform::Lane {
                width,
                logical_size,
            } => lane_inverse(&physical, *width, *logical_size)?,
            Transform::Delimiter {
                delimiter,
                logical_size,
            } => delimiter_inverse(&physical, *delimiter, *logical_size)?,
            Transform::Hierarchical {
                primary,
                secondary,
                prefix_planes,
                logical_size,
            } => hierarchy_inverse(
                &physical,
                *primary,
                *secondary,
                *prefix_planes,
                *logical_size,
            )?,
        };
        let mut crc = Crc32::new();
        crc.update(&original);
        if crc.finalize() != record.crc32 || sha256(&original) != record.logical_sha {
            return Err(PortableError::Integrity(
                "G0-G4 inverse record CRC/SHA identity mismatch".into(),
            ));
        }
        self.touched_records
            .entry(record_id)
            .or_insert(original.len() as u64);
        let value = Arc::new(original);
        if self.record_cache_bytes.saturating_add(value.len()) <= MAX_RECORD_CACHE_BYTES {
            self.record_cache_bytes += value.len();
            self.record_cache.insert(record_id, Arc::clone(&value));
        }
        Ok(value)
    }

    fn node(&mut self, node_id: usize) -> Result<Arc<Vec<u8>>, PortableError> {
        if let Some(value) = self.node_cache.get(&node_id) {
            return Ok(Arc::clone(value));
        }
        let node = self.archive.nodes.get(node_id).cloned().ok_or_else(|| {
            PortableError::Format("G0-G4 node reference out of range".into())
        })?;
        let (raw, expected) = match node {
            Node::Direct {
                record,
                offset,
                length,
                sha,
            } => {
                let pack = self.record(record)?;
                let end = offset
                    .checked_add(length)
                    .ok_or_else(|| PortableError::Limit("G0-G4 direct slice overflow".into()))?;
                if end > pack.len() {
                    return Err(PortableError::Format("G0-G4 direct slice bounds".into()));
                }
                (pack[offset..end].to_vec(), sha)
            }
            Node::Delta {
                base,
                record,
                length,
                sha,
            } => {
                let base = self.node(base)?;
                let recipe = self.record(record)?;
                (delta_decode(&base, &recipe, length)?, sha)
            }
            Node::DeltaPack {
                base,
                record,
                recipe_offset,
                recipe_len,
                length,
                sha,
            } => {
                let base = self.node(base)?;
                let pack = self.record(record)?;
                if pack.len() as u64 > MAX_RESIDUAL_PACK {
                    return Err(PortableError::Limit(
                        "G0-G4 residual pack exceeds policy".into(),
                    ));
                }
                let end = recipe_offset.checked_add(recipe_len).ok_or_else(|| {
                    PortableError::Limit("G0-G4 packed-delta slice overflow".into())
                })?;
                if end > pack.len() {
                    return Err(PortableError::Format(
                        "G0-G4 packed-delta recipe bounds".into(),
                    ));
                }
                let amp = pack.len() as f64 / length.max(1) as f64;
                if amp > MAX_ADDITIONAL_RECIPE_AMP {
                    return Err(PortableError::Limit(
                        "G0-G4 packed-delta recipe amplification exceeds policy".into(),
                    ));
                }
                (delta_decode(&base, &pack[recipe_offset..end], length)?, sha)
            }
            Node::Mosaic {
                bases,
                record,
                length,
                sha,
            } => {
                let mut roots = Vec::with_capacity(bases.len());
                for base in bases {
                    roots.push(self.node(base)?);
                }
                let recipe = self.record(record)?;
                (mosaic_decode(&roots, &recipe, length)?, sha)
            }
            Node::PackMosaic {
                record,
                offset,
                recipe_len,
                bases,
                length,
                sha,
            } => {
                let mut roots = Vec::with_capacity(bases.len());
                for base in bases {
                    roots.push(self.node(base)?);
                }
                let pack = self.record(record)?;
                let end = offset.checked_add(recipe_len).ok_or_else(|| {
                    PortableError::Limit("G0-G4 pack-mosaic slice overflow".into())
                })?;
                if end > pack.len() {
                    return Err(PortableError::Format(
                        "G0-G4 pack-mosaic recipe bounds".into(),
                    ));
                }
                (mosaic_decode(&roots, &pack[offset..end], length)?, sha)
            }
        };
        if raw.len() as u64 > MAX_CHUNK || sha256(&raw) != expected {
            return Err(PortableError::Integrity(
                "G0-G4 logical node identity mismatch".into(),
            ));
        }
        let value = Arc::new(raw);
        if self.node_cache_bytes.saturating_add(value.len()) <= MAX_NODE_CACHE_BYTES {
            self.node_cache_bytes += value.len();
            self.node_cache.insert(node_id, Arc::clone(&value));
        }
        Ok(value)
    }
}

fn read_primary(file: &mut File) -> Result<AuthMeta, PortableError> {
    file.seek(SeekFrom::Start(0))?;
    let mut header = [0u8; HEADER_SIZE as usize];
    file.read_exact(&mut header)?;
    if &header[0..8] != MAGIC {
        return Err(PortableError::Format("not G0-G4 archive".into()));
    }
    let compressed_size = u64_le(&header[8..16])?;
    let raw_size = u64_le(&header[16..24])?;
    let count = u32_le(&header[24..28])? as usize;
    let max_decode = u64_le(&header[28..36])?;
    let max_memory = u64_le(&header[36..44])?;
    if compressed_size > MAX_META_BYTES
        || raw_size > MAX_META_BYTES
        || count > MAX_NODES
        || max_decode > MAX_DECODE_UNIT
        || max_memory > MAX_DECODER_MEMORY
    {
        return Err(PortableError::Limit(
            "G0-G4 primary resource declaration exceeds policy".into(),
        ));
    }
    let expected: [u8; 32] = header[44..76]
        .try_into()
        .map_err(|_| PortableError::Format("G0-G4 metadata SHA field".into()))?;
    let merkle: [u8; 32] = header[76..108]
        .try_into()
        .map_err(|_| PortableError::Format("G0-G4 Merkle field".into()))?;
    let mut compressed = vec![0u8; compressed_size as usize];
    file.read_exact(&mut compressed)?;
    let raw = bounded_zstd_decode(&compressed, raw_size, MAX_META_BYTES, None)?;
    if sha256(&raw) != expected {
        return Err(PortableError::Integrity(
            "G0-G4 primary metadata authentication".into(),
        ));
    }
    Ok(AuthMeta {
        value: parse_msgpack(&raw)?,
        compressed_size,
        meta_sha: expected,
        merkle,
        expected_count: Some(count),
        tail_offset: None,
    })
}

fn read_tail(file: &mut File, file_len: u64) -> Result<AuthMeta, PortableError> {
    if file_len < FOOTER_SIZE {
        return Err(PortableError::Format("short G0-G4 tail".into()));
    }
    file.seek(SeekFrom::Start(file_len - FOOTER_SIZE))?;
    let mut footer = [0u8; FOOTER_SIZE as usize];
    file.read_exact(&mut footer)?;
    if &footer[0..8] != TAIL {
        return Err(PortableError::Format("G0-G4 tail magic".into()));
    }
    let compressed_size = u64_le(&footer[8..16])?;
    let raw_size = u64_le(&footer[16..24])?;
    if compressed_size > MAX_META_BYTES || raw_size > MAX_META_BYTES {
        return Err(PortableError::Limit(
            "G0-G4 tail metadata declaration exceeds policy".into(),
        ));
    }
    let expected: [u8; 32] = footer[24..56]
        .try_into()
        .map_err(|_| PortableError::Format("G0-G4 tail metadata SHA field".into()))?;
    let merkle: [u8; 32] = footer[56..88]
        .try_into()
        .map_err(|_| PortableError::Format("G0-G4 tail Merkle field".into()))?;
    let tail_offset = file_len
        .checked_sub(FOOTER_SIZE)
        .and_then(|value| value.checked_sub(compressed_size))
        .ok_or_else(|| PortableError::Format("G0-G4 tail metadata offset".into()))?;
    if tail_offset < HEADER_SIZE {
        return Err(PortableError::Format("G0-G4 tail overlaps header".into()));
    }
    file.seek(SeekFrom::Start(tail_offset))?;
    let mut compressed = vec![0u8; compressed_size as usize];
    file.read_exact(&mut compressed)?;
    let raw = bounded_zstd_decode(&compressed, raw_size, MAX_META_BYTES, None)?;
    if sha256(&raw) != expected {
        return Err(PortableError::Integrity(
            "G0-G4 tail metadata authentication".into(),
        ));
    }
    Ok(AuthMeta {
        value: parse_msgpack(&raw)?,
        compressed_size,
        meta_sha: expected,
        merkle,
        expected_count: None,
        tail_offset: Some(tail_offset),
    })
}

fn parse_meta(value: &Value, expected_count: Option<usize>) -> Result<ParsedMeta, PortableError> {
    let map = as_map(value, "G0-G4 metadata")?;
    if text(field(map, "engine")?, "G0-G4 engine")? != ENGINE {
        return Err(PortableError::Format("unsupported G0-G4 engine".into()));
    }
    let tree_sha = tree_digest(text(field(map, "tree_sha256")?, "G0-G4 tree SHA")?)?;
    let leaves_value = as_array(field(map, "record_leaf_sha256")?, "G0-G4 record leaves")?;
    let offsets_value = as_array(field(map, "record_rel_offsets")?, "G0-G4 record offsets")?;
    let transforms_value = as_array(field(map, "physical_geometry")?, "G0-G4 geometry table")?;
    if leaves_value.len() > MAX_NODES
        || leaves_value.len() != offsets_value.len()
        || leaves_value.len() != transforms_value.len()
        || expected_count.is_some_and(|count| count != leaves_value.len())
    {
        return Err(PortableError::Format(
            "G0-G4 physical table length declaration".into(),
        ));
    }
    let leaves = leaves_value
        .iter()
        .map(|value| digest32(value, "G0-G4 payload leaf"))
        .collect::<Result<Vec<_>, _>>()?;
    let mut offsets = Vec::with_capacity(offsets_value.len());
    let mut previous = None;
    for value in offsets_value {
        let offset = uint(value, "G0-G4 record offset", u64::MAX)?;
        if previous.is_none() && offset != 0 {
            return Err(PortableError::Format(
                "G0-G4 first record offset must be zero".into(),
            ));
        }
        if previous.is_some_and(|prior| offset <= prior) {
            return Err(PortableError::Format(
                "G0-G4 record offsets are not strictly increasing".into(),
            ));
        }
        previous = Some(offset);
        offsets.push(offset);
    }
    let transforms = transforms_value
        .iter()
        .map(parse_transform)
        .collect::<Result<Vec<_>, _>>()?;

    validate_hierarchical_contract(field(map, "hierarchical_geometry")?)?;
    let declared_amplification = optional_field(map, "max_geometry_member_read_amplification")
        .map(|value| number(value, "G0-G4 member read amplification"))
        .transpose()?
        .unwrap_or(MAX_MEMBER_READ_AMP);
    if !declared_amplification.is_finite() || declared_amplification > MAX_MEMBER_READ_AMP {
        return Err(PortableError::Limit(
            "G0-G4 locality declaration exceeds release policy".into(),
        ));
    }
    if let Some(value) = optional_field(map, "max_decode_unit") {
        uint(value, "G0-G4 max decode unit", MAX_DECODE_UNIT)?;
    }
    if let Some(value) = optional_field(map, "max_decoder_memory") {
        uint(value, "G0-G4 max decoder memory", MAX_DECODER_MEMORY)?;
    }

    let node_values = as_array(field(map, "nodes")?, "G0-G4 nodes")?;
    if node_values.len() > MAX_NODES {
        return Err(PortableError::Limit("G0-G4 node count exceeds policy".into()));
    }
    let mut nodes = Vec::with_capacity(node_values.len());
    for value in node_values {
        nodes.push(parse_node(value, node_values.len(), leaves.len())?);
    }
    for node in &nodes {
        match node {
            Node::Delta { base, .. } | Node::DeltaPack { base, .. } => {
                if !nodes.get(*base).is_some_and(Node::is_direct) {
                    return Err(PortableError::Format(
                        "G0-G4 delta dependency depth exceeds one".into(),
                    ));
                }
            }
            Node::Mosaic { bases, .. } | Node::PackMosaic { bases, .. } => {
                if bases.iter().any(|base| !nodes.get(*base).is_some_and(Node::is_direct)) {
                    return Err(PortableError::Format(
                        "G0-G4 mosaic dependency depth exceeds one".into(),
                    ));
                }
            }
            Node::Direct { .. } => {}
        }
    }

    let file_map = as_map(field(map, "files")?, "G0-G4 files")?;
    if file_map.is_empty() || file_map.len() > MAX_FILES {
        return Err(PortableError::Format("G0-G4 file-count declaration".into()));
    }
    let mut files = BTreeMap::new();
    let mut aggregate = 0u64;
    for (key, value) in file_map {
        let rel = text(key, "G0-G4 logical path")?;
        safe_relpath(rel)?;
        let file = parse_file(value, nodes.len(), leaves.len())?;
        let size = match &file {
            GFile::Preflate { size, .. } | GFile::Nodes { size, .. } => *size,
        };
        aggregate = aggregate
            .checked_add(size)
            .ok_or_else(|| PortableError::Limit("G0-G4 aggregate logical size overflow".into()))?;
        if aggregate > MAX_DECLARED_LOGICAL_BYTES {
            return Err(PortableError::Limit(
                "G0-G4 aggregate logical size exceeds policy".into(),
            ));
        }
        if files.insert(rel.to_owned(), file).is_some() {
            return Err(PortableError::Format("duplicate G0-G4 logical path".into()));
        }
    }

    Ok(ParsedMeta {
        files,
        nodes,
        offsets,
        leaves,
        transforms,
        tree_sha,
        declared_amplification,
    })
}

fn parse_transform(value: &Value) -> Result<Transform, PortableError> {
    if value.is_nil() {
        return Ok(Transform::None);
    }
    let row = as_array(value, "G0-G4 transform")?;
    let kind = row
        .first()
        .map(|value| text(value, "G0-G4 transform kind"))
        .transpose()?
        .ok_or_else(|| PortableError::Format("empty G0-G4 transform".into()))?;
    match kind {
        "lane" if row.len() == 3 => {
            let width = uint(&row[1], "G0-G4 lane width", 16)?;
            if !LANE_WIDTHS.contains(&width) {
                return Err(PortableError::Format("unsupported G0-G4 lane width".into()));
            }
            let logical_size = uint(&row[2], "G0-G4 lane logical size", MAX_DECODE_UNIT)?;
            Ok(Transform::Lane {
                width: width as usize,
                logical_size: logical_size as usize,
            })
        }
        "delimiter" if row.len() == 3 => Ok(Transform::Delimiter {
            delimiter: uint(&row[1], "G0-G4 delimiter byte", 255)? as u8,
            logical_size: uint(&row[2], "G0-G4 delimiter logical size", MAX_DECODE_UNIT)? as usize,
        }),
        "hierarchical" if row.len() == 5 => Ok(Transform::Hierarchical {
            primary: uint(&row[1], "G0-G4 hierarchy primary", 255)? as u8,
            secondary: uint(&row[2], "G0-G4 hierarchy secondary", 255)? as u8,
            prefix_planes: match uint(&row[3], "G0-G4 hierarchy prefix flag", 1)? {
                0 => false,
                1 => true,
                _ => unreachable!(),
            },
            logical_size: uint(&row[4], "G0-G4 hierarchy logical size", MAX_DECODE_UNIT)? as usize,
        }),
        _ => Err(PortableError::Format(
            "unknown/malformed G0-G4 transform descriptor".into(),
        )),
    }
}

fn parse_node(value: &Value, node_count: usize, record_count: usize) -> Result<Node, PortableError> {
    let row = as_array(value, "G0-G4 node")?;
    let kind = row
        .first()
        .map(|value| text(value, "G0-G4 node kind"))
        .transpose()?
        .ok_or_else(|| PortableError::Format("empty G0-G4 node".into()))?;
    let node_id = |value: &Value, label: &str| -> Result<usize, PortableError> {
        Ok(uint(value, label, node_count.saturating_sub(1) as u64)? as usize)
    };
    let record_id = |value: &Value, label: &str| -> Result<usize, PortableError> {
        Ok(uint(value, label, record_count.saturating_sub(1) as u64)? as usize)
    };
    let chunk = |value: &Value, label: &str| -> Result<usize, PortableError> {
        Ok(uint(value, label, MAX_CHUNK)? as usize)
    };
    match kind {
        "direct" if row.len() == 5 => Ok(Node::Direct {
            record: record_id(&row[1], "G0-G4 direct record id")?,
            offset: uint(&row[2], "G0-G4 direct offset", MAX_DECODE_UNIT)? as usize,
            length: chunk(&row[3], "G0-G4 direct length")?,
            sha: digest32(&row[4], "G0-G4 direct node digest")?,
        }),
        "delta" if row.len() == 5 => Ok(Node::Delta {
            base: node_id(&row[1], "G0-G4 delta base id")?,
            record: record_id(&row[2], "G0-G4 delta record id")?,
            length: chunk(&row[3], "G0-G4 delta length")?,
            sha: digest32(&row[4], "G0-G4 delta node digest")?,
        }),
        "delta_pack" if row.len() == 7 => Ok(Node::DeltaPack {
            base: node_id(&row[1], "G0-G4 packed-delta base id")?,
            record: record_id(&row[2], "G0-G4 packed-delta record id")?,
            recipe_offset: uint(&row[3], "G0-G4 packed-delta offset", MAX_RESIDUAL_PACK)? as usize,
            recipe_len: uint(&row[4], "G0-G4 packed-delta length", MAX_RESIDUAL_PACK)? as usize,
            length: chunk(&row[5], "G0-G4 packed-delta logical length")?,
            sha: digest32(&row[6], "G0-G4 packed-delta digest")?,
        }),
        "mosaic" if row.len() == 5 => {
            let bases = parse_bases(&row[1], node_count)?;
            Ok(Node::Mosaic {
                bases,
                record: record_id(&row[2], "G0-G4 mosaic record id")?,
                length: chunk(&row[3], "G0-G4 mosaic length")?,
                sha: digest32(&row[4], "G0-G4 mosaic digest")?,
            })
        }
        "pack_mosaic" if row.len() == 7 => {
            let bases = parse_bases(&row[4], node_count)?;
            Ok(Node::PackMosaic {
                record: record_id(&row[1], "G0-G4 pack-mosaic record id")?,
                offset: uint(&row[2], "G0-G4 pack-mosaic offset", MAX_DECODE_UNIT)? as usize,
                recipe_len: uint(&row[3], "G0-G4 pack-mosaic recipe length", MAX_DECODE_UNIT)? as usize,
                bases,
                length: chunk(&row[5], "G0-G4 pack-mosaic logical length")?,
                sha: digest32(&row[6], "G0-G4 pack-mosaic digest")?,
            })
        }
        _ => Err(PortableError::Format(
            "unknown/malformed G0-G4 node descriptor".into(),
        )),
    }
}

fn parse_bases(value: &Value, node_count: usize) -> Result<Vec<usize>, PortableError> {
    let values = as_array(value, "G0-G4 mosaic bases")?;
    if values.len() < 2 || values.len() > MAX_MOSAIC_BASES {
        return Err(PortableError::Format("G0-G4 mosaic base count".into()));
    }
    let mut seen = HashSet::with_capacity(values.len());
    let mut out = Vec::with_capacity(values.len());
    for value in values {
        let id = uint(value, "G0-G4 mosaic base id", node_count.saturating_sub(1) as u64)? as usize;
        if !seen.insert(id) {
            return Err(PortableError::Format("duplicate G0-G4 mosaic base id".into()));
        }
        out.push(id);
    }
    Ok(out)
}

fn parse_file(value: &Value, node_count: usize, record_count: usize) -> Result<GFile, PortableError> {
    let row = as_array(value, "G0-G4 file descriptor")?;
    let kind = row
        .first()
        .map(|value| text(value, "G0-G4 file kind"))
        .transpose()?
        .ok_or_else(|| PortableError::Format("empty G0-G4 file descriptor".into()))?;
    match kind {
        "preflate" if row.len() == 4 => Ok(GFile::Preflate {
            record: uint(&row[1], "G0-G4 preflate record id", record_count.saturating_sub(1) as u64)? as usize,
            size: uint(&row[2], "G0-G4 preflate logical size", MAX_DECODE_UNIT)?,
            sha: digest32(&row[3], "G0-G4 preflate file digest")?,
        }),
        "nodes" if row.len() == 4 => {
            let ids = as_array(&row[1], "G0-G4 file node list")?;
            let mut nodes = Vec::with_capacity(ids.len());
            let mut expected = 0u64;
            for id in ids {
                let id = uint(id, "G0-G4 file node id", node_count.saturating_sub(1) as u64)? as usize;
                nodes.push(id);
                // Exact node-length sum is checked after all nodes are parsed by the caller's file stream.
                expected = expected.saturating_add(1);
            }
            let size = uint(&row[2], "G0-G4 file logical size", MAX_DECLARED_LOGICAL_BYTES)?;
            let _ = expected;
            Ok(GFile::Nodes {
                nodes,
                size,
                sha: digest32(&row[3], "G0-G4 file digest")?,
            })
        }
        _ => Err(PortableError::Format(
            "unknown/malformed G0-G4 file descriptor".into(),
        )),
    }
}

fn validate_hierarchical_contract(value: &Value) -> Result<(), PortableError> {
    let map = as_map(value, "G0-G4 hierarchical resource contract")?;
    if map.len() != 7 {
        return Err(PortableError::Format(
            "G0-G4 hierarchical resource contract drift".into(),
        ));
    }
    let expected = [
        ("max_rows", HG_MAX_ROWS),
        ("max_fields_per_row", HG_MAX_FIELDS_PER_ROW),
        ("max_field_descriptors", HG_MAX_FIELD_DESCRIPTORS),
        ("max_cell_scans", HG_MAX_CELL_SCANS),
        ("max_exact_finalists", HG_MAX_EXACT_FINALISTS),
        ("screen_level", HG_SCREEN_LEVEL),
        ("exact_level", HG_EXACT_LEVEL),
    ];
    for (name, expected) in expected {
        if uint(field(map, name)?, name, expected)? != expected {
            return Err(PortableError::Format(
                "G0-G4 hierarchical resource contract drift".into(),
            ));
        }
    }
    Ok(())
}

fn get_varint(buf: &[u8], pos: &mut usize) -> Result<u64, PortableError> {
    let mut value = 0u64;
    let mut shift = 0u32;
    for _ in 0..10 {
        let byte = *buf
            .get(*pos)
            .ok_or_else(|| PortableError::Format("short r25 varint".into()))?;
        *pos += 1;
        value |= u64::from(byte & 0x7f) << shift;
        if byte & 0x80 == 0 {
            return Ok(value);
        }
        shift += 7;
    }
    Err(PortableError::Format("overlong r25 varint".into()))
}

fn lane_inverse(stored: &[u8], width: usize, logical_size: usize) -> Result<Vec<u8>, PortableError> {
    if !LANE_WIDTHS.contains(&(width as u64)) || stored.len() != logical_size {
        return Err(PortableError::Format("invalid G0-G4 lane descriptor".into()));
    }
    let full = logical_size - logical_size % width;
    let rows = full / width;
    let mut out = vec![0u8; logical_size];
    for lane in 0..width {
        let start = lane * rows;
        let end = start + rows;
        for (row, byte) in stored[start..end].iter().copied().enumerate() {
            out[row * width + lane] = byte;
        }
    }
    out[full..].copy_from_slice(&stored[full..]);
    Ok(out)
}

fn delimiter_inverse(encoded: &[u8], descriptor_delimiter: u8, logical_size: usize) -> Result<Vec<u8>, PortableError> {
    if encoded.len() < 6
        || &encoded[0..4] != b"DGO1"
        || encoded[4] != descriptor_delimiter
        || logical_size as u64 > MAX_OVERLAY_RECORD
    {
        return Err(PortableError::Format("invalid G0-G4 delimiter descriptor".into()));
    }
    let mut pos = 5;
    let count = get_varint(encoded, &mut pos)?;
    if count == 0 || count > MAX_DELIMITER_SEGMENTS {
        return Err(PortableError::Limit("G0-G4 delimiter segment count".into()));
    }
    let mut lengths = Vec::with_capacity(count as usize);
    let mut members = 0u64;
    let mut max_len = 0u64;
    for _ in 0..count {
        let len = get_varint(encoded, &mut pos)?;
        members = members
            .checked_add(len)
            .ok_or_else(|| PortableError::Limit("G0-G4 delimiter length overflow".into()))?;
        if members > MAX_OVERLAY_RECORD {
            return Err(PortableError::Limit("G0-G4 delimiter length budget".into()));
        }
        max_len = max_len.max(len);
        lengths.push(len as usize);
    }
    if members + count - 1 != logical_size as u64
        || count.saturating_mul(max_len) > MAX_DELIMITER_CELL_SCANS
        || encoded.len().saturating_sub(pos) as u64 != members
    {
        return Err(PortableError::Format(
            "G0-G4 delimiter logical/body declaration mismatch".into(),
        ));
    }
    let mut rows: Vec<Vec<u8>> = lengths.iter().map(|len| vec![0u8; *len]).collect();
    let mut cursor = pos;
    for column in 0..max_len as usize {
        for (row, len) in rows.iter_mut().zip(&lengths) {
            if column < *len {
                row[column] = encoded[cursor];
                cursor += 1;
            }
        }
    }
    if cursor != encoded.len() {
        return Err(PortableError::Format(
            "trailing G0-G4 delimiter payload".into(),
        ));
    }
    let mut out = Vec::with_capacity(logical_size);
    for (index, row) in rows.into_iter().enumerate() {
        if index != 0 {
            out.push(descriptor_delimiter);
        }
        out.extend_from_slice(&row);
    }
    Ok(out)
}

fn hierarchy_inverse(
    encoded: &[u8],
    descriptor_primary: u8,
    descriptor_secondary: u8,
    descriptor_prefix: bool,
    logical_size: usize,
) -> Result<Vec<u8>, PortableError> {
    if encoded.len() < 7
        || (&encoded[0..4] != HG_MAGIC_PLAIN && &encoded[0..4] != HG_MAGIC_PREFIX)
        || encoded[4] != descriptor_primary
        || encoded[5] != descriptor_secondary
        || descriptor_primary == descriptor_secondary
        || (&encoded[0..4] == HG_MAGIC_PREFIX) != descriptor_prefix
    {
        return Err(PortableError::Format(
            "invalid G0-G4 hierarchical descriptor/physical identity".into(),
        ));
    }
    let prefix = descriptor_prefix;
    let mut pos = 6;
    let row_count = get_varint(encoded, &mut pos)?;
    if row_count == 0 || row_count > HG_MAX_ROWS {
        return Err(PortableError::Limit("hierarchical row count".into()));
    }
    let mut lengths: Vec<Vec<usize>> = Vec::with_capacity(row_count as usize);
    let mut total_fields = 0u64;
    let mut total_field_bytes = 0u64;
    let mut max_fields = 0usize;
    let mut separator_bytes = row_count - 1;
    for _ in 0..row_count {
        let field_count = get_varint(encoded, &mut pos)?;
        if field_count == 0 || field_count > HG_MAX_FIELDS_PER_ROW {
            return Err(PortableError::Limit("hierarchical field count".into()));
        }
        total_fields += field_count;
        if total_fields > HG_MAX_FIELD_DESCRIPTORS {
            return Err(PortableError::Limit(
                "hierarchical field descriptor count".into(),
            ));
        }
        let mut row = Vec::with_capacity(field_count as usize);
        for _ in 0..field_count {
            let len = get_varint(encoded, &mut pos)?;
            total_field_bytes = total_field_bytes
                .checked_add(len)
                .ok_or_else(|| PortableError::Limit("hierarchical field byte overflow".into()))?;
            if len > MAX_CHUNK || total_field_bytes > MAX_CHUNK {
                return Err(PortableError::Limit("hierarchical field length budget".into()));
            }
            row.push(len as usize);
        }
        separator_bytes += field_count - 1;
        max_fields = max_fields.max(row.len());
        lengths.push(row);
    }
    if row_count.saturating_mul(max_fields as u64) > HG_MAX_CELL_SCANS
        || total_field_bytes + separator_bytes != logical_size as u64
        || logical_size as u64 > MAX_CHUNK
    {
        return Err(PortableError::Format(
            "hierarchical logical/work declaration mismatch".into(),
        ));
    }
    let mut prefixes: Vec<Vec<usize>> = lengths.iter().map(|row| vec![0; row.len()]).collect();
    if prefix {
        for column in 0..max_fields {
            let mut previous_len = 0usize;
            for (row_index, row) in lengths.iter().enumerate() {
                if column >= row.len() {
                    continue;
                }
                let prefix_len = get_varint(encoded, &mut pos)? as usize;
                if prefix_len > previous_len.min(row[column]) {
                    return Err(PortableError::Format(
                        "hierarchical prefix exceeds neighboring field".into(),
                    ));
                }
                prefixes[row_index][column] = prefix_len;
                previous_len = row[column];
            }
        }
    }
    let mut rows: Vec<Vec<Vec<u8>>> = lengths
        .iter()
        .map(|row| row.iter().map(|_| Vec::new()).collect())
        .collect();
    let mut cursor = pos;
    for column in 0..max_fields {
        let mut previous = Vec::new();
        for (row_index, row) in lengths.iter().enumerate() {
            if column >= row.len() {
                continue;
            }
            let len = row[column];
            let prefix_len = prefixes[row_index][column];
            let suffix_len = len - prefix_len;
            let end = cursor
                .checked_add(suffix_len)
                .ok_or_else(|| PortableError::Limit("hierarchical payload offset overflow".into()))?;
            if end > encoded.len() {
                return Err(PortableError::Format("short hierarchical payload".into()));
            }
            let mut field = Vec::with_capacity(len);
            field.extend_from_slice(&previous[..prefix_len]);
            field.extend_from_slice(&encoded[cursor..end]);
            if field.len() != len {
                return Err(PortableError::Integrity(
                    "hierarchical field reconstruction length".into(),
                ));
            }
            rows[row_index][column] = field.clone();
            previous = field;
            cursor = end;
        }
    }
    if cursor != encoded.len() {
        return Err(PortableError::Format(
            "trailing hierarchical payload".into(),
        ));
    }
    let mut out = Vec::with_capacity(logical_size);
    for (row_index, row) in rows.iter().enumerate() {
        if row_index != 0 {
            out.push(descriptor_primary);
        }
        for (field_index, field) in row.iter().enumerate() {
            if field_index != 0 {
                out.push(descriptor_secondary);
            }
            out.extend_from_slice(field);
        }
    }
    if out.len() != logical_size {
        return Err(PortableError::Integrity(
            "hierarchical inverse logical size mismatch".into(),
        ));
    }
    Ok(out)
}

fn delta_decode(base: &[u8], payload: &[u8], expected_size: usize) -> Result<Vec<u8>, PortableError> {
    let mut out = Vec::with_capacity(expected_size);
    let mut pos = 0usize;
    while pos < payload.len() {
        let tag = payload[pos];
        pos += 1;
        match tag {
            0 => {
                let len = get_varint(payload, &mut pos)? as usize;
                let end = pos
                    .checked_add(len)
                    .ok_or_else(|| PortableError::Limit("delta literal offset overflow".into()))?;
                if end > payload.len() || len > expected_size.saturating_sub(out.len()) {
                    return Err(PortableError::Format("delta literal exceeds bounds".into()));
                }
                out.extend_from_slice(&payload[pos..end]);
                pos = end;
            }
            1 => {
                let offset = get_varint(payload, &mut pos)? as usize;
                let len = get_varint(payload, &mut pos)? as usize;
                let end = offset
                    .checked_add(len)
                    .ok_or_else(|| PortableError::Limit("delta copy offset overflow".into()))?;
                if end > base.len() || len > expected_size.saturating_sub(out.len()) {
                    return Err(PortableError::Format("delta copy exceeds bounds".into()));
                }
                out.extend_from_slice(&base[offset..end]);
            }
            _ => return Err(PortableError::Format("unknown delta opcode".into())),
        }
    }
    if out.len() != expected_size {
        return Err(PortableError::Integrity(
            "delta reconstructed wrong length".into(),
        ));
    }
    Ok(out)
}

fn mosaic_decode(
    bases: &[Arc<Vec<u8>>],
    payload: &[u8],
    expected_size: usize,
) -> Result<Vec<u8>, PortableError> {
    if bases.len() > MAX_MOSAIC_BASES
        || bases.iter().map(|base| base.len() as u64).sum::<u64>() > MAX_MOSAIC_SOURCE_INDEX
    {
        return Err(PortableError::Limit("mosaic source policy".into()));
    }
    let mut out = Vec::with_capacity(expected_size);
    let mut pos = 0usize;
    while pos < payload.len() {
        let tag = payload[pos];
        pos += 1;
        match tag {
            0 => {
                let len = get_varint(payload, &mut pos)? as usize;
                let end = pos
                    .checked_add(len)
                    .ok_or_else(|| PortableError::Limit("mosaic literal offset overflow".into()))?;
                if end > payload.len() || len > expected_size.saturating_sub(out.len()) {
                    return Err(PortableError::Format("mosaic literal exceeds bounds".into()));
                }
                out.extend_from_slice(&payload[pos..end]);
                pos = end;
            }
            2 => {
                let slot = get_varint(payload, &mut pos)? as usize;
                let offset = get_varint(payload, &mut pos)? as usize;
                let len = get_varint(payload, &mut pos)? as usize;
                let base = bases.get(slot).ok_or_else(|| {
                    PortableError::Format("mosaic copy references missing base".into())
                })?;
                let end = offset
                    .checked_add(len)
                    .ok_or_else(|| PortableError::Limit("mosaic copy offset overflow".into()))?;
                if end > base.len() || len > expected_size.saturating_sub(out.len()) {
                    return Err(PortableError::Format("mosaic copy exceeds bounds".into()));
                }
                out.extend_from_slice(&base[offset..end]);
            }
            _ => return Err(PortableError::Format("unknown mosaic opcode".into())),
        }
    }
    if out.len() != expected_size {
        return Err(PortableError::Integrity(
            "mosaic reconstructed wrong length".into(),
        ));
    }
    Ok(out)
}

struct LimitedVec {
    inner: Vec<u8>,
    limit: usize,
}

impl Write for LimitedVec {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        if buf.len() > self.limit.saturating_sub(self.inner.len()) {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                "preflate reconstruction exceeds output ceiling",
            ));
        }
        self.inner.extend_from_slice(buf);
        Ok(buf.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

fn preflate_unpack(payload: &[u8], expected_size: u64) -> Result<Vec<u8>, PortableError> {
    if expected_size > MAX_DECODE_UNIT || payload.len() as u64 > MAX_DECODE_UNIT {
        return Err(PortableError::Limit("preflate record exceeds decode unit".into()));
    }
    let config = PreflateContainerConfig {
        max_chunk_size: MAX_DECODE_UNIT as usize,
        total_plain_text_limit: 64 * 1024 * 1024,
        chunk_plain_text_limit: 64 * 1024 * 1024,
        validate_compression: false,
        max_chain_length: 4096,
        ..PreflateContainerConfig::default()
    };
    let mut input = Cursor::new(payload);
    let mut output = LimitedVec {
        inner: Vec::with_capacity(expected_size as usize),
        limit: expected_size as usize,
    };
    let mut decoder = RecreateContainerProcessor::new(config.chunk_plain_text_limit);
    decoder
        .copy_to_end_size(&mut input, &mut output, MAX_DECODE_UNIT as usize)
        .map_err(|error| PortableError::Format(format!("preflate recreate: {error:?}")))?;
    if output.inner.len() as u64 != expected_size {
        return Err(PortableError::Integrity(format!(
            "preflate reconstructed {} bytes, expected {expected_size}",
            output.inner.len()
        )));
    }
    Ok(output.inner)
}
