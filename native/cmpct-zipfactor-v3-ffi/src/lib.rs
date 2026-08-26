//! Research-only in-process verifier for exact CMP25Z3 bytes.
//!
//! The implementation is deliberately included from the existing preparity binary so this ABI cannot drift
//! into a second ZIP-factor grammar. It does not enter the public portable dispatch and earns no release credit.

use std::ffi::CStr;
use std::os::raw::c_char;

mod preparity {
    include!("../../cmpct-portable/src/bin/cmpct-zipfactor-v3-preparity.rs");

    pub(super) fn verify_path(path: &std::path::Path) -> Result<(), String> {
        verify(path)
    }
}

/// Verify an exact CMP25Z3 archive in-process.
///
/// Returns 0 on success, 1 on verification failure, and 2 for an invalid ABI/path argument. Panics are caught
/// and fail closed. Archive open/read/decompression/identity/locality work remains inside the call.
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
