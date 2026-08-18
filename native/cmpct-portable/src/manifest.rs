use crate::format::{
    as_array, as_map, field, parse_msgpack, safe_relpath, text, uint, MAX_META_BYTES,
    MAX_PATH_BYTES,
};
use crate::{PortableEntry, PortableError};
use rmpv::Value;
use std::collections::{HashMap, HashSet};

pub(crate) const INTERNAL_ROOT: &str = ".__cmpct_r25_internal__";
pub(crate) const FILESYSTEM_MANIFEST: &str =
    ".__cmpct_r25_internal__/filesystem-v1.msgpack";
const PROFILE: &str = "cmpct-r25-filesystem-manifest-v1";
const VERSION: u64 = 1;
const MAX_ENTRIES: usize = 65_536;
const MAX_XATTRS_PER_ENTRY: usize = 4_096;

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
    ) -> Result<Self, PortableError> {
        if raw.len() as u64 > MAX_META_BYTES {
            return Err(PortableError::Limit(
                "r25 filesystem manifest exceeds 8 MiB policy".into(),
            ));
        }
        let root = parse_msgpack(raw)?;
        let map = as_map(&root, "r25 filesystem manifest")?;
        if uint(
            field(map, "v")?,
            "r25 filesystem manifest version",
            VERSION,
        )? != VERSION
            || text(
                field(map, "profile")?,
                "r25 filesystem manifest profile",
            )? != PROFILE
            || text(
                field(map, "internal_path")?,
                "r25 filesystem manifest internal path",
            )? != FILESYSTEM_MANIFEST
        {
            return Err(PortableError::Format(
                "unsupported r25 filesystem manifest identity".into(),
            ));
        }
        let rows = as_array(
            field(map, "entries")?,
            "r25 filesystem manifest entries",
        )?;
        if rows.len() > MAX_ENTRIES {
            return Err(PortableError::Limit(
                "r25 filesystem manifest entry count exceeds policy".into(),
            ));
        }

        let mut entries = Vec::with_capacity(rows.len());
        let mut by_path = HashMap::with_capacity(rows.len());
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
            let path = text(&row[0], "r25 filesystem path")?.to_owned();
            safe_relpath(&path)?;
            if path == INTERNAL_ROOT || path.starts_with(&format!("{INTERNAL_ROOT}/")) {
                return Err(PortableError::Path(path));
            }
            if !seen.insert(path.clone()) {
                return Err(PortableError::Format(
                    "duplicate r25 filesystem path".into(),
                ));
            }
            let kind = text(&row[1], "r25 filesystem entry kind")?;
            let mode = uint(&row[2], "r25 filesystem mode", 0o7777)? as u32;
            let mtime_ns = nonnegative_i64(&row[3], "r25 filesystem mtime_ns")?;
            let uid = uint(&row[4], "r25 filesystem uid", u32::MAX as u64)? as u32;
            let gid = uint(&row[5], "r25 filesystem gid", u32::MAX as u64)? as u32;
            let xattrs = parse_xattrs(&row[6])?;
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
                        PortableError::Format(
                            "r25 regular-file digest must be SHA-256".into(),
                        )
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
                    if target.contains('\0') || target.len() > MAX_PATH_BYTES {
                        return Err(PortableError::Path(format!("{path} -> {target}")));
                    }
                    FsKind::Symlink { target }
                }
                "h" => {
                    let target = text(&row[7], "r25 hardlink target")?.to_owned();
                    if !seen.contains(&target) {
                        // Footnote: the canonical grammar only permits backward hardlink references. That
                        // makes cycles impossible without a graph walk controlled by hostile metadata.
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
            let index = entries.len();
            by_path.insert(path.clone(), index);
            entries.push(FsEntry {
                path,
                kind,
                metadata: FsMetadata {
                    mode,
                    mtime_ns,
                    uid,
                    gid,
                    xattrs,
                },
            });
        }

        let actual_content: HashSet<String> = content_entries
            .iter()
            .map(|entry| entry.path.clone())
            .collect();
        if actual_content != expected_content {
            return Err(PortableError::Integrity(
                "r25 content profile and filesystem manifest disagree on logical members".into(),
            ));
        }
        if content_entries.iter().any(|entry| entry.kind != 0) {
            return Err(PortableError::Format(
                "r25 content graph contains a non-regular internal member".into(),
            ));
        }

        let manifest = Self { entries, by_path };
        // Resolve every hardlink now so a backward reference to a directory/symlink is rejected before any
        // extraction path can materialize it. Python reaches the same refusal during restoration; native moves
        // it into authenticated preflight so list/read/extract all share one deterministic admission result.
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

    pub(crate) fn resolve_regular<'a>(
        &'a self,
        path: &str,
    ) -> Result<&'a FsEntry, PortableError> {
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

fn nonnegative_i64(value: &Value, label: &str) -> Result<i64, PortableError> {
    let value = value
        .as_i64()
        .or_else(|| value.as_u64().and_then(|value| i64::try_from(value).ok()))
        .filter(|value| *value >= 0)
        .ok_or_else(|| PortableError::Format(format!("{label} declaration")))?;
    Ok(value)
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
