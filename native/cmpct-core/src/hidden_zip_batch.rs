//! Bounded creator-side batch validation for hidden ZIP Deflate members.
//!
//! This is deliberately not reader grammar. Python owns ZIP parsing, ownership fixed points,
//! deterministic commit, and the final live-source rebind. This boundary only validates already-bounded
//! RFC-1951 slices and returns decoded bytes plus logical SHA-256 in caller-owned buffers.

use crate::CmpctStatus;
use flate2::read::DeflateDecoder;
use sha2::{Digest, Sha256};
use std::io::Read;
use std::os::raw::c_int;

const MAX_BATCH_STREAMS: usize = 4096;
const MAX_BATCH_INPUT: usize = 64 * 1024 * 1024;
const MAX_BATCH_OUTPUT: usize = 256 * 1024 * 1024;

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct HiddenZipDeflateJob {
    pub stream_offset: usize,
    pub stream_len: usize,
    pub output_offset: usize,
    pub output_len: usize,
    pub crc32: u32,
}

fn status(value: CmpctStatus) -> c_int { value as c_int }

/// Validate a batch of exact RFC-1951 member streams and materialize their logical bytes.
///
/// Every range is checked before decode. A stream must terminate exactly at its declared logical
/// length and match ZIP's CRC-32. SHA-256 is written as 32 bytes per job. No allocation crosses FFI.
///
/// # Safety
/// `input`, `jobs`, `output`, and `hashes` must be valid for their declared lengths when non-empty.
/// Job output ranges must be disjoint; callers should assign a packed output layout.
#[no_mangle]
pub unsafe extern "C" fn cmpct_hidden_zip_validate_deflate_batch(
    input: *const u8,
    input_len: usize,
    jobs: *const HiddenZipDeflateJob,
    job_count: usize,
    output: *mut u8,
    output_cap: usize,
    hashes: *mut u8,
    hashes_cap: usize,
) -> c_int {
    if input_len > MAX_BATCH_INPUT || output_cap > MAX_BATCH_OUTPUT || job_count > MAX_BATCH_STREAMS {
        return status(CmpctStatus::Limit);
    }
    if (input_len > 0 && input.is_null()) || (job_count > 0 && jobs.is_null())
        || (output_cap > 0 && output.is_null()) || (job_count > 0 && hashes.is_null()) {
        return status(CmpctStatus::Null);
    }
    if hashes_cap < job_count.saturating_mul(32) { return status(CmpctStatus::Range); }
    let result = std::panic::catch_unwind(|| {
        let src = if input_len == 0 { &[] } else { std::slice::from_raw_parts(input, input_len) };
        let specs = if job_count == 0 { &[] } else { std::slice::from_raw_parts(jobs, job_count) };
        let dst = if output_cap == 0 { &mut [] } else { std::slice::from_raw_parts_mut(output, output_cap) };
        let digest_out = if hashes_cap == 0 { &mut [] } else { std::slice::from_raw_parts_mut(hashes, hashes_cap) };
        let mut ranges = Vec::with_capacity(specs.len());
        for spec in specs {
            let send = spec.stream_offset.checked_add(spec.stream_len).ok_or(CmpctStatus::Range)?;
            let oend = spec.output_offset.checked_add(spec.output_len).ok_or(CmpctStatus::Range)?;
            if send > src.len() || oend > dst.len() { return Err(CmpctStatus::Range); }
            ranges.push((spec.output_offset, oend));
        }
        ranges.sort_unstable();
        if ranges.windows(2).any(|w| w[0].1 > w[1].0) { return Err(CmpctStatus::Range); }
        for (i, spec) in specs.iter().enumerate() {
            let stream = &src[spec.stream_offset..spec.stream_offset + spec.stream_len];
            let mut decoder = DeflateDecoder::new(stream);
            let mut logical = Vec::with_capacity(spec.output_len.min(1024 * 1024));
            decoder.take((spec.output_len as u64).saturating_add(1)).read_to_end(&mut logical).map_err(|_| CmpctStatus::Format)?;
            if logical.len() != spec.output_len { return Err(CmpctStatus::Format); }
            let mut crc = crc32fast::Hasher::new(); crc.update(&logical);
            if crc.finalize() != spec.crc32 { return Err(CmpctStatus::Format); }
            dst[spec.output_offset..spec.output_offset + spec.output_len].copy_from_slice(&logical);
            let hash = Sha256::digest(&logical);
            digest_out[i * 32..(i + 1) * 32].copy_from_slice(&hash);
        }
        Ok(())
    });
    match result {
        Ok(Ok(())) => status(CmpctStatus::Ok),
        Ok(Err(value)) => status(value),
        Err(_) => status(CmpctStatus::Panic),
    }
}
