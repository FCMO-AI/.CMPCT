mod canonical;
mod format;
mod g04;
mod identity;
mod manifest;
mod prefix;

use crate::canonical::Canonical25Archive;
use crate::format::safe_relpath;
use crate::identity::{classify, R25Identity};
use cmpct_core::Archive as R24Archive;
use std::ffi::CStr;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::os::raw::{c_char, c_int};
use std::path::{Path, PathBuf};
use std::ptr;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;

const R24_MAGIC: &[u8; 8] = b"CMPCT24\0";
const R24_VERIFY_MATERIALIZE_LIMIT: u64 = 256 * 1024 * 1024;

#[derive(Debug, Error)]
pub enum PortableError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("I/O state error: {0}")]
    IoState(String),
    #[error("format error: {0}")]
    Format(String),
    #[error("integrity error: {0}")]
    Integrity(String),
    #[error("resource limit: {0}")]
    Limit(String),
    #[error("unsafe logical path: {0}")]
    Path(String),
    #[error("unsupported operation: {0}")]
    Unsupported(String),
    #[error("requested range/buffer is invalid")]
    Range,
    #[error("revision-24 core: {0}")]
    R24(#[from] cmpct_core::CmpctError),
}

#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub enum Profile {
    Revision24,
    G04,
    PrefixGraph,
    ResearchG04,
    ResearchPrefixGraph,
}

impl Profile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Revision24 => "r24",
            Self::G04 => "g04-r25",
            Self::PrefixGraph => "prefixgraph-r25",
            Self::ResearchG04 => "research-g04",
            Self::ResearchPrefixGraph => "research-prefixgraph",
        }
    }

    pub fn revision(self) -> u32 {
        match self {
            Self::Revision24 => 24,
            Self::G04 | Self::PrefixGraph => 25,
            Self::ResearchG04 | Self::ResearchPrefixGraph => 0,
        }
    }
}

#[derive(Debug, Clone)]
pub struct PortableEntry {
    pub path: String,
    pub size: u64,
    pub kind: u8,
    pub mode: u32,
    pub mtime_ns: i64,
}

#[derive(Debug, Clone, Copy)]
pub struct MemberReadStats {
    pub logical_bytes: u64,
    pub decoded_context_bytes: u64,
    pub amplification: f64,
    pub profile: &'static str,
}

#[derive(Debug)]
pub enum PortableArchive {
    Revision24(R24Archive),
    Canonical25(Canonical25Archive),
    ResearchG04(g04::G04Archive),
    ResearchPrefixGraph(prefix::PrefixArchive),
}

impl PortableArchive {
    pub fn open(path: &Path) -> Result<Self, PortableError> {
        let mut probe = File::open(path)?;
        let mut magic = [0u8; 8];
        probe.read_exact(&mut magic)?;
        if &magic == R24_MAGIC {
            return Ok(Self::Revision24(R24Archive::open(path)?));
        }
        let identity = classify(&magic).ok_or_else(|| {
            PortableError::Format("archive magic is not a supported r24/r25 representation".into())
        })?;
        match identity {
            R25Identity::CanonicalG04 | R25Identity::CanonicalPrefix => {
                Ok(Self::Canonical25(Canonical25Archive::open(path, identity)?))
            }
            R25Identity::ResearchG04 => {
                Ok(Self::ResearchG04(g04::G04Archive::open(path, identity)?))
            }
            R25Identity::ResearchPrefix => Ok(Self::ResearchPrefixGraph(
                prefix::PrefixArchive::open(path, identity)?,
            )),
        }
    }

    pub fn profile(&self) -> Profile {
        match self {
            Self::Revision24(_) => Profile::Revision24,
            Self::Canonical25(archive) => archive.profile(),
            Self::ResearchG04(_) => Profile::ResearchG04,
            Self::ResearchPrefixGraph(_) => Profile::ResearchPrefixGraph,
        }
    }

    pub fn revision(&self) -> u32 {
        self.profile().revision()
    }

    pub fn tail_metadata_authenticated(&self) -> bool {
        match self {
            Self::Revision24(_) => false,
            Self::Canonical25(archive) => archive.tail_authenticated(),
            Self::ResearchG04(archive) => archive.tail_authenticated(),
            Self::ResearchPrefixGraph(archive) => archive.tail_authenticated(),
        }
    }

