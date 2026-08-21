use crate::format::{
    MAX_META_BYTES, as_array, as_map, bounded_zstd_decode, digest32, field, parse_msgpack, sha256,
    text, uint,
};
use crate::manifest::{FILESYSTEM_MANIFEST, FsKind, FsManifest};
use crate::{MemberReadStats, PortableEntry, PortableError};
use rmpv::Value;
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::{Cursor, Read, Seek, SeekFrom, Write};
use std::path::Path;
use std::sync::Mutex;

const MAGIC: &[u8; 8] = b"CMP25Z2\0";
const PROFILE: &str = "zip-framing-factor-compact-v2";
const VERSION: u64 = 2;
const TEMPLATE_MAGIC: &[u8; 4] = b"ZFT1";
const GROUP_MAGIC: &[u8; 4] = b"ZCG2";
const LOCAL: u32 = 0x0403_4b50;
const CENTRAL: u32 = 0x0201_4b50;
const EOCD: u32 = 0x0605_4b50;
const MAX_FILES: usize = 65_535;
const MAX_DECODE: u64 = 8 * 1024 * 1024;
const MAX_MEMBER_READ_AMP: f64 = 8.0;
const MAX_COMPRESSED_BLOB: u64 = MAX_DECODE + 1024 * 1024;

#[derive(Debug, Clone)]
struct TemplateRow {
    name: Vec<u8>,
    local_extra: Vec<u8>,
    version: u16,
    flags: u16,
    method: u16,
    mtime: u16,
    mdate: u16,
    made: u16,
    needed: u16,
    cflags: u16,
    cmethod: u16,
    cmtime: u16,
    cmdate: u16,
    disk: u16,
    internal_attr: u16,
    external_attr: u32,
    central_extra: Vec<u8>,
    central_comment: Vec<u8>,
}

#[derive(Debug, Clone)]
struct Template {
    rows: Vec<TemplateRow>,
    disk: u16,
    disk_cd: u16,
    comment: Vec<u8>,
}

#[derive(Debug, Clone)]
struct GroupDesc {
    raw_size: u64,
    raw_sha: [u8; 32],
    paths: Vec<String>,
    blob_offset: u64,
    blob_size: u64,
}

#[derive(Debug)]
pub(crate) struct ZipFactorArchive {
    entries: Vec<PortableEntry>,
    identities: Vec<(u64, [u8; 32])>,
    manifest_raw: Vec<u8>,
    manifest_index: usize,
    template_raw: Vec<u8>,
    template: Template,
    groups: Vec<GroupDesc>,
    path_group: HashMap<String, (usize, usize)>,
    declared_amplification: f64,
    file: Mutex<File>,
}

