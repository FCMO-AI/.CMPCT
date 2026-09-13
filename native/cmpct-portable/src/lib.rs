mod canonical;
#[doc(hidden)]
pub mod compact_control;
mod format;
mod g04;
mod identity;
mod logs;
mod logs_public;
mod manifest;
mod prefix;
#[doc(hidden)]
pub mod zipfactor;

#[cfg(test)]
mod implicit_v4_vector_tests;
#[cfg(test)]
mod logs_preparity_tests;
#[cfg(test)]
mod logs_semantic_tests;

#[doc(hidden)]
pub use crate::canonical::Canonical25Archive;
use crate::compact_control::CompactControlArchive;
use crate::format::safe_relpath;
#[doc(hidden)]
pub use crate::g04::G04Archive;
use crate::identity::{R25Identity, classify};
use crate::logs::LogsInverseArchive;
use crate::logs_public::LogsPublicView;
#[doc(hidden)]
pub use crate::prefix::PrefixArchive;
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
const LOGS_INVERSE_MAGIC: &[u8; 8] = b"C25LG12\0";
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
    LogsInverse,
    CompactControl,
    ResearchG04,
    ResearchPrefixGraph,
}

impl Profile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Revision24 => "r24",
            Self::G04 => "g04-r25",
            Self::PrefixGraph => "prefixgraph-r25",
            Self::LogsInverse => "logs-inverse-r25",
            Self::CompactControl => "r24-compact-control-v1",
            Self::ResearchG04 => "research-g04",
            Self::ResearchPrefixGraph => "research-prefixgraph",
        }
    }

    pub fn revision(self) -> u32 {
        match self {
            Self::Revision24 => 24,
            Self::G04 | Self::PrefixGraph | Self::LogsInverse | Self::CompactControl => 25,
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

pub trait ArchiveReader {
    fn profile(&self) -> Profile;
    fn entries(&self) -> &[PortableEntry];
    fn verify(&self) -> Result<(), PortableError>;
    fn read_member(&self, index: usize) -> Result<Vec<u8>, PortableError>;
    fn extract_all(&self, destination: &Path) -> Result<(), PortableError>;
}

pub struct PortableArchive {
    reader: Box<dyn ArchiveReader>,
}

impl PortableArchive {
    pub fn open(path: impl AsRef<Path>) -> Result<Self, PortableError> {
        let path = path.as_ref();
        let identity = classify(path)?;
        let reader: Box<dyn ArchiveReader> = match identity {
            R25Identity::G04 => Box::new(G04Archive::open(path)?),
            R25Identity::PrefixGraph => Box::new(PrefixArchive::open(path)?),
            R25Identity::LogsInverse => Box::new(LogsInverseArchive::open(path)?),
            R25Identity::CompactControl => Box::new(CompactControlArchive::open(path)?),
            R25Identity::Revision24 => Box::new(R24PortableArchive::open(path)?),
            R25Identity::ResearchG04 => Box::new(G04Archive::open_research(path)?),
            R25Identity::ResearchPrefixGraph => Box::new(PrefixArchive::open_research(path)?),
        };
        Ok(Self { reader })
    }

    pub fn profile(&self) -> Profile {
        self.reader.profile()
    }

    pub fn revision(&self) -> u32 {
        self.profile().revision()
    }

    pub fn entries(&self) -> &[PortableEntry] {
        self.reader.entries()
    }

    pub fn verify(&self) -> Result<(), PortableError> {
        self.reader.verify()
    }

    pub fn read_member(&self, index: usize) -> Result<Vec<u8>, PortableError> {
        self.reader.read_member(index)
    }

    pub fn extract_all(&self, destination: impl AsRef<Path>) -> Result<(), PortableError> {
        self.reader.extract_all(destination.as_ref())
    }
}

struct R24PortableArchive {
    path: PathBuf,
    entries: Vec<PortableEntry>,
}

impl R24PortableArchive {
    fn open(path: &Path) -> Result<Self, PortableError> {
        let archive = R24Archive::open(path)?;
        let entries = archive
            .entries()
            .iter()
            .map(|entry| PortableEntry {
                path: entry.name.clone(),
                size: entry.size,
                kind: 0,
                mode: entry.mode,
                mtime_ns: entry.mtime_ns,
            })
            .collect();
        Ok(Self {
            path: path.to_path_buf(),
            entries,
        })
    }
}

impl ArchiveReader for R24PortableArchive {
    fn profile(&self) -> Profile {
        Profile::Revision24
    }

    fn entries(&self) -> &[PortableEntry] {
        &self.entries
    }

    fn verify(&self) -> Result<(), PortableError> {
        let archive = R24Archive::open(&self.path)?;
        for (index, entry) in self.entries.iter().enumerate() {
            if entry.size > R24_VERIFY_MATERIALIZE_LIMIT {
                return Err(PortableError::Limit(format!(
                    "revision-24 verify would materialize a member larger than {R24_VERIFY_MATERIALIZE_LIMIT} bytes"
                )));
            }
            let _ = archive.read_member(index)?;
        }
        Ok(())
    }

    fn read_member(&self, index: usize) -> Result<Vec<u8>, PortableError> {
        let archive = R24Archive::open(&self.path)?;
        Ok(archive.read_member(index)?)
    }

    fn extract_all(&self, destination: &Path) -> Result<(), PortableError> {
        let archive = R24Archive::open(&self.path)?;
        archive.extract_all(destination)?;
        Ok(())
    }
}

fn prepare_destination(destination: &Path) -> Result<PathBuf, PortableError> {
    if destination.exists() {
        return Err(PortableError::IoState(
            "destination already exists; refusing to overwrite".into(),
        ));
    }
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    let name = destination
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| PortableError::Path("destination basename is not valid UTF-8".into()))?;
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| PortableError::IoState("system clock is before UNIX epoch".into()))?
        .as_nanos();
    let tmp = parent.join(format!(".{name}.cmpct-tmp-{}-{stamp}", std::process::id()));
    if tmp.exists() {
        return Err(PortableError::IoState(
            "temporary extraction directory already exists".into(),
        ));
    }
    fs::create_dir(&tmp)?;
    Ok(tmp)
}

