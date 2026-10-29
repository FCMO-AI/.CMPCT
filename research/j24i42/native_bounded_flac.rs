//! J24I42: *research-only* bounded Claxon view into original physical CMPCT file.
//! This is not an archive verifier: authoritative r24 index/wire audit runs independently,
//! and the existing native product owner (#765/#759) remains unchanged.
use claxon::FlacReader;
use cmpct_core::Archive;
use rmpv::Value;
use sha2::{Digest, Sha256};
use std::cell::Cell;
use std::env;
use std::fs::{self, File};
use std::io::{self, BufReader, Cursor, Read, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::rc::Rc;
use std::time::Instant;

/// Bounded virtual file: logical offset zero is the first encoded FLAC byte.
/// Even a decoder seeking past EOF cannot access CMPCT's adjacent index/footer.
struct SpanReader {
    source: File,
    base: u64,
    len: u64,
    pos: u64,
    counted: Rc<Cell<u64>>,
}
impl SpanReader {
    fn new(source: File, base: u64, len: u64, counted: Rc<Cell<u64>>) -> io::Result<Self> {
        let end = base.checked_add(len).ok_or_else(|| io::Error::new(
            io::ErrorKind::InvalidInput, "physical range overflow"
        ))?;
        if end > source.metadata()?.len() {
            return Err(io::Error::new(io::ErrorKind::UnexpectedEof, "span beyond physical file"));
        }
        Ok(Self { source, base, len, pos: 0, counted })
    }
}
impl Read for SpanReader {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        if self.pos == self.len || buf.is_empty() {
            return Ok(0);
        }
        let remain = self.len - self.pos;
        let want = usize::try_from(remain).unwrap_or(usize::MAX).min(buf.len());
        self.source.seek(SeekFrom::Start(self.base + self.pos))?;
        let got = self.source.read(&mut buf[..want])?;
        self.pos += got as u64;
        self.counted.set(self.counted.get().saturating_add(got as u64));
        Ok(got)
    }
}
impl Seek for SpanReader {
    fn seek(&mut self, from: SeekFrom) -> io::Result<u64> {
        let desired = match from {
            SeekFrom::Start(n) => i128::from(n),
            SeekFrom::End(n) => i128::from(self.len) + i128::from(n),
            SeekFrom::Current(n) => i128::from(self.pos) + i128::from(n),
        };
        if desired < 0 || desired > i128::from(self.len) {
            return Err(io::Error::new(io::ErrorKind::InvalidInput, "seek outside FLAC span"));
        }
        self.pos = desired as u64;
        Ok(self.pos)
    }
}