    pub fn declared_member_read_amplification(&self) -> Option<f64> {
        match self {
            Self::Revision24(_) => None,
            Self::Canonical25(archive) => Some(archive.declared_amplification()),
            Self::ResearchG04(archive) => Some(archive.declared_amplification()),
            Self::ResearchPrefixGraph(_) => Some(8.0),
        }
    }

    pub fn entries(&self) -> Vec<PortableEntry> {
        match self {
            Self::Revision24(archive) => archive
                .entries()
                .iter()
                .map(|entry| PortableEntry {
                    path: entry.path.clone(),
                    size: entry.size,
                    kind: entry.kind,
                    mode: entry.mode,
                    mtime_ns: entry.mtime_ns,
                })
                .collect(),
            Self::Canonical25(archive) => archive.entries().to_vec(),
            Self::ResearchG04(archive) => archive.entries().to_vec(),
            Self::ResearchPrefixGraph(archive) => archive.entries().to_vec(),
        }
    }

    pub fn entry_index(&self, path: &str) -> Option<usize> {
        self.entries().iter().position(|entry| entry.path == path)
    }

    pub fn stream_member<W: Write>(
        &self,
        index: usize,
        mut output: W,
    ) -> Result<MemberReadStats, PortableError> {
        match self {
            Self::Revision24(archive) => {
                let entry = archive
                    .entries()
                    .get(index)
                    .ok_or_else(|| PortableError::Format("r24 entry id out of range".into()))?;
                if entry.kind != 0 {
                    return Err(PortableError::Unsupported(
                        "r24 stream_member currently accepts regular files only".into(),
                    ));
                }
                // Footnote: the r24 adapter delegates every byte read to cmpct-core. Chunking here is only
                // output plumbing; no r24 MessagePack/blob grammar is duplicated in the r25 dispatcher.
                let mut offset = 0u64;
                let mut buffer = vec![0u8; 1024 * 1024];
                while offset < entry.size {
                    let take = usize::try_from((entry.size - offset).min(buffer.len() as u64))
                        .map_err(|_| PortableError::Range)?;
                    let got = archive.read_range(index, offset, &mut buffer[..take])?;
                    if got != take {
                        return Err(PortableError::Integrity(
                            "r24 core returned short logical member range".into(),
                        ));
                    }
                    output.write_all(&buffer[..take])?;
                    offset += take as u64;
                }
                Ok(MemberReadStats {
                    logical_bytes: entry.size,
                    decoded_context_bytes: entry.size,
                    amplification: 1.0,
                    profile: "r24",
                })
            }
            Self::Canonical25(archive) => archive.stream_member(index, output),
            Self::ResearchG04(archive) => archive.stream_member(index, output),
            Self::ResearchPrefixGraph(archive) => archive.stream_member(index, output),
        }
    }

