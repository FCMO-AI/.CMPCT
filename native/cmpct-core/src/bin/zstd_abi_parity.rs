//! Fail-closed falsifier for the package-owned Zstd route used by #176.
//!
//! This intentionally exercises zstd-safe's low-level CCtx/DCtx dictionary calls rather than the
//! higher-level zstd convenience API. Shipping ownership must not move unless these semantics remain
//! byte-identical to the canonical one-shot libzstd calls on the frozen discriminator corpus.

use std::process::ExitCode;
use zstd::zstd_safe::{self, CCtx, DCtx};

fn payload() -> Vec<u8> {
    // Preserve the known #177 discriminator length while avoiding fixture-identity dependence: the
    // content combines repeated structure and deterministic perturbations so dictionary matching is
    // material rather than accidental.
    let mut out = Vec::with_capacity(155_648);
    let phrase = b"cmpct exact raw dictionary ownership boundary\0";
    while out.len() < 155_648 {
        let i = out.len();
        out.extend_from_slice(phrase);
        out.extend_from_slice(&(i as u64).to_le_bytes());
        out.extend_from_slice(&phrase[..(i / 17) % phrase.len()]);
    }
    out.truncate(155_648);
    out
}

fn dictionary() -> Vec<u8> {
    let mut d = Vec::with_capacity(8192);
    let seed = b"cmpct exact raw dictionary ownership boundary\0";
    while d.len() < 8192 {
        d.extend_from_slice(seed);
        d.extend_from_slice(&(d.len() as u32).to_le_bytes());
    }
    d.truncate(8192);
    d
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
        println!(
            "level={level} usize={} csize={}",
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