impl ZipFactorArchive {
    pub(crate) fn open(path: &Path) -> Result<Self, PortableError> {
        let mut file = File::open(path)?;
        let file_len = file.metadata()?.len();
        let mut magic = [0u8; 8];
        file.read_exact(&mut magic)?;
        if &magic != MAGIC {
            return Err(PortableError::Format(
                "not a compact ZIP-factor r25 archive".into(),
            ));
        }
        let mut raw4 = [0u8; 4];
        file.read_exact(&mut raw4)?;
        let meta_raw_size = u32::from_le_bytes(raw4) as u64;
        if meta_raw_size > MAX_META_BYTES {
            return Err(PortableError::Limit(
                "ZIP-factor metadata declaration exceeds policy".into(),
            ));
        }
        let meta_blob = read_blob(&mut file, MAX_COMPRESSED_BLOB)?;
        let meta_raw = bounded_zstd_decode(&meta_blob, meta_raw_size, MAX_META_BYTES, None)?;
        let meta_value = parse_msgpack(&meta_raw)?;
        let meta = as_map(&meta_value, "ZIP-factor metadata")?;
        if uint(field(meta, "v")?, "ZIP-factor metadata version", VERSION)? != VERSION
            || text(field(meta, "profile")?, "ZIP-factor metadata profile")? != PROFILE
        {
            return Err(PortableError::Format(
                "unsupported ZIP-factor metadata identity".into(),
            ));
        }
        let manifest_raw_size = uint(
            field(meta, "manifest_raw")?,
            "ZIP-factor manifest size",
            MAX_DECODE,
        )?;
        let manifest_sha = digest32(
            field(meta, "manifest_sha")?,
            "ZIP-factor manifest SHA-256",
        )?;
        let template_raw_size = uint(
            field(meta, "template_raw")?,
            "ZIP-factor template size",
            MAX_DECODE,
        )?;
        let template_sha = digest32(
            field(meta, "template_sha")?,
            "ZIP-factor template SHA-256",
        )?;
        let declared_amp = field(meta, "max_member_read_amplification")?
            .as_f64()
            .ok_or_else(|| {
                PortableError::Format("ZIP-factor amplification must be a finite number".into())
            })?;
        if !declared_amp.is_finite() || !(1.0..=MAX_MEMBER_READ_AMP).contains(&declared_amp) {
            return Err(PortableError::Limit(
                "ZIP-factor declared amplification exceeds policy".into(),
            ));
        }
        let declared_decode = uint(
            field(meta, "max_decode_unit")?,
            "ZIP-factor max decode unit",
            MAX_DECODE,
        )?;
        if declared_decode > MAX_DECODE {
            return Err(PortableError::Limit(
                "ZIP-factor declared decode unit exceeds policy".into(),
            ));
        }

        let group_values = as_array(field(meta, "groups")?, "ZIP-factor groups")?;
        if group_values.is_empty() || group_values.len() > MAX_FILES {
            return Err(PortableError::Limit(
                "ZIP-factor group count exceeds policy".into(),
            ));
        }
        let mut group_specs = Vec::with_capacity(group_values.len());
        let mut seen_paths = HashSet::new();
        for value in group_values {
            let row = as_array(value, "ZIP-factor group descriptor")?;
            if row.len() != 3 {
                return Err(PortableError::Format(
                    "malformed ZIP-factor group descriptor".into(),
                ));
            }
            let raw_size = uint(&row[0], "ZIP-factor group raw size", MAX_DECODE)?;
            let raw_sha = digest32(&row[1], "ZIP-factor group SHA-256")?;
            let paths = as_array(&row[2], "ZIP-factor group paths")?;
            if paths.is_empty() || paths.len() > MAX_FILES {
                return Err(PortableError::Limit(
                    "ZIP-factor group path count exceeds policy".into(),
                ));
            }
            let mut names = Vec::with_capacity(paths.len());
            for path in paths {
                let path = text(path, "ZIP-factor logical path")?.to_owned();
                crate::format::safe_relpath(&path)?;
                if !seen_paths.insert(path.clone()) {
                    return Err(PortableError::Format(
                        "duplicate ZIP-factor logical path".into(),
                    ));
                }
                names.push(path);
            }
            group_specs.push((raw_size, raw_sha, names));
        }
        if seen_paths.len() > MAX_FILES {
            return Err(PortableError::Limit(
                "ZIP-factor file count exceeds policy".into(),
            ));
        }

        let manifest_blob = read_blob(&mut file, MAX_COMPRESSED_BLOB)?;
        let manifest_raw =
            bounded_zstd_decode(&manifest_blob, manifest_raw_size, MAX_DECODE, None)?;
        if sha256(&manifest_raw) != manifest_sha {
            return Err(PortableError::Integrity(
                "ZIP-factor manifest SHA-256 mismatch".into(),
            ));
        }
        let template_blob = read_blob(&mut file, MAX_COMPRESSED_BLOB)?;
        let template_raw =
            bounded_zstd_decode(&template_blob, template_raw_size, MAX_DECODE, None)?;
        if sha256(&template_raw) != template_sha {
            return Err(PortableError::Integrity(
                "ZIP-factor template SHA-256 mismatch".into(),
            ));
        }
        let template = parse_template(&template_raw)?;

        let mut groups = Vec::with_capacity(group_specs.len());
        for (raw_size, raw_sha, paths) in group_specs {
            let blob_size = read_uvarint(&mut file)?;
            if blob_size > MAX_COMPRESSED_BLOB {
                return Err(PortableError::Limit(
                    "ZIP-factor compressed group exceeds policy".into(),
                ));
            }
            let blob_offset = file.stream_position()?;
            let end = blob_offset
                .checked_add(blob_size)
                .ok_or_else(|| PortableError::Limit("ZIP-factor group offset overflow".into()))?;
            if end > file_len {
                return Err(PortableError::Format(
                    "truncated ZIP-factor compressed group".into(),
                ));
            }
            file.seek(SeekFrom::Start(end))?;
            groups.push(GroupDesc {
                raw_size,
                raw_sha,
                paths,
                blob_offset,
                blob_size,
            });
        }
        if file.stream_position()? != file_len {
            return Err(PortableError::Format(
                "trailing bytes after ZIP-factor groups".into(),
            ));
        }

        // Parse the canonical filesystem manifest with a path-only provisional content index. The parser owns
        // filesystem grammar validation and verifies that the content-path set is exactly manifest + regular files.
        let mut provisional = Vec::with_capacity(seen_paths.len() + 1);
        provisional.push(PortableEntry {
            path: FILESYSTEM_MANIFEST.to_owned(),
            size: manifest_raw.len() as u64,
            kind: 0,
            mode: 0,
            mtime_ns: 0,
        });
        for group in &groups {
            for path in &group.paths {
                provisional.push(PortableEntry {
                    path: path.clone(),
                    size: 0,
                    kind: 0,
                    mode: 0,
                    mtime_ns: 0,
                });
            }
        }
        let manifest = FsManifest::parse(&manifest_raw, &provisional)?;
        let mut by_regular = HashMap::new();
        for entry in manifest.entries() {
            if let FsKind::File { size, sha256 } = &entry.kind {
                by_regular.insert(entry.path.clone(), (*size, *sha256));
            }
        }
        if by_regular.len() != seen_paths.len()
            || !seen_paths.iter().all(|path| by_regular.contains_key(path))
        {
            return Err(PortableError::Integrity(
                "ZIP-factor manifest regular set mismatch".into(),
            ));
        }

        let mut entries = Vec::with_capacity(seen_paths.len() + 1);
        let mut identities = Vec::with_capacity(seen_paths.len() + 1);
        let manifest_index = 0;
        entries.push(PortableEntry {
            path: FILESYSTEM_MANIFEST.to_owned(),
            size: manifest_raw.len() as u64,
            kind: 0,
            mode: 0,
            mtime_ns: 0,
        });
        identities.push((manifest_raw.len() as u64, manifest_sha));
        let mut path_group = HashMap::new();
        for (group_index, group) in groups.iter().enumerate() {
            for (file_index, path) in group.paths.iter().enumerate() {
                let (size, digest) = *by_regular
                    .get(path)
                    .expect("manifest regular checked above");
                entries.push(PortableEntry {
                    path: path.clone(),
                    size,
                    kind: 0,
                    mode: 0,
                    mtime_ns: 0,
                });
                identities.push((size, digest));
                path_group.insert(path.clone(), (group_index, file_index));
            }
        }

        Ok(Self {
            entries,
            identities,
            manifest_raw,
            manifest_index,
            template_raw,
            template,
            groups,
            path_group,
            declared_amplification: declared_amp,
            file: Mutex::new(file),
        })
    }

