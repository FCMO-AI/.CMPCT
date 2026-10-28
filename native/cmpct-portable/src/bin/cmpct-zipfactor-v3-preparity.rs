//! Research-only native verifier for the binary-control ZIP-factor v3 candidate.
//!
//! This deliberately does not enter `PortableArchive` production dispatch. It exists to measure the exact
//! CMP25Z3 candidate with a Rust implementation while recovery/platform promotion remains a separate gate.

use rmpv::Value;
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, env, fs, io::Cursor, path::Path};

const MAGIC: &[u8; 8] = b"CMP25Z3\0";
const PROFILE: &str = "zip-framing-factor-binary-control-v3";
const REVISION: u32 = 25;
const TEMPLATE_MAGIC: &[u8; 4] = b"ZFT1";
const GROUP_MAGIC: &[u8; 4] = b"ZCG2";
const LOCAL: u32 = 0x0403_4b50;
const CENTRAL: u32 = 0x0201_4b50;
const EOCD: u32 = 0x0605_4b50;
const MAX_FILES: usize = 65_535;
const MAX_DECODE: usize = 8 * 1024 * 1024;
const MAX_BLOB: usize = MAX_DECODE + 1024 * 1024;
const MAX_PATH: usize = 16 * 1024;

#[derive(Clone)]
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

struct Template {
    rows: Vec<TemplateRow>,
    disk: u16,
    disk_cd: u16,
    comment: Vec<u8>,
}

#[derive(Clone)]
struct GroupDesc {
    raw_size: usize,
    raw_sha: [u8; 32],
    member_count: usize,
}

struct Parsed {
    manifest_raw: Vec<u8>,
    template_raw: Vec<u8>,
    template: Template,
    regular: BTreeMap<String, (u64, [u8; 32])>,
    groups: Vec<(GroupDesc, Vec<u8>)>,
}

fn err(message: impl Into<String>) -> Result<(), String> {
    Err(message.into())
}

fn sha(raw: &[u8]) -> [u8; 32] {
    Sha256::digest(raw).into()
}

fn take<'a>(raw: &'a [u8], at: &mut usize, n: usize, label: &str) -> Result<&'a [u8], String> {
    let end = at
        .checked_add(n)
        .ok_or_else(|| format!("{label} offset overflow"))?;
    let out = raw
        .get(*at..end)
        .ok_or_else(|| format!("truncated {label}"))?;
    *at = end;
    Ok(out)
}

fn u16_le(raw: &[u8], at: &mut usize, label: &str) -> Result<u16, String> {
    Ok(u16::from_le_bytes(
        take(raw, at, 2, label)?.try_into().unwrap(),
    ))
}

fn u32_le(raw: &[u8], at: &mut usize, label: &str) -> Result<u32, String> {
    Ok(u32::from_le_bytes(
        take(raw, at, 4, label)?.try_into().unwrap(),
    ))
}

fn uvarint(raw: &[u8], at: &mut usize, label: &str) -> Result<u64, String> {
    let mut value = 0u64;
    for shift in (0..70).step_by(7) {
        let byte = *take(raw, at, 1, label)?.first().unwrap();
        value |= u64::from(byte & 0x7f) << shift;
        if byte & 0x80 == 0 {
            return Ok(value);
        }
    }
    Err(format!("oversized {label} uvarint"))
}

fn blob(raw: &[u8], at: &mut usize, label: &str) -> Result<Vec<u8>, String> {
    let n =
        usize::try_from(uvarint(raw, at, label)?).map_err(|_| format!("{label} size overflow"))?;
    if n > MAX_BLOB {
        return Err(format!("{label} compressed blob exceeds policy"));
    }
    Ok(take(raw, at, n, label)?.to_vec())
}

fn decompress(blob: &[u8], expected: usize, label: &str) -> Result<Vec<u8>, String> {
    if expected > MAX_DECODE || blob.len() > MAX_BLOB {
        return Err(format!("{label} declaration exceeds policy"));
    }
    let decoded =
        zstd::stream::decode_all(Cursor::new(blob)).map_err(|e| format!("{label} zstd: {e}"))?;
    if decoded.len() != expected || decoded.len() > MAX_DECODE {
        return Err(format!("{label} decoded size mismatch"));
    }
    Ok(decoded)
}

fn safe_relpath(path: &str) -> bool {
    !path.is_empty()
        && path.len() <= MAX_PATH
        && !path.starts_with('/')
        && !path.starts_with('\\')
        && !path.contains('\0')
        && !path
            .split('/')
            .any(|part| part.is_empty() || part == "." || part == "..")
        && !(path.len() >= 2 && path.as_bytes()[1] == b':')
}