    pub fn read_member(&self, index: usize) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        match self {
            Self::Revision24(archive) => {
                let entry = archive
                    .entries()
                    .get(index)
                    .ok_or_else(|| PortableError::Format("r24 entry id out of range".into()))?;
                if entry.kind != 0 || entry.size > R24_VERIFY_MATERIALIZE_LIMIT {
                    return Err(PortableError::Limit(
                        "r24 whole-member materialization is limited to regular files <=256 MiB".into(),
                    ));
                }
                let mut out = vec![0u8; entry.size as usize];
                let got = archive.read_range(index, 0, &mut out)?;
                if got != out.len() {
                    return Err(PortableError::Integrity(
                        "r24 core returned short whole-member read".into(),
                    ));
                }
                Ok((
                    out,
                    MemberReadStats {
                        logical_bytes: entry.size,
                        decoded_context_bytes: entry.size,
                        amplification: 1.0,
                        profile: "r24",
                    },
                ))
            }
            Self::Canonical25(archive) => archive.read_member(index),
            Self::ResearchG04(archive) => archive.read_member(index),
            Self::ResearchPrefixGraph(archive) => archive.read_member(index),
        }
    }

    pub fn read_member_path(&self, path: &str) -> Result<(Vec<u8>, MemberReadStats), PortableError> {
        let index = self
            .entry_index(path)
            .ok_or_else(|| PortableError::Format(format!("member not found: {path}")))?;
        self.read_member(index)
    }

    pub fn read_range(
        &self,
        index: usize,
        offset: u64,
        output: &mut [u8],
    ) -> Result<usize, PortableError> {
        let entry = self
            .entries()
            .get(index)
            .cloned()
            .ok_or_else(|| PortableError::Range)?;
        if entry.kind == 1 || offset > entry.size {
            return Err(PortableError::Range);
        }
        let wanted = usize::try_from((entry.size - offset).min(output.len() as u64))
            .map_err(|_| PortableError::Range)?;
        if wanted == 0 {
            return Ok(0);
        }
        if let Self::Revision24(archive) = self {
            return Ok(archive.read_range(index, offset, &mut output[..wanted])?);
        }

        // Footnote: r25's release locality contract is member-selective, not arbitrary sub-member random access.
        // The bridge therefore avoids materializing a giant file but still authenticates the complete selected
        // member before returning its requested window. r24 retains its mature exact range path above.
        let mut writer = RangeWriter::new(offset, &mut output[..wanted]);
        self.stream_member(index, &mut writer)?;
        if writer.written != wanted {
            return Err(PortableError::Integrity(
                "r25 range read ended before the requested logical window".into(),
            ));
        }
        Ok(writer.written)
    }

    pub fn member_stats(&self, index: usize) -> Result<MemberReadStats, PortableError> {
        match self {
            Self::Revision24(archive) => {
                let entry = archive
                    .entries()
                    .get(index)
                    .ok_or_else(|| PortableError::Format("r24 entry id out of range".into()))?;
                Ok(MemberReadStats {
                    logical_bytes: entry.size,
                    decoded_context_bytes: entry.size,
                    amplification: 1.0,
                    profile: "r24",
                })
            }
            _ => self.stream_member(index, std::io::sink()),
        }
    }

    pub fn verify(&self) -> Result<(), PortableError> {
        match self {
            Self::Revision24(archive) => {
                for (index, entry) in archive.entries().iter().enumerate() {
                    if entry.kind != 0 {
                        continue;
                    }
                    if entry.size > R24_VERIFY_MATERIALIZE_LIMIT {
                        return Err(PortableError::Limit(
                            "native r24 verify requires a <=256 MiB whole-member read; use the mature r24 verifier for larger objects".into(),
                        ));
                    }
                    let mut bytes = vec![0u8; entry.size as usize];
                    archive.read_range(index, 0, &mut bytes)?;
                }
                Ok(())
            }
            Self::Canonical25(archive) => archive.verify(),
            Self::ResearchG04(archive) => archive.verify(),
            Self::ResearchPrefixGraph(archive) => archive.verify(),
        }
    }

    pub fn extract_transactional(&self, destination: &Path) -> Result<(), PortableError> {
        let stage = unique_sibling(destination, "cmpct-stage")?;
        let backup = unique_sibling(destination, "cmpct-backup")?;
        fs::create_dir_all(&stage)?;
        let result = self.extract_into(&stage);
        if let Err(error) = result {
            let _ = fs::remove_dir_all(&stage);
            return Err(error);
        }

        let had_destination = destination.exists();
        if had_destination {
            fs::rename(destination, &backup)?;
        }
        if let Err(error) = fs::rename(&stage, destination) {
            if had_destination {
                let _ = fs::rename(&backup, destination);
            }
            let _ = fs::remove_dir_all(&stage);
            return Err(PortableError::Io(error));
        }
        if had_destination {
            let _ = fs::remove_dir_all(&backup);
        }
        Ok(())
    }

    fn extract_into(&self, root: &Path) -> Result<(), PortableError> {
        if let Self::Canonical25(archive) = self {
            return archive.extract_into(root);
        }
        let entries = self.entries();
        for (index, entry) in entries.iter().enumerate() {
            let rel = safe_relpath(&entry.path)?;
            let target = root.join(rel);
            match entry.kind {
                0 => {
                    if let Some(parent) = target.parent() {
                        fs::create_dir_all(parent)?;
                    }
                    let mut file = File::create(&target)?;
                    self.stream_member(index, &mut file)?;
                    file.flush()?;
                }
                1 => fs::create_dir_all(&target)?,
                2 | 3 => {
                    return Err(PortableError::Unsupported(
                        "portable native extraction refuses r24 links rather than weakening link-safety semantics".into(),
                    ));
                }
                _ => {
                    return Err(PortableError::Format(
                        "unknown logical entry kind during extraction".into(),
                    ));
                }
            }
        }
        Ok(())
    }

    pub fn export_zip(&self, destination: &Path) -> Result<(), PortableError> {
        if let Self::Canonical25(archive) = self {
            return archive.export_zip(destination);
        }
        let file = File::create(destination)?;
        let mut writer = zip::ZipWriter::new(file);
        let options = zip::write::SimpleFileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated);
        for (index, entry) in self.entries().iter().enumerate() {
            match entry.kind {
                0 => {
                    writer
                        .start_file(&entry.path, options)
                        .map_err(|error| PortableError::Format(format!("ZIP start_file: {error}")))?;
                    self.stream_member(index, &mut writer)?;
                }
                1 => {
                    let name = if entry.path.ends_with('/') {
                        entry.path.clone()
                    } else {
                        format!("{}/", entry.path)
                    };
                    writer
                        .add_directory(name, options)
                        .map_err(|error| PortableError::Format(format!("ZIP add_directory: {error}")))?;
                }
                2 | 3 => {
                    return Err(PortableError::Unsupported(
                        "ZIP export refuses r24 links until their fidelity policy is explicitly mapped".into(),
                    ));
                }
                _ => return Err(PortableError::Format("unknown logical entry kind".into())),
            }
        }
        writer
            .finish()
            .map_err(|error| PortableError::Format(format!("ZIP finish: {error}")))?;
        Ok(())
    }
}

