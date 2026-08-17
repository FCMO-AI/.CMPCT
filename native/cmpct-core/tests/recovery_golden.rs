#[path = "../src/msgpack_guard.rs"]
mod msgpack_guard;

#[path = "../src/recovery.rs"]
mod recovery;

use rmpv::Value;
use std::fs::{self, File};
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

fn decode_base64(input: &str) -> Vec<u8> {
    fn value(byte: u8) -> Option<u8> {
        match byte {
            b'A'..=b'Z' => Some(byte - b'A'),
            b'a'..=b'z' => Some(byte - b'a' + 26),
            b'0'..=b'9' => Some(byte - b'0' + 52),
            b'+' => Some(62),
            b'/' => Some(63),
            _ => None,
        }
    }
    let bytes = input.as_bytes();
    assert_eq!(bytes.len() % 4, 0);
    let mut out = Vec::with_capacity(bytes.len() / 4 * 3);
    for block in bytes.chunks_exact(4) {
        let a = value(block[0]).unwrap() as u32;
        let b = value(block[1]).unwrap() as u32;
        let c = if block[2] == b'=' {
            0
        } else {
            value(block[2]).unwrap() as u32
        };
        let d = if block[3] == b'=' {
            0
        } else {
            value(block[3]).unwrap() as u32
        };
        let packed = (a << 18) | (b << 12) | (c << 6) | d;
        out.push((packed >> 16) as u8);
        if block[2] != b'=' {
            out.push((packed >> 8) as u8);
        }
        if block[3] != b'=' {
            out.push(packed as u8);
        }
    }
    out
}

fn map_field<'a>(value: &'a Value, key: &str) -> &'a Value {
    value
        .as_map()
        .unwrap()
        .iter()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
        .unwrap()
}

fn recovered_names(index: &Value) -> Vec<String> {
    map_field(index, "files")
        .as_array()
        .unwrap()
        .iter()
        .map(|row| row.as_array().unwrap()[0].as_str().unwrap().to_owned())
        .collect()
}

fn temporary_archive(bytes: &[u8], label: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "cmpct-recovery-{}-{}-{nonce}.cmpct",
        std::process::id(),
        label
    ));
    fs::write(&path, bytes).unwrap();
    path
}

fn exercise(vector: &serde_json::Value, field: &str, label: &str) {
    let bytes = decode_base64(vector[field].as_str().unwrap());
    let path = temporary_archive(&bytes, label);
    let mut file = File::open(&path).unwrap();
    let recovered =
        recovery::latest_committed_index(&mut file, bytes.len() as u64, 16 * 1024 * 1024, 128)
            .unwrap()
            .expect("at least the original committed checkpoint must survive");
    fs::remove_file(path).unwrap();

    let expected_files: Vec<String> = vector["expected_files"]
        .as_array()
        .unwrap()
        .iter()
        .map(|value| value.as_str().unwrap().to_owned())
        .collect();
    assert_eq!(recovered_names(&recovered.index), expected_files);
    assert_eq!(
        map_field(&recovered.index, "blobs")
            .as_array()
            .unwrap()
            .len(),
        vector["expected_blob_count"].as_u64().unwrap() as usize
    );
    assert_eq!(
        recovered.footer_pos,
        vector["latest_footer_pos"].as_u64().unwrap()
    );
    assert_eq!(recovered.delta_depth, 1);
    assert!(recovered.committed_data_end < recovered.footer_pos);
}

#[test]
fn fixed_revision24_generation_chain_recovers_latest_valid_state() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("../../../tests/conformance/v24-recovery.json")).unwrap();
    let vector = &fixture["vector"];
    exercise(vector, "valid_archive_base64", "valid");
}

#[test]
fn corrupt_primary_index_does_not_hide_valid_tail_generation() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("../../../tests/conformance/v24-recovery.json")).unwrap();
    exercise(
        &fixture["vector"],
        "primary_corrupt_base64",
        "primary-corrupt",
    );
}

#[test]
fn torn_or_invalid_newest_append_falls_back_to_prior_commit() {
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("../../../tests/conformance/v24-recovery.json")).unwrap();
    let vector = &fixture["vector"];
    exercise(vector, "torn_tail_base64", "torn-tail");
    exercise(
        vector,
        "invalid_newest_footer_base64",
        "invalid-newest-footer",
    );
}
