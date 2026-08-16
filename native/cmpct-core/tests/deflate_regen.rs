#[path = "../src/deflate_regen.rs"]
mod deflate_regen;

fn decode_hex(input: &str) -> Vec<u8> {
    assert_eq!(input.len() % 2, 0);
    (0..input.len())
        .step_by(2)
        .map(|index| u8::from_str_radix(&input[index..index + 2], 16).expect("hex byte"))
        .collect()
}

#[cfg(unix)]
#[test]
fn fixed_mode2_oracle_regenerates_python_zlib_stream_byte_exactly() {
    let fixture: serde_json::Value = serde_json::from_str(include_str!(
        "../../../tests/conformance/v24-virtual-zip-deflate-mode2.json"
    ))
    .expect("mode-2 fixture JSON");
    let vector = &fixture["vector"];
    let member = &vector["member"];
    let recipe = &vector["recipe"];

    let raw = b"hello-cmpct\n";
    let exact = decode_hex(member["exact_deflate_hex"].as_str().unwrap());
    let level = recipe["zlib_level"].as_u64().unwrap() as u8;

    let mut whole = vec![0u8; exact.len()];
    deflate_regen::exact_range(
        raw,
        level,
        exact.len() as u64,
        0,
        &mut whole,
        1024 * 1024,
    )
    .expect("stock zlib regeneration");
    assert_eq!(whole, exact);

    // Footnote: virtual archive clients overwhelmingly issue selective reads. Proving a non-zero
    // range against the same fixed RFC-1951 oracle prevents an implementation that only happens to
    // reproduce the whole stream when copied from byte zero.
    let mut range = vec![0u8; 7];
    deflate_regen::exact_range(
        raw,
        level,
        exact.len() as u64,
        3,
        &mut range,
        1024 * 1024,
    )
    .expect("mode-2 selective range");
    assert_eq!(range, exact[3..10]);

    assert_eq!(
        deflate_regen::exact_range(
            raw,
            level,
            exact.len() as u64 + 1,
            0,
            &mut whole,
            1024 * 1024,
        ),
        Err(deflate_regen::DeflateRegenError::StreamLength)
    );
    assert_eq!(
        deflate_regen::exact_range(raw, 10, exact.len() as u64, 0, &mut whole, 1024 * 1024),
        Err(deflate_regen::DeflateRegenError::Level)
    );
}