struct RangeWriter<'a> {
    offset: u64,
    cursor: u64,
    output: &'a mut [u8],
    written: usize,
}

impl<'a> RangeWriter<'a> {
    fn new(offset: u64, output: &'a mut [u8]) -> Self {
        Self {
            offset,
            cursor: 0,
            output,
            written: 0,
        }
    }
}

impl Write for RangeWriter<'_> {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        let start = self.cursor;
        let end = self.cursor.saturating_add(buf.len() as u64);
        let wanted_end = self.offset.saturating_add(self.output.len() as u64);
        if end > self.offset && start < wanted_end && self.written < self.output.len() {
            let source_start = self.offset.saturating_sub(start) as usize;
            let source_end = ((wanted_end.min(end) - start) as usize).min(buf.len());
            if source_start < source_end {
                let take = (source_end - source_start).min(self.output.len() - self.written);
                self.output[self.written..self.written + take]
                    .copy_from_slice(&buf[source_start..source_start + take]);
                self.written += take;
            }
        }
        self.cursor = end;
        Ok(buf.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

fn unique_sibling(destination: &Path, role: &str) -> Result<PathBuf, PortableError> {
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    let name = destination
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| PortableError::Path(destination.display().to_string()))?;
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    Ok(parent.join(format!(
        ".{name}.{role}.{}.{}",
        std::process::id(),
        nanos
    )))
}

#[repr(C)]
#[derive(Debug, Copy, Clone, Eq, PartialEq)]
pub enum PortableStatus {
    Ok = 0,
    Null = -1,
    Io = -2,
    Format = -3,
    Limit = -4,
    Utf8 = -5,
    Range = -6,
    Unsupported = -7,
    Integrity = -8,
    Panic = -127,
}

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct PortableEntryInfo {
    pub kind: u8,
    pub _reserved: [u8; 3],
    pub mode: u32,
    pub size: u64,
    pub mtime_ns: i64,
}

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct PortableMemberStats {
    pub logical_bytes: u64,
    pub decoded_context_bytes: u64,
    pub amplification: f64,
}

