//! Research-only native preparity verifier for the recovery-safe ZIP-factor v4 envelope.
//!
//! This intentionally does not enter `PortableArchive` dispatch. It validates the recovery envelope locally while
//! delegating every reconstructed CMP25Z3 semantic check to the exact in-process V3 owner. Primary control is tried
//! first; if it fails, the authenticated tail control is used. Both-invalid input fails closed. No scratch V3 file
//! or nested verifier process is used.

use sha2::{Digest, Sha256};
use std::{env, fs, path::Path};

const REC_MAGIC: &[u8; 8] = b"CMP25Z4\0";
const V3_MAGIC: &[u8; 8] = b"CMP25Z3\0";
const TAIL_MAGIC: &[u8; 8] = b"ZFRTAIL1";
const FOOTER_SIZE: usize = 8 + 4 + 32;
const MAX_CONTROL: usize = 1024 * 1024;

fn u32_at(raw: &[u8], at: usize, label: &str) -> Result<u32, String> {
    let bytes: [u8; 4] = raw
        .get(at..at + 4)
        .ok_or_else(|| format!("truncated {label}"))?
        .try_into()
        .map_err(|_| format!("invalid {label}"))?;
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
    let expected: [u8; 32] = raw
        .get(footer + 12..footer + 44)
        .ok_or("truncated tail control hash")?
        .try_into()
        .map_err(|_| "invalid tail control hash")?;
    Ok((control_len, control_start, expected))
}

fn candidate(
    raw: &[u8],
    control: &[u8],
    body_start: usize,
    body_end: usize,
) -> Result<Vec<u8>, String> {
    if body_start > body_end || body_end > raw.len() {
        return Err("recovery body bounds".into());
    }
    let capacity = 8usize
        .checked_add(control.len())
        .and_then(|v| v.checked_add(body_end - body_start))
        .ok_or("recovery candidate size overflow")?;
    let mut out = Vec::with_capacity(capacity);
    out.extend_from_slice(V3_MAGIC);
    out.extend_from_slice(control);
    out.extend_from_slice(&raw[body_start..body_end]);
    Ok(out)
}

fn verify_v3_bytes(raw: &[u8]) -> Result<(), String> {
    // SAFETY: the owned candidate slice remains readable and stable for the complete call; the ABI neither retains
    // nor mutates it. This is the same exact semantic owner used by the winning in-memory FFI frontier.
    let status = unsafe {
        cmpct_zipfactor_v3_ffi::cmpct_zipfactor_v3_verify_bytes(raw.as_ptr(), raw.len())
    };
    match status {
        0 => Ok(()),
        1 => Err("V3 semantic owner rejected reconstructed candidate".into()),
        2 => Err("V3 semantic owner rejected ABI argument".into()),
        other => Err(format!("unexpected V3 semantic-owner status: {other}")),
    }
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
    if verify_v3_bytes(&primary_candidate).is_ok() {
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
    verify_v3_bytes(&tail_candidate)
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
        Ok(copy) => println!("ok profile=zip-framing-factor-recovery-v4 recovered_from={copy} verifier=in-process"),
        Err(message) => {
            eprintln!("cmpct-zipfactor-v4-recovery-preparity: {message}");
            std::process::exit(1);
        }
    }
}
