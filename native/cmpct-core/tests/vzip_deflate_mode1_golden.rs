#[path = "../src/vzip.rs"]
mod vzip;

use rmpv::Value;
use sha2::{Digest, Sha256};
use std::io::Cursor;
use vzip::{parse_recipe, ProjectionSegment};

const HEADER_SIZE: usize = 68;
const BLOB_HEADER_SIZE: usize = 64;

fn map_field<'a>(value: &'a Value, key: &str) -> &'a Value {
    value
        .as_map()
        .expect("index map")
        .iter()
        .find_map(|(name, value)| (name.as_str() == Some(key)).then_some(value))
        .expect("index field")
}

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
        let a = value(block[0]).expect("base64 digit") as u32;
        let b = value(block[1]).expect("base64 digit") as u32;
        let c = if block[2] == b'=' { 0 } else { value(block[2]).expect("base64 digit") as u32 };
        let d = if block[3] == b'=' { 0 } else { value(block[3]).expect("base64 digit") as u32 };
        let packed = (a << 18) | (b << 12) | (c << 6) | d;
        out.push((packed >> 16) as u8);
        if block[2] != b'=' { out.push((packed >> 8) as u8); }
        if block[3] != b'=' { out.push(packed as u8); }
    }
    out
}

fn decode_hex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|index| u8::from_str_radix(&input[index..index + 2], 16).expect("hex byte"))
        .collect()
}

#[test]
fn fixed_revision24_retained_exact_deflate_projects_without_recompression() {
    let fixture: serde_json::Value = serde_json::from_str(include_str!(
        "../../../tests/conformance/v24-virtual-zip-deflate-mode1.json"
    ))
    .expect("mode-1 fixture JSON");
    let vector = &fixture["vector"];
    let archive = decode_base64(vector["archive_base64"].as_str().unwrap());
    let compressed_len = u64::from_le_bytes(archive[12..20].try_into().unwrap()) as usize;
    let index_bytes = zstd::stream::decode_all(Cursor::new(
        &archive[HEADER_SIZE..HEADER_SIZE + compressed_len],
    ))
    .expect("zstd primary index");
    let mut cursor = Cursor::new(index_bytes.as_slice());
    let index = rmpv::decode::read_value(&mut cursor).expect("MessagePack primary index");

    let blobs = map_field(&index, "blobs").as_array().expect("blob rows");
    let blob_sizes: Vec<u64> = blobs
        .iter()
        .map(|value| value.as_array().unwrap()[1].as_u64().unwrap())
        .collect();
    let files = map_field(&index, "files").as_array().expect("file rows");
    let file = files[0].as_array().expect("file row");
    let logical_size = file[4].as_u64().unwrap();
    let storage = file[6].as_array().expect("storage row");
    let recipe_index = storage[1].as_u64().unwrap() as usize;
    let recipes = map_field(&index, "recipes").as_array().expect("recipe rows");
    let recipe = parse_recipe(&recipes[recipe_index], &blob_sizes, logical_size)
        .expect("retained exact Deflate mode-1 recipe");

    assert_eq!(recipe.payloads.len(), 1);
    assert_eq!(recipe.payloads[0].blob_index, 1, "mode 1 must project the exact-stream blob");
    assert_eq!(recipe.payloads[0].logical_len, 14);

    let data_base = HEADER_SIZE + compressed_len;
    let raw_blobs: Vec<Vec<u8>> = blobs
        .iter()
        .map(|value| {
            let row = value.as_array().unwrap();
            let offset = row[0].as_u64().unwrap() as usize;
            let logical_len = row[1].as_u64().unwrap() as usize;
            let compressed_len = row[2].as_u64().unwrap() as usize;
            let codec = row[3].as_u64().unwrap();
            let meta_len = row[4].as_u64().unwrap() as usize;
            assert_eq!(codec, 0, "fixed mode-1 vector keeps its three CMPCT blobs RAW");
            assert_eq!(compressed_len, logical_len);
            let payload = data_base + offset + BLOB_HEADER_SIZE + meta_len;
            archive[payload..payload + logical_len].to_vec()
        })
        .collect();

    let mut rebuilt = vec![0u8; logical_size as usize];
    for ProjectionSegment {
        blob_index,
        blob_offset,
        output_offset,
        length,
        ..
    } in recipe.plan_range(0, logical_size).expect("complete range plan") {
        let src_start = blob_offset as usize;
        let src_end = src_start + length as usize;
        let dst_start = output_offset as usize;
        let dst_end = dst_start + length as usize;
        rebuilt[dst_start..dst_end].copy_from_slice(&raw_blobs[blob_index][src_start..src_end]);
    }
    let want_hash = decode_hex(vector["logical_sha256"].as_str().unwrap());
    assert_eq!(Sha256::digest(&rebuilt).as_slice(), want_hash.as_slice());

    let plan = recipe.plan_range(36, 18).expect("cross-boundary plan");
    assert_eq!(plan.len(), 3);
    assert_eq!(plan[1].blob_index, 1);
    assert_eq!(plan[1].length, 14);
    assert_eq!(raw_blobs[1], decode_hex(vector["member"]["exact_deflate_hex"].as_str().unwrap()));
}