fn status(error: &PortableError) -> PortableStatus {
    match error {
        PortableError::Io(_) | PortableError::IoState(_) => PortableStatus::Io,
        PortableError::Limit(_) => PortableStatus::Limit,
        PortableError::Range => PortableStatus::Range,
        PortableError::Unsupported(_) => PortableStatus::Unsupported,
        PortableError::Integrity(_) => PortableStatus::Integrity,
        PortableError::Path(_) | PortableError::Format(_) | PortableError::R24(_) => {
            PortableStatus::Format
        }
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_open(
    path: *const c_char,
    out: *mut *mut PortableArchive,
) -> c_int {
    if path.is_null() || out.is_null() {
        return PortableStatus::Null as c_int;
    }
    unsafe { *out = ptr::null_mut() };
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let path = unsafe { CStr::from_ptr(path) }
            .to_str()
            .map_err(|_| PortableStatus::Utf8)?;
        PortableArchive::open(Path::new(path)).map_err(|error| status(&error))
    }));
    match result {
        Ok(Ok(archive)) => {
            unsafe { *out = Box::into_raw(Box::new(archive)) };
            PortableStatus::Ok as c_int
        }
        Ok(Err(error)) => error as c_int,
        Err(_) => PortableStatus::Panic as c_int,
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_close(handle: *mut PortableArchive) {
    if !handle.is_null() {
        let _ = unsafe { Box::from_raw(handle) };
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_revision(
    handle: *const PortableArchive,
    out: *mut u32,
) -> c_int {
    if handle.is_null() || out.is_null() {
        return PortableStatus::Null as c_int;
    }
    unsafe { *out = (&*handle).revision() };
    PortableStatus::Ok as c_int
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_count(
    handle: *const PortableArchive,
    out: *mut usize,
) -> c_int {
    if handle.is_null() || out.is_null() {
        return PortableStatus::Null as c_int;
    }
    let archive = unsafe { &*handle };
    unsafe { *out = archive.entries().len() };
    PortableStatus::Ok as c_int
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_info(
    handle: *const PortableArchive,
    index: usize,
    out: *mut PortableEntryInfo,
) -> c_int {
    if handle.is_null() || out.is_null() {
        return PortableStatus::Null as c_int;
    }
    let archive = unsafe { &*handle };
    let entries = archive.entries();
    let Some(entry) = entries.get(index) else {
        return PortableStatus::Range as c_int;
    };
    unsafe {
        *out = PortableEntryInfo {
            kind: entry.kind,
            _reserved: [0; 3],
            mode: entry.mode,
            size: entry.size,
            mtime_ns: entry.mtime_ns,
        }
    };
    PortableStatus::Ok as c_int
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_path(
    handle: *const PortableArchive,
    index: usize,
    buffer: *mut u8,
    capacity: usize,
    required: *mut usize,
) -> c_int {
    if handle.is_null() || required.is_null() {
        return PortableStatus::Null as c_int;
    }
    let archive = unsafe { &*handle };
    let entries = archive.entries();
    let Some(entry) = entries.get(index) else {
        return PortableStatus::Range as c_int;
    };
    let bytes = entry.path.as_bytes();
    unsafe { *required = bytes.len() };
    if buffer.is_null() {
        return PortableStatus::Ok as c_int;
    }
    if capacity < bytes.len() {
        return PortableStatus::Range as c_int;
    }
    unsafe { ptr::copy_nonoverlapping(bytes.as_ptr(), buffer, bytes.len()) };
    PortableStatus::Ok as c_int
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_read_range(
    handle: *const PortableArchive,
    index: usize,
    offset: u64,
    buffer: *mut u8,
    capacity: usize,
    written: *mut usize,
) -> c_int {
    if handle.is_null() || written.is_null() || (buffer.is_null() && capacity != 0) {
        return PortableStatus::Null as c_int;
    }
    let archive = unsafe { &*handle };
    if capacity == 0 {
        unsafe { *written = 0 };
        return PortableStatus::Ok as c_int;
    }
    let output = unsafe { std::slice::from_raw_parts_mut(buffer, capacity) };
    match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        archive.read_range(index, offset, output)
    })) {
        Ok(Ok(count)) => {
            unsafe { *written = count };
            PortableStatus::Ok as c_int
        }
        Ok(Err(error)) => status(&error) as c_int,
        Err(_) => PortableStatus::Panic as c_int,
    }
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_read(
    handle: *const PortableArchive,
    index: usize,
    buffer: *mut u8,
    capacity: usize,
    written: *mut usize,
    stats: *mut PortableMemberStats,
) -> c_int {
    if handle.is_null() || written.is_null() {
        return PortableStatus::Null as c_int;
    }
    let archive = unsafe { &*handle };
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| archive.read_member(index)));
    let (bytes, member_stats) = match result {
        Ok(Ok(value)) => value,
        Ok(Err(error)) => return status(&error) as c_int,
        Err(_) => return PortableStatus::Panic as c_int,
    };
    unsafe { *written = bytes.len() };
    if buffer.is_null() || capacity < bytes.len() {
        return PortableStatus::Range as c_int;
    }
    unsafe { ptr::copy_nonoverlapping(bytes.as_ptr(), buffer, bytes.len()) };
    if !stats.is_null() {
        unsafe {
            *stats = PortableMemberStats {
                logical_bytes: member_stats.logical_bytes,
                decoded_context_bytes: member_stats.decoded_context_bytes,
                amplification: member_stats.amplification,
            }
        };
    }
    PortableStatus::Ok as c_int
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_verify(handle: *const PortableArchive) -> c_int {
    if handle.is_null() {
        return PortableStatus::Null as c_int;
    }
    let archive = unsafe { &*handle };
    match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| archive.verify())) {
        Ok(Ok(())) => PortableStatus::Ok as c_int,
        Ok(Err(error)) => status(&error) as c_int,
        Err(_) => PortableStatus::Panic as c_int,
    }
}
