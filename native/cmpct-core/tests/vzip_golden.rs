#[path = "../src/vzip.rs"]
mod vzip;

use rmpv::Value;
use sha2::{Digest, Sha256};
use std::io::Cursor;
use vzip::{parse_stored_recipe, ProjectionSegment, VirtualZipError, VirtualZipRecipe};

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
    assert_eq!(bytes.len() % 4, 0, "fixed fixture must use padded base64");
    let mut out = Vec::with_capacity(bytes.len() / 4 * 3);
    for block in bytes.chunks_exact(4) {
        let a = value(block[0]).expect("base64 digit") as u32;
        let b = value(block[1]).expect("base64 digit") as u32;
        let c = if block[2] == b'=' {
            0
        } else {
            value(block[2]).expect("base64 digit") as u32
        };
        let d = if block[3] == b'=' {
            0
        } else {
            value(block[3]).expect("base64 digit") as u32
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

fn decode_hex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|index| u8::from_str_radix(&input[index..index + 2], 16).expect("hex byte"))
        .collect()
}

fn fixture() -> (serde_json::Value, Vec<u8>, Value, usize) {
    let fixture: serde_json::Value = serde_json::from_str(include_str!(
        "../../../tests/conformance/v24-virtual-zip.json"
    ))
    .expect("virtual ZIP fixture JSON");
    let vector = &fixture["vector"];
    let archive = decode_base64(vector["archive_base64"].as_str().expect("archive base64"));
    assert_eq!(&archive[..8], b"CMPCT24\0");
    let compressed_len = u64::from_le_bytes(archive[12..20].try_into().unwrap()) as usize;
    let index_bytes = zstd::stream::decode_all(Cursor::new(
        &archive[HEADER_SIZE..HEADER_SIZE + compressed_len],
    ))
    .expect("zstd primary index");
    let mut cursor = Cursor::new(index_bytes.as_slice());
    let index = rmpv::decode::read_value(&mut cursor).expect("MessagePack primary index");
    (fixture, archive, index, compressed_len)
}

fn raw_blobs(archive: &[u8], index: &Value, compressed_len: usize) -> Vec<Vec<u8>> {
    let data_base = HEADER_SIZE + compressed_len;
    map_field(index, "blobs")
        .as_array()
        .expect("blob rows")
        .iter()
        .map(|value| {
            let row = value.as_array().expect("blob row");
            let offset = row[0].as_u64().expect("blob offset") as usize;
            let logical_len = row[1].as_u64().expect("blob size") as usize;
            let compressed_len = row[2].as_u64().expect("blob compressed size") as usize;
            let codec = row[3].as_u64().expect("blob codec");
            let meta_len = row[4].as_u64().expect("blob metadata length") as usize;
            assert_eq!(codec, 0, "this first fixed S_VZIP vector uses RAW blobs");
            assert_eq!(compressed_len, logical_len);
            let header = data_base + offset;
            assert_eq!(&archive[header..header + 4], b"CMA4");
            let payload = header + BLOB_HEADER_SIZE + meta_len;
            archive[payload..payload + logical_len].to_vec()
        })
        .collect()
}

fn recipe_parts(index: &Value) -> (&Value, Vec<u64>, u64) {
    let files = map_field(index, "files").as_array().expect("file rows");
    let file = files[0].as_array().expect("file row");
    let logical_size = file[4].as_u64().expect("logical size");
    let storage = file[6].as_array().expect("storage row");
    assert_eq!(storage[0].as_u64(), Some(2), "S_VZIP storage kind");
    let recipe_index = storage[1].as_u64().expect("recipe index") as usize;
    let recipes = map_field(index, "recipes").as_array().expect("recipe rows");
    let blob_sizes: Vec<u64> = map_field(index, "blobs")
        .as_array()
        .expect("blob rows")
        .iter()
        .map(|value| value.as_array().unwrap()[1].as_u64().unwrap())
        .collect();
    (&recipes[recipe_index], blob_sizes, logical_size)
}

fn recipe_from_index(index: &Value) -> VirtualZipRecipe {
    let (recipe, blob_sizes, logical_size) = recipe_parts(index);
    parse_stored_recipe(recipe, &blob_sizes, logical_size)
        .expect("fixed stored-payload virtual ZIP recipe")
}

