use crate::format::{
    MAX_META_BYTES, MAX_PATH_BYTES, as_array, as_map, field, parse_msgpack, safe_relpath, text,
    uint,
};
use crate::{PortableEntry, PortableError};
use rmpv::Value;
use std::collections::{HashMap, HashSet};

pub(crate) const INTERNAL_ROOT: &str = ".__cmpct_r25_internal__";
pub(crate) const FILESYSTEM_MANIFEST: &str = ".__cmpct_r25_internal__/filesystem-v1.msgpack";
const PROFILE: &str = "cmpct-r25-filesystem-manifest-v1";
const VERSION: u64 = 1;
const IMPLICIT_V4_VERSION: u64 = 4;
const MAX_ENTRIES: usize = 65_536;
const MAX_XATTRS_PER_ENTRY: usize = 4_096;
const MODE: u64 = 1 << 0;
const MTIME: u64 = 1 << 1;
const UID: u64 = 1 << 2;
const GID: u64 = 1 << 3;
const XATTRS: u64 = 1 << 4;
const ALL_OVERRIDE_BITS: u64 = MODE | MTIME | UID | GID | XATTRS;

pub(crate) type ContentIdentities = HashMap<String, (u64, [u8; 32])>;

#[derive(Debug, Clone)]
pub(crate) struct FsMetadata {
    pub mode: u32,
    pub mtime_ns: i64,
    pub uid: u32,
    pub gid: u32,
    pub xattrs: Vec<(String, Vec<u8>)>,
}

#[derive(Debug, Clone)]
pub(crate) enum FsKind {
    File { size: u64, sha256: [u8; 32] },
    Directory,
    Symlink { target: String },
    Hardlink { target: String },
}

#[derive(Debug, Clone)]
pub(crate) struct FsEntry {
    pub path: String,
    pub kind: FsKind,
    pub metadata: FsMetadata,
}

#[derive(Debug, Clone)]
pub(crate) struct FsManifest {
    entries: Vec<FsEntry>,
    by_path: HashMap<String, usize>,
}

impl FsManifest {
    pub(crate) fn parse(
        raw: &[u8],
        content_entries: &[PortableEntry],
        content_identities: &ContentIdentities,
    ) -> Result<Self, PortableError> {
        if raw.len() as u64 > MAX_META_BYTES {
            return Err(PortableError::Limit(
                "r25 filesystem manifest exceeds 8 MiB policy".into(),
            ));
        }
        if content_entries.iter().any(|entry| entry.kind != 0) {
            return Err(PortableError::Format(
                "r25 content graph contains a non-regular internal member".into(),
            ));
        }
        let actual_content: HashSet<String> = content_entries
            .iter()
            .map(|entry| entry.path.clone())
            .collect();
        let identity_paths: HashSet<String> = content_identities.keys().cloned().collect();
        if actual_content != identity_paths || !actual_content.contains(FILESYSTEM_MANIFEST) {
            return Err(PortableError::Integrity(
                "r25 content graph entry/identity sets disagree".into(),
            ));
        }

        let root = parse_msgpack(raw)?;
        let mut entries = match &root {
            Value::Map(_) => parse_v1(&root, &actual_content)?,
            Value::Array(_) => parse_implicit_v4(&root, content_entries, content_identities)?,
            _ => {
                return Err(PortableError::Format(
                    "unsupported r25 filesystem control shape".into(),
                ));
            }
        };
        if entries.len() > MAX_ENTRIES {
            return Err(PortableError::Limit(
                "r25 filesystem manifest entry count exceeds policy".into(),
            ));
        }
        entries.sort_by(|left, right| left.path.cmp(&right.path));
        let mut by_path = HashMap::with_capacity(entries.len());
        for (index, entry) in entries.iter().enumerate() {
            if by_path.insert(entry.path.clone(), index).is_some() {
                return Err(PortableError::Format(
                    "duplicate r25 filesystem path".into(),
                ));
            }
        }

        let manifest = Self { entries, by_path };
        for entry in &manifest.entries {
            if let FsKind::Hardlink { target } = &entry.kind {
                let owner = manifest.resolve_regular(target)?;
                if !matches!(&owner.kind, FsKind::File { .. }) {
                    return Err(PortableError::Format(
                        "r25 hardlink owner is not a regular file".into(),
                    ));
                }
            }
        }
        Ok(manifest)
    }

