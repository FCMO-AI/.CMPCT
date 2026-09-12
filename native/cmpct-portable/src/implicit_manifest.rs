use crate::format::{MAX_META_BYTES, MAX_PATH_BYTES, as_array, parse_msgpack, safe_relpath, text, uint};
use crate::manifest::{FILESYSTEM_MANIFEST, FsEntry, FsKind, FsMetadata, INTERNAL_ROOT};
use crate::{PortableEntry, PortableError};
use rmpv::Value;
use std::collections::{HashMap, HashSet};

const VERSION: u64 = 4;
const MAX_ENTRIES: usize = 65_536;
const MAX_XATTRS_PER_ENTRY: usize = 4_096;
const MODE: u64 = 1 << 0;
const MTIME: u64 = 1 << 1;
const UID: u64 = 1 << 2;
const GID: u64 = 1 << 3;
const XATTRS: u64 = 1 << 4;
const ALL_MASK: u64 = MODE | MTIME | UID | GID | XATTRS;

pub(crate) type GraphIdentities = HashMap<String, (u64, [u8; 32])>;

pub(crate) fn parse(
    raw: &[u8],
    content_entries: &[PortableEntry],
    graph_identities: &GraphIdentities,
) -> Result<Vec<FsEntry>, PortableError> {
    if raw.len() as u64 > MAX_META_BYTES {
        return Err(PortableError::Limit(
            "r25 implicit-v4 filesystem control exceeds 8 MiB policy".into(),
        ));
    }
    let root = parse_msgpack(raw)?;
    let root = as_array(&root, "r25 implicit-v4 filesystem control")?;
    if root.len() != 4 || uint(&root[0], "r25 implicit-v4 version", VERSION)? != VERSION {
        return Err(PortableError::Format(
            "unsupported r25 implicit-v4 filesystem control identity".into(),
        ));
    }

    let default = parse_metadata(&root[1], "r25 implicit-v4 default metadata")?;
    let regular_overrides = as_array(&root[2], "r25 implicit-v4 regular metadata")?;
    let explicit_rows = as_array(&root[3], "r25 implicit-v4 explicit rows")?;
    if regular_overrides.len() > MAX_ENTRIES || explicit_rows.len() > MAX_ENTRIES {
        return Err(PortableError::Limit(
            "r25 implicit-v4 entry count exceeds policy".into(),
        ));
    }
    let total = regular_overrides
        .len()
        .checked_add(explicit_rows.len())
        .ok_or_else(|| PortableError::Limit("r25 implicit-v4 entry counter overflow".into()))?;
    if total > MAX_ENTRIES {
        return Err(PortableError::Limit(
            "r25 implicit-v4 total entry count exceeds policy".into(),
        ));
    }

    if content_entries.iter().any(|entry| entry.kind != 0) {
        return Err(PortableError::Format(
            "r25 content graph contains a non-regular internal member".into(),
        ));
    }
    let graph_paths: HashSet<String> = content_entries.iter().map(|entry| entry.path.clone()).collect();
    if graph_paths.len() != content_entries.len() {
        return Err(PortableError::Integrity(
            "r25 content graph contains duplicate logical members".into(),
        ));
    }
    if !graph_paths.contains(FILESYSTEM_MANIFEST) {
        return Err(PortableError::Integrity(
            "r25 implicit-v4 content graph is missing its control member".into(),
        ));
    }
    if graph_identities.len() != content_entries.len()
        || graph_identities.keys().any(|path| !graph_paths.contains(path))
        || graph_paths.iter().any(|path| !graph_identities.contains_key(path))
    {
        return Err(PortableError::Integrity(
            "r25 implicit-v4 graph identity map does not match content members".into(),
        ));
    }

    let mut regular_paths: Vec<String> = graph_paths
        .iter()
        .filter(|path| path.as_str() != FILESYSTEM_MANIFEST)
        .cloned()
        .collect();
    regular_paths.sort();
    if regular_paths.len() != regular_overrides.len() {
        return Err(PortableError::Integrity(format!(
            "r25 implicit-v4 regular-count mismatch: control={} graph={}",
            regular_overrides.len(),
            regular_paths.len()
        )));
    }

    let mut entries = Vec::with_capacity(total);
    let mut all_paths = HashSet::with_capacity(total);
    for (path, encoded) in regular_paths.iter().zip(regular_overrides.iter()) {
        safe_user_path(path)?;
        if !all_paths.insert(path.clone()) {
            return Err(PortableError::Format(
                "duplicate r25 implicit-v4 regular path".into(),
            ));
        }
        let metadata = apply_override(&default, encoded)?;
        let (size, sha256) = graph_identities.get(path).copied().ok_or_else(|| {
            PortableError::Integrity(format!("missing r25 implicit-v4 graph identity: {path}"))
        })?;
        entries.push(FsEntry {
            path: path.clone(),
            kind: FsKind::File { size, sha256 },
            metadata,
        });
    }

    let mut previous = String::new();
    let mut last_explicit: Option<String> = None;
    for encoded in explicit_rows {
        let row = as_array(encoded, "r25 implicit-v4 explicit row")?;
        if row.len() != 5 {
            return Err(PortableError::Format(
                "malformed r25 implicit-v4 explicit row".into(),
            ));
        }
        let prefix = uint(&row[0], "r25 implicit-v4 path prefix", u64::MAX)? as usize;
        let suffix = text(&row[1], "r25 implicit-v4 path suffix")?;
        let previous_chars = previous.chars().count();
        if prefix > previous_chars {
            return Err(PortableError::Format(
                "r25 implicit-v4 path prefix exceeds previous path".into(),
            ));
        }
        // Python's frozen encoder counts/slices Unicode code points, not UTF-8 bytes. Reconstruct the exact same
        // grammar rather than indexing a Rust String by bytes and accidentally making non-ASCII archives diverge.
        let mut path: String = previous.chars().take(prefix).collect();
        path.push_str(suffix);
        safe_user_path(&path)?;
        if let Some(last) = &last_explicit
            && path <= *last
        {
            return Err(PortableError::Format(
                "r25 implicit-v4 explicit paths are not strictly sorted/unique".into(),
            ));
        }
        if !all_paths.insert(path.clone()) {
            return Err(PortableError::Format(
                "r25 implicit-v4 regular and explicit path sets overlap".into(),
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
                    "r25 implicit-v4 hardlink owner index",
                    regular_paths.len().saturating_sub(1) as u64,
                )? as usize;
                let target = regular_paths.get(owner_index).cloned().ok_or_else(|| {
                    PortableError::Format("r25 implicit-v4 hardlink owner index out of range".into())
                })?;
                FsKind::Hardlink { target }
            }
            _ => {
                return Err(PortableError::Format(
                    "unknown r25 implicit-v4 entry kind".into(),
                ));
            }
        };
        entries.push(FsEntry {
            path: path.clone(),
            kind,
            metadata,
        });
        previous = path.clone();
        last_explicit = Some(path);
    }

    entries.sort_by(|left, right| left.path.cmp(&right.path));
    Ok(entries)
}