fn commit_destination(tmp: &Path, destination: &Path) -> Result<(), PortableError> {
    fs::rename(tmp, destination)?;
    Ok(())
}

fn remove_temp_destination(tmp: &Path) {
    let _ = fs::remove_dir_all(tmp);
}

#[repr(C)]
pub struct CmpctPortableArchive {
    archive: PortableArchive,
}

#[repr(C)]
pub struct CmpctPortableEntryInfo {
    pub kind: u8,
    pub mode: u32,
    pub mtime_ns: i64,
    pub size: u64,
    pub path_len: usize,
}

fn ffi_archive<'a>(handle: *const CmpctPortableArchive) -> Result<&'a CmpctPortableArchive, c_int> {
    unsafe { handle.as_ref() }.ok_or(-1)
}

fn ffi_out<T>(ptr: *mut T) -> Result<&'static mut T, c_int> {
    unsafe { ptr.as_mut() }.ok_or(-1)
}

/// Opens a CMPCT archive through the shared portable reader.
///
/// # Safety
/// `path` must point to a valid NUL-terminated UTF-8 C string, and `out` must point to writable storage.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_open(
    path: *const c_char,
    out: *mut *mut CmpctPortableArchive,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        let path = unsafe { CStr::from_ptr(path) }
            .to_str()
            .map_err(|_| -2)?;
        let archive = PortableArchive::open(path).map_err(|_| -3)?;
        *ffi_out(out)? = Box::into_raw(Box::new(CmpctPortableArchive { archive }));
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}

/// Frees an archive handle returned by [`cmpct_portable_open`].
///
/// # Safety
/// `handle` must either be null or a pointer previously returned by [`cmpct_portable_open`], exactly once.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_close(handle: *mut CmpctPortableArchive) {
    if !handle.is_null() {
        drop(unsafe { Box::from_raw(handle) });
    }
}

