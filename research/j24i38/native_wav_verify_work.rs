//! J24I38: research-only authentic Builder WAV-FLAC verify-work court.
//! Copy into unmodified cmpct-core src/bin at CI runtime. The one-shot control
//! is *not* RSS-equivalent and cannot be promoted as a bounded verifier.
use cmpct_core::Archive;
use sha2::{Digest, Sha256};
use std::{env, fs, path::Path, time::Instant};

fn proc_num(file: &str, prefix: &str) -> u64 {
    fs::read_to_string(file)
        .expect("Linux procfs available")
        .lines()
        .find_map(|line| line.strip_prefix(prefix))
        .expect("proc key")
        .split_whitespace()
        .next()
        .expect("value")
        .parse::<u64>()
        .expect("numeric value")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 5, "usage: PROBE ARCHIVE verify|oneshot SIZE_MIB MANIFEST");
    let mib: u64 = args[3].parse().expect("size");
    assert!([8, 32].contains(&mib));
    let size = mib * 1024 * 1024 + 44; // Unmodified canonical Python wave writer RIFF header
    assert!(args[2] == "verify" || args[2] == "oneshot");
    let manifest: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&args[4]).expect("manifest")).expect("json");
    let key = mib.to_string();
    let record = &manifest["records"][key.as_str()];
    let digest_expected = record["payload_sha256"].as_str().expect("SHA");
    let crc_expected = record["crc32"].as_u64().expect("CRC");
    assert_eq!(record["logical_bytes"].as_u64(), Some(size));
    let archive = Archive::open(Path::new(&args[1])).expect("r24 open");
    assert_eq!(archive.entries().len(), 1);
    assert_eq!(archive.entries()[0].kind, 0);
    assert_eq!(archive.entries()[0].size, size);
    for iteration in 0..4 {
        let before = proc_num("/proc/self/io", "rchar:");
        let start = Instant::now();
        if args[2] == "verify" {
            assert_eq!(archive.verify_complete().expect("strong verify"), 1);
        } else {
            // Optimistic control: full-size allocation, with SHA+CRC as well as
            // read_range's own compressed member SHA. This deliberately exports RSS.
            let mut data = vec![0u8; size as usize];
            assert_eq!(
                archive.read_range(0, 0, &mut data).expect("whole member read"),
                size as usize
            );
            let hash = Sha256::digest(&data);
            let actual = hash.iter().map(|b| format!("{b:02x}")).collect::<String>();
            assert_eq!(actual, digest_expected);
            assert_eq!(crc32fast::hash(&data) as u64, crc_expected);
        }
        let wall = start.elapsed().as_nanos();
        let rchar = proc_num("/proc/self/io", "rchar:").saturating_sub(before);
        let highwater = proc_num("/proc/self/status", "VmHWM:");
        println!(
            "J24I38 size={mib} iter={iteration} wall_ns={wall} rchar={rchar} vmhwm_kib={highwater}"
        );
    }
}