fn safe_user_path(path: &str) -> Result<(), PortableError> {
    safe_relpath(path)?;
    if path == INTERNAL_ROOT || path.starts_with(&format!("{INTERNAL_ROOT}/")) {
        return Err(PortableError::Path(path.to_owned()));
    }
    Ok(())
}

fn parse_metadata(value: &Value, label: &str) -> Result<FsMetadata, PortableError> {
    let row = as_array(value, label)?;
    if row.len() != 5 {
        return Err(PortableError::Format(format!("{label} declaration")));
    }
    Ok(FsMetadata {
        mode: uint(&row[0], "r25 implicit-v4 mode", 0o7777)? as u32,
        mtime_ns: signed_i64(&row[1], "r25 implicit-v4 mtime_ns")?,
        uid: uint(&row[2], "r25 implicit-v4 uid", u32::MAX as u64)? as u32,
        gid: uint(&row[3], "r25 implicit-v4 gid", u32::MAX as u64)? as u32,
        xattrs: parse_xattrs(&row[4])?,
    })
}

fn apply_override(default: &FsMetadata, value: &Value) -> Result<FsMetadata, PortableError> {
    let row = as_array(value, "r25 implicit-v4 metadata override")?;
    if row.is_empty() {
        return Err(PortableError::Format(
            "r25 implicit-v4 metadata override declaration".into(),
        ));
    }
    let mask = uint(&row[0], "r25 implicit-v4 metadata mask", ALL_MASK)?;
    if mask & !ALL_MASK != 0 {
        return Err(PortableError::Format(
            "r25 implicit-v4 metadata mask contains unknown bits".into(),
        ));
    }
    let mut cursor = 1usize;
    let mut out = default.clone();
    if mask & MODE != 0 {
        let delta = next_delta(row, &mut cursor, "mode")?;
        out.mode = checked_delta_u32(out.mode, delta, 0o7777, "mode")?;
    }
    if mask & MTIME != 0 {
        let delta = next_delta(row, &mut cursor, "mtime")?;
        out.mtime_ns = out.mtime_ns.checked_add(delta).ok_or_else(|| {
            PortableError::Format("r25 implicit-v4 mtime delta overflow".into())
        })?;
    }
    if mask & UID != 0 {
        let delta = next_delta(row, &mut cursor, "uid")?;
        out.uid = checked_delta_u32(out.uid, delta, u32::MAX as u64, "uid")?;
    }
    if mask & GID != 0 {
        let delta = next_delta(row, &mut cursor, "gid")?;
        out.gid = checked_delta_u32(out.gid, delta, u32::MAX as u64, "gid")?;
    }
    if mask & XATTRS != 0 {
        let value = row.get(cursor).ok_or_else(|| {
            PortableError::Format("r25 implicit-v4 xattr override missing value".into())
        })?;
        out.xattrs = parse_xattrs(value)?;
        cursor += 1;
    }
    if cursor != row.len() {
        return Err(PortableError::Format(
            "r25 implicit-v4 metadata override has trailing fields".into(),
        ));
    }
    Ok(out)
}