/// Returns the detected archive revision through the C ABI.
///
/// # Safety
/// `handle` must reference a live `CmpctPortableArchive` and `out` must point to writable `u32` storage.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_revision(
    handle: *const CmpctPortableArchive,
    out: *mut u32,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        *ffi_out(out)? = ffi_archive(handle)?.archive.revision();
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}

/// Returns the number of logical entries through the C ABI.
///
/// # Safety
/// `handle` must reference a live `CmpctPortableArchive` and `out` must point to writable `usize` storage.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_count(
    handle: *const CmpctPortableArchive,
    out: *mut usize,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        *ffi_out(out)? = ffi_archive(handle)?.archive.entries().len();
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}

/// Copies fixed metadata for one logical entry through the C ABI.
///
/// # Safety
/// `handle` must reference a live archive and `out` must point to writable [`CmpctPortableEntryInfo`].
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_info(
    handle: *const CmpctPortableArchive,
    index: usize,
    out: *mut CmpctPortableEntryInfo,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        let archive = &ffi_archive(handle)?.archive;
        let entry = archive.entries().get(index).ok_or(-2)?;
        *ffi_out(out)? = CmpctPortableEntryInfo {
            kind: entry.kind,
            mode: entry.mode,
            mtime_ns: entry.mtime_ns,
            size: entry.size,
            path_len: entry.path.as_bytes().len(),
        };
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}

/// Copies one logical entry path into `buffer` and returns the required byte count in `out_len`.
///
/// # Safety
/// `handle` must reference a live archive; `buffer` must be writable for `capacity` bytes when non-null;
/// `out_len` must point to writable `usize` storage.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_entry_path(
    handle: *const CmpctPortableArchive,
    index: usize,
    buffer: *mut u8,
    capacity: usize,
    out_len: *mut usize,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        let archive = &ffi_archive(handle)?.archive;
        let entry = archive.entries().get(index).ok_or(-2)?;
        let bytes = entry.path.as_bytes();
        *ffi_out(out_len)? = bytes.len();
        if bytes.len() > capacity {
            return Err(-3);
        }
        if !bytes.is_empty() {
            if buffer.is_null() {
                return Err(-4);
            }
            unsafe { ptr::copy_nonoverlapping(bytes.as_ptr(), buffer, bytes.len()) };
        }
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}

/// Reads one logical member into a caller buffer and returns the required byte count in `out_len`.
///
/// # Safety
/// `handle` must reference a live archive; `buffer` must be writable for `capacity` bytes when non-null;
/// `out_len` must point to writable `usize` storage.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_read_member(
    handle: *const CmpctPortableArchive,
    index: usize,
    buffer: *mut u8,
    capacity: usize,
    out_len: *mut usize,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        let archive = &ffi_archive(handle)?.archive;
        let bytes = archive.read_member(index).map_err(|_| -2)?;
        *ffi_out(out_len)? = bytes.len();
        if bytes.len() > capacity {
            return Err(-3);
        }
        if !bytes.is_empty() {
            if buffer.is_null() {
                return Err(-4);
            }
            unsafe { ptr::copy_nonoverlapping(bytes.as_ptr(), buffer, bytes.len()) };
        }
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}

/// Performs strong archive verification through the shared portable reader.
///
/// # Safety
/// `handle` must reference a live archive.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_verify(handle: *const CmpctPortableArchive) -> c_int {
    ffi_archive(handle)
        .and_then(|archive| archive.archive.verify().map_err(|_| -2))
        .map_or_else(|code| code, |_| 0)
}

/// Extracts all logical members transactionally through the shared portable reader.
///
/// # Safety
/// `handle` must reference a live archive and `destination` must point to a valid NUL-terminated UTF-8 path.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_portable_extract_all(
    handle: *const CmpctPortableArchive,
    destination: *const c_char,
) -> c_int {
    let result = (|| -> Result<(), c_int> {
        let path = unsafe { CStr::from_ptr(destination) }
            .to_str()
            .map_err(|_| -2)?;
        ffi_archive(handle)?
            .archive
            .extract_all(Path::new(path))
            .map_err(|_| -3)?;
        Ok(())
    })();
    result.map_or_else(|code| code, |_| 0)
}
