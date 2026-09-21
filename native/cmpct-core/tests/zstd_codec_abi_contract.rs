#[path = "../src/codec_abi.rs"]
mod codec_abi;

use sha2::{Digest, Sha256};

fn structured_payload() -> Vec<u8> {
    let mut out = Vec::new();
    for _ in 0..8192 {
        out.extend_from_slice(b"structured-record\0");
    }
    for _ in 0..128 {
        out.extend(0u8..64u8);
    }
    out
}

fn raw_dictionary() -> Vec<u8> {
    let seed = b"alpha beta gamma delta structured-record\0";
    let mut out = Vec::new();
    while out.len() < 4096 {
        out.extend_from_slice(seed);
    }
    out.truncate(4096);
    out
}

fn sha(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

#[test]
fn caller_buffer_plain_preserves_canonical_bytes_and_roundtrips() {
    let payload = structured_payload();
    let bound = unsafe { codec_abi::cmpct_codec_zstd_compress_bound(payload.len()) };
    let mut encoded = vec![0u8; bound];
    let mut encoded_len = 0usize;
    let status = unsafe {
        codec_abi::cmpct_codec_zstd_compress(
            payload.as_ptr(),
            payload.len(),
            9,
            encoded.as_mut_ptr(),
            encoded.len(),
            &mut encoded_len,
        )
    };
    assert_eq!(status, 0);
    encoded.truncate(encoded_len);
    assert_eq!(encoded.len(), 119);
    assert_eq!(
        sha(&encoded),
        "0f0d7dac31b82339d014530440ef4d494e9cdc183cdea81b6e13822ead857c0f"
    );

    let mut decoded = vec![0u8; payload.len()];
    let mut decoded_len = 0usize;
    let status = unsafe {
        codec_abi::cmpct_codec_zstd_decompress(
            encoded.as_ptr(),
            encoded.len(),
            decoded.as_mut_ptr(),
            decoded.len(),
            &mut decoded_len,
        )
    };
    assert_eq!(status, 0);
    assert_eq!(decoded_len, payload.len());
    assert_eq!(decoded, payload);
}

#[test]
fn caller_buffer_dictionary_preserves_exact_shipping_bytes_and_roundtrips() {
    let payload = structured_payload();
    let dict = raw_dictionary();
    let bound = unsafe { codec_abi::cmpct_codec_zstd_compress_bound(payload.len()) };
    let mut encoded = vec![0u8; bound];
    let mut encoded_len = 0usize;
    let status = unsafe {
        codec_abi::cmpct_codec_zstd_compress_using_dict(
            payload.as_ptr(),
            payload.len(),
            dict.as_ptr(),
            dict.len(),
            9,
            encoded.as_mut_ptr(),
            encoded.len(),
            &mut encoded_len,
        )
    };
    assert_eq!(status, 0);
    encoded.truncate(encoded_len);
    assert_eq!(encoded.len(), 104);
    assert_eq!(
        sha(&encoded),
        "0c265b0a03ec404b40749d13212420813cb546a6eecf5dcd0397f20ce15e23a6"
    );

    let mut decoded = vec![0u8; payload.len()];
    let mut decoded_len = 0usize;
    let status = unsafe {
        codec_abi::cmpct_codec_zstd_decompress_using_dict(
            encoded.as_ptr(),
            encoded.len(),
            dict.as_ptr(),
            dict.len(),
            decoded.as_mut_ptr(),
            decoded.len(),
            &mut decoded_len,
        )
    };
    assert_eq!(status, 0);
    assert_eq!(decoded_len, payload.len());
    assert_eq!(decoded, payload);
}

#[test]
fn undersized_output_is_bounded_and_reports_no_partial_success() {
    let payload = structured_payload();
    let mut tiny = [0u8; 8];
    let mut out_len = usize::MAX;
    let status = unsafe {
        codec_abi::cmpct_codec_zstd_compress(
            payload.as_ptr(),
            payload.len(),
            9,
            tiny.as_mut_ptr(),
            tiny.len(),
            &mut out_len,
        )
    };
    assert_eq!(status, -6);
    assert_eq!(out_len, 0);
}
