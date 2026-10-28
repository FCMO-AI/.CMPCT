#![forbid(unsafe_code)]

use preflate_container::{
    PreflateContainerConfig, PreflateContainerProcessor, ProcessBuffer, RecreateContainerProcessor,
};
use std::env;
use std::fs::{self, File};
use std::io::{self, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

const MAX_INPUT_CHUNK: usize = 8 * 1024 * 1024;
const MAX_PLAINTEXT_WORK: usize = 64 * 1024 * 1024;

fn config() -> PreflateContainerConfig {
    PreflateContainerConfig {
        // Footnote: the research archive declares a 96 MiB decoder-memory ceiling. Preflate's own
        // potentially expanded plaintext workspace is therefore capped at 64 MiB, leaving explicit
        // headroom for the 8 MiB reconstructed object, correction data and bounded I/O buffers. A
        // compression bomb that needs more workspace is an unsupported transform, not an excuse to
        // allocate past the archive contract.
        max_chunk_size: MAX_INPUT_CHUNK,
        // Footnote: upstream defines this one aggregate work counter as u64 while the per-buffer
        // ceilings are usize. The explicit widening preserves the exact same 64 MiB byte value; it is
        // a type-boundary conversion, not a larger allowance.
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
        Self {
            inner,
            limit,
            written: 0,
        }
    }
}

impl<W: Write> Write for LimitedWriter<W> {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        // Footnote: `ProcessBuffer::copy_to_end_size` bounds how much compressed input is fed into one
        // call; it does *not* cap total reconstructed output. Enforce that independent dimension at the
        // writer itself so a malicious correction stream cannot create an arbitrarily large file and
        // rely on Python to reject its length afterwards.
        let remaining = self.limit.saturating_sub(self.written);
        if buf.len() > remaining {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "preflate reconstruction exceeds output ceiling",
            ));
        }
        let n = self.inner.write(buf)?;
        self.written = self
            .written
            .checked_add(n)
            .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "output byte counter overflow"))?;
        Ok(n)
    }

    fn flush(&mut self) -> io::Result<()> {
        self.inner.flush()
    }
}

fn recreate(
    input: &Path,
    output: &Path,
    cfg: &PreflateContainerConfig,
    output_limit: usize,
    exact_size: Option<usize>,
) -> Result<(), String> {
    if output_limit > MAX_INPUT_CHUNK {
        return Err(format!(
            "requested reconstruction ceiling exceeds {} bytes",
            MAX_INPUT_CHUNK
        ));
    }
    let result = (|| {
        let mut reader = BufReader::new(File::open(input).map_err(|e| format!("open input: {e}"))?);
        let raw_writer = BufWriter::new(File::create(output).map_err(|e| format!("create output: {e}"))?);
        let mut writer = LimitedWriter::new(raw_writer, output_limit);
        let mut decoder = RecreateContainerProcessor::new(cfg.chunk_plain_text_limit);
        decoder
            .copy_to_end_size(&mut reader, &mut writer, MAX_INPUT_CHUNK)
            .map_err(|e| format!("preflate recreate: {e:?}"))?;
        writer.flush().map_err(|e| format!("flush output: {e}"))?;
        if let Some(expected) = exact_size {
            if writer.written != expected {
                return Err(format!(
                    "preflate reconstructed {} bytes, expected {}",
                    writer.written, expected
                ));
            }
        }
        Ok(())
    })();
    if result.is_err() {
        // A failed bounded reconstruction is never a useful partial artifact. Removing it also keeps a
        // caller from accidentally consuming a truncated output after correctly observing an error.
        let _ = fs::remove_file(output);
    }
    result
}

fn equal_files(a: &Path, b: &Path) -> Result<bool, String> {
    let ma = fs::metadata(a).map_err(|e| format!("stat source: {e}"))?;
    let mb = fs::metadata(b).map_err(|e| format!("stat restored: {e}"))?;
    if ma.len() != mb.len() {
        return Ok(false);
    }
    let mut ra = BufReader::new(File::open(a).map_err(|e| format!("open source: {e}"))?);
    let mut rb = BufReader::new(File::open(b).map_err(|e| format!("open restored: {e}"))?);
    let mut ba = [0u8; 256 * 1024];
    let mut bb = [0u8; 256 * 1024];
    loop {
        let na = ra.read(&mut ba).map_err(|e| format!("read source: {e}"))?;
        let nb = rb.read(&mut bb).map_err(|e| format!("read restored: {e}"))?;
        if na != nb || ba[..na] != bb[..nb] {
            return Ok(false);
        }
        if na == 0 {
            return Ok(true);
        }
    }
}

fn pack(input: &Path, output: &Path) -> Result<(), String> {
    let cfg = config();
    let input_len = fs::metadata(input).map_err(|e| format!("stat input: {e}"))?.len();
    if input_len > MAX_INPUT_CHUNK as u64 {
        return Err(format!("input exceeds {} byte bridge ceiling", MAX_INPUT_CHUNK));
    }
    let input_len = input_len as usize;
    let mut reader = BufReader::new(File::open(input).map_err(|e| format!("open input: {e}"))?);
    let mut writer = BufWriter::new(File::create(output).map_err(|e| format!("create output: {e}"))?);
    let mut encoder = PreflateContainerProcessor::new(&cfg, 12, false);
    encoder
        .copy_to_end_size(&mut reader, &mut writer, MAX_INPUT_CHUNK)
        .map_err(|e| format!("preflate pack: {e:?}"))?;
    writer.flush().map_err(|e| format!("flush output: {e}"))?;

    // Footnote: builder+reader agreement is not accepted on trust. Every bridge payload is immediately
    // reconstructed through the opposite upstream path and compared in bounded buffers before it can
    // enter an EntropyGraph-II archive. The verification writer is capped to the exact original size,
    // so this correctness check doubles as a decompression-bomb check for every emitted transform.
    let mut verify = output.as_os_str().to_owned();
    verify.push(".verify.tmp");
    let verify_path = PathBuf::from(verify);
    let result = (|| {
        recreate(output, &verify_path, &cfg, input_len, Some(input_len))?;
        if !equal_files(input, &verify_path)? {
            return Err("preflate bridge failed byte-exact verification".to_string());
        }
        Ok(())
    })();
    let _ = fs::remove_file(&verify_path);
    if result.is_err() {
        let _ = fs::remove_file(output);
    }
    result
}

fn usage() -> ! {
    eprintln!("usage: cmpct-preflate-bridge <pack|unpack> <input> <output>");
    std::process::exit(2)
}

fn run() -> Result<(), String> {
    let mut args = env::args_os().skip(1);
    let Some(command) = args.next() else { usage() };
    let Some(input) = args.next() else { usage() };
    let Some(output) = args.next() else { usage() };
    if args.next().is_some() {
        usage();
    }
    let input = PathBuf::from(input);
    let output = PathBuf::from(output);
    match command.to_string_lossy().as_ref() {
        "pack" => pack(&input, &output),
        // Research archives already authenticate the expected logical size and reject anything above
        // 8 MiB. The bridge independently caps raw output to that same ceiling before Python sees it;
        // the caller then checks the exact expected length and SHA-256.
        "unpack" => recreate(&input, &output, &config(), MAX_INPUT_CHUNK, None),
        _ => usage(),
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("cmpct-preflate-bridge: {error}");
        std::process::exit(1);
    }
}