    pub(crate) fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    pub(crate) fn entry_identity(&self, index: usize) -> Result<(u64, [u8; 32]), PortableError> {
        self.identities
            .get(index)
            .copied()
            .ok_or_else(|| PortableError::Format("ZIP-factor member id out of range".into()))
    }

    pub(crate) fn tail_authenticated(&self) -> bool {
        false
    }

    pub(crate) fn declared_amplification(&self) -> f64 {
        self.declared_amplification
    }

    fn group_raw(&self, index: usize) -> Result<Vec<u8>, PortableError> {
        let group = self
            .groups
            .get(index)
            .ok_or_else(|| PortableError::Format("ZIP-factor group id out of range".into()))?;
        let size = usize::try_from(group.blob_size)
            .map_err(|_| PortableError::Limit("ZIP-factor blob size does not fit host".into()))?;
        let mut blob = vec![0u8; size];
        let mut file = self
            .file
            .lock()
            .map_err(|_| PortableError::IoState("ZIP-factor file lock poisoned".into()))?;
        file.seek(SeekFrom::Start(group.blob_offset))?;
        file.read_exact(&mut blob)?;
        drop(file);
        let raw = bounded_zstd_decode(&blob, group.raw_size, MAX_DECODE, None)?;
        if sha256(&raw) != group.raw_sha {
            return Err(PortableError::Integrity(
                "ZIP-factor group SHA-256 mismatch".into(),
            ));
        }
        Ok(raw)
    }