    pub(crate) fn entries(&self) -> &[FsEntry] {
        &self.entries
    }

    pub(crate) fn entry(&self, index: usize) -> Result<&FsEntry, PortableError> {
        self.entries
            .get(index)
            .ok_or_else(|| PortableError::Format("r25 filesystem entry id out of range".into()))
    }

    pub(crate) fn public_entries(&self) -> Result<Vec<PortableEntry>, PortableError> {
        self.entries
            .iter()
            .map(|entry| {
                let (kind, size) = match &entry.kind {
                    FsKind::File { size, .. } => (0, *size),
                    FsKind::Directory => (1, 0),
                    FsKind::Symlink { target } => (2, target.len() as u64),
                    FsKind::Hardlink { target } => {
                        let owner = self.resolve_regular(target)?;
                        let FsKind::File { size, .. } = &owner.kind else {
                            return Err(PortableError::Format(
                                "r25 hardlink owner is not a regular file".into(),
                            ));
                        };
                        (3, *size)
                    }
                };
                Ok(PortableEntry {
                    path: entry.path.clone(),
                    size,
                    kind,
                    mode: entry.metadata.mode,
                    mtime_ns: entry.metadata.mtime_ns,
                })
            })
            .collect()
    }

    pub(crate) fn resolve_regular<'a>(&'a self, path: &str) -> Result<&'a FsEntry, PortableError> {
        let mut current = path;
        for _ in 0..=self.entries.len() {
            let index = *self.by_path.get(current).ok_or_else(|| {
                PortableError::Format(format!("r25 hardlink target not found: {current}"))
            })?;
            let entry = &self.entries[index];
            match &entry.kind {
                FsKind::File { .. } => return Ok(entry),
                FsKind::Hardlink { target } => current = target,
                _ => {
                    return Err(PortableError::Format(
                        "r25 hardlink target is not a regular file".into(),
                    ));
                }
            }
        }
        Err(PortableError::Format(
            "r25 hardlink chain exceeded manifest bound".into(),
        ))
    }
}

fn parse_v1(root: &Value, actual_content: &HashSet<String>) -> Result<Vec<FsEntry>, PortableError> {
    let map = as_map(root, "r25 filesystem manifest")?;
    if uint(field(map, "v")?, "r25 filesystem manifest version", VERSION)? != VERSION
        || text(field(map, "profile")?, "r25 filesystem manifest profile")? != PROFILE
        || text(
            field(map, "internal_path")?,
            "r25 filesystem manifest internal path",
        )? != FILESYSTEM_MANIFEST
    {
        return Err(PortableError::Format(
            "unsupported r25 filesystem manifest identity".into(),
        ));
    }
    let rows = as_array(field(map, "entries")?, "r25 filesystem manifest entries")?;
    if rows.len() > MAX_ENTRIES {
        return Err(PortableError::Limit(
            "r25 filesystem manifest entry count exceeds policy".into(),
        ));
    }

    let mut entries = Vec::with_capacity(rows.len());
    let mut seen = HashSet::with_capacity(rows.len());
    let mut expected_content = HashSet::new();
    expected_content.insert(FILESYSTEM_MANIFEST.to_owned());

    for row in rows {
        let row = as_array(row, "r25 filesystem manifest entry")?;
        if row.len() != 8 {
            return Err(PortableError::Format(
                "malformed r25 filesystem manifest entry".into(),
            ));
        }
        let path = public_path(text(&row[0], "r25 filesystem path")?)?;
        if !seen.insert(path.clone()) {
            return Err(PortableError::Format(
                "duplicate r25 filesystem path".into(),
            ));
        }
        let kind = text(&row[1], "r25 filesystem entry kind")?;
        let metadata = parse_metadata_fields(&row[2..7])?;
        let kind = match kind {
            "f" => {
                let identity = as_array(&row[7], "r25 regular-file identity")?;
                if identity.len() != 2 {
                    return Err(PortableError::Format(
                        "r25 regular-file identity shape".into(),
                    ));
                }
                let size = uint(&identity[0], "r25 regular-file size", u64::MAX)?;
                let Value::Binary(digest) = &identity[1] else {
                    return Err(PortableError::Format(
                        "r25 regular-file digest must be binary".into(),
                    ));
                };
                let sha256: [u8; 32] = digest.as_slice().try_into().map_err(|_| {
                    PortableError::Format("r25 regular-file digest must be SHA-256".into())
                })?;
                expected_content.insert(path.clone());
                FsKind::File { size, sha256 }
            }
            "d" => {
                if !row[7].is_nil() {
                    return Err(PortableError::Format(
                        "r25 directory carries unexpected payload".into(),
                    ));
                }
                FsKind::Directory
            }
            "l" => {
                let target = text(&row[7], "r25 symlink target")?.to_owned();
                if !safe_symlink_target(&target) {
                    return Err(PortableError::Path(format!("{path} -> {target}")));
                }
                FsKind::Symlink { target }
            }
            "h" => {
                let target = text(&row[7], "r25 hardlink target")?.to_owned();
                if !seen.contains(&target) {
                    return Err(PortableError::Format(
                        "r25 hardlink target must be an earlier manifest path".into(),
                    ));
                }
                FsKind::Hardlink { target }
            }
            _ => {
                return Err(PortableError::Format(
                    "unknown r25 filesystem entry kind".into(),
                ));
            }
        };
        entries.push(FsEntry {
            path,
            kind,
            metadata,
        });
    }
    if &expected_content != actual_content {
        return Err(PortableError::Integrity(
            "r25 content profile and filesystem manifest disagree on logical members".into(),
        ));
    }
    Ok(entries)
}

