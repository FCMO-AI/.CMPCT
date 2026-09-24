use flate2::bufread::DeflateDecoder;
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::io::Read;
use std::os::raw::c_int;

const MAX_BATCH_STREAMS: usize = 4096;
const MAX_BATCH_INPUT: usize = 64 * 1024 * 1024;
const MAX_BATCH_OUTPUT: usize = 256 * 1024 * 1024;
const OK: c_int = 0; const NULL: c_int = -1; const FORMAT: c_int = -3;
const LIMIT: c_int = -4; const RANGE: c_int = -6; const PANIC: c_int = -127;

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct HiddenZipDeflateJob { pub stream_offset:usize,pub stream_len:usize,pub output_offset:usize,pub output_len:usize,pub crc32:u32 }

fn decode_exact(stream:&[u8], logical:&mut [u8], expected_crc:u32)->Result<[u8;32],c_int>{
    let mut decoder=DeflateDecoder::new(stream);decoder.read_exact(logical).map_err(|_|FORMAT)?;let mut extra=[0u8;1];
    if decoder.read(&mut extra).map_err(|_|FORMAT)?!=0||decoder.total_in()as usize!=stream.len(){return Err(FORMAT)}
    let mut crc=crc32fast::Hasher::new();crc.update(logical);if crc.finalize()!=expected_crc{return Err(FORMAT)}
    Ok(Sha256::digest(logical).into())
}

/// Creator-side experiment: validate bounded RFC-1951 slices and materialize logical bytes/hashes.
/// Python still owns ZIP parsing, ownership, deterministic commit, and the final live-source rebind.
/// No allocation crosses FFI; all source/output ranges are charged to caller-owned buffers.
#[no_mangle]
pub unsafe extern "C" fn cmpct_hidden_zip_validate_deflate_batch(input:*const u8,input_len:usize,jobs:*const HiddenZipDeflateJob,job_count:usize,output:*mut u8,output_cap:usize,hashes:*mut u8,hashes_cap:usize)->c_int {
    if input_len>MAX_BATCH_INPUT||output_cap>MAX_BATCH_OUTPUT||job_count>MAX_BATCH_STREAMS{return LIMIT}
    if(input_len>0&&input.is_null())||(job_count>0&&jobs.is_null())||(output_cap>0&&output.is_null())||(job_count>0&&hashes.is_null()){return NULL}
    if hashes_cap<job_count.saturating_mul(32){return RANGE}
    let result=std::panic::catch_unwind(||{
        let src=if input_len==0{&[]}else{std::slice::from_raw_parts(input,input_len)};
        let specs=if job_count==0{&[]}else{std::slice::from_raw_parts(jobs,job_count)};
        let dst=if output_cap==0{&mut []}else{std::slice::from_raw_parts_mut(output,output_cap)};
        let digest_out=if hashes_cap==0{&mut []}else{std::slice::from_raw_parts_mut(hashes,hashes_cap)};
        let mut ranges=Vec::with_capacity(specs.len());
        for spec in specs{let send=spec.stream_offset.checked_add(spec.stream_len).ok_or(RANGE)?;let oend=spec.output_offset.checked_add(spec.output_len).ok_or(RANGE)?;if send>src.len()||oend>dst.len(){return Err(RANGE)}ranges.push((spec.output_offset,oend));}
        ranges.sort_unstable();if ranges.windows(2).any(|w|w[0].1>w[1].0){return Err(RANGE)}
        for(i,spec)in specs.iter().enumerate(){
            let stream=&src[spec.stream_offset..spec.stream_offset+spec.stream_len];let logical=&mut dst[spec.output_offset..spec.output_offset+spec.output_len];
            let digest=decode_exact(stream,logical,spec.crc32)?;digest_out[i*32..(i+1)*32].copy_from_slice(&digest);
        }Ok(())
    });match result{Ok(Ok(()))=>OK,Ok(Err(code))=>code,Err(_)=>PANIC}
}