    fn decode_path(&self, path: &str) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let (group_index, wanted_index) = *self.path_group.get(path).ok_or_else(|| {
            PortableError::Format("ZIP-factor path not present in group index".into())
        })?;
        let group = &self.groups[group_index];
        let raw = self.group_raw(group_index)?;
        let mut cursor = Cursor::new(raw.as_slice());
        let mut magic = [0u8; 4];
        cursor.read_exact(&mut magic)?;
        if &magic != GROUP_MAGIC {
            return Err(PortableError::Format("bad ZIP-factor group magic".into()));
        }
        let count = read_uvarint(&mut cursor)?;
        if count as usize != group.paths.len() {
            return Err(PortableError::Integrity(
                "ZIP-factor group file-count mismatch".into(),
            ));
        }
        let mut selected = None;
        for file_index in 0..count as usize {
            let mut dynamics = Vec::with_capacity(self.template.rows.len());
            for _ in &self.template.rows {
                let crc = read_u32(&mut cursor)?;
                let csize = read_u32(&mut cursor)?;
                let usize_ = read_u32(&mut cursor)?;
                if csize as u64 > MAX_DECODE {
                    return Err(PortableError::Limit(
                        "ZIP-factor compressed member payload exceeds policy".into(),
                    ));
                }
                let mut payload = vec![0u8; csize as usize];
                cursor.read_exact(&mut payload)?;
                dynamics.push((crc, csize, usize_, payload));
            }
            if file_index == wanted_index {
                selected = Some(rebuild_zip(&self.template, &dynamics)?);
            }
        }
        if cursor.position() != raw.len() as u64 {
            return Err(PortableError::Format(
                "ZIP-factor group trailing bytes".into(),
            ));
        }
        let restored = selected.ok_or_else(|| {
            PortableError::Integrity("ZIP-factor selected file missing from group".into())
        })?;
        let entry_index = self
            .entries
            .iter()
            .position(|entry| entry.path == path)
            .ok_or_else(|| {
                PortableError::Integrity("ZIP-factor logical path disappeared".into())
            })?;
        let (expected_size, expected_sha) = self.identities[entry_index];
        if restored.len() as u64 != expected_size || sha256(&restored) != expected_sha {
            return Err(PortableError::Integrity(format!(
                "ZIP-factor reconstructed identity mismatch: {path}"
            )));
        }
        let decoded_context = self.template_raw.len() as u64 + raw.len() as u64;
        let amplification = decoded_context as f64 / expected_size.max(1) as f64;
        if decoded_context > MAX_DECODE || amplification > MAX_MEMBER_READ_AMP {
            return Err(PortableError::Limit(format!(
                "ZIP-factor locality ceiling exceeded: {path}"
            )));
        }
        Ok((
            restored,
            MemberReadStats {
                logical_bytes: expected_size,
                decoded_context_bytes: decoded_context,
                amplification,
                profile: PROFILE,
            },
        ))
    }

    pub(crate) fn read_member(
        &self,
        index: usize,
    ) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        if index == self.manifest_index {
            let raw = self.manifest_raw.clone();
            return Ok((
                raw.clone(),
                MemberReadStats {
                    logical_bytes: raw.len() as u64,
                    decoded_context_bytes: raw.len() as u64,
                    amplification: 1.0,
                    profile: PROFILE,
                },
            ));
        }
        let path = self
            .entries
            .get(index)
            .ok_or_else(|| PortableError::Format("ZIP-factor member id out of range".into()))?
            .path
            .clone();
        self.decode_path(&path)
    }

    pub(crate) fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        let (raw, stats) = self.read_member(index)?;
        output.write_all(&raw)?;
        Ok(stats)
    }

    pub(crate) fn verify(&self) -> Result<(), PortableError> {
        for index in 0..self.entries.len() {
            let (raw, _stats) = self.read_member(index)?;
            let (size, digest) = self.identities[index];
            if raw.len() as u64 != size || sha256(&raw) != digest {
                return Err(PortableError::Integrity(
                    "ZIP-factor full verification identity mismatch".into(),
                ));
            }
        }
        Ok(())
    }
}

fn read_u32<R: Read>(reader: &mut R) -> Result<u32, PortableError> {
    let mut raw = [0u8; 4];
    reader.read_exact(&mut raw)?;
    Ok(u32::from_le_bytes(raw))
}

fn read_uvarint<R: Read>(reader: &mut R) -> Result<u64, PortableError> {
    let mut value = 0u64;
    for shift in (0..70).step_by(7) {
        let mut raw = [0u8; 1];
        reader.read_exact(&mut raw)?;
        value |= u64::from(raw[0] & 0x7f) << shift;
        if raw[0] & 0x80 == 0 {
            return Ok(value);
        }
    }
    Err(PortableError::Format(
        "oversized ZIP-factor uvarint".into(),
    ))
}

