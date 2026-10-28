use crc32fast::Hasher as Crc32;
use sha2::{Digest, Sha256};
use std::slice;

const CHUNK: usize = 64 * 1024;

/// Compute the full CRC32 and SHA-256 identities of one decoded pack through one FFI call.
///
/// # Safety
/// `data` must reference `len` readable bytes for the duration of the call. `crc_out` must reference one
/// writable u32 and `sha_out` must reference at least 32 writable bytes. Zero length accepts a null data pointer.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_logs_auth_fused(
    data: *const u8,
    len: usize,
    crc_out: *mut u32,
    sha_out: *mut u8,
) -> i32 {
    if crc_out.is_null() || sha_out.is_null() || (len != 0 && data.is_null()) {
        return 1;
    }
    let bytes: &[u8] = if len == 0 {
        &[]
    } else {
        // SAFETY: required by the FFI contract above.
        unsafe { slice::from_raw_parts(data, len) }
    };
    let mut crc = Crc32::new();
    let mut sha = Sha256::new();
    for chunk in bytes.chunks(CHUNK) {
        crc.update(chunk);
        sha.update(chunk);
    }
    let crc = crc.finalize();
    let digest = sha.finalize();
    // SAFETY: writable outputs are required by the FFI contract above.
    unsafe {
        *crc_out = crc;
        std::ptr::copy_nonoverlapping(digest.as_ptr(), sha_out, 32);
    }
    0
}
