#![forbid(unsafe_code)]

//! One-process research front door for amortizing preflate orchestration across a bounded file cohort.
//!
//! The existing `cmpct-preflate-bridge` intentionally accepts one object per process. That is a clean security
//! boundary for ordinary research, but process startup dominates v0.30's tiny nested-ZIP creation benchmark.
//! This companion binary keeps the exact same upstream transform, limits and pack->recreate byte verification,
//! while processing an explicitly supplied finite list in one process. It does not define a CMPCT archive format.

use preflate_container::{
    PreflateContainerConfig, PreflateContainerProcessor, ProcessBuffer, RecreateContainerProcessor,
};
use std::env;
use std::fs::{self, File};
use std::io::{self, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

const MAX_INPUT_CHUNK: usize = 8 * 1024 * 1024;
const MAX_PLAINTEXT_WORK: usize = 64 * 1024 * 1024;
const MAX_BATCH_FILES: usize = 256;

fn config() -> PreflateContainerConfig {
    PreflateContainerConfig {
        max_chunk_size: MAX_INPUT_CHUNK,
        total_plain_text_limit: MAX_PLAINTEXT_WORK as u64,
        chunk_plain_text_limit: MAX_PLAINTEXT_WORK,
        validate_compression: false,
        max_chain_length: 4096,
        ..PreflateContainerConfig::default()
    }
}

struct LimitedWriter<W: Write> {
    inner: W,
    limit: usize,
    written: usize,
}

impl<W: Write> LimitedWriter<W> {
    fn new(inner: W, limit: usize) -> Self {
        Self { inner, limit, written: 0 }
    }
}

impl<W: Write> Write for LimitedWriter<W> {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        let remaining = self.limit.saturating_sub(self.written);
        if buf.len() > remaining {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "preflate reconstruction exceeds output ceiling"));
        }
        let n = self.inner.write(buf)?;
        self.written = self.written.checked_add(n)
            .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "output byte counter overflow"))?;
        Ok(n)
    }
    fn flush(&mut self) -> io::Result<()> { self.inner.flush() }
}

fn recreate(input: &Path, output: &Path, cfg: &PreflateContainerConfig, exact_size: usize) -> Result<(), String> {
    if exact_size > MAX_INPUT_CHUNK {
        return Err(format!("requested reconstruction exceeds {MAX_INPUT_CHUNK} byte ceiling"));
    }
    let result = (|| {
        let mut reader = BufReader::new(File::open(input).map_err(|e| format!("open packed: {e}"))?);
        let raw_writer = BufWriter::new(File::create(output).map_err(|e| format!("create verify: {e}"))?);
        let mut writer = LimitedWriter::new(raw_writer, exact_size);
        let mut decoder = RecreateContainerProcessor::new(cfg.chunk_plain_text_limit);
        decoder.copy_to_end_size(&mut reader, &mut writer, MAX_INPUT_CHUNK)
            .map_err(|e| format!("preflate recreate: {e:?}"))?;
        writer.flush().map_err(|e| format!("flush verify: {e}"))?;
        if writer.written != exact_size {
            return Err(format!("reconstructed {} bytes, expected {exact_size}", writer.written));
        }
        Ok(())
    })();
    if result.is_err() { let _ = fs::remove_file(output); }
    result
}

fn equal_files(a: &Path, b: &Path) -> Result<bool, String> {
    if fs::metadata(a).map_err(|e| format!("stat source: {e}"))?.len()
        != fs::metadata(b).map_err(|e| format!("stat verify: {e}"))?.len() {
        return Ok(false);
    }
    let mut ra = BufReader::new(File::open(a).map_err(|e| format!("open source: {e}"))?);
    let mut rb = BufReader::new(File::open(b).map_err(|e| format!("open verify: {e}"))?);
    let mut ba = [0u8; 64 * 1024];
    let mut bb = [0u8; 64 * 1024];
    loop {
        let na = ra.read(&mut ba).map_err(|e| format!("read source: {e}"))?;
        let nb = rb.read(&mut bb).map_err(|e| format!("read verify: {e}"))?;
        if na != nb || ba[..na] != bb[..nb] { return Ok(false); }
        if na == 0 { return Ok(true); }
    }
}

fn pack_verified(input: &Path, output: &Path, cfg: &PreflateContainerConfig) -> Result<(), String> {
    let input_len = fs::metadata(input).map_err(|e| format!("stat input: {e}"))?.len();
    if input_len > MAX_INPUT_CHUNK as u64 {
        return Err(format!("input exceeds {MAX_INPUT_CHUNK} byte bridge ceiling"));
    }
    let input_len = input_len as usize;
    let mut reader = BufReader::new(File::open(input).map_err(|e| format!("open input: {e}"))?);
    let mut writer = BufWriter::new(File::create(output).map_err(|e| format!("create packed: {e}"))?);
    let mut encoder = PreflateContainerProcessor::new(cfg, 12, false);
    encoder.copy_to_end_size(&mut reader, &mut writer, MAX_INPUT_CHUNK)
        .map_err(|e| format!("preflate pack: {e:?}"))?;
    writer.flush().map_err(|e| format!("flush packed: {e}"))?;

    let verify = output.with_extension("verify.tmp");
    let result = (|| {
        recreate(output, &verify, cfg, input_len)?;
        if !equal_files(input, &verify)? {
            return Err("preflate batch item failed byte-exact verification".to_string());
        }
        Ok(())
    })();
    let _ = fs::remove_file(&verify);
    if result.is_err() { let _ = fs::remove_file(output); }
    result
}

fn usage() -> ! {
    eprintln!("usage: cmpct-preflate-batch <output-dir> <input> [input ...]");
    std::process::exit(2)
}

fn run() -> Result<(), String> {
    let mut args = env::args_os().skip(1);
    let Some(output_dir) = args.next() else { usage() };
    let inputs: Vec<PathBuf> = args.map(PathBuf::from).collect();
    if inputs.is_empty() || inputs.len() > MAX_BATCH_FILES {
        return Err(format!("batch requires 1..={MAX_BATCH_FILES} input files"));
    }
    let output_dir = PathBuf::from(output_dir);
    fs::create_dir_all(&output_dir).map_err(|e| format!("create output directory: {e}"))?;
    let cfg = config();
    for (index, input) in inputs.iter().enumerate() {
        let output = output_dir.join(format!("{index:04}.pflt"));
        pack_verified(input, &output, &cfg)?;
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("cmpct-preflate-batch: {error}");
        std::process::exit(1);
    }
}