/// Research-only identity-first boundary. Every occurrence is fully decoded/CRC-validated/hashed once, but only
/// one exact representative of each logical identity is copied into the caller-visible material buffer. Per-job
/// offsets point at that representative. SHA collisions are not trusted: an equal digest must also match length
/// and bytes or the batch fails closed. This changes ownership/materialization work, not archive semantics.
#[no_mangle]
pub unsafe extern "C" fn cmpct_hidden_zip_validate_dedup_deflate_batch(input:*const u8,input_len:usize,jobs:*const HiddenZipDeflateJob,job_count:usize,output:*mut u8,output_cap:usize,hashes:*mut u8,hashes_cap:usize,owner_offsets:*mut usize,owner_offsets_cap:usize,used_output:*mut usize)->c_int {
    if input_len>MAX_BATCH_INPUT||output_cap>MAX_BATCH_OUTPUT||job_count>MAX_BATCH_STREAMS{return LIMIT}
    if(input_len>0&&input.is_null())||(job_count>0&&jobs.is_null())||(output_cap>0&&output.is_null())||(job_count>0&&hashes.is_null())||(job_count>0&&owner_offsets.is_null())||used_output.is_null(){return NULL}
    if hashes_cap<job_count.saturating_mul(32)||owner_offsets_cap<job_count{return RANGE}
    let result=std::panic::catch_unwind(||{
        let src=if input_len==0{&[]}else{std::slice::from_raw_parts(input,input_len)};
        let specs=if job_count==0{&[]}else{std::slice::from_raw_parts(jobs,job_count)};
        let dst=if output_cap==0{&mut []}else{std::slice::from_raw_parts_mut(output,output_cap)};
        let digest_out=if hashes_cap==0{&mut []}else{std::slice::from_raw_parts_mut(hashes,hashes_cap)};
        let offsets=if owner_offsets_cap==0{&mut []}else{std::slice::from_raw_parts_mut(owner_offsets,owner_offsets_cap)};
        let mut owners:HashMap<[u8;32],(usize,usize)>=HashMap::with_capacity(specs.len());let mut cursor=0usize;let mut scratch=Vec::<u8>::new();
        for(i,spec)in specs.iter().enumerate(){
            let send=spec.stream_offset.checked_add(spec.stream_len).ok_or(RANGE)?;if send>src.len(){return Err(RANGE)}
            scratch.resize(spec.output_len,0);let stream=&src[spec.stream_offset..send];let digest=decode_exact(stream,&mut scratch,spec.crc32)?;digest_out[i*32..(i+1)*32].copy_from_slice(&digest);
            if let Some(&(off,len))=owners.get(&digest){
                if len!=spec.output_len||off.checked_add(len).ok_or(RANGE)?>cursor||dst[off..off+len]!=scratch[..]{return Err(FORMAT)}
                offsets[i]=off;
            }else{
                let end=cursor.checked_add(spec.output_len).ok_or(RANGE)?;if end>dst.len(){return Err(RANGE)}
                dst[cursor..end].copy_from_slice(&scratch);owners.insert(digest,(cursor,spec.output_len));offsets[i]=cursor;cursor=end;
            }
        }
        *used_output=cursor;Ok(())
    });match result{Ok(Ok(()))=>OK,Ok(Err(code))=>code,Err(_)=>PANIC}
}

#[cfg(test)]mod tests{use super::*;use flate2::{write::DeflateEncoder,Compression};use std::io::Write;
fn enc(raw:&[u8])->Vec<u8>{let mut e=DeflateEncoder::new(Vec::new(),Compression::new(6));e.write_all(raw).unwrap();e.finish().unwrap()}
fn crc(raw:&[u8])->u32{let mut c=crc32fast::Hasher::new();c.update(raw);c.finalize()}
#[test]fn batch_validates_crc_hash_and_exact_stream_bounds(){let raw=b"shared logical member".repeat(1024);let stream=enc(&raw);let job=HiddenZipDeflateJob{stream_offset:0,stream_len:stream.len(),output_offset:0,output_len:raw.len(),crc32:crc(&raw)};let mut out=vec![0;raw.len()];let mut hashes=[0u8;32];let rc=unsafe{cmpct_hidden_zip_validate_deflate_batch(stream.as_ptr(),stream.len(),&job,1,out.as_mut_ptr(),out.len(),hashes.as_mut_ptr(),hashes.len())};assert_eq!(rc,OK);assert_eq!(out,raw);assert_eq!(&hashes[..],Sha256::digest(&raw).as_slice());let bad=HiddenZipDeflateJob{crc32:job.crc32^1,..job};let rc=unsafe{cmpct_hidden_zip_validate_deflate_batch(stream.as_ptr(),stream.len(),&bad,1,out.as_mut_ptr(),out.len(),hashes.as_mut_ptr(),hashes.len())};assert_eq!(rc,FORMAT);let mut tailed=stream.clone();tailed.extend_from_slice(b"junk");let tailed_job=HiddenZipDeflateJob{stream_len:tailed.len(),..job};let rc=unsafe{cmpct_hidden_zip_validate_deflate_batch(tailed.as_ptr(),tailed.len(),&tailed_job,1,out.as_mut_ptr(),out.len(),hashes.as_mut_ptr(),hashes.len())};assert_eq!(rc,FORMAT);let short=HiddenZipDeflateJob{output_len:job.output_len+1,..job};let mut too_long=vec![0;short.output_len];let rc=unsafe{cmpct_hidden_zip_validate_deflate_batch(stream.as_ptr(),stream.len(),&short,1,too_long.as_mut_ptr(),too_long.len(),hashes.as_mut_ptr(),hashes.len())};assert_eq!(rc,FORMAT);}
#[test]fn identity_first_materializer_exports_one_exact_owner(){let raw=b"same logical bytes".repeat(4096);let a=enc(&raw);let mut e=DeflateEncoder::new(Vec::new(),Compression::new(9));e.write_all(&raw).unwrap();let b=e.finish().unwrap();let mut src=a.clone();let boff=src.len();src.extend_from_slice(&b);let jobs=[HiddenZipDeflateJob{stream_offset:0,stream_len:a.len(),output_offset:0,output_len:raw.len(),crc32:crc(&raw)},HiddenZipDeflateJob{stream_offset:boff,stream_len:b.len(),output_offset:raw.len(),output_len:raw.len(),crc32:crc(&raw)}];let mut out=vec![0;raw.len()*2];let mut hashes=[0u8;64];let mut offs=[usize::MAX;2];let mut used=0usize;let rc=unsafe{cmpct_hidden_zip_validate_dedup_deflate_batch(src.as_ptr(),src.len(),jobs.as_ptr(),jobs.len(),out.as_mut_ptr(),out.len(),hashes.as_mut_ptr(),hashes.len(),offs.as_mut_ptr(),offs.len(),&mut used)};assert_eq!(rc,OK);assert_eq!(used,raw.len());assert_eq!(offs,[0,0]);assert_eq!(&out[..used],raw.as_slice());assert_eq!(&hashes[..32],&hashes[32..]);}}
