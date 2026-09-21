//! Linkage gate for the package-owned codec ABI.
//!
//! Unlike `codec_abi_contract`, this test does not compile the implementation by path. It declares
//! only the C symbols and therefore proves that the shipping crate actually links the staged ABI.

use sha2::{Digest, Sha256};

extern "C" {
    fn cmpct_codec_zstd_compress_bound(input_len: usize) -> usize;
    fn cmpct_codec_zstd_compress_using_dict(
        input: *const u8,
        input_len: usize,
        dictionary: *const u8,
        dictionary_len: usize,
        level: i32,
        output: *mut u8,
        output_capacity: usize,
        output_len: *mut usize,
    ) -> i32;
}

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

#[test]
fn shipping_crate_exports_exact_dictionary_encoder() {
    let payload = structured_payload();
    let dictionary = raw_dictionary();
    let capacity = unsafe { cmpct_codec_zstd_compress_bound(payload.len()) };
    let mut encoded = vec![0u8; capacity];
    let mut encoded_len = 0usize;
    let status = unsafe {
        cmpct_codec_zstd_compress_using_dict(
            payload.as_ptr(),
            payload.len(),
            dictionary.as_ptr(),
            dictionary.len(),
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
        format!("{:x}", Sha256::digest(&encoded)),
        "0c265b0a03ec404b40749d13212420813cb546a6eecf5dcd0397f20ce15e23a6"
    );
}
