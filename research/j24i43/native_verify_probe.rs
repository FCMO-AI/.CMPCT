//! J24I43 product-path complete-verify referee. Runs against an installed exact native crate.
use cmpct_core::Archive;
use std::env;
use std::fs;
use std::path::Path;
use std::time::Instant;

#[cfg(target_os = "linux")]
fn metric(path: &str, prefix: &str) -> u64 {
    fs::read_to_string(path).unwrap().lines()
        .find_map(|s| s.strip_prefix(prefix)).unwrap()
        .split_whitespace().next().unwrap().parse().unwrap()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 4, "probe ORIGINAL_OR_MUTANT expected-pass|expected-fail size-mib");
    let path = Path::new(&args[1]);
    let mode = args[2].as_str();
    assert!(mode == "expected-pass" || mode == "expected-fail");
    let size: u64 = args[3].parse().unwrap();
    assert!([8,32].contains(&size));
    let archive = Archive::open(path).expect("well-formed index and on-disk bounds");
    assert_eq!(archive.entries().len(), 1);
    assert_eq!(archive.entries()[0].size, size * 1024 * 1024 + 44);
    if mode == "expected-fail" {
        let result = archive.verify_complete();
        assert!(result.is_err(), "J24I43_UNSAFE_ACCEPT: malformed physical WAV accepted");
        println!("J24I43_REJECTED {}", result.unwrap_err());
        return;
    }
    for i in 0..4 {
        #[cfg(target_os = "linux")]
        let before = metric("/proc/self/io", "rchar:");
        let t = Instant::now();
        assert_eq!(archive.verify_complete().expect("native complete verify"), 1);
        let elapsed = t.elapsed().as_nanos();
        #[cfg(target_os = "linux")]
        let (rchar,hwm) = (
            metric("/proc/self/io", "rchar:") - before,
            metric("/proc/self/status", "VmHWM:")
        );
        #[cfg(not(target_os = "linux"))]
        let (rchar,hwm) = (0,0);
        println!("J24I43 iter={i} size={size} ns={elapsed} rchar={rchar} vmhwm_kib={hwm}");
    }
}
