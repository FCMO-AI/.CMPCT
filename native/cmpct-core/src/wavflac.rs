//! Revision-24 codec-2 (WAV/FLAC) reconstruction.
//!
//! Codec 2 stores a FLAC stream plus MessagePack metadata `[prefix, suffix, channels, rate, bits]`.
//! The prefix and suffix are archive bytes, not a WAV template: they must be copied verbatim around
//! the decoded PCM so unusual-but-valid RIFF layout survives byte-for-byte.

use claxon::FlacReader;
use rmpv::Value;
use std::io::Cursor;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum WavFlacError {
    #[error("codec-2 metadata is invalid: {0}")]
    Metadata(String),
    #[error("FLAC stream is invalid: {0}")]
    Flac(String),
    #[error("codec-2 reconstruction exceeds the caller's byte budget")]
    Limit,
    #[error("FLAC stream properties do not match authenticated codec-2 metadata")]
    StreamInfo,
    #[error("decoded PCM byte count does not match the declared WAV size")]
    Length,
}

struct Metadata {
    prefix: Vec<u8>,
    suffix: Vec<u8>,
    channels: u32,
    sample_rate: u32,
    bits_per_sample: u32,
}

fn as_u32(value: &Value, name: &str) -> Result<u32, WavFlacError> {
    value
        .as_u64()
        .and_then(|v| u32::try_from(v).ok())
        .ok_or_else(|| WavFlacError::Metadata(format!("{name} must be an unsigned 32-bit integer")))
}

fn as_bytes(value: &Value, name: &str) -> Result<Vec<u8>, WavFlacError> {
    match value {
        Value::Binary(bytes) => Ok(bytes.clone()),
        _ => Err(WavFlacError::Metadata(format!(
            "{name} must be MessagePack binary"
        ))),
    }
}

fn parse_metadata(meta: &[u8]) -> Result<Metadata, WavFlacError> {
    let mut cursor = Cursor::new(meta);
    let value = rmpv::decode::read_value(&mut cursor)
        .map_err(|e| WavFlacError::Metadata(e.to_string()))?;
    if cursor.position() != meta.len() as u64 {
        return Err(WavFlacError::Metadata(
            "trailing bytes after codec-2 metadata".into(),
        ));
    }
    let fields = value
        .as_array()
        .ok_or_else(|| WavFlacError::Metadata("root must be a five-element array".into()))?;
    if fields.len() != 5 {
        return Err(WavFlacError::Metadata(
            "root must contain exactly five fields".into(),
        ));
    }

    let bits_per_sample = as_u32(&fields[4], "bits")?;
    if !matches!(bits_per_sample, 16 | 32) {
        // Revision 24's Python encoder deliberately emits codec 2 only for PCM16/PCM32. Refusing
        // unimplemented widths is safer than inventing sign/packing semantics in a platform handler.
        return Err(WavFlacError::Metadata(
            "native codec 2 currently supports PCM16 and PCM32 only".into(),
        ));
    }

    Ok(Metadata {
        prefix: as_bytes(&fields[0], "prefix")?,
        suffix: as_bytes(&fields[1], "suffix")?,
        channels: as_u32(&fields[2], "channels")?,
        sample_rate: as_u32(&fields[3], "sample_rate")?,
        bits_per_sample,
    })
}

/// Reconstruct one revision-24 codec-2 logical WAV exactly.
///
/// `logical_size` is the authenticated physical blob `usize`. It both bounds allocation and proves
/// that metadata + decoded PCM + suffix account for every logical byte before anything is returned.
pub fn decode_wav_flac(
    compressed: &[u8],
    meta: &[u8],
    logical_size: u64,
    max_output: u64,
) -> Result<Vec<u8>, WavFlacError> {
    if logical_size > max_output {
        return Err(WavFlacError::Limit);
    }

    let metadata = parse_metadata(meta)?;
    if metadata.channels == 0 || metadata.sample_rate == 0 {
        return Err(WavFlacError::Metadata(
            "channels and sample_rate must be non-zero".into(),
        ));
    }

    let fixed_bytes = metadata
        .prefix
        .len()
        .checked_add(metadata.suffix.len())
        .ok_or(WavFlacError::Limit)?;
    let logical_size_usize = usize::try_from(logical_size).map_err(|_| WavFlacError::Limit)?;
    if fixed_bytes > logical_size_usize {
        return Err(WavFlacError::Length);
    }
    let pcm_bytes_expected = logical_size_usize - fixed_bytes;
    let sample_width = (metadata.bits_per_sample / 8) as usize;
    if pcm_bytes_expected % sample_width != 0 {
        return Err(WavFlacError::Length);
    }

    let mut reader =
        FlacReader::new(Cursor::new(compressed)).map_err(|e| WavFlacError::Flac(e.to_string()))?;
    let info = reader.streaminfo();
    if info.channels != metadata.channels
        || info.sample_rate != metadata.sample_rate
        || info.bits_per_sample != metadata.bits_per_sample
    {
        return Err(WavFlacError::StreamInfo);
    }

    let mut out = Vec::with_capacity(logical_size_usize);
    out.extend_from_slice(&metadata.prefix);

    let mut pcm_bytes = 0usize;
    for sample in reader.samples() {
        let sample = sample.map_err(|e| WavFlacError::Flac(e.to_string()))?;
        match metadata.bits_per_sample {
            16 => {
                let narrowed = i16::try_from(sample).map_err(|_| WavFlacError::StreamInfo)?;
                out.extend_from_slice(&narrowed.to_le_bytes());
                pcm_bytes = pcm_bytes.checked_add(2).ok_or(WavFlacError::Limit)?;
            }
            32 => {
                out.extend_from_slice(&sample.to_le_bytes());
                pcm_bytes = pcm_bytes.checked_add(4).ok_or(WavFlacError::Limit)?;
            }
            _ => unreachable!(),
        }
        if pcm_bytes > pcm_bytes_expected {
            return Err(WavFlacError::Length);
        }
    }

    if pcm_bytes != pcm_bytes_expected {
        return Err(WavFlacError::Length);
    }
    out.extend_from_slice(&metadata.suffix);
    if out.len() != logical_size_usize {
        return Err(WavFlacError::Length);
    }
    Ok(out)
}
