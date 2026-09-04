use cmpct_portable::{PortableArchive, Profile};
use std::ffi::CStr;
use std::os::raw::{c_char, c_int};
use std::path::{Path, PathBuf};

fn c_path(ptr: *const c_char) -> Result<PathBuf, String> {
    if ptr.is_null() {
        return Err("null path".into());
    }
    // SAFETY: callers must provide a valid NUL-terminated C string for the duration of this call.
    let raw = unsafe { CStr::from_ptr(ptr) };
    let text = raw.to_str().map_err(|_| "path is not valid UTF-8")?;
    Ok(PathBuf::from(text))
}

fn open_logs(path: &Path) -> Result<PortableArchive, String> {
    let archive = PortableArchive::open(path).map_err(|error| error.to_string())?;
    if archive.profile() != Profile::LogsInverse || archive.revision() != 25 {
        return Err("archive is not canonical logs-inverse revision 25".into());
    }
    Ok(archive)
}

fn ffi_guard<F>(operation: F) -> c_int
where
    F: FnOnce() -> Result<(), String> + std::panic::UnwindSafe,
{
    match std::panic::catch_unwind(operation) {
        Ok(Ok(())) => 0,
        Ok(Err(_)) => 1,
        Err(_) => 2,
    }
}

/// Strong-verify a canonical logs-inverse archive through the existing portable semantic owner.
///
/// # Safety
/// `archive_path` must point to a valid NUL-terminated UTF-8 C string for the duration of the call.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_logs_verify(archive_path: *const c_char) -> c_int {
    ffi_guard(|| {
        let archive_path = c_path(archive_path)?;
        let archive = open_logs(&archive_path)?;
        archive.verify().map_err(|error| error.to_string())
    })
}

/// Transactionally extract a canonical logs-inverse archive with a caller-supplied output budget.
///
/// # Safety
/// Both path pointers must reference valid NUL-terminated UTF-8 C strings for the duration of the call.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_logs_extract(
    archive_path: *const c_char,
    destination_path: *const c_char,
    maximum_output_bytes: u64,
) -> c_int {
    ffi_guard(|| {
        let archive_path = c_path(archive_path)?;
        let destination_path = c_path(destination_path)?;
        let archive = open_logs(&archive_path)?;
        let logical_regular_bytes = archive
            .entries()
            .iter()
            .filter(|entry| entry.kind == 0)
            .try_fold(0u64, |total, entry| total.checked_add(entry.size))
            .ok_or_else(|| "logical output byte accounting overflow".to_string())?;
        if logical_regular_bytes > maximum_output_bytes {
            return Err("caller output budget exceeded before publication".into());
        }
        archive
            .extract_transactional(&destination_path)
            .map_err(|error| error.to_string())
    })
}