fn execute_plan(recipe: &VirtualZipRecipe, blobs: &[Vec<u8>], start: u64, length: u64) -> Vec<u8> {
    let mut out = vec![0u8; length as usize];
    for ProjectionSegment {
        blob_index,
        blob_offset,
        output_offset,
        length,
    } in recipe.plan_range(start, length).expect("range plan")
    {
        let src_start = blob_offset as usize;
        let src_end = src_start + length as usize;
        let dst_start = output_offset as usize;
        let dst_end = dst_start + length as usize;
        out[dst_start..dst_end].copy_from_slice(&blobs[blob_index][src_start..src_end]);
    }
    out
}

#[test]
fn fixed_revision24_stored_virtual_zip_projects_exact_bytes() {
    let (fixture, archive, index, compressed_len) = fixture();
    let vector = &fixture["vector"];
    let recipe = recipe_from_index(&index);
    let blobs = raw_blobs(&archive, &index, compressed_len);

    assert_eq!(
        recipe.skeleton_blob,
        vector["recipe"]["skeleton_blob"].as_u64().unwrap() as usize
    );
    assert_eq!(recipe.literal_lengths, vec![39, 77]);
    assert_eq!(recipe.payloads.len(), 1);
    assert_eq!(recipe.logical_size, 128);

    let rebuilt = execute_plan(&recipe, &blobs, 0, recipe.logical_size);
    let want_hash = decode_hex(vector["logical_sha256"].as_str().unwrap());
    assert_eq!(Sha256::digest(&rebuilt).as_slice(), want_hash.as_slice());
    assert_eq!(Sha256::digest(&rebuilt).as_slice(), recipe.logical_sha256);
    assert_eq!(&rebuilt[..4], b"PK\x03\x04");
    assert!(rebuilt.windows(9).any(|window| window == b"hello.txt"));
    assert!(rebuilt.windows(4).any(|window| window == b"PK\x05\x06"));

    for range in vector["ranges"].as_array().unwrap() {
        let offset = range["offset"].as_u64().unwrap();
        let length = range["length"].as_u64().unwrap();
        let want = decode_hex(range["hex"].as_str().unwrap());
        assert_eq!(execute_plan(&recipe, &blobs, offset, length), want);
    }
}

#[test]
fn selective_projection_touches_only_intersecting_recipe_segments() {
    let (_, _, index, _) = fixture();
    let recipe = recipe_from_index(&index);

    // Offset 36 crosses the last three bytes of the first skeleton literal, the complete 12-byte
    // stored payload, and one byte of the trailing skeleton. A native handler therefore needs three
    // small blob reads rather than materializing the 128-byte nested ZIP.
    let plan = recipe.plan_range(36, 16).expect("cross-boundary plan");
    assert_eq!(plan.len(), 3);
    assert_eq!(plan[0].blob_index, recipe.skeleton_blob);
    assert_eq!(plan[0].length, 3);
    assert_eq!(plan[1].blob_index, recipe.payloads[0].blob_index);
    assert_eq!(plan[1].length, 12);
    assert_eq!(plan[2].blob_index, recipe.skeleton_blob);
    assert_eq!(plan[2].length, 1);

    let tail_only = recipe.plan_range(52, 20).expect("tail literal plan");
    assert_eq!(tail_only.len(), 1);
    assert_eq!(tail_only[0].blob_index, recipe.skeleton_blob);
    assert_eq!(tail_only[0].length, 20);
    assert!(recipe.plan_range(127, 2).is_err());
}

#[test]
fn malformed_recipe_accounting_and_ungated_deflate_fail_closed() {
    let (_, _, index, _) = fixture();
    let (recipe, blob_sizes, logical_size) = recipe_parts(&index);

    let mut bad_literals = recipe.clone();
    let row = bad_literals.as_array_mut().expect("recipe row");
    row[1] = Value::Array(vec![Value::from(38u64), Value::from(77u64)]);
    assert!(matches!(
        parse_stored_recipe(&bad_literals, &blob_sizes, logical_size),
        Err(VirtualZipError::Schema(_))
    ));

    let mut deflate = recipe.clone();
    let row = deflate.as_array_mut().expect("recipe row");
    let payloads = row[2].as_array_mut().expect("payload rows");
    let payload = payloads[0].as_array_mut().expect("payload row");
    payload[1] = Value::from(8u64);
    assert_eq!(
        parse_stored_recipe(&deflate, &blob_sizes, logical_size),
        Err(VirtualZipError::UnsupportedPayload)
    );
}
