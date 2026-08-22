use crate::format::{safe_relpath, sha256};
use crate::g04::G04Archive;
use crate::identity::R25Identity;
use crate::manifest::{FILESYSTEM_MANIFEST, FsEntry, FsKind, FsManifest, FsMetadata};
use crate::prefix::PrefixArchive;
use crate::{MemberReadStats, PortableEntry, PortableError, Profile};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Write;
use std::path::Path;

#[derive(Debug)]
enum ContentArchive {
    G04(G04Archive),
    Prefix(PrefixArchive),
}

impl ContentArchive {
    fn open(path: &Path, identity: R25Identity) -> Result<Self, PortableError> {
        match identity {
            R25Identity::CanonicalG04 => Ok(Self::G04(G04Archive::open(path, identity)?)),
            R25Identity::CanonicalPrefix => Ok(Self::Prefix(PrefixArchive::open(path, identity)?)),
            _ => Err(PortableError::Format(
                "canonical r25 wrapper received a research profile identity".into(),
            )),
        }
    }

    fn entries(&self) -> &[PortableEntry] {
        match self {
            Self::G04(archive) => archive.entries(),
            Self::Prefix(archive) => archive.entries(),
        }
    }

    fn entry_identity(&self, index: usize) -> Result<(u64, [u8; 32]), PortableError> {
        match self {
            Self::G04(archive) => archive.entry_identity(index),
            Self::Prefix(archive) => archive.entry_identity(index),
        }
    }

    fn stream_member<W: Write>(
        &self,
        index: usize,
        output: W,
    ) -> Result<MemberReadStats, PortableError> {
        match self {
            Self::G04(archive) => archive.stream_member(index, output),
            Self::Prefix(archive) => archive.stream_member(index, output),
        }
    }

    fn read_member(&self, index: usize) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        match self {
            Self::G04(archive) => archive.read_member(index),
            Self::Prefix(archive) => archive.read_member(index),
        }
    }

    fn verify(&self) -> Result<(), PortableError> {
        match self {
            Self::G04(archive) => archive.verify(),
            Self::Prefix(archive) => archive.verify(),
        }
    }

    fn tail_authenticated(&self) -> bool {
        match self {
            Self::G04(archive) => archive.tail_authenticated(),
            Self::Prefix(archive) => archive.tail_authenticated(),
        }
    }

    fn declared_amplification(&self) -> f64 {
        match self {
            Self::G04(archive) => archive.declared_amplification(),
            Self::Prefix(_) => 8.0,
        }
    }
}

#[derive(Debug)]
pub struct Canonical25Archive {
    identity: R25Identity,
    content: ContentArchive,
    manifest: FsManifest,
    entries: Vec<PortableEntry>,
}

impl Canonical25Archive {
    pub(crate) fn open(path: &Path, identity: R25Identity) -> Result<Self, PortableError> {
        if !identity.is_canonical() {
            return Err(PortableError::Format(
                "research CMPNX bytes cannot enter the canonical r25 wrapper".into(),
            ));
        }
        let content = ContentArchive::open(path, identity)?;
        let manifest_index = content
            .entries()
            .iter()
            .position(|entry| entry.path == FILESYSTEM_MANIFEST)
            .ok_or_else(|| {
                PortableError::Format(
                    "canonical r25 archive is missing its filesystem manifest".into(),
                )
            })?;
        let (manifest_raw, _) = content.read_member(manifest_index)?;
        let manifest = FsManifest::parse(&manifest_raw, content.entries())?;

        let (manifest_size, manifest_sha) = content.entry_identity(manifest_index)?;
        if manifest_size != manifest_raw.len() as u64 || manifest_sha != sha256(&manifest_raw) {
            return Err(PortableError::Integrity(
                "canonical r25 manifest graph identity mismatch".into(),
            ));
        }
        for entry in manifest.entries() {
            let FsKind::File { size, sha256 } = &entry.kind else {
                continue;
            };
            let index = content
                .entries()
                .iter()
                .position(|candidate| candidate.path == entry.path)
                .ok_or_else(|| {
                    PortableError::Integrity(format!("missing r25 graph member: {}", entry.path))
                })?;
            let (graph_size, graph_sha) = content.entry_identity(index)?;
            if graph_size != *size || graph_sha != *sha256 {
                return Err(PortableError::Integrity(format!(
                    "r25 manifest/content identity mismatch: {}",
                    entry.path
                )));
            }
        }
        let entries = manifest.public_entries()?;
        Ok(Self {
            identity,
            content,
            manifest,
            entries,
        })
    }