fn as_map<'a>(value: &'a Value, label: &str) -> Result<&'a Vec<(Value, Value)>, String> {
    value
        .as_map()
        .ok_or_else(|| format!("{label} must be a map"))
}

fn field<'a>(map: &'a [(Value, Value)], key: &str) -> Result<&'a Value, String> {
    map.iter()
        .find_map(|(k, v)| (k.as_str() == Some(key)).then_some(v))
        .ok_or_else(|| format!("missing manifest field {key}"))
}

fn manifest_regular(raw: &[u8]) -> Result<BTreeMap<String, (u64, [u8; 32])>, String> {
    let value = rmpv::decode::read_value(&mut Cursor::new(raw))
        .map_err(|e| format!("manifest msgpack: {e}"))?;
    let map = as_map(&value, "manifest")?;
    if field(map, "v")?.as_u64() != Some(1)
        || field(map, "profile")?.as_str() != Some("cmpct-r25-filesystem-manifest-v1")
        || field(map, "internal_path")?.as_str()
            != Some(".__cmpct_r25_internal__/filesystem-v1.msgpack")
    {
        return Err("unsupported filesystem manifest identity".into());
    }
    let rows = field(map, "entries")?
        .as_array()
        .ok_or("manifest entries must be an array")?;
    if rows.len() > MAX_FILES + 1 {
        return Err("manifest entry count exceeds policy".into());
    }
    let mut regular = BTreeMap::new();
    for value in rows {
        let row = value.as_array().ok_or("manifest row must be an array")?;
        if row.len() != 8 {
            return Err("malformed manifest row".into());
        }
        let path = row[0].as_str().ok_or("manifest path must be text")?;
        if !safe_relpath(path) || path.starts_with(".__cmpct_r25_internal__") {
            return Err(format!("unsafe manifest path: {path}"));
        }
        let kind = row[1].as_str().ok_or("manifest kind must be text")?;
        if kind != "f" {
            continue;
        }
        let identity = row[7].as_array().ok_or("regular identity must be array")?;
        if identity.len() != 2 {
            return Err("regular identity shape".into());
        }
        let size = identity[0]
            .as_u64()
            .ok_or("regular size must be unsigned")?;
        let digest = identity[1]
            .as_slice()
            .ok_or("regular digest must be binary")?;
        let digest: [u8; 32] = digest
            .try_into()
            .map_err(|_| "regular digest must be SHA-256")?;
        if regular.insert(path.to_owned(), (size, digest)).is_some() {
            return Err(format!("duplicate regular path: {path}"));
        }
    }
    if regular.is_empty() || regular.len() > MAX_FILES {
        return Err("regular file count outside policy".into());
    }
    Ok(regular)
}

fn template_blob(raw: &[u8], at: &mut usize, label: &str) -> Result<Vec<u8>, String> {
    let n =
        usize::try_from(uvarint(raw, at, label)?).map_err(|_| format!("{label} size overflow"))?;
    if n > MAX_DECODE {
        return Err(format!("{label} exceeds policy"));
    }
    Ok(take(raw, at, n, label)?.to_vec())
}

fn narrow_u16(value: u64, label: &str) -> Result<u16, String> {
    u16::try_from(value).map_err(|_| format!("{label} exceeds u16"))
}

fn narrow_u32(value: u64, label: &str) -> Result<u32, String> {
    u32::try_from(value).map_err(|_| format!("{label} exceeds u32"))
}

