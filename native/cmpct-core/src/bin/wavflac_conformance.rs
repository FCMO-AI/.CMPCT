#[path = "../wavflac.rs"]
mod wavflac;

use sha2::{Digest, Sha256};
use std::env;
use std::fs;
use std::process::ExitCode;

fn hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(&mut out, "{byte:02x}");
    }
    out
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() != 5 {
        eprintln!("usage: cmpct-wavflac-conformance META.bin PAYLOAD.flac LOGICAL_SIZE OUTPUT.wav");
        return ExitCode::from(2);
    }

    let meta = match fs::read(&args[1]) {
        Ok(bytes) => bytes,
        Err(error) => {
            eprintln!("cannot read codec metadata: {error}");
            return ExitCode::from(2);
        }
    };
    let compressed = match fs::read(&args[2]) {
        Ok(bytes) => bytes,
        Err(error) => {
            eprintln!("cannot read FLAC payload: {error}");
            return ExitCode::from(2);
        }
    };
    let logical_size = match args[3].parse::<u64>() {
        Ok(value) => value,
        Err(error) => {
            eprintln!("invalid logical size: {error}");
            return ExitCode::from(2);
        }
    };

    let decoded =
        match wavflac::decode_wav_flac(&compressed, &meta, logical_size, 256 * 1024 * 1024) {
            Ok(bytes) => bytes,
            Err(error) => {
                eprintln!("codec-2 reconstruction failed: {error}");
                return ExitCode::from(1);
            }
        };

    if let Err(error) = fs::write(&args[4], &decoded) {
        eprintln!("cannot write reconstructed WAV: {error}");
        return ExitCode::from(2);
    }

    println!(
        "{{\"logical_size\":{},\"sha256\":\"{}\"}}",
        decoded.len(),
        hex(&Sha256::digest(&decoded))
    );
    ExitCode::SUCCESS
}