fn parse_implicit_v4(
    root: &Value,
    content_entries: &[PortableEntry],
    content_identities: &ContentIdentities,
) -> Result<Vec<FsEntry>, PortableError> {
    let payload = as_array(root, "r25 implicit-v4 filesystem control")?;
    if payload.len() != 4
        || uint(
            &payload[0],
            "r25 implicit-v4 filesystem control version",
            IMPLICIT_V4_VERSION,
        )? != IMPLICIT_V4_VERSION
    {
        return Err(PortableError::Format(
            "unsupported r25 implicit-v4 filesystem control version".into(),
        ));
    }
    let default = parse_metadata_tuple(&payload[1])?;
    let regular_meta = as_array(&payload[2], "r25 implicit-v4 regular metadata")?;
    let explicit_rows = as_array(&payload[3], "r25 implicit-v4 explicit entries")?;
    if regular_meta.len() > MAX_ENTRIES
        || explicit_rows.len() > MAX_ENTRIES
        || regular_meta.len().saturating_add(explicit_rows.len()) > MAX_ENTRIES
    {
        return Err(PortableError::Limit(
            "r25 implicit-v4 entry count exceeds policy".into(),
        ));
    }

    let mut regular_paths: Vec<String> = content_entries
        .iter()
        .filter(|entry| entry.path != FILESYSTEM_MANIFEST)
        .map(|entry| entry.path.clone())
        .collect();
    regular_paths.sort();
    if regular_paths.len() != regular_meta.len() {
        return Err(PortableError::Integrity(
            "r25 content profile and filesystem control disagree on logical members".into(),
        ));
    }

    let mut entries = Vec::with_capacity(regular_meta.len() + explicit_rows.len());
    let mut seen = HashSet::with_capacity(entries.capacity());
    for (path, encoded_meta) in regular_paths.iter().zip(regular_meta, strict=true) {
        let path = public_path(path)?;
        if !seen.insert(path.clone()) {
            return Err(PortableError::Format(
                "duplicate r25 implicit-v4 regular path".into(),
            ));
        }
        let (size, sha256) = content_identities.get(&path).copied().ok_or_else(|| {
            PortableError::Integrity(format!("missing authenticated r25 graph identity: {path}"))
        })?;
        entries.push(FsEntry {
            path,
            kind: FsKind::File { size, sha256 },
            metadata: apply_override(&default, encoded_meta)?,
        });
    }

    let mut previous = String::new();
    let mut previous_explicit: Option<String> = None;
    for encoded in explicit_rows {
        let row = as_array(encoded, "r25 implicit-v4 explicit entry")?;
        if row.len() != 5 {
            return Err(PortableError::Format(
                "malformed r25 implicit-v4 explicit entry".into(),
            ));
        }
        let prefix = uint(&row[0], "r25 implicit-v4 path prefix", u64::MAX)?;
        let prefix = usize::try_from(prefix)
            .map_err(|_| PortableError::Limit("r25 implicit-v4 path prefix does not fit host".into()))?;
        let previous_chars = previous.chars().count();
        if prefix > previous_chars {
            return Err(PortableError::Format(
                "r25 implicit-v4 path prefix exceeds previous path".into(),
            ));
        }
        let suffix = text(&row[1], "r25 implicit-v4 path suffix")?;
        let mut path: String = previous.chars().take(prefix).collect();
        path.push_str(suffix);
        let path = public_path(&path)?;
        if let Some(last) = &previous_explicit {
            if path <= *last {
                return Err(PortableError::Format(
                    "r25 implicit-v4 explicit paths are not strictly sorted/unique".into(),
                ));
            }
        }
        if !seen.insert(path.clone()) {
            return Err(PortableError::Format(
                "r25 implicit-v4 explicit path collides with authenticated regular path".into(),
            ));
        }
        let code = uint(&row[2], "r25 implicit-v4 entry kind", 3)?;
        let metadata = apply_override(&default, &row[3])?;
        let kind = match code {
            1 => {
                if !row[4].is_nil() {
                    return Err(PortableError::Format(
                        "r25 implicit-v4 directory carries unexpected payload".into(),
                    ));
                }
                FsKind::Directory
            }
            2 => {
                let target = text(&row[4], "r25 implicit-v4 symlink target")?.to_owned();
                if !safe_symlink_target(&target) {
                    return Err(PortableError::Path(format!("{path} -> {target}")));
                }
                FsKind::Symlink { target }
            }
            3 => {
                let owner_index = uint(
                    &row[4],
                    "r25 implicit-v4 hardlink regular-owner index",
                    regular_paths.len().saturating_sub(1) as u64,
                )? as usize;
                let target = regular_paths.get(owner_index).cloned().ok_or_else(|| {
                    PortableError::Format(
                        "r25 implicit-v4 hardlink owner index is out of range".into(),
                    )
                })?;
                FsKind::Hardlink { target }
            }
            _ => {
                return Err(PortableError::Format(
                    "unknown r25 implicit-v4 entry kind".into(),
                ));
            }
        };
        previous = path.clone();
        previous_explicit = Some(path.clone());
        entries.push(FsEntry {
            path,
            kind,
            metadata,
        });
    }
    Ok(entries)
}

