use cmpct_core::Archive;
use serde_json::json;
use std::env;
use std::path::Path;

fn main() {
    let path = env::args().nth(1).expect("usage: cmpct-native-inspect ARCHIVE.cmpct");
    let archive = Archive::open(Path::new(&path)).unwrap_or_else(|e| {
        eprintln!("{e}");
        std::process::exit(2);
    });
    let entries = archive.entries().iter().map(|e| json!({
        "path": e.path,
        "kind": e.kind,
        "mode": e.mode,
        "mtime_ns": e.mtime_ns,
        "size": e.size,
    })).collect::<Vec<_>>();
    println!("{}", serde_json::to_string(&json!({
        "revision": archive.revision(),
        "entries": entries,
    })).unwrap());
}
