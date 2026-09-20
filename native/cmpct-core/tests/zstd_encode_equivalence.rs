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

fn hex_sha(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

#[test]
fn rust_zstd_plain_matches_shipping_ctypes_vector() {
    let encoded = zstd::bulk::compress(&structured_payload(), 9).expect("plain zstd encode");
    assert_eq!(encoded.len(), 119);
    assert_eq!(hex_sha(&encoded), "0f0d7dac31b82339d014530440ef4d494e9cdc183cdea81b6e13822ead857c0f");
}

#[test]
fn rust_zstd_raw_dictionary_matches_shipping_using_dict_vector() {
    let payload = structured_payload();
    let dictionary = raw_dictionary();
    let mut compressor = zstd::bulk::Compressor::with_dictionary(9, &dictionary)
        .expect("raw dictionary compressor");
    let encoded = compressor.compress(&payload).expect("dictionary zstd encode");
    // Exact shipping ctypes vector recovered from #177 artifact 10604540852.
    assert_eq!(encoded.len(), 104);
    assert_eq!(hex_sha(&encoded), "0c265b0a03ec404b40749d13212420813cb546a6eecf5dcd0397f20ce15e23a6");
}
