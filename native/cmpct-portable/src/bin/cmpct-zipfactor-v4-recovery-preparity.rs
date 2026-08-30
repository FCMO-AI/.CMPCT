//! Research-only native preparity verifier for the recovery-safe ZIP-factor v4 envelope.
//!
//! This intentionally does not enter `PortableArchive` dispatch. It exercises the exact recovery envelope through
//! the same in-process V3/V4 semantic owner used by the measured FFI frontier. There is no scratch V3 publication
//! and no nested verifier process; malformed or double-control-corrupt input still fails closed in the shared owner.

use std::{env, fs, path::Path};

fn verify_path(path: &Path) -> Result<(), String> {
    let raw = fs::read(path).map_err(|e| format!("read archive: {e}"))?;
    // SAFETY: `raw` owns a stable readable allocation for the full duration of the call. The verifier does not
    // retain or mutate the pointer. Empty input is valid at the ABI boundary and is rejected semantically.
    let status = unsafe {
        cmpct_zipfactor_v3_ffi::cmpct_zipfactor_v4_recovery_verify_bytes(raw.as_ptr(), raw.len())
    };
    match status {
        0 => Ok(()),
        1 => Err("in-process recovery semantic owner rejected archive".into()),
        2 => Err("in-process recovery semantic owner rejected ABI argument".into()),
        other => Err(format!("unexpected recovery semantic-owner status: {other}")),
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 || args[1] != "verify" {
        eprintln!("usage: cmpct-zipfactor-v4-recovery-preparity verify <archive>");
        std::process::exit(2);
    }
    match verify_path(Path::new(&args[2])) {
        Ok(()) => println!("ok profile=zip-framing-factor-recovery-v4 verifier=in-process"),
        Err(message) => {
            eprintln!("cmpct-zipfactor-v4-recovery-preparity: {message}");
            std::process::exit(1);
        }
    }
}
