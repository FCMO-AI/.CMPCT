use std::{env, fs, path::PathBuf};

fn main() {
    let manifest = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"));
    let source = manifest
        .join("../cmpct-portable/src/bin/cmpct-zipfactor-v3-preparity.rs")
        .canonicalize()
        .expect("canonical preparity source");
    println!("cargo:rerun-if-changed={}", source.display());

    let raw = fs::read_to_string(&source).expect("read preparity verifier source");
    // `include!` inside a module cannot accept the binary crate's leading inner doc comments. Strip only the
    // documentation marker; every executable token remains sourced from the exact preparity verifier.
    let generated = raw
        .lines()
        .map(|line| line.strip_prefix("//!").map_or(line.to_owned(), |rest| format!("//{rest}")))
        .collect::<Vec<_>>()
        .join("\n");

    let out = PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("zipfactor_v3_preparity.rs");
    fs::write(out, format!("{generated}\n")).expect("write generated preparity source");
}
