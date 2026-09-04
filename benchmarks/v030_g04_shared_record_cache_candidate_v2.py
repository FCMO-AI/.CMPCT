from __future__ import annotations

"""Build the superseding v2 G0-G4 shared-record-cache research candidate.

This helper runs only after the exact-current G0-G4 hunks from
``benchmarks/patches/v030_g04_operation_record_cache.patch`` have been applied.
It deliberately changes execution reuse only: no archive bytes, grammar,
selector, memory/locality limits, integrity checks, or output-budget law.
"""

from pathlib import Path

G04 = Path("native/cmpct-portable/src/g04.rs")
CANONICAL = Path("native/cmpct-portable/src/canonical.rs")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    g04 = G04.read_text(encoding="utf-8")
    g04 = replace_once(
        g04,
        "use std::path::Path;\n",
        "use std::path::{Path, PathBuf};\n",
        "g04 PathBuf import",
    )
    anchor = """    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
        let mut record_cache = SharedRecordCache::new();
"""
    insert = """    pub(crate) fn extract_members_shared(
        &self,
        targets: &[(usize, PathBuf)],
    ) -> Result<(), PortableError> {
        let mut record_cache = SharedRecordCache::new();
        for (index, target) in targets {
            if let Some(parent) = target.parent() {
                fs::create_dir_all(parent)?;
            }
            let mut file = File::create(target)?;
            self.stream_member_with_record_cache(*index, &mut file, &mut record_cache)?;
            file.flush()?;
        }
        Ok(())
    }

    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
        let mut record_cache = SharedRecordCache::new();
"""
    g04 = replace_once(g04, anchor, insert, "g04 shared member extractor")
    G04.write_text(g04, encoding="utf-8")

    canonical = CANONICAL.read_text(encoding="utf-8")
    old = """    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
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

"""
    new = """    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
        if let ContentArchive::G04(archive) = &self.content {
            let mut targets = Vec::new();
            for entry in self.manifest.entries() {
                if !matches!(&entry.kind, FsKind::File { .. }) {
                    continue;
                }
                let content_index = self.content_index(&entry.path)?;
                targets.push((content_index, root.join(safe_relpath(&entry.path)?)));
            }
            archive.extract_members_shared(&targets)?;
        } else {
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
        }

"""
    canonical = replace_once(
        canonical,
        old,
        new,
        "canonical G04 shared extraction route",
    )
    CANONICAL.write_text(canonical, encoding="utf-8")


if __name__ == "__main__":
    main()
