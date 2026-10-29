//! J24I39 research-only: file-backed Claxon PCM digest oracle vs real native archive verify.
//! A standalone split FLAC input is NOT an archive verifier and cannot earn product credit.
use claxon::FlacReader;
use cmpct_core::Archive;
use rmpv::Value;
use sha2::{Digest, Sha256};
use std::env;
use std::fs::{self, File};
use std::io::{BufReader, Cursor};
use std::path::Path;
use std::time::Instant;

fn proc_num(path: &str, prefix: &str) -> u64 {
    fs::read_to_string(path)
        .expect("Linux procfs")
        .lines()
        .find_map(|line| line.strip_prefix(prefix))
        .expect("procfs metric")
        .split_whitespace()
        .next()
        .expect("numeric")
        .parse::<u64>()
        .expect("u64")
}
fn binary(value: &Value) -> &[u8] {
    match value {
        Value::Binary(data) => data,
        _ => panic!("expected msgpack binary prefix/suffix"),
    }
}
fn field(value: &Value) -> u64 {
    value.as_u64().expect("unsigned metadata integer")
}
fn feed(data: &[u8], sha: &mut Sha256, crc: &mut crc32fast::Hasher, count: &mut u64) {
    sha.update(data);
    crc.update(data);
    *count = count.checked_add(data.len() as u64).expect("byte count overflow");
}

/// Only a research-level reconstruction oracle: physical archive verification belongs to Archive.
/// The FLAC encoded stream is File-backed and the decoded PCM passes through a 64KiB buffer.
/// Trailing/multiple FLAC frame acceptance remains explicitly UNPROVEN.
fn verify_file_backed(
    flac_path: &Path,
    meta_path: &Path,
    expected_size: u64,
    expected_sha: &str,
    expected_crc: u32,
) {
    let meta = fs::read(meta_path).expect("exact audited codec metadata");
    let mut cursor = Cursor::new(meta.as_slice());
    let parsed = rmpv::decode::read_value(&mut cursor).expect("msgpack metadata");
    assert_eq!(cursor.position(), meta.len() as u64, "no trailing metadata");
    let fields = parsed.as_array().expect("codec2 metadata array");
    assert_eq!(fields.len(), 5);
    let prefix = binary(&fields[0]);
    let suffix = binary(&fields[1]);
    let channels = field(&fields[2]) as u32;
    let rate = field(&fields[3]) as u32;
    let bits = field(&fields[4]) as u32;
    assert!(channels > 0 && rate > 0 && matches!(bits, 16 | 32));
    let fixed = (prefix.len() as u64).checked_add(suffix.len() as u64).expect("fixed bytes");
    assert!(fixed <= expected_size);
    let expected_pcm = expected_size - fixed;
    assert_eq!(expected_pcm % (bits / 8) as u64, 0);

    let file = File::open(flac_path).expect("audited FLAC payload");
    assert!(file.metadata().expect("stat").len() <= 256 * 1024 * 1024);
    let mut flac = FlacReader::new(BufReader::new(file)).expect("FLAC stream start");
    let stream = flac.streaminfo();
    assert_eq!(stream.channels, channels);
    assert_eq!(stream.sample_rate, rate);
    assert_eq!(stream.bits_per_sample, bits);

    let mut sha = Sha256::new();
    let mut crc = crc32fast::Hasher::new();
    let mut logical_bytes = 0u64;
    feed(prefix, &mut sha, &mut crc, &mut logical_bytes);

    let mut chunk = Vec::with_capacity(64 * 1024);
    let mut pcm_bytes = 0u64;
    for sample in flac.samples() {
        let sample = sample.expect("valid complete FLAC frames");
        if bits == 16 {
            let value = i16::try_from(sample).expect("16-bit sample");
            chunk.extend_from_slice(&value.to_le_bytes());
        } else {
            chunk.extend_from_slice(&sample.to_le_bytes());
        }
        pcm_bytes += (bits / 8) as u64;
        assert!(pcm_bytes <= expected_pcm, "more samples than declared");
        if chunk.len() >= 64 * 1024 {
            feed(&chunk, &mut sha, &mut crc, &mut logical_bytes);
            chunk.clear();
        }
    }
    feed(&chunk, &mut sha, &mut crc, &mut logical_bytes);
    assert_eq!(pcm_bytes, expected_pcm, "missing FLAC PCM samples");
    feed(suffix, &mut sha, &mut crc, &mut logical_bytes);
    assert_eq!(logical_bytes, expected_size);
    let hash: [u8; 32] = sha.finalize().into();
    let got = hash.iter().map(|b| format!("{b:02x}")).collect::<String>();
    assert_eq!(got, expected_sha, "exact reconstructed WAV SHA");
    assert_eq!(crc.finalize(), expected_crc, "complete reconstructed WAV CRC");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 7, "PROBE ARCHIVE META FLAC MANIFEST SIZE_MIB native|stream");
    let mib: u64 = args[5].parse().expect("size MiB");
    assert!([8, 32].contains(&mib));
    assert!(args[6] == "native" || args[6] == "stream");
    let record_json: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&args[4]).expect("manifest")).expect("manifest json");
    assert_eq!(record_json["schema"].as_str(), Some("j24i39-independent-split-v1"));
    let record = &record_json["records"][mib.to_string().as_str()];
    let size = mib * 1024 * 1024 + 44;
    assert_eq!(record["logical_bytes"].as_u64(), Some(size));
    let expected_sha = record["payload_sha256"].as_str().expect("SHA");
    let expected_crc = record["crc32"].as_u64().expect("CRC") as u32;
    let archive = Archive::open(Path::new(&args[1])).expect("original archive opens");
    assert_eq!(archive.entries().len(), 1);
    assert_eq!(archive.entries()[0].size, size);

    for i in 0..4 {
        let before = proc_num("/proc/self/io", "rchar:");
        let timer = Instant::now();
        if args[6] == "native" {
            assert_eq!(archive.verify_complete().expect("native verify"), 1);
        } else {
            verify_file_backed(
                Path::new(&args[3]), Path::new(&args[2]), size, expected_sha, expected_crc
            );
        }
        let elapsed = timer.elapsed().as_nanos();
        let rchar = proc_num("/proc/self/io", "rchar:").saturating_sub(before);
        let vmhwm = proc_num("/proc/self/status", "VmHWM:");
        println!("J24I39 size={mib} mode={} iter={i} wall_ns={elapsed} rchar={rchar} vmhwm_kib={vmhwm}", args[6]);
    }
}