fn parse_template(raw: &[u8]) -> Result<Template, String> {
    let mut at = 0usize;
    if take(raw, &mut at, 4, "template magic")? != TEMPLATE_MAGIC {
        return Err("bad template magic".into());
    }
    let count = usize::try_from(uvarint(raw, &mut at, "template count")?)
        .map_err(|_| "template count overflow")?;
    if count == 0 || count > MAX_FILES {
        return Err("template count exceeds policy".into());
    }
    let mut rows = Vec::with_capacity(count);
    for _ in 0..count {
        let name = template_blob(raw, &mut at, "template name")?;
        let local_extra = template_blob(raw, &mut at, "template local extra")?;
        let mut values = [0u64; 14];
        for value in &mut values {
            *value = uvarint(raw, &mut at, "template field")?;
        }
        let central_extra = template_blob(raw, &mut at, "template central extra")?;
        let central_comment = template_blob(raw, &mut at, "template central comment")?;
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
    let disk = narrow_u16(uvarint(raw, &mut at, "EOCD disk")?, "EOCD disk")?;
    let disk_cd = narrow_u16(
        uvarint(raw, &mut at, "EOCD central disk")?,
        "EOCD central disk",
    )?;
    let comment = template_blob(raw, &mut at, "EOCD comment")?;
    if at != raw.len() {
        return Err("template trailing bytes".into());
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
) -> Result<Vec<u8>, String> {
    if dynamics.len() != template.rows.len() {
        return Err("dynamic member count mismatch".into());
    }
    let mut out = Vec::new();
    let mut offsets = Vec::with_capacity(template.rows.len());
    for (row, (crc, csize, usize_, payload)) in template.rows.iter().zip(dynamics) {
        if payload.len() != *csize as usize {
            return Err("compressed payload length mismatch".into());
        }
        offsets.push(u32::try_from(out.len()).map_err(|_| "local offset exceeds u32")?);
        out.extend_from_slice(&LOCAL.to_le_bytes());
        for v in [row.version, row.flags, row.method, row.mtime, row.mdate] {
            out.extend_from_slice(&v.to_le_bytes());
        }
        out.extend_from_slice(&crc.to_le_bytes());
        out.extend_from_slice(&csize.to_le_bytes());
        out.extend_from_slice(&usize_.to_le_bytes());
        out.extend_from_slice(
            &u16::try_from(row.name.len())
                .map_err(|_| "name too long")?
                .to_le_bytes(),
        );
        out.extend_from_slice(
            &u16::try_from(row.local_extra.len())
                .map_err(|_| "extra too long")?
                .to_le_bytes(),
        );
        out.extend_from_slice(&row.name);
        out.extend_from_slice(&row.local_extra);
        out.extend_from_slice(payload);
    }
    let cd_start = u32::try_from(out.len()).map_err(|_| "central offset exceeds u32")?;
    for ((row, (crc, csize, usize_, _)), offset) in template.rows.iter().zip(dynamics).zip(offsets)
    {
        out.extend_from_slice(&CENTRAL.to_le_bytes());
        for v in [
            row.made,
            row.needed,
            row.cflags,
            row.cmethod,
            row.cmtime,
            row.cmdate,
        ] {
            out.extend_from_slice(&v.to_le_bytes());
        }
        out.extend_from_slice(&crc.to_le_bytes());
        out.extend_from_slice(&csize.to_le_bytes());
        out.extend_from_slice(&usize_.to_le_bytes());
        out.extend_from_slice(
            &u16::try_from(row.name.len())
                .map_err(|_| "name too long")?
                .to_le_bytes(),
        );
        out.extend_from_slice(
            &u16::try_from(row.central_extra.len())
                .map_err(|_| "central extra too long")?
                .to_le_bytes(),
        );
        out.extend_from_slice(
            &u16::try_from(row.central_comment.len())
                .map_err(|_| "central comment too long")?
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
    let cd_size = u32::try_from(out.len()).map_err(|_| "central size exceeds u32")? - cd_start;
    let count = u16::try_from(template.rows.len()).map_err(|_| "entry count exceeds u16")?;
    out.extend_from_slice(&EOCD.to_le_bytes());
    out.extend_from_slice(&template.disk.to_le_bytes());
    out.extend_from_slice(&template.disk_cd.to_le_bytes());
    out.extend_from_slice(&count.to_le_bytes());
    out.extend_from_slice(&count.to_le_bytes());
    out.extend_from_slice(&cd_size.to_le_bytes());
    out.extend_from_slice(&cd_start.to_le_bytes());
    out.extend_from_slice(
        &u16::try_from(template.comment.len())
            .map_err(|_| "comment too long")?
            .to_le_bytes(),
    );
    out.extend_from_slice(&template.comment);
    Ok(out)
}

fn parse(path: &Path) -> Result<Parsed, String> {
    let raw = fs::read(path).map_err(|e| format!("read archive: {e}"))?;
    let mut at = 0usize;
    if take(&raw, &mut at, 8, "archive magic")? != MAGIC {
        return Err("not a binary-control ZIP-factor v3 archive".into());
    }
    let manifest_size = u32_le(&raw, &mut at, "manifest size")? as usize;
    let manifest_sha: [u8; 32] = take(&raw, &mut at, 32, "manifest sha")?.try_into().unwrap();
    let template_size = u32_le(&raw, &mut at, "template size")? as usize;
    let template_sha: [u8; 32] = take(&raw, &mut at, 32, "template sha")?.try_into().unwrap();
    let group_count = u16_le(&raw, &mut at, "group count")? as usize;
    if manifest_size > MAX_DECODE
        || template_size > MAX_DECODE
        || group_count == 0
        || group_count > MAX_FILES
    {
        return Err("fixed header exceeds policy".into());
    }
    let mut descs = Vec::with_capacity(group_count);
    for _ in 0..group_count {
        let raw_size = u32_le(&raw, &mut at, "group raw size")? as usize;
        let raw_sha: [u8; 32] = take(&raw, &mut at, 32, "group sha")?.try_into().unwrap();
        let member_count = u16_le(&raw, &mut at, "group member count")? as usize;
        if raw_size > MAX_DECODE || member_count == 0 || member_count > MAX_FILES {
            return Err("group descriptor exceeds policy".into());
        }
        descs.push(GroupDesc {
            raw_size,
            raw_sha,
            member_count,
        });
    }
    let manifest_blob = blob(&raw, &mut at, "manifest")?;
    let template_blob = blob(&raw, &mut at, "template")?;
    let mut group_blobs = Vec::with_capacity(group_count);
    for _ in 0..group_count {
        group_blobs.push(blob(&raw, &mut at, "group")?);
    }
    if at != raw.len() {
        return Err("trailing archive bytes".into());
    }
    let manifest_raw = decompress(&manifest_blob, manifest_size, "manifest")?;
    let template_raw = decompress(&template_blob, template_size, "template")?;
    if sha(&manifest_raw) != manifest_sha || sha(&template_raw) != template_sha {
        return Err("direct member SHA-256 mismatch".into());
    }
    let regular = manifest_regular(&manifest_raw)?;
    if descs.iter().map(|d| d.member_count).sum::<usize>() != regular.len() {
        return Err("manifest/group membership mismatch".into());
    }
    let template = parse_template(&template_raw)?;
    Ok(Parsed {
        manifest_raw,
        template_raw,
        template,
        regular,
        groups: descs.into_iter().zip(group_blobs).collect(),
    })
}

fn verify(path: &Path) -> Result<(), String> {
    let parsed = parse(path)?;
    let paths: Vec<_> = parsed.regular.keys().cloned().collect();
    let mut path_at = 0usize;
    for (desc, compressed) in &parsed.groups {
        let group_raw = decompress(compressed, desc.raw_size, "group")?;
        if sha(&group_raw) != desc.raw_sha {
            return err("group SHA-256 mismatch");
        }
        let mut at = 0usize;
        if take(&group_raw, &mut at, 4, "group magic")? != GROUP_MAGIC {
            return err("bad group magic");
        }
        let count = usize::try_from(uvarint(&group_raw, &mut at, "group count")?)
            .map_err(|_| "group count overflow")?;
        if count != desc.member_count {
            return err("group count mismatch");
        }
        let context = parsed.template_raw.len() + group_raw.len();
        if context > MAX_DECODE {
            return err("decode-unit ceiling exceeded");
        }
        for _ in 0..count {
            let rel = paths.get(path_at).ok_or("group path overflow")?;
            path_at += 1;
            let mut dynamics = Vec::with_capacity(parsed.template.rows.len());
            for _ in &parsed.template.rows {
                let crc = u32_le(&group_raw, &mut at, "crc")?;
                let csize = u32_le(&group_raw, &mut at, "compressed size")?;
                let usize_ = u32_le(&group_raw, &mut at, "uncompressed size")?;
                let payload =
                    take(&group_raw, &mut at, csize as usize, "compressed payload")?.to_vec();
                dynamics.push((crc, csize, usize_, payload));
            }
            let restored = rebuild_zip(&parsed.template, &dynamics)?;
            let (expected_size, expected_sha) = parsed.regular.get(rel).unwrap();
            if restored.len() as u64 != *expected_size || sha(&restored) != *expected_sha {
                return Err(format!("reconstructed identity mismatch: {rel}"));
            }
            let amp = context as f64 / (*expected_size).max(1) as f64;
            if amp > 8.0 {
                return Err(format!("locality ceiling exceeded: {rel}"));
            }
        }
        if at != group_raw.len() {
            return err("group trailing bytes");
        }
    }
    if path_at != paths.len() {
        return err("not all regular paths verified");
    }
    if sha(&parsed.manifest_raw) == [0; 32] {
        return err("impossible manifest digest");
    }
    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 || !matches!(args[1].as_str(), "verify" | "info") {
        eprintln!("usage: cmpct-zipfactor-v3-preparity <verify|info> <archive>");
        std::process::exit(2);
    }
    let path = Path::new(&args[2]);
    let result = if args[1] == "verify" {
        verify(path).map(|()| println!("ok profile={PROFILE}"))
    } else {
        parse(path).map(|parsed| {
            println!("profile={PROFILE}");
            println!("revision={REVISION}");
            println!("regular_files={}", parsed.regular.len());
        })
    };
    if let Err(message) = result {
        eprintln!("cmpct-zipfactor-v3-preparity: {message}");
        std::process::exit(1);
    }
}
