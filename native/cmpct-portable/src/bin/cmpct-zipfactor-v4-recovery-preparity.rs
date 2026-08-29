//! Research-only native preparity verifier for the recovery-safe ZIP-factor v4 envelope.
//!
//! This intentionally does not enter `PortableArchive` dispatch. It proves that the exact recovery envelope can
//! be validated natively while delegating all reconstructed CMP25Z3 semantics to the single existing V3 source.
//! Primary control is tried first; if it fails, the authenticated tail control is used. Both-invalid fails closed.

use sha2::{Digest, Sha256};
use std::{env, fs, path::Path};

const REC_MAGIC: &[u8; 8] = b"CMP25Z4\0";
const V3_MAGIC: &[u8; 8] = b"CMP25Z3\0";
const TAIL_MAGIC: &[u8; 8] = b"ZFRTAIL1";
const FOOTER_SIZE: usize = 8 + 4 + 32;
const MAX_CONTROL: usize = 1024 * 1024;

// Compile the exact same V3 grammar used by the existing preparity binary and research FFI. The wrapper lives
// inside the child module so it may call the source's private byte-slice verifier without making research API public.
#[allow(dead_code)]
mod v3 {
    include!("cmpct-zipfactor-v3-preparity.rs");

    pub(super) fn verify_exact_bytes(raw: &[u8]) -> Result<(), String> {
        verify_slice(raw)
    }
}

fn u32_at(raw: &[u8], at: usize, label: &str) -> Result<u32, String> {
    let bytes: [u8; 4] = raw
        .get(at..at + 4)
        .ok_or_else(|| format!("truncated {label}"))?
        .try_into()
        .unwrap();
    Ok(u32::from_le_bytes(bytes))
}

fn tail_layout(raw: &[u8]) -> Result<(usize, usize, [u8; 32]), String> {
    if raw.len() < 8 + FOOTER_SIZE || raw.get(..8) != Some(REC_MAGIC) {
        return Err("not a ZIP-factor recovery archive".into());
    }
    let footer = raw.len() - FOOTER_SIZE;
    if raw.get(footer..footer + 8) != Some(TAIL_MAGIC) {
        return Err("invalid ZIP-factor recovery footer magic".into());
    }
    let control_len = usize::try_from(u32_at(raw, footer + 8, "tail control length")?)
        .map_err(|_| "tail control length overflow")?;
    if control_len == 0 || control_len > MAX_CONTROL {
        return Err("tail control length exceeds policy".into());
    }
    let control_start = footer
        .checked_sub(control_len)
        .ok_or("tail control offset underflow")?;
    if control_start <= 8 + control_len {
        return Err("tail control overlaps primary/body".into());
    }
    let expected: [u8; 32] = raw[footer + 12..footer + 44].try_into().unwrap();
    Ok((control_len, control_start, expected))
}

fn candidate(raw: &[u8], control: &[u8], body_start: usize, body_end: usize) -> Result<Vec<u8>, String> {
    if body_start > body_end || body_end > raw.len() {
        return Err("recovery body bounds".into());
    }
    let mut out = Vec::with_capacity(8 + control.len() + body_end - body_start);
    out.extend_from_slice(V3_MAGIC);
    out.extend_from_slice(control);
    out.extend_from_slice(&raw[body_start..body_end]);
    Ok(out)
}

fn verify_recovery_bytes(raw: &[u8]) -> Result<&'static str, String> {
    let (control_len, tail_start, tail_sha) = tail_layout(raw)?;
    let primary_start = 8usize;
    let body_start = primary_start
        .checked_add(control_len)
        .ok_or("primary control offset overflow")?;
    if body_start > tail_start {
        return Err("primary control overlaps payload".into());
    }

    let primary = raw
        .get(primary_start..body_start)
        .ok_or("truncated primary control")?;
    let primary_candidate = candidate(raw, primary, body_start, tail_start)?;
    if v3::verify_exact_bytes(&primary_candidate).is_ok() {
        return Ok("primary");
    }

    let tail = raw
        .get(tail_start..tail_start + control_len)
        .ok_or("truncated tail control")?;
    let observed: [u8; 32] = Sha256::digest(tail).into();
    if observed != tail_sha {
        return Err("primary invalid and tail control authentication failed".into());
    }
    let tail_candidate = candidate(raw, tail, body_start, tail_start)?;
    v3::verify_exact_bytes(&tail_candidate)
        .map(|()| "tail")
        .map_err(|e| format!("both recovery controls invalid: {e}"))
}

fn verify_path(path: &Path) -> Result<&'static str, String> {
    let raw = fs::read(path).map_err(|e| format!("read archive: {e}"))?;
    verify_recovery_bytes(&raw)
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 || args[1] != "verify" {
        eprintln!("usage: cmpct-zipfactor-v4-recovery-preparity verify <archive>");
        std::process::exit(2);
    }
    match verify_path(Path::new(&args[2])) {
        Ok(copy) => println!("ok profile=zip-framing-factor-recovery-v4 recovered_from={copy}"),
        Err(message) => {
            eprintln!("cmpct-zipfactor-v4-recovery-preparity: {message}");
            std::process::exit(1);
        }
    }
}
