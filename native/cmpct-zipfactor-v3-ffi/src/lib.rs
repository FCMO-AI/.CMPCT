//! Research-only in-process verifier for exact CMP25Z3 and recovery-safe CMP25Z4 bytes.
//!
//! The V3 implementation is deliberately included from the existing preparity binary so this ABI cannot drift
//! into a second ZIP-factor grammar. The V4 entry point adds only the recovery envelope parser and delegates every
//! reconstructed V3 semantic check to that exact owner. It does not enter public portable dispatch and earns no
//! release credit until the product/native/Android authority stack explicitly promotes it.

use sha2::{Digest, Sha256};
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

const REC_MAGIC: &[u8; 8] = b"CMP25Z4\0";
const V3_MAGIC: &[u8; 8] = b"CMP25Z3\0";
const TAIL_MAGIC: &[u8; 8] = b"ZFRTAIL1";
const FOOTER_SIZE: usize = 8 + 4 + 32;
const MAX_CONTROL: usize = 1024 * 1024;

fn recovery_u32_at(raw: &[u8], at: usize, label: &str) -> Result<u32, String> {
    let bytes: [u8; 4] = raw
        .get(at..at + 4)
        .ok_or_else(|| format!("truncated {label}"))?
        .try_into()
        .map_err(|_| format!("invalid {label}"))?;
    Ok(u32::from_le_bytes(bytes))
}

fn recovery_tail_layout(raw: &[u8]) -> Result<(usize, usize, [u8; 32]), String> {
    if raw.len() < 8 + FOOTER_SIZE || raw.get(..8) != Some(REC_MAGIC) {
        return Err("not a ZIP-factor recovery archive".into());
    }
    let footer = raw.len() - FOOTER_SIZE;
    if raw.get(footer..footer + 8) != Some(TAIL_MAGIC) {
        return Err("invalid ZIP-factor recovery footer magic".into());
    }
    let control_len = usize::try_from(recovery_u32_at(raw, footer + 8, "tail control length")?)
        .map_err(|_| "tail control length overflow")?;
    if control_len == 0 || control_len > MAX_CONTROL {
        return Err("tail control length exceeds policy".into());
    }
    let control_start = footer
        .checked_sub(control_len)
        .ok_or("tail control offset underflow")?;
    if control_start <= 8 + control_len {
        return Err("tail control overlaps primary/body".into());
    }
    let expected: [u8; 32] = raw
        .get(footer + 12..footer + 44)
        .ok_or("truncated tail control hash")?
        .try_into()
        .map_err(|_| "invalid tail control hash")?;
    Ok((control_len, control_start, expected))
}

fn recovery_v3_candidate(
    raw: &[u8],
    control: &[u8],
    body_start: usize,
    body_end: usize,
) -> Result<Vec<u8>, String> {
    if body_start > body_end || body_end > raw.len() {
        return Err("recovery body bounds".into());
    }
    let capacity = 8usize
        .checked_add(control.len())
        .and_then(|v| v.checked_add(body_end - body_start))
        .ok_or("recovery candidate size overflow")?;
    let mut out = Vec::with_capacity(capacity);
    out.extend_from_slice(V3_MAGIC);
    out.extend_from_slice(control);
    out.extend_from_slice(&raw[body_start..body_end]);
    Ok(out)
}

fn verify_recovery_bytes(raw: &[u8]) -> Result<(), String> {
    let (control_len, tail_start, tail_sha) = recovery_tail_layout(raw)?;
    let primary_start = 8usize;
    let body_start = primary_start
        .checked_add(control_len)
        .ok_or("primary control offset overflow")?;
    if body_start > tail_start {
        return Err("primary control overlaps payload".into());
    }

    let primary = raw
        .get(primary_start..body_start)
        .ok_or("truncated primary control")?;
    let primary_candidate = recovery_v3_candidate(raw, primary, body_start, tail_start)?;
    if preparity::verify_bytes(&primary_candidate).is_ok() {
        return Ok(());
    }

    let tail = raw
        .get(tail_start..tail_start + control_len)
        .ok_or("truncated tail control")?;
    let observed: [u8; 32] = Sha256::digest(tail).into();
    if observed != tail_sha {
        return Err("primary invalid and tail control authentication failed".into());
    }
    let tail_candidate = recovery_v3_candidate(raw, tail, body_start, tail_start)?;
    preparity::verify_bytes(&tail_candidate)
        .map_err(|e| format!("both recovery controls invalid: {e}"))
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

/// Verify an exact recovery-safe CMP25Z4 envelope already resident in the caller process.
///
/// The recovery wrapper is parsed natively. A valid primary control is preferred; if it fails the exact V3 semantic
/// owner, the authenticated tail control is reconstructed and tried. Both-invalid input fails closed. Returns 0 on
/// success, 1 on verification failure, and 2 for an invalid ABI argument.
///
/// # Safety
///
/// For `len > 0`, `data` must point to `len` readable bytes that remain valid and unmodified for the duration of
/// the call. `data` may be null only when `len == 0`. The function never takes ownership of the buffer.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cmpct_zipfactor_v4_recovery_verify_bytes(
    data: *const u8,
    len: usize,
) -> i32 {
    if data.is_null() && len != 0 {
        return 2;
    }
    let raw: &[u8] = if len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(data, len) }
    };
    match std::panic::catch_unwind(|| verify_recovery_bytes(raw)) {
        Ok(Ok(())) => 0,
        Ok(Err(_)) => 1,
        Err(_) => 1,
    }
}