    pub(crate) fn profile(&self) -> Profile {
        match self.identity {
            R25Identity::CanonicalG04 => Profile::G04,
            R25Identity::CanonicalPrefix => Profile::PrefixGraph,
            _ => unreachable!("Canonical25Archive identity checked at open"),
        }
    }

    pub(crate) fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    pub(crate) fn tail_authenticated(&self) -> bool {
        self.content.tail_authenticated()
    }

    pub(crate) fn declared_amplification(&self) -> f64 {
        self.content.declared_amplification()
    }

    fn content_index(&self, path: &str) -> Result<usize, PortableError> {
        self.content
            .entries()
            .iter()
            .position(|entry| entry.path == path)
            .ok_or_else(|| {
                PortableError::Integrity(format!(
                    "canonical r25 content member disappeared: {path}"
                ))
            })
    }

    fn regular_owner<'a>(&'a self, entry: &'a FsEntry) -> Result<&'a FsEntry, PortableError> {
        match &entry.kind {
            FsKind::File { .. } => Ok(entry),
            FsKind::Hardlink { target } => self.manifest.resolve_regular(target),
            _ => Err(PortableError::Unsupported(
                "requested r25 entry does not have regular-file content".into(),
            )),
        }
    }

    pub(crate) fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        let entry = self.manifest.entry(index)?;
        match &entry.kind {
            FsKind::Directory => Err(PortableError::Unsupported(
                "directories do not have a byte stream".into(),
            )),
            FsKind::Symlink { target } => {
                output.write_all(target.as_bytes())?;
                Ok(MemberReadStats {
                    logical_bytes: target.len() as u64,
                    decoded_context_bytes: target.len() as u64,
                    amplification: 1.0,
                    profile: self.identity.profile_name(),
                })
            }
            FsKind::File { .. } | FsKind::Hardlink { .. } => {
                let owner = self.regular_owner(entry)?;
                let FsKind::File {
                    size: expected_size,
                    sha256: expected_sha,
                } = &owner.kind
                else {
                    unreachable!("regular_owner returns file")
                };
                let content_index = self.content_index(&owner.path)?;
                let mut verified = IdentityWriter {
                    inner: &mut output,
                    digest: Sha256::new(),
                    bytes: 0,
                };
                let stats = self.content.stream_member(content_index, &mut verified)?;
                let got_sha: [u8; 32] = verified.digest.finalize().into();
                if verified.bytes != *expected_size || got_sha != *expected_sha {
                    return Err(PortableError::Integrity(format!(
                        "r25 streamed filesystem identity mismatch: {}",
                        owner.path
                    )));
                }
                Ok(MemberReadStats {
                    logical_bytes: *expected_size,
                    ..stats
                })
            }
        }
    }

    pub(crate) fn read_member(
        &self,
        index: usize,
    ) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let entry = self.manifest.entry(index)?;
        let capacity = match &entry.kind {
            FsKind::File { size, .. } => *size,
            FsKind::Hardlink { target } => match &self.manifest.resolve_regular(target)?.kind {
                FsKind::File { size, .. } => *size,
                _ => unreachable!("resolve_regular returns file"),
            },
            FsKind::Symlink { target } => target.len() as u64,
            FsKind::Directory => 0,
        };
        if capacity > 64 * 1024 * 1024 {
            return Err(PortableError::Limit(
                "canonical r25 whole-member materialization is limited to 64 MiB; use stream_member".into(),
            ));
        }
        let mut bytes = Vec::with_capacity(capacity as usize);
        let stats = self.stream_member(index, &mut bytes)?;
        Ok((bytes, stats))
    }

    pub(crate) fn verify(&self) -> Result<(), PortableError> {
        // Footnote: open() already cross-checks every regular-file size/SHA against authenticated graph
        // metadata. The profile verifier then authenticates/decompresses every physical record and recomputes
        // the graph tree hash, avoiding a second full decode solely to re-prove manifest identities.
        self.content.verify()
    }

    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
        for (index, entry) in self.manifest.entries().iter().enumerate() {
            if !matches!(&entry.kind, FsKind::File { .. }) {
                continue;
            }
            let target = root.join(safe_relpath(&entry.path)?);
            if let Some(parent) = target.parent() {
                fs::create_dir_all(parent)?;
            }
            let mut file = File::create(&target)?;
            self.stream_member(index, &mut file)?;
            file.flush()?;
        }

        for entry in self.manifest.entries() {
            let target = root.join(safe_relpath(&entry.path)?);
            match &entry.kind {
                FsKind::Directory => fs::create_dir_all(&target)?,
                FsKind::Symlink {
                    target: link_target,
                } => {
                    ensure_safe_symlink(link_target, &entry.path)?;
                    if let Some(parent) = target.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    create_symlink(link_target, &target)?;
                }
                FsKind::Hardlink { target: owner } => {
                    if let Some(parent) = target.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    let owner = root.join(safe_relpath(owner)?);
                    fs::hard_link(owner, target)?;
                }
                FsKind::File { .. } => {}
            }
        }

        // Apply children before directory metadata so creating a child cannot perturb the restored directory
        // mode/mtime. Ownership/xattrs are best-effort just like the Python product bridge: insufficient host
        // privilege must not turn a valid archive into partial publication because extraction is staged.
        for entry in self
            .manifest
            .entries()
            .iter()
            .filter(|entry| !matches!(&entry.kind, FsKind::Directory))
        {
            let target = root.join(safe_relpath(&entry.path)?);
            apply_metadata_best_effort(
                &target,
                &entry.metadata,
                matches!(&entry.kind, FsKind::Symlink { .. }),
            );
        }
        let mut directories: Vec<&FsEntry> = self
            .manifest
            .entries()
            .iter()
            .filter(|entry| matches!(&entry.kind, FsKind::Directory))
            .collect();
        directories.sort_by_key(|entry| std::cmp::Reverse(entry.path.matches('/').count()));
        for entry in directories {
            let target = root.join(safe_relpath(&entry.path)?);
            apply_metadata_best_effort(&target, &entry.metadata, false);
        }
        Ok(())
    }

    pub(crate) fn export_zip(&self, destination: &Path) -> Result<(), PortableError> {
        let file = File::create(destination)?;
        let mut writer = zip::ZipWriter::new(file);
        let options = zip::write::SimpleFileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated);
        for (index, entry) in self.manifest.entries().iter().enumerate() {
            match &entry.kind {
                FsKind::File { .. } | FsKind::Hardlink { .. } => {
                    writer.start_file(&entry.path, options).map_err(|error| {
                        PortableError::Format(format!("ZIP start_file: {error}"))
                    })?;
                    self.stream_member(index, &mut writer)?;
                }
                FsKind::Directory => {
                    writer
                        .add_directory(format!("{}/", entry.path.trim_end_matches('/')), options)
                        .map_err(|error| {
                            PortableError::Format(format!("ZIP add_directory: {error}"))
                        })?;
                }
                FsKind::Symlink { .. } => {
                    return Err(PortableError::Unsupported(
                        "portable ZIP export refuses symlinks instead of silently changing link semantics"
                            .into(),
                    ));
                }
            }
        }
        writer
            .finish()
            .map_err(|error| PortableError::Format(format!("ZIP finish: {error}")))?;
        Ok(())
    }
}

