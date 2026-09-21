//! Caller-owned-buffer Zstd codec boundary for CMPCT packaging.
//!
//! This module deliberately owns no allocation across FFI. It is compiled and exercised independently
//! before being wired into the shipping cdylib so byte identity and error semantics can be falsified
//! without changing the existing read-only platform ABI.

use std::os::raw::c_int;
use std::ptr;

const OK: c_int = 0;
const NULL: c_int = -1;
const FORMAT: c_int = -3;
const RANGE: c_int = -6;
const PANIC: c_int = -127;

fn slices<'a>(
    input: *const u8,
    input_len: usize,
    output: *mut u8,
    output_cap: usize,
) -> Result<(&'a [u8], &'a mut [u8]), c_int> {
    if (input_len > 0 && input.is_null()) || (output_cap > 0 && output.is_null()) {
        return Err(NULL);
    }
    let src = if input_len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(input, input_len) }
    };
    let dst = if output_cap == 0 {
        &mut []
    } else {
        unsafe { std::slice::from_raw_parts_mut(output, output_cap) }
    };
    Ok((src, dst))
}

fn dictionary<'a>(dict: *const u8, dict_len: usize) -> Result<&'a [u8], c_int> {
    if dict_len > 0 && dict.is_null() {
        return Err(NULL);
    }
    Ok(if dict_len == 0 {
        &[]
    } else {
        unsafe { std::slice::from_raw_parts(dict, dict_len) }
    })
}

fn finish(result: Result<usize, c_int>, out_len: *mut usize) -> c_int {
    if out_len.is_null() {
        return NULL;
    }
    unsafe {
        *out_len = 0;
    }
    match result {
        Ok(n) => {
            unsafe {
                *out_len = n;
            }
            OK
        }
        Err(status) => status,
    }
}

#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_compress_bound(input_len: usize) -> usize {
    zstd::zstd_safe::compress_bound(input_len)
}

#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_compress(
    input: *const u8,
    input_len: usize,
    level: c_int,
    output: *mut u8,
    output_cap: usize,
    out_len: *mut usize,
) -> c_int {
    if out_len.is_null() {
        return NULL;
    }
    let result = std::panic::catch_unwind(|| {
        let (src, dst) = slices(input, input_len, output, output_cap)?;
        zstd::zstd_safe::compress(dst, src, level).map_err(|_| RANGE)
    });
    match result {
        Ok(value) => finish(value, out_len),
        Err(_) => {
            *out_len = 0;
            PANIC
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_compress_using_dict(
    input: *const u8,
    input_len: usize,
    dict: *const u8,
    dict_len: usize,
    level: c_int,
    output: *mut u8,
    output_cap: usize,
    out_len: *mut usize,
) -> c_int {
    if out_len.is_null() {
        return NULL;
    }
    let result = std::panic::catch_unwind(|| {
        let (src, dst) = slices(input, input_len, output, output_cap)?;
        let dict = dictionary(dict, dict_len)?;
        let mut cctx = zstd::zstd_safe::CCtx::create();
        cctx.compress_using_dict(dst, src, dict, level)
            .map_err(|_| RANGE)
    });
    match result {
        Ok(value) => finish(value, out_len),
        Err(_) => {
            *out_len = 0;
            PANIC
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_decompress(
    input: *const u8,
    input_len: usize,
    output: *mut u8,
    output_cap: usize,
    out_len: *mut usize,
) -> c_int {
    if out_len.is_null() {
        return NULL;
    }
    let result = std::panic::catch_unwind(|| {
        let (src, dst) = slices(input, input_len, output, output_cap)?;
        zstd::zstd_safe::decompress(dst, src).map_err(|_| FORMAT)
    });
    match result {
        Ok(value) => finish(value, out_len),
        Err(_) => {
            *out_len = 0;
            PANIC
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cmpct_codec_zstd_decompress_using_dict(
    input: *const u8,
    input_len: usize,
    dict: *const u8,
    dict_len: usize,
    output: *mut u8,
    output_cap: usize,
    out_len: *mut usize,
) -> c_int {
    if out_len.is_null() {
        return NULL;
    }
    let result = std::panic::catch_unwind(|| {
        let (src, dst) = slices(input, input_len, output, output_cap)?;
        let dict = dictionary(dict, dict_len)?;
        let mut dctx = zstd::zstd_safe::DCtx::create();
        dctx.decompress_using_dict(dst, src, dict)
            .map_err(|_| FORMAT)
    });
    match result {
        Ok(value) => finish(value, out_len),
        Err(_) => {
            *out_len = 0;
            PANIC
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn null_and_capacity_contract_is_fail_closed() {
        let mut n = 99usize;
        let status = unsafe {
            cmpct_codec_zstd_compress(ptr::null(), 1, 3, ptr::null_mut(), 0, &mut n)
        };
        assert_eq!(status, NULL);
        assert_eq!(n, 0);
    }
}
