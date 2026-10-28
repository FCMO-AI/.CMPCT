//! Reusable dictionary decoder boundary for package-owned Zstd.
//!
//! The handle owns one `DCtx` whose dictionary is copied into Zstd once at creation. Python may keep
//! the opaque pointer per archive and serialize access with its existing reader lock. Allocation and
//! destruction both happen inside this cdylib; no Rust allocation crosses the FFI boundary.

use crate::CmpctStatus;
use std::ffi::c_void;
use std::os::raw::c_int;

struct DictDecoder {
    dctx: zstd::zstd_safe::DCtx<'static>,
}

fn status(value: CmpctStatus) -> c_int {
    value as c_int
}

fn bytes<'a>(ptr: *const u8, len: usize) -> Result<&'a [u8], c_int> {
    if len > 0 && ptr.is_null() {
        return Err(status(CmpctStatus::Null));
    }
    Ok(if len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(ptr, len) }
    })
}

/// Create one reusable decoder and copy `dict` into its Zstd context.
///
/// # Safety
/// `dict` must be readable for `dict_len` bytes when non-zero and `out_handle` must be writable for
/// one pointer. The returned opaque handle must be released exactly once with
/// `cmpct_codec_zstd_dict_decoder_free` and must not be used concurrently without caller locking.
#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_dict_decoder_create(
    dict: *const u8,
    dict_len: usize,
    out_handle: *mut *mut c_void,
) -> c_int {
    if out_handle.is_null() {
        return status(CmpctStatus::Null);
    }
    *out_handle = std::ptr::null_mut();
    let result = std::panic::catch_unwind(|| {
        let dictionary = bytes(dict, dict_len)?;
        let mut dctx = zstd::zstd_safe::DCtx::create();
        dctx.load_dictionary(dictionary)
            .map_err(|_| status(CmpctStatus::Format))?;
        Ok::<_, c_int>(Box::new(DictDecoder { dctx }))
    });
    match result {
        Ok(Ok(decoder)) => {
            *out_handle = Box::into_raw(decoder).cast::<c_void>();
            status(CmpctStatus::Ok)
        }
        Ok(Err(value)) => value,
        Err(_) => status(CmpctStatus::Panic),
    }
}

/// Decode one frame using the dictionary loaded when the handle was created.
///
/// # Safety
/// `handle` must be a live handle returned by this module and exclusively owned for this call. `input`
/// and `output` obey the same readable/writable rules as the stateless codec ABI; `out_len` must be
/// writable for one `usize`.
#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_dict_decoder_decompress(
    handle: *mut c_void,
    input: *const u8,
    input_len: usize,
    output: *mut u8,
    output_cap: usize,
    out_len: *mut usize,
) -> c_int {
    if handle.is_null() || out_len.is_null() || (output_cap > 0 && output.is_null()) {
        if !out_len.is_null() {
            *out_len = 0;
        }
        return status(CmpctStatus::Null);
    }
    *out_len = 0;
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let src = bytes(input, input_len)?;
        let dst = if output_cap == 0 {
            &mut []
        } else {
            std::slice::from_raw_parts_mut(output, output_cap)
        };
        let decoder = &mut *handle.cast::<DictDecoder>();
        decoder
            .dctx
            .decompress(dst, src)
            .map_err(|_| status(CmpctStatus::Format))
    }));
    match result {
        Ok(Ok(n)) => {
            *out_len = n;
            status(CmpctStatus::Ok)
        }
        Ok(Err(value)) => value,
        Err(_) => status(CmpctStatus::Panic),
    }
}

/// Release one reusable dictionary decoder.
///
/// # Safety
/// A non-null handle must be a live pointer returned by `cmpct_codec_zstd_dict_decoder_create` and
/// must not be used again after this call.
#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_dict_decoder_free(handle: *mut c_void) -> c_int {
    if handle.is_null() {
        return status(CmpctStatus::Ok);
    }
    let result = std::panic::catch_unwind(|| drop(Box::from_raw(handle.cast::<DictDecoder>())));
    match result {
        Ok(()) => status(CmpctStatus::Ok),
        Err(_) => status(CmpctStatus::Panic),
    }
}