fn public_path(path: &str) -> Result<String, PortableError> {
    safe_relpath(path)?;
    if path == INTERNAL_ROOT || path.starts_with(&format!("{INTERNAL_ROOT}/")) {
        return Err(PortableError::Path(path.to_owned()));
    }
    Ok(path.to_owned())
}

fn parse_metadata_fields(values: &[Value]) -> Result<FsMetadata, PortableError> {
    if values.len() != 5 {
        return Err(PortableError::Format(
            "r25 filesystem metadata tuple declaration".into(),
        ));
    }
    Ok(FsMetadata {
        mode: uint(&values[0], "r25 filesystem mode", 0o7777)? as u32,
        mtime_ns: signed_i64(&values[1], "r25 filesystem mtime_ns")?,
        uid: uint(&values[2], "r25 filesystem uid", u32::MAX as u64)? as u32,
        gid: uint(&values[3], "r25 filesystem gid", u32::MAX as u64)? as u32,
        xattrs: parse_xattrs(&values[4])?,
    })
}

fn parse_metadata_tuple(value: &Value) -> Result<FsMetadata, PortableError> {
    let values = as_array(value, "r25 implicit-v4 default metadata")?;
    parse_metadata_fields(values)
}

fn integer_i128(value: &Value, label: &str) -> Result<i128, PortableError> {
    value
        .as_i64()
        .map(i128::from)
        .or_else(|| value.as_u64().map(i128::from))
        .ok_or_else(|| PortableError::Format(format!("{label} declaration")))
}

