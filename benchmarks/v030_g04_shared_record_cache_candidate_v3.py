from __future__ import annotations

"""Construct the superseding v3 G0-G4 shared-record-cache candidate.

This fail-closed mutator targets the exact canonical Rust source shape frozen by the
v3 preregistration. It changes only operation-scoped execution reuse: authenticated
physical records may be reused across members during one verify/extract operation.
Representation bytes, grammar, selector, integrity, locality, decode-unit and caller
publication-budget laws are unchanged.
"""

from pathlib import Path

G04 = Path("native/cmpct-portable/src/g04.rs")
CANONICAL = Path("native/cmpct-portable/src/canonical.rs")


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one source match, found {n}")
    return text.replace(old, new, 1)


def main() -> None:
    g = G04.read_text(encoding="utf-8")
    g = once(g, "use std::fs::File;\n", "use std::fs::{self, File};\n", "fs import")
    g = once(g, "use std::path::Path;\n", "use std::path::{Path, PathBuf};\n", "PathBuf import")

    g = once(
        g,
        """    pub(crate) fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        let (_, file) = self.file_at(index)?;
        let mut context = DecodeContext::new(self);
""",
        """    pub(crate) fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        let mut record_cache = SharedRecordCache::new();
        self.stream_member_with_record_cache(index, &mut output, &mut record_cache)
    }

    fn stream_member_with_record_cache<W: Write>(
        &self,
        index: usize,
        mut output: W,
        record_cache: &mut SharedRecordCache,
    ) -> Result<MemberReadStats, PortableError> {
        let (_, file) = self.file_at(index)?;
        let mut context = DecodeContext::new(self, record_cache);
""",
        "shared stream entry",
    )

    g = once(
        g,
        """    pub(crate) fn verify(&self) -> Result<(), PortableError> {
        let mut tree = Sha256::new();
        for (index, entry) in self.entries.iter().enumerate() {
            tree_hasher_prefix(&mut tree, &entry.path, entry.size);
            let mut sink = DigestWriter(&mut tree);
            self.stream_member(index, &mut sink)?;
        }
""",
        """    pub(crate) fn verify(&self) -> Result<(), PortableError> {
        let mut tree = Sha256::new();
        let mut record_cache = SharedRecordCache::new();
        for (index, entry) in self.entries.iter().enumerate() {
            tree_hasher_prefix(&mut tree, &entry.path, entry.size);
            let mut sink = DigestWriter(&mut tree);
            self.stream_member_with_record_cache(index, &mut sink, &mut record_cache)?;
        }
""",
        "shared verify route",
    )

    g = once(
        g,
        """        Ok(())
    }
}

struct DigestWriter<'a>(&'a mut Sha256);
""",
        """        Ok(())
    }

    pub(crate) fn extract_members_shared(
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
}

struct DigestWriter<'a>(&'a mut Sha256);
""",
        "shared extraction method",
    )

    g = once(
        g,
        """struct DecodeContext<'a> {
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
""",
        """struct SharedRecordCache {
    values: HashMap<usize, Arc<Vec<u8>>>,
    bytes: usize,
}

impl SharedRecordCache {
    fn new() -> Self {
        Self {
            values: HashMap::new(),
            bytes: 0,
        }
    }
}

struct DecodeContext<'a, 'c> {
    archive: &'a G04Archive,
    record_cache: &'c mut SharedRecordCache,
    node_cache: HashMap<usize, Arc<Vec<u8>>>,
    node_cache_bytes: usize,
    touched_records: HashMap<usize, u64>,
}

impl<'a, 'c> DecodeContext<'a, 'c> {
    fn new(archive: &'a G04Archive, record_cache: &'c mut SharedRecordCache) -> Self {
        Self {
            archive,
            record_cache,
            node_cache: HashMap::new(),
            node_cache_bytes: 0,
            touched_records: HashMap::new(),
        }
    }
""",
        "shared cache context",
    )

    g = once(
        g,
        """        if let Some(value) = self.record_cache.get(&record_id) {
            return Ok(Arc::clone(value));
        }
""",
        """        if let Some(value) = self.record_cache.values.get(&record_id) {
            self.touched_records
                .entry(record_id)
                .or_insert(value.len() as u64);
            return Ok(Arc::clone(value));
        }
""",
        "cache-hit locality charge",
    )

    g = once(
        g,
        """        if self.record_cache_bytes.saturating_add(value.len()) <= MAX_RECORD_CACHE_BYTES {
            self.record_cache_bytes += value.len();
            self.record_cache.insert(record_id, Arc::clone(&value));
        }
""",
        """        if self.record_cache.bytes.saturating_add(value.len()) <= MAX_RECORD_CACHE_BYTES {
            self.record_cache.bytes += value.len();
            self.record_cache
                .values
                .insert(record_id, Arc::clone(&value));
        }
""",
        "shared cache insertion",
    )
    G04.write_text(g, encoding="utf-8")

    c = CANONICAL.read_text(encoding="utf-8")
    c = once(
        c,
        """    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
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

""",
        """    pub(crate) fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
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

""",
        "canonical G04 shared extraction route",
    )
    CANONICAL.write_text(c, encoding="utf-8")


if __name__ == "__main__":
    main()