fn next_delta(row: &[Value], cursor: &mut usize, label: &str) -> Result<i64, PortableError> {
    let value = row.get(*cursor).ok_or_else(|| {
        PortableError::Format(format!("r25 implicit-v4 {label} delta missing value"))
    })?;
    *cursor += 1;
    signed_i64(value, &format!("r25 implicit-v4 {label} delta"))
}

fn checked_delta_u32(
    base: u32,
    delta: i64,
    maximum: u64,
    label: &str,
) -> Result<u32, PortableError> {
    let value = i64::from(base)
        .checked_add(delta)
        .ok_or_else(|| PortableError::Format(format!("r25 implicit-v4 {label} delta overflow")))?;
    if value < 0 || value as u64 > maximum {
        return Err(PortableError::Format(format!(
            "r25 implicit-v4 {label} reconstructed value outside domain"
        )));
    }
    Ok(value as u32)
}

fn signed_i64(value: &Value, label: &str) -> Result<i64, PortableError> {
    value
        .as_i64()
        .or_else(|| value.as_u64().and_then(|value| i64::try_from(value).ok()))
        .ok_or_else(|| PortableError::Format(format!("{label} declaration")))
}

fn parse_xattrs(value: &Value) -> Result<Vec<(String, Vec<u8>)>, PortableError> {
    let rows = as_array(value, "r25 implicit-v4 xattrs")?;
    if rows.len() > MAX_XATTRS_PER_ENTRY {
        return Err(PortableError::Limit(
            "r25 implicit-v4 xattr count exceeds policy".into(),
        ));
    }
    let mut out = Vec::with_capacity(rows.len());
    let mut total = 0usize;
    for row in rows {
        let row = as_array(row, "r25 implicit-v4 xattr")?;
        if row.len() != 2 {
            return Err(PortableError::Format(
                "malformed r25 implicit-v4 xattr item".into(),
            ));
        }
        let name = text(&row[0], "r25 implicit-v4 xattr name")?.to_owned();
        let Value::Binary(data) = &row[1] else {
            return Err(PortableError::Format(
                "r25 implicit-v4 xattr value must be binary".into(),
            ));
        };
        total = total
            .checked_add(name.len())
            .and_then(|value| value.checked_add(data.len()))
            .ok_or_else(|| PortableError::Limit("r25 implicit-v4 xattr byte counter overflow".into()))?;
        if total > MAX_META_BYTES as usize {
            return Err(PortableError::Limit(
                "r25 implicit-v4 xattr bytes exceed manifest policy".into(),
            ));
        }
        out.push((name, data.clone()));
    }
    Ok(out)
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn checked_unsigned_deltas_fail_closed() {
        assert_eq!(checked_delta_u32(0o640, 4, 0o7777, "mode").unwrap(), 0o644);
        assert!(checked_delta_u32(0, -1, u32::MAX as u64, "uid").is_err());
        assert!(checked_delta_u32(u32::MAX, 1, u32::MAX as u64, "uid").is_err());
    }

    #[test]
    fn unicode_prefix_length_is_counted_as_codepoints() {
        let previous = "αβ/folder";
        let prefix = 2usize;
        let rebuilt: String = previous.chars().take(prefix).collect::<String>() + "γ";
        assert_eq!(rebuilt, "αβγ");
    }
}

// Staging module for the proven implicit-v4 D5 seam. Decoder work is deterministic and bounded; it never reruns
// encoder admission/search. Promotion requires reconciliation onto the exact authoritative Python landing head,
// frozen-vector parity, hostile malformed-control tests, canonical recovery, native authority and Android parity.