fn checked_delta(base: i128, delta: i128, min: i128, max: i128, label: &str) -> Result<i128, PortableError> {
    let value = base
        .checked_add(delta)
        .ok_or_else(|| PortableError::Limit(format!("{label} delta overflow")))?;
    if value < min || value > max {
        return Err(PortableError::Format(format!("{label} delta leaves admitted domain")));
    }
    Ok(value)
}

fn apply_override(default: &FsMetadata, value: &Value) -> Result<FsMetadata, PortableError> {
    let encoded = as_array(value, "r25 implicit-v4 metadata override")?;
    if encoded.is_empty() {
        return Err(PortableError::Format(
            "r25 implicit-v4 metadata override declaration".into(),
        ));
    }
    let mask = uint(&encoded[0], "r25 implicit-v4 metadata override mask", ALL_OVERRIDE_BITS)?;
    if mask & !ALL_OVERRIDE_BITS != 0 {
        return Err(PortableError::Format(
            "r25 implicit-v4 metadata override mask".into(),
        ));
    }
    let mut cursor = 1usize;
    let mut out = default.clone();
    for (bit, label) in [(MODE, "mode"), (MTIME, "mtime"), (UID, "uid"), (GID, "gid")] {
        if mask & bit == 0 {
            continue;
        }
        let delta = encoded.get(cursor).ok_or_else(|| {
            PortableError::Format("r25 implicit-v4 numeric metadata delta".into())
        })?;
        let delta = integer_i128(delta, "r25 implicit-v4 numeric metadata delta")?;
        match bit {
            MODE => {
                out.mode = checked_delta(i128::from(out.mode), delta, 0, 0o7777, label)? as u32;
            }
            MTIME => {
                out.mtime_ns = checked_delta(
                    i128::from(out.mtime_ns),
                    delta,
                    i128::from(i64::MIN),
                    i128::from(i64::MAX),
                    label,
                )? as i64;
            }
            UID => {
                out.uid = checked_delta(i128::from(out.uid), delta, 0, i128::from(u32::MAX), label)? as u32;
            }
            GID => {
                out.gid = checked_delta(i128::from(out.gid), delta, 0, i128::from(u32::MAX), label)? as u32;
            }
            _ => unreachable!(),
        }
        cursor += 1;
    }
    if mask & XATTRS != 0 {
        let xattrs = encoded.get(cursor).ok_or_else(|| {
            PortableError::Format("r25 implicit-v4 xattr override".into())
        })?;
        out.xattrs = parse_xattrs(xattrs)?;
        cursor += 1;
    }
    if cursor != encoded.len() {
        return Err(PortableError::Format(
            "r25 implicit-v4 metadata override trailing fields".into(),
        ));
    }
    Ok(out)
}

fn signed_i64(value: &Value, label: &str) -> Result<i64, PortableError> {
    value
        .as_i64()
        .or_else(|| value.as_u64().and_then(|value| i64::try_from(value).ok()))
        .ok_or_else(|| PortableError::Format(format!("{label} declaration")))
}

fn safe_symlink_target(target: &str) -> bool {
    if target.is_empty() || target.contains('\0') || target.len() > MAX_PATH_BYTES {
        return false;
    }
    let normalized = target.replace('\\', "/");
    let bytes = normalized.as_bytes();
    if normalized.starts_with('/')
        || normalized.starts_with("//")
        || (bytes.len() >= 2 && bytes[1] == b':' && bytes[0].is_ascii_alphabetic())
    {
        return false;
    }
    normalized
        .split('/')
        .all(|part| !part.is_empty() && part != "..")
}