struct IdentityWriter<'a, W> {
    inner: &'a mut W,
    digest: Sha256,
    bytes: u64,
}

impl<W: Write> Write for IdentityWriter<'_, W> {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        let written = self.inner.write(buf)?;
        self.digest.update(&buf[..written]);
        self.bytes = self.bytes.saturating_add(written as u64);
        Ok(written)
    }

    fn flush(&mut self) -> std::io::Result<()> {
        self.inner.flush()
    }
}

fn ensure_safe_symlink(target: &str, rel: &str) -> Result<(), PortableError> {
    let normalized = target.replace('\\', "/");
    let bytes = normalized.as_bytes();
    let has_windows_drive = bytes.len() >= 2 && bytes[1] == b':' && bytes[0].is_ascii_alphabetic();
    let has_parent = normalized.split('/').any(|part| part == "..");
    if target.is_empty()
        || target.contains('\0')
        || normalized.starts_with('/')
        || has_windows_drive
        || has_parent
    {
        return Err(PortableError::Path(format!(
            "unsafe r25 symlink target in {rel}: {target}"
        )));
    }
    // Footnote: the manifest already enforces this portable lexical rule at authenticated preflight. Repeat the
    // same rule immediately before materialization so a future parser/extractor refactor cannot make a target
    // safe on Linux but traversal-capable when the same archive is later extracted on Windows.
    Ok(())
}