fn read_blob(file: &mut File, limit: u64) -> Result<Vec<u8>, PortableError> {
    let size = read_uvarint(file)?;
    if size > limit {
        return Err(PortableError::Limit(
            "ZIP-factor compressed blob exceeds policy".into(),
        ));
    }
    let size = usize::try_from(size)
        .map_err(|_| PortableError::Limit("ZIP-factor blob does not fit host".into()))?;
    let mut out = vec![0u8; size];
    file.read_exact(&mut out)?;
    Ok(out)
}

fn read_mem_uvarint(cursor: &mut Cursor<&[u8]>) -> Result<u64, PortableError> {
    read_uvarint(cursor)
}

fn read_mem_blob(cursor: &mut Cursor<&[u8]>) -> Result<Vec<u8>, PortableError> {
    let size = read_mem_uvarint(cursor)?;
    if size > MAX_DECODE {
        return Err(PortableError::Limit(
            "ZIP-factor template blob exceeds policy".into(),
        ));
    }
    let mut out = vec![0u8; size as usize];
    cursor.read_exact(&mut out)?;
    Ok(out)
}

fn narrow_u16(value: u64, label: &str) -> Result<u16, PortableError> {
    u16::try_from(value)
        .map_err(|_| PortableError::Format(format!("ZIP-factor {label} exceeds u16")))
}

fn narrow_u32(value: u64, label: &str) -> Result<u32, PortableError> {
    u32::try_from(value)
        .map_err(|_| PortableError::Format(format!("ZIP-factor {label} exceeds u32")))
}

fn parse_template(raw: &[u8]) -> Result<Template, PortableError> {
    let mut cursor = Cursor::new(raw);
    let mut magic = [0u8; 4];
    cursor.read_exact(&mut magic)?;
    if &magic != TEMPLATE_MAGIC {
        return Err(PortableError::Format(
            "bad ZIP-factor template magic".into(),
        ));
    }
    let count = read_mem_uvarint(&mut cursor)?;
    if count == 0 || count as usize > MAX_FILES {
        return Err(PortableError::Limit(
            "ZIP-factor template member count exceeds policy".into(),
        ));
    }
    let mut rows = Vec::with_capacity(count as usize);
    for _ in 0..count {
        let name = read_mem_blob(&mut cursor)?;
        let local_extra = read_mem_blob(&mut cursor)?;
        let mut values = [0u64; 14];
        for value in &mut values {
            *value = read_mem_uvarint(&mut cursor)?;
        }
        let central_extra = read_mem_blob(&mut cursor)?;
        let central_comment = read_mem_blob(&mut cursor)?;
        rows.push(TemplateRow {
            name,
            local_extra,
            version: narrow_u16(values[0], "local version")?,
            flags: narrow_u16(values[1], "local flags")?,
            method: narrow_u16(values[2], "local method")?,
            mtime: narrow_u16(values[3], "local mtime")?,
            mdate: narrow_u16(values[4], "local mdate")?,
            made: narrow_u16(values[5], "central made")?,
            needed: narrow_u16(values[6], "central needed")?,
            cflags: narrow_u16(values[7], "central flags")?,
            cmethod: narrow_u16(values[8], "central method")?,
            cmtime: narrow_u16(values[9], "central mtime")?,
            cmdate: narrow_u16(values[10], "central mdate")?,
            disk: narrow_u16(values[11], "central disk")?,
            internal_attr: narrow_u16(values[12], "central internal attr")?,
            external_attr: narrow_u32(values[13], "central external attr")?,
            central_extra,
            central_comment,
        });
    }
    let disk = narrow_u16(read_mem_uvarint(&mut cursor)?, "EOCD disk")?;
    let disk_cd = narrow_u16(read_mem_uvarint(&mut cursor)?, "EOCD central disk")?;
    let comment = read_mem_blob(&mut cursor)?;
    if cursor.position() != raw.len() as u64 {
        return Err(PortableError::Format(
            "ZIP-factor template trailing bytes".into(),
        ));
    }
    Ok(Template {
        rows,
        disk,
        disk_cd,
        comment,
    })
}

