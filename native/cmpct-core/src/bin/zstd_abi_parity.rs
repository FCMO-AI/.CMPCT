//! Fail-closed falsifier for the package-owned Zstd route used by #176.
//!
//! This intentionally exercises zstd-safe's low-level CCtx/DCtx dictionary calls rather than the
//! higher-level zstd convenience API. Shipping ownership must not move unless these semantics remain
//! byte-identical to the canonical one-shot libzstd calls on the frozen #177 discriminator corpus.

use sha2::{Digest, Sha256};
use std::process::ExitCode;
use zstd::zstd_safe::{self, CCtx, DCtx};

fn payload() -> Vec<u8> {
    // Exact structured discriminator that exposed the 104 B vs 105 B dictionary mismatch in #177.
    let mut out = Vec::with_capacity(155_648);
    for _ in 0..8192 {
        out.extend_from_slice(b"structured-record\0");
    }
    for _ in 0..128 {
        out.extend(0u8..=63);
    }
    assert_eq!(out.len(), 155_648);
    out
}

fn dictionary() -> Vec<u8> {
    let seed = b"alpha beta gamma delta structured-record\0";
    let mut out = Vec::with_capacity(4096);
    while out.len() < 4096 {
        out.extend_from_slice(seed);
    }
    out.truncate(4096);
    out
}

fn probe() -> Result<(), String> {
    let src = payload();
    let dict = dictionary();
    let mut cctx = CCtx::create();
    let mut dctx = DCtx::create();

    for level in [1, 3, 9, 19] {
        let bound = zstd_safe::compress_bound(src.len());
        let mut compressed = vec![0u8; bound];
        let n = cctx
            .compress_using_dict(&mut compressed[..], &src, &dict, level)
            .map_err(|code| {
                format!(
                    "compress_using_dict failed at level {level}: {}",
                    zstd_safe::get_error_name(code)
                )
            })?;
        compressed.truncate(n);

        let mut decoded = vec![0u8; src.len()];
        let m = dctx
            .decompress_using_dict(&mut decoded[..], &compressed, &dict)
            .map_err(|code| {
                format!(
                    "decompress_using_dict failed at level {level}: {}",
                    zstd_safe::get_error_name(code)
                )
            })?;
        if m != src.len() || decoded != src {
            return Err(format!("dictionary roundtrip mismatch at level {level}"));
        }
        let digest = Sha256::digest(&compressed);
        println!(
            "level={level} usize={} csize={} sha256={digest:x}",
            src.len(),
            compressed.len()
        );
    }
    Ok(())
}

fn main() -> ExitCode {
    match probe() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::probe;

    #[test]
    fn package_owned_dictionary_calls_roundtrip_discriminator() {
        probe().unwrap();
    }
}