fn parse_xattrs(value: &Value) -> Result<Vec<(String, Vec<u8>)>, PortableError> {
    let rows = as_array(value, "r25 filesystem xattrs")?;
    if rows.len() > MAX_XATTRS_PER_ENTRY {
        return Err(PortableError::Limit(
            "r25 xattr count exceeds policy".into(),
        ));
    }
    let mut out = Vec::with_capacity(rows.len());
    let mut total = 0usize;
    for row in rows {
        let row = as_array(row, "r25 filesystem xattr")?;
        if row.len() != 2 {
            return Err(PortableError::Format("malformed r25 xattr item".into()));
        }
        let name = text(&row[0], "r25 xattr name")?.to_owned();
        let Value::Binary(data) = &row[1] else {
            return Err(PortableError::Format(
                "r25 xattr value must be binary".into(),
            ));
        };
        total = total
            .checked_add(name.len())
            .and_then(|value| value.checked_add(data.len()))
            .ok_or_else(|| PortableError::Limit("r25 xattr byte counter overflow".into()))?;
        if total > MAX_META_BYTES as usize {
            return Err(PortableError::Limit(
                "r25 xattr bytes exceed manifest policy".into(),
            ));
        }
        out.push((name, data.clone()));
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use rmpv::Value;

    fn implicit_fixture() -> (Vec<u8>, Vec<PortableEntry>, ContentIdentities) {
        let regular_path = "src/member.bin".to_owned();
        let digest = [7u8; 32];
        let payload = Value::Array(vec![
            Value::from(IMPLICIT_V4_VERSION),
            Value::Array(vec![
                Value::from(0o644),
                Value::from(-1_i64),
                Value::from(10_u64),
                Value::from(20_u64),
                Value::Array(vec![]),
            ]),
            Value::Array(vec![Value::Array(vec![Value::from(0_u64)])]),
            Value::Array(vec![]),
        ]);
        let mut raw = Vec::new();
        rmpv::encode::write_value(&mut raw, &payload).unwrap();
        let content_entries = vec![
            PortableEntry {
                path: FILESYSTEM_MANIFEST.to_owned(),
                size: raw.len() as u64,
                kind: 0,
                mode: 0,
                mtime_ns: 0,
            },
            PortableEntry {
                path: regular_path.clone(),
                size: 3,
                kind: 0,
                mode: 0,
                mtime_ns: 0,
            },
        ];
        let mut identities = ContentIdentities::new();
        identities.insert(FILESYSTEM_MANIFEST.to_owned(), (raw.len() as u64, [0u8; 32]));
        identities.insert(regular_path, (3, digest));
        (raw, content_entries, identities)
    }

    #[test]
    fn signed_mtime_domain_accepts_pre_epoch_values() {
        assert_eq!(signed_i64(&Value::from(-1_i64), "mtime").unwrap(), -1);
        assert_eq!(
            signed_i64(&Value::from(i64::MIN), "mtime").unwrap(),
            i64::MIN
        );
        assert_eq!(
            signed_i64(&Value::from(i64::MAX), "mtime").unwrap(),
            i64::MAX
        );
    }

    #[test]
    fn symlink_policy_is_portable_across_posix_and_windows_grammars() {
        for target in [
            "../x",
            "..\\x",
            "/x",
            "C:\\x",
            "C:/x",
            "\\\\server\\share",
            "\\rooted",
        ] {
            assert!(
                !safe_symlink_target(target),
                "accepted hostile target {target:?}"
            );
        }
        assert!(safe_symlink_target("folder/file.txt"));
    }

    #[test]
    fn implicit_v4_reconstructs_regular_identity_from_authenticated_graph() {
        let (raw, entries, identities) = implicit_fixture();
        let manifest = FsManifest::parse(&raw, &entries, &identities).unwrap();
        assert_eq!(manifest.entries().len(), 1);
        let entry = &manifest.entries()[0];
        assert_eq!(entry.path, "src/member.bin");
        assert_eq!(entry.metadata.mtime_ns, -1);
        match &entry.kind {
            FsKind::File { size, sha256 } => {
                assert_eq!(*size, 3);
                assert_eq!(*sha256, [7u8; 32]);
            }
            _ => panic!("implicit regular entry did not reconstruct as file"),
        }
    }

    #[test]
    fn implicit_v4_rejects_graph_count_mismatch() {
        let (raw, mut entries, mut identities) = implicit_fixture();
        entries.push(PortableEntry {
            path: "extra.bin".into(),
            size: 1,
            kind: 0,
            mode: 0,
            mtime_ns: 0,
        });
        identities.insert("extra.bin".into(), (1, [1u8; 32]));
        assert!(matches!(
            FsManifest::parse(&raw, &entries, &identities),
            Err(PortableError::Integrity(_))
        ));
    }
}
