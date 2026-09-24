use flate2::read::DeflateDecoder;
use sha2::{Digest, Sha256};
use std::io::Read;
use std::os::raw::c_int;

const MAX_BATCH_STREAMS: usize = 4096;
const MAX_BATCH_INPUT: usize = 64 * 1024 * 1024;
const MAX_BATCH_OUTPUT: usize = 256 * 1024 * 1024;
const OK: c_int = 0; const NULL: c_int = -1; const FORMAT: c_int = -3;
const LIMIT: c_int = -4; const RANGE: c_int = -6; const PANIC: c_int = -127;

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct HiddenZipDeflateJob {
    pub stream_offset: usize,
    pub stream_len: usize,
    pub output_offset: usize,
    pub output_len: usize,
    pub crc32: u32,
}

/// Creator-side experiment: validate bounded RFC-1951 slices and materialize logical bytes/hashes.
/// Python still owns ZIP parsing, ownership, deterministic commit, and the final live-source rebind.
/// No allocation crosses FFI; all source/output ranges are charged to caller-owned buffers.
#[no_mangle]
pub unsafe extern "C" fn cmpct_hidden_zip_validate_deflate_batch(
    input: *const u8, input_len: usize,
    jobs: *const HiddenZipDeflateJob, job_count: usize,
    output: *mut u8, output_cap: usize,
    hashes: *mut u8, hashes_cap: usize,
) -> c_int {
    if input_len > MAX_BATCH_INPUT || output_cap > MAX_BATCH_OUTPUT || job_count > MAX_BATCH_STREAMS { return LIMIT; }
    if (input_len > 0 && input.is_null()) || (job_count > 0 && jobs.is_null())
        || (output_cap > 0 && output.is_null()) || (job_count > 0 && hashes.is_null()) { return NULL; }
    if hashes_cap < job_count.saturating_mul(32) { return RANGE; }
    let result = std::panic::catch_unwind(|| {
        let src = if input_len == 0 { &[] } else { std::slice::from_raw_parts(input, input_len) };
        let specs = if job_count == 0 { &[] } else { std::slice::from_raw_parts(jobs, job_count) };
        let dst = if output_cap == 0 { &mut [] } else { std::slice::from_raw_parts_mut(output, output_cap) };
        let digest_out = if hashes_cap == 0 { &mut [] } else { std::slice::from_raw_parts_mut(hashes, hashes_cap) };
        let mut ranges = Vec::with_capacity(specs.len());
        for spec in specs {
            let send = spec.stream_offset.checked_add(spec.stream_len).ok_or(RANGE)?;
            let oend = spec.output_offset.checked_add(spec.output_len).ok_or(RANGE)?;
            if send > src.len() || oend > dst.len() { return Err(RANGE); }
            ranges.push((spec.output_offset, oend));
        }
        ranges.sort_unstable();
        if ranges.windows(2).any(|w| w[0].1 > w[1].0) { return Err(RANGE); }
        for (i, spec) in specs.iter().enumerate() {
            let stream = &src[spec.stream_offset..spec.stream_offset + spec.stream_len];
            let decoder = DeflateDecoder::new(stream);
            let mut logical = Vec::with_capacity(spec.output_len.min(1024 * 1024));
            decoder.take((spec.output_len as u64).saturating_add(1)).read_to_end(&mut logical).map_err(|_| FORMAT)?;
            if logical.len() != spec.output_len { return Err(FORMAT); }
            let mut crc = crc32fast::Hasher::new(); crc.update(&logical);
            if crc.finalize() != spec.crc32 { return Err(FORMAT); }
            dst[spec.output_offset..spec.output_offset + spec.output_len].copy_from_slice(&logical);
            digest_out[i*32..(i+1)*32].copy_from_slice(&Sha256::digest(&logical));
        }
        Ok(())
    });
    match result { Ok(Ok(())) => OK, Ok(Err(code)) => code, Err(_) => PANIC }
}

#[cfg(test)]
mod tests {
    use super::*;
    use flate2::{write::DeflateEncoder, Compression};
    use std::io::Write;
    #[test]
    fn batch_validates_crc_hash_and_bounds() {
        let raw=b"shared logical member".repeat(1024); let mut enc=DeflateEncoder::new(Vec::new(),Compression::new(6)); enc.write_all(&raw).unwrap(); let stream=enc.finish().unwrap();
        let mut crc=crc32fast::Hasher::new(); crc.update(&raw); let job=HiddenZipDeflateJob{stream_offset:0,stream_len:stream.len(),output_offset:0,output_len:raw.len(),crc32:crc.finalize()};
        let mut out=vec![0;raw.len()]; let mut hashes=[0u8;32];
        let rc=unsafe{cmpct_hidden_zip_validate_deflate_batch(stream.as_ptr(),stream.len(),&job,1,out.as_mut_ptr(),out.len(),hashes.as_mut_ptr(),hashes.len())};
        assert_eq!(rc,OK); assert_eq!(out,raw); assert_eq!(&hashes[..],Sha256::digest(&raw).as_slice());
        let bad=HiddenZipDeflateJob{crc32:job.crc32^1,..job};
        let rc=unsafe{cmpct_hidden_zip_validate_deflate_batch(stream.as_ptr(),stream.len(),&bad,1,out.as_mut_ptr(),out.len(),hashes.as_mut_ptr(),hashes.len())}; assert_eq!(rc,FORMAT);
    }
}
