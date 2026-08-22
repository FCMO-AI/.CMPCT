use super::logs::LogsInverseArchive;
use crate::manifest::{FILESYSTEM_MANIFEST, FsKind, FsManifest};
use crate::{MemberReadStats, PortableEntry, PortableError};

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
            .ok_or_else(|| PortableError::Integrity("logs inverse filesystem manifest missing".into()))?;
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

    pub fn read_member(
        &self,
        index: usize,
    ) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let entry = self.manifest.entry(index)?;
        let owner_path = match &entry.kind {
            FsKind::File { .. } => entry.path.as_str(),
            FsKind::Hardlink { target } => self.manifest.resolve_regular(target)?.path.as_str(),
            FsKind::Directory => {
                return Err(PortableError::Unsupported(
                    "cannot read bytes from a logs inverse directory entry".into(),
                ));
            }
            FsKind::Symlink { .. } => {
                return Err(PortableError::Unsupported(
                    "cannot read bytes from a logs inverse symlink entry".into(),
                ));
            }
        };
        self.archive.read_member(self.content_index(owner_path)?)
    }
}