fn rebuild_zip(
    template: &Template,
    dynamics: &[(u32, u32, u32, Vec<u8>)],
) -> Result<Vec<u8>, PortableError> {
    if dynamics.len() != template.rows.len() {
        return Err(PortableError::Format(
            "ZIP-factor dynamic member count mismatch".into(),
        ));
    }
    let mut out = Vec::new();
    let mut offsets = Vec::with_capacity(template.rows.len());
    for (row, (crc, csize, usize_, payload)) in template.rows.iter().zip(dynamics) {
        if payload.len() != *csize as usize {
            return Err(PortableError::Integrity(
                "ZIP-factor compressed payload length mismatch".into(),
            ));
        }
        offsets.push(
            u32::try_from(out.len())
                .map_err(|_| PortableError::Limit("ZIP-factor local offset exceeds u32".into()))?,
        );
        out.extend_from_slice(&LOCAL.to_le_bytes());
        out.extend_from_slice(&row.version.to_le_bytes());
        out.extend_from_slice(&row.flags.to_le_bytes());
        out.extend_from_slice(&row.method.to_le_bytes());
        out.extend_from_slice(&row.mtime.to_le_bytes());
        out.extend_from_slice(&row.mdate.to_le_bytes());
        out.extend_from_slice(&crc.to_le_bytes());
        out.extend_from_slice(&csize.to_le_bytes());
        out.extend_from_slice(&usize_.to_le_bytes());
        out.extend_from_slice(
            &u16::try_from(row.name.len())
                .map_err(|_| PortableError::Limit("ZIP-factor name too long".into()))?
                .to_le_bytes(),
        );
        out.extend_from_slice(
            &u16::try_from(row.local_extra.len())
                .map_err(|_| PortableError::Limit("ZIP-factor extra too long".into()))?
                .to_le_bytes(),
        );
        out.extend_from_slice(&row.name);
        out.extend_from_slice(&row.local_extra);
        out.extend_from_slice(payload);
    }
    let cd_start = u32::try_from(out.len())
        .map_err(|_| PortableError::Limit("ZIP-factor central offset exceeds u32".into()))?;
    for ((row, (crc, csize, usize_, _payload)), offset) in
        template.rows.iter().zip(dynamics).zip(offsets)
    {
        out.extend_from_slice(&CENTRAL.to_le_bytes());
        out.extend_from_slice(&row.made.to_le_bytes());
        out.extend_from_slice(&row.needed.to_le_bytes());
        out.extend_from_slice(&row.cflags.to_le_bytes());
        out.extend_from_slice(&row.cmethod.to_le_bytes());
        out.extend_from_slice(&row.cmtime.to_le_bytes());
        out.extend_from_slice(&row.cmdate.to_le_bytes());
        out.extend_from_slice(&crc.to_le_bytes());
        out.extend_from_slice(&csize.to_le_bytes());
        out.extend_from_slice(&usize_.to_le_bytes());
        out.extend_from_slice(
            &u16::try_from(row.name.len())
                .map_err(|_| PortableError::Limit("ZIP-factor name too long".into()))?
                .to_le_bytes(),
        );
        out.extend_from_slice(
            &u16::try_from(row.central_extra.len())
                .map_err(|_| PortableError::Limit("ZIP-factor central extra too long".into()))?
                .to_le_bytes(),
        );
        out.extend_from_slice(
            &u16::try_from(row.central_comment.len())
                .map_err(|_| PortableError::Limit("ZIP-factor central comment too long".into()))?
                .to_le_bytes(),
        );
        out.extend_from_slice(&row.disk.to_le_bytes());
        out.extend_from_slice(&row.internal_attr.to_le_bytes());
        out.extend_from_slice(&row.external_attr.to_le_bytes());
        out.extend_from_slice(&offset.to_le_bytes());
        out.extend_from_slice(&row.name);
        out.extend_from_slice(&row.central_extra);
        out.extend_from_slice(&row.central_comment);
    }
    let cd_size = u32::try_from(out.len())
        .map_err(|_| PortableError::Limit("ZIP-factor central size exceeds u32".into()))?
        - cd_start;
    let count = u16::try_from(template.rows.len())
        .map_err(|_| PortableError::Limit("ZIP-factor entry count exceeds u16".into()))?;
    out.extend_from_slice(&EOCD.to_le_bytes());
    out.extend_from_slice(&template.disk.to_le_bytes());
    out.extend_from_slice(&template.disk_cd.to_le_bytes());
    out.extend_from_slice(&count.to_le_bytes());
    out.extend_from_slice(&count.to_le_bytes());
    out.extend_from_slice(&cd_size.to_le_bytes());
    out.extend_from_slice(&cd_start.to_le_bytes());
    out.extend_from_slice(
        &u16::try_from(template.comment.len())
            .map_err(|_| PortableError::Limit("ZIP-factor EOCD comment too long".into()))?
            .to_le_bytes(),
    );
    out.extend_from_slice(&template.comment);
    Ok(out)
}
