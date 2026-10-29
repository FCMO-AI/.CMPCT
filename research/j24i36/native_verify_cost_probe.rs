//! J24I36 source-exact *in-process* native full verification cost probe.
//! Research helper, copied into each exact-source Cargo workspace when measuring.
//! Distinguishes verify wall from startup/open/build. Does not claim CPU/RSS.
use cmpct_core::Archive;
use std::env;
use std::path::Path;
use std::time::Instant;

fn main() {
    let mut args = env::args().skip(1);
    let path = args.next().expect("usage: j24i36-perf PATH");
    assert!(args.next().is_none(), "exactly one archive path");
    let archive = Archive::open(Path::new(&path)).expect("source-exact r24 archive must open");
    let expected_count = archive.entries().iter().filter(|row| row.kind == 0 || row.kind == 2).count();
    for iteration in 0..7 {
        let t0 = Instant::now();
        let count = archive.verify_complete().expect("strong verification must pass");
        let wall = t0.elapsed().as_nanos();
        assert_eq!(count, expected_count, "no skipped payload-bearing entries");
        println!("J24I36_PERF iteration={iteration} verified={count} wall_ns={wall}");
    }
}