fn binary(v: &Value) -> Result<&[u8], String> {
    match v { Value::Binary(b) => Ok(b), _ => Err("expected binary PCM metadata".into()) }
}
fn number(v: &Value) -> Result<u32, String> {
    v.as_u64().and_then(|n| u32::try_from(n).ok())
        .ok_or_else(|| "invalid u32 FLAC property".into())
}
fn feed(data: &[u8], sha: &mut Sha256, crc: &mut crc32fast::Hasher, n: &mut u64) -> Result<(), String> {
    sha.update(data);
    crc.update(data);
    *n = n.checked_add(data.len() as u64).ok_or("byte count overflow")?;
    Ok(())
}
fn verify_range(
    path: &Path, meta_path: &Path, off: u64, encoded_len: u64,
    logical_size: u64, expected_sha: &str, expected_crc: u32
) -> Result<u64, String> {
    let raw_meta = fs::read(meta_path).map_err(|e| e.to_string())?;
    let mut cursor = Cursor::new(raw_meta.as_slice());
    let parsed = rmpv::decode::read_value(&mut cursor).map_err(|e| e.to_string())?;
    if cursor.position() != raw_meta.len() as u64 { return Err("trailing codec metadata".into()); }
    let fields = parsed.as_array().ok_or("codec metadata not array")?;
    if fields.len() != 5 { return Err("codec metadata not five elements".into()); }
    let prefix = binary(&fields[0])?;
    let suffix = binary(&fields[1])?;
    let channels = number(&fields[2])?;
    let rate = number(&fields[3])?;
    let bits = number(&fields[4])?;
    if channels == 0 || rate == 0 || !matches!(bits, 16 | 32) {
        return Err("unsupported stream properties".into());
    }
    let fixed = (prefix.len() as u64).checked_add(suffix.len() as u64)
        .ok_or("metadata length overflow")?;
    let expected_pcm = logical_size.checked_sub(fixed).ok_or("metadata > logical size")?;
    let sample_width = u64::from(bits / 8);
    if expected_pcm % sample_width != 0 { return Err("PCM size misaligned".into()); }
    let source = File::open(path).map_err(|e| e.to_string())?;
    let counter = Rc::new(Cell::new(0));
    let limited = SpanReader::new(source, off, encoded_len, counter.clone())
        .map_err(|e| e.to_string())?;
    let mut flac = FlacReader::new(BufReader::new(limited)).map_err(|e| e.to_string())?;
    let info = flac.streaminfo();
    if info.channels != channels || info.sample_rate != rate || info.bits_per_sample != bits {
        return Err("STREAMINFO mismatch".into());
    }
    let mut sha = Sha256::new();
    let mut crc = crc32fast::Hasher::new();
    let mut logical = 0u64;
    feed(prefix, &mut sha, &mut crc, &mut logical)?;
    let mut chunk = Vec::with_capacity(64 * 1024);
    let mut pcm = 0u64;
    for sample in flac.samples() {
        let sample = sample.map_err(|e| format!("FLAC frame rejected: {e}"))?;
        if bits == 16 {
            let narrow = i16::try_from(sample).map_err(|_| "16-bit sample out of range")?;
            chunk.extend_from_slice(&narrow.to_le_bytes());
        } else {
            chunk.extend_from_slice(&sample.to_le_bytes());
        }
        pcm = pcm.checked_add(sample_width).ok_or("PCM overflow")?;
        if pcm > expected_pcm { return Err("excess FLAC samples".into()); }
        if chunk.len() >= 64 * 1024 {
            feed(&chunk, &mut sha, &mut crc, &mut logical)?;
            chunk.clear();
        }
    }
    feed(&chunk, &mut sha, &mut crc, &mut logical)?;
    if pcm != expected_pcm { return Err("truncated FLAC samples".into()); }
    feed(suffix, &mut sha, &mut crc, &mut logical)?;
    if logical != logical_size { return Err("logical length mismatch".into()); }
    let hash: [u8; 32] = sha.finalize().into();
    let result_sha = hash.iter().map(|b| format!("{b:02x}")).collect::<String>();
    if result_sha != expected_sha { return Err("SHA256 mismatch".into()); }
    if crc.finalize() != expected_crc { return Err("CRC32 mismatch".into()); }
    Ok(counter.get())
}
fn test_bounds(path: &Path, start: u64, len: u64) -> Result<(), String> {
    let count = Rc::new(Cell::new(0));
    let mut span = SpanReader::new(File::open(path).map_err(|e| e.to_string())?,
                                   start, len, count).map_err(|e| e.to_string())?;
    if span.seek(SeekFrom::End(1)).is_ok() { return Err("seek crossed upper bound".into()); }
    if span.seek(SeekFrom::Current(-1)).is_ok() { return Err("seek crossed lower bound".into()); }
    span.seek(SeekFrom::End(0)).map_err(|e| e.to_string())?;
    let mut byte = [0u8;1];
    if span.read(&mut byte).map_err(|e| e.to_string())? != 0 {
        return Err("reader crossed EOF into CMPCT index".into());
    }
    span.seek(SeekFrom::Start(0)).map_err(|e| e.to_string())?;
    let mut magic = [0u8;4];
    span.read_exact(&mut magic).map_err(|e| e.to_string())?;
    if &magic != b"fLaC" { return Err("range does not begin with FLAC".into()); }
    span.seek(SeekFrom::End(-3)).map_err(|e| e.to_string())?;
    let mut tail = [0u8;3];
    span.read_exact(&mut tail).map_err(|e| e.to_string())?;
    if span.read(&mut byte).map_err(|e| e.to_string())? != 0 {
        return Err("read escaped span after tail".into());
    }
    Ok(())
}
fn proc_num(path: &str, prefix: &str) -> u64 {
    fs::read_to_string(path).expect("Linux procfs").lines()
        .find_map(|line| line.strip_prefix(prefix))
        .expect("procfs metric").split_whitespace().next()
        .expect("number").parse::<u64>().expect("u64")
}
fn main() {
    let args = env::args().collect::<Vec<_>>();
    assert_eq!(args.len(), 6, "PROBE ORIGINAL_ARCHIVE META MANIFEST SIZE_MIB native|bounded|truncated|badmagic");
    let mib: u64 = args[4].parse().expect("size");
    assert!([8,32].contains(&mib));
    let mode = args[5].as_str();
    assert!(matches!(mode, "native" | "bounded" | "truncated" | "badmagic"));
    let archive = PathBuf::from(&args[1]);
    let meta = PathBuf::from(&args[2]);
    let record: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&args[3]).expect("range manifest")).expect("JSON");
    assert_eq!(record["schema"].as_str(), Some("j24i42-audited-original-container-ranges-v1"));
    let row = &record["records"][mib.to_string().as_str()];
    let off = row["encoded_offset"].as_u64().expect("encoded offset");
    let encoded = row["encoded_bytes"].as_u64().expect("encoded bytes");
    let logical = row["logical_bytes"].as_u64().expect("logical bytes");
    let sha = row["logical_sha256"].as_str().expect("SHA");
    let crc = row["logical_crc32"].as_u64().expect("CRC") as u32;
    assert_eq!(logical, mib * 1024 * 1024 + 44);
    assert_eq!(row["archive_path"].as_str(), archive.file_name().and_then(|v|v.to_str()));
    assert_eq!(row["metadata_path"].as_str(), meta.file_name().and_then(|v|v.to_str()));
    let original = Archive::open(&archive).expect("authentic archive opens");
    assert_eq!(original.entries().len(), 1);
    assert_eq!(original.entries()[0].size, logical);
    test_bounds(&archive, off, encoded).expect("span seek/EOF controls");
    if mode == "truncated" || mode == "badmagic" {
        let physical = if mode == "badmagic" {
            archive.parent().expect("directory").join(
                row["corrupt_path"].as_str().expect("corrupt path"))
        } else { archive.clone() };
        let cap = if mode == "truncated" { encoded - 64 } else { encoded };
        match verify_range(&physical, &meta, off, cap, logical, sha, crc) {
            Ok(_) => { eprintln!("J24I42_UNSAFE_ACCEPT mode={mode}"); std::process::exit(2); }
            Err(e) => { println!("J24I42_REJECTED_INVALID mode={mode} reason={e}"); return; }
        }
    }
    for iter in 0..4 {
        let before = proc_num("/proc/self/io","rchar:");
        let start = Instant::now();
        let read_bytes = if mode == "native" {
            assert_eq!(original.verify_complete().expect("native verify"), 1);
            0
        } else {
            verify_range(&archive,&meta,off,encoded,logical,sha,crc)
                .expect("in-archive bounded verifier")
        };
        let wall_ns = start.elapsed().as_nanos();
        let rchar = proc_num("/proc/self/io","rchar:").saturating_sub(before);
        let hwm = proc_num("/proc/self/status","VmHWM:");
        println!("J24I42 size={mib} mode={mode} iter={iter} wall_ns={wall_ns} rchar={rchar} vmhwm_kib={hwm} bounded_read={read_bytes}");
    }
}
