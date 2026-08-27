//! Research-only in-process verifier for exact CMP25Z3 bytes.
//!
//! The implementation is deliberately included from the existing preparity binary so this ABI cannot drift
//! into a second ZIP-factor grammar. It does not enter the public portable dispatch and earns no release credit.

use std::ffi::CStr;
use std::os::raw::c_char;

// The included source is also a standalone preparity binary. Its binary-only entry point/profile constants are
// intentionally unused when the exact same verifier is compiled as this research-only library wrapper.
#[allow(dead_code)]
mod preparity {
    include!(concat!(env!("OUT_DIR"), "/zipfactor_v3_preparity.rs"));

    pub(super) fn verify_path(path: &std::path::Path) -> Result<(), String> {
        verify(path)
    }

    pub(super) fn verify_bytes(raw: &[u8]) -> Result<(), String> {
        verify_slice(raw)
    }
}

/// Verify an exact CMP25Z3 archive in-process by path.
///
/// Returns 0 on success, 1 on verification failure, and 2 for an invalid ABI/path argument. Panics are caught
/// and fail closed. Archive open/read/decompression/identity/locality work remains inside the call.
///
/// # Safety
///
/// `path` must be either null or point to a valid, NUL-terminated C string for the duration of this call. The
/// pointed-to bytes must remain readable and unmodified until the function returns. A null, non-UTF-8, or
/// otherwise invalid path is rejected with status 2; the function never takes ownership of the pointer.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_zipfactor_v3_verify_path(path: *const c_char) -> i32 {
    if path.is_null() {
        return 2;
    }
    let path = match unsafe { CStr::from_ptr(path) }.to_str() {
        Ok(value) => value,
        Err(_) => return 2,
    };
    match std::panic::catch_unwind(|| preparity::verify_path(std::path::Path::new(path))) {
        Ok(Ok(())) => 0,
        Ok(Err(_)) => 1,
        Err(_) => 1,
    }
}

/// Verify exact CMP25Z3 bytes already resident in the caller process.
///
/// Returns 0 on success, 1 on verification failure, and 2 for an invalid ABI argument. This entry point executes
/// the exact same parser, SHA-256 checks, ZIP reconstruction and locality policy as the path ABI, but removes
/// transient scratch-file publication/open from callers that already hold the reconstructed V3 bytes.
///
/// # Safety
///
/// For `len > 0`, `data` must point to `len` readable bytes that remain valid and unmodified for the duration of
/// the call. `data` may be null only when `len == 0`; an empty input is then rejected by the verifier as malformed.
/// The function never takes ownership of the buffer.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_zipfactor_v3_verify_bytes(data: *const u8, len: usize) -> i32 {
    if data.is_null() && len != 0 {
        return 2;
    }
    let raw: &[u8] = if len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(data, len) }
    };
    match std::panic::catch_unwind(|| preparity::verify_bytes(raw)) {
        Ok(Ok(())) => 0,
        Ok(Err(_)) => 1,
        Err(_) => 1,
    }
}
