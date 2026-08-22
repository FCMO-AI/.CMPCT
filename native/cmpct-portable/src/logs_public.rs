use super::logs::LogsInverseArchive;
use crate::format::safe_relpath;
use crate::manifest::{FILESYSTEM_MANIFEST, FsEntry, FsKind, FsManifest, FsMetadata};
use crate::{MemberReadStats, PortableEntry, PortableError};
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::Write;
use std::path::Path;

/// Canonical filesystem view layered over the hidden logs inverse content reader.
///
/// Logs profile bytes carry only regular content members plus the authenticated filesystem manifest. Production
/// r25 semantics, however, expose directories, symlinks and hardlinks from that manifest. Keeping this adapter
/// separate from the content grammar mirrors `Canonical25Archive`: the native content decoder stays focused on
/// bounded reconstruction while one manifest implementation owns public filesystem semantics.
pub struct LogsPublicView<'a> {
    archive: &'a LogsInverseArchive,
    manifest: FsManifest,
    public_entries: Vec<PortableEntry>,
}

impl<'a> LogsPublicView<'a> {
    pub fn new(archive: &'a LogsInverseArchive) -> Result<Self, PortableError> {
        let manifest_index = archive
            .entries()
            .iter()
            .position(|entry| entry.path == FILESYSTEM_MANIFEST)
            .ok_or_else(|| {
                PortableError::Integrity("logs inverse filesystem manifest missing".into())
            })?;
        let (manifest_raw, _) = archive.read_member(manifest_index)?;
        let manifest = FsManifest::parse(&manifest_raw, archive.entries())?;
        let public_entries = manifest.public_entries()?;
        Ok(Self {
            archive,
            manifest,
            public_entries,
        })
    }

    pub fn entries(&self) -> &[PortableEntry] {
        &self.public_entries
    }

    fn content_index(&self, path: &str) -> Result<usize, PortableError> {
        self.archive
            .entries()
            .iter()
            .position(|entry| entry.path == path)
            .ok_or_else(|| {
                PortableError::Integrity(format!(
                    "logs inverse filesystem manifest references missing content member: {path}"
                ))
            })
    }

    fn regular_owner<'b>(&'b self, entry: &'b FsEntry) -> Result<&'b FsEntry, PortableError> {
        match &entry.kind {
            FsKind::File { .. } => Ok(entry),
            FsKind::Hardlink { target } => self.manifest.resolve_regular(target),
            _ => Err(PortableError::Unsupported(
                "requested logs inverse entry does not have regular-file content".into(),
            )),
        }
    }

    pub fn stream_member<W: Write>(
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
                    profile: "logs-inverse-r25-preparity",
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
                let (raw, stats) = self.archive.read_member(content_index)?;
                let got_sha: [u8; 32] = Sha256::digest(&raw).into();
                if raw.len() as u64 != *expected_size || got_sha != *expected_sha {
                    return Err(PortableError::Integrity(format!(
                        "logs inverse streamed filesystem identity mismatch: {}",
                        owner.path
                    )));
                }
                output.write_all(&raw)?;
                Ok(MemberReadStats {
                    logical_bytes: *expected_size,
                    ..stats
                })
            }
        }
    }

    pub fn read_member(&self, index: usize) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
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
                "logs inverse whole-member materialization is limited to 64 MiB; use stream_member"
                    .into(),
            ));
        }
        let mut bytes = Vec::with_capacity(capacity as usize);
        let stats = self.stream_member(index, &mut bytes)?;
        Ok((bytes, stats))
    }

    pub fn verify(&self) -> Result<(), PortableError> {
        self.archive.verify()?;
        // Re-resolve every public regular/hardlink through the authenticated filesystem manifest. This keeps
        // preparity honest about the exact public namespace that production dispatch will expose.
        for index in 0..self.public_entries.len() {
            let entry = self.manifest.entry(index)?;
            if matches!(&entry.kind, FsKind::File { .. } | FsKind::Hardlink { .. }) {
                self.stream_member(index, std::io::sink())?;
            }
        }
        Ok(())
    }

    /// Materialize the authenticated canonical filesystem into an already-staged directory.
    ///
    /// This deliberately mirrors the production canonical-r25 materializer but remains reachable only through
    /// logs preparity. Transactional publication stays owned by `PortableArchive` once dispatch is promoted.
    pub fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
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

    pub fn export_zip(&self, destination: &Path) -> Result<(), PortableError> {
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
    }
    let _ = (metadata.uid, metadata.gid, &metadata.xattrs);
}