#[cfg(unix)]
fn create_symlink(target: &str, destination: &Path) -> Result<(), PortableError> {
    std::os::unix::fs::symlink(target, destination)?;
    Ok(())
}

#[cfg(windows)]
fn create_symlink(_target: &str, _destination: &Path) -> Result<(), PortableError> {
    Err(PortableError::Unsupported(
        "safe r25 symlink extraction on Windows requires an explicit file-vs-directory target contract"
            .into(),
    ))
}

#[cfg(not(any(unix, windows)))]
fn create_symlink(_target: &str, _destination: &Path) -> Result<(), PortableError> {
    Err(PortableError::Unsupported(
        "symlink extraction is unavailable on this platform".into(),
    ))
}

fn system_time_from_unix_nanos(nanos: i64) -> Option<std::time::SystemTime> {
    let duration = std::time::Duration::from_nanos(nanos.unsigned_abs());
    if nanos >= 0 {
        std::time::UNIX_EPOCH.checked_add(duration)
    } else {
        std::time::UNIX_EPOCH.checked_sub(duration)
    }
}

fn apply_metadata_best_effort(path: &Path, metadata: &FsMetadata, is_symlink: bool) {
    if !is_symlink {
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let _ = fs::set_permissions(path, fs::Permissions::from_mode(metadata.mode));
        }
        if let Ok(file) = File::open(path)
            && let Some(time) = system_time_from_unix_nanos(metadata.mtime_ns)
        {
            let _ = file.set_times(std::fs::FileTimes::new().set_modified(time));
        }
        // Footnote: ``mtime_ns`` is a signed archive field. Converting a negative value to ``u64`` first wraps
        // it into the distant future and silently defeats pre-1970 restoration; checked add/sub preserves the
        // exact signed domain admitted by the manifest while remaining best-effort on limited host filesystems.
    }
    let _ = (metadata.uid, metadata.gid, &metadata.xattrs);
    // Footnote: uid/gid/xattr restoration is intentionally retained in the parsed contract even on hosts where
    // this small portable crate cannot set it without privilege/platform-specific APIs. The staged extractor
    // never fabricates values; platform adapters may add best-effort setters without changing archive grammar.
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn materializer_symlink_guard_matches_portable_manifest_policy() {
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
                ensure_safe_symlink(target, "link").is_err(),
                "materializer accepted hostile target {target:?}"
            );
        }
        for target in ["folder/file.txt", "folder\\file.txt", "same-file", "a..b"] {
            assert!(
                ensure_safe_symlink(target, "link").is_ok(),
                "materializer rejected benign target {target:?}"
            );
        }
        // Footnote: this duplicates the parser's hostile vector intentionally. The test protects the second
        // trust boundary immediately before ``symlink()`` so parser hardening cannot later be weakened by a
        // host-only materializer check.
    }

    #[test]
    fn signed_mtime_conversion_preserves_both_sides_of_unix_epoch() {
        let before = system_time_from_unix_nanos(-1_000_000_000).expect("pre-epoch time");
        let after = system_time_from_unix_nanos(1_000_000_000).expect("post-epoch time");
        assert_eq!(
            std::time::UNIX_EPOCH.duration_since(before).unwrap(),
            std::time::Duration::from_secs(1)
        );
        assert_eq!(
            after.duration_since(std::time::UNIX_EPOCH).unwrap(),
            std::time::Duration::from_secs(1)
        );
        assert!(system_time_from_unix_nanos(i64::MIN).is_some());
        assert!(system_time_from_unix_nanos(i64::MAX).is_some());

        // Footnote: parser parity is incomplete if extraction silently maps every negative timestamp to an
        // unusable wrapped future duration. This test pins the same signed i64 domain at materialization time.
    }
}
