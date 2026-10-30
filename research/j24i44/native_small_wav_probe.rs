//! J24I44 — exact native product-path complete verifier for Builder-selected small WAV.
//! This is research instrumentation; compiled twice against source-locked native crates.

use cmpct_core::Archive;
use std::env;
use std::fs;
use std::path::Path;
use std::time::Instant;

#[cfg(target_os = "linux")]
fn metric(path: &str, prefix: &str) -> u64 {
    fs::read_to_string(path)
        .expect("procfs metric available")
        .lines()
        .find_map(|line| line.strip_prefix(prefix))
        .expect("required procfs metric present")
        .split_whitespace()
        .next()
        .unwrap()
        .parse()
        .expect("numeric process metric")
}

fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 3, "usage: native_small_wav_probe archive-file pcm-kib");
    let pcm_kib: u64 = args[2].parse().unwrap();
    assert!([64, 256, 1024, 2048, 4096, 8192].contains(&pcm_kib));
    let archive = Archive::open(Path::new(&args[1])).expect("authenticated r24 Builder archive");
    assert_eq!(archive.entries().len(), 1);
    assert_eq!(archive.entries()[0].size, pcm_kib * 1024 + 44);
    // Every A/B run must perform the actual product complete verifier, not a
    // detached FLAC-only decoder. Four warmups permit local per-process drift
    // analysis without changing the validity or difficulty of the work.
    for iteration in 0..12 {
        #[cfg(target_os = "linux")]
        let before = metric("/proc/self/io", "rchar:");
        let start = Instant::now();
        assert_eq!(
            archive.verify_complete().expect("complete native verification"),
            1
        );
        let elapsed_ns = start.elapsed().as_nanos();
        #[cfg(target_os = "linux")]
        let (rchar, peak_kib) = (
            metric("/proc/self/io", "rchar:") - before,
            metric("/proc/self/status", "VmHWM:"),
        );
        #[cfg(not(target_os = "linux"))]
        let (rchar, peak_kib) = (0, 0);
        println!(
            "J24I44 iter={iteration} kib={pcm_kib} ns={elapsed_ns} rchar={rchar} vmhwm_kib={peak_kib}"
        );
    }
}
