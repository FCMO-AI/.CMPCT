#[path = "../src/vzip.rs"]
mod vzip;

use rmpv::Value;
use vzip::{parse_recipe, parse_recipe_with_physical_deflate, ProjectionSource, VirtualZipError};

#[test]
fn mode0_planner_marks_only_the_deflate_stream_as_physical() {
    // Mirrors the independently frozen mode-0 oracle: content blob 0 decodes to 12 logical bytes,
    // skeleton blob 1 contains 116 literal ZIP bytes, and the projected raw Deflate stream is 14 bytes.
    let recipe = Value::Array(vec![
        Value::from(1u64),
        Value::Array(vec![Value::from(39u64), Value::from(77u64)]),
        Value::Array(vec![Value::Array(vec![
            Value::from(0u64),
            Value::from(8u64),
            Value::from(0u64),
            Value::from(0u64),
            Value::from(14u64),
            Value::from(6u64),
        ])]),
        Value::Binary(vec![0u8; 32]),
        Value::from(130u64),
        Value::from(0u64),
    ]);
    let blob_sizes = [12u64, 116u64];

    // The production parser remains closed until archive dispatch can authenticate physical slices.
    assert_eq!(
        parse_recipe(&recipe, &blob_sizes, 130),
        Err(VirtualZipError::UnsupportedPayload)
    );

    let parsed = parse_recipe_with_physical_deflate(&recipe, &blob_sizes, 130)
        .expect("mode-0 planner gate");
    assert_eq!(parsed.payloads.len(), 1);
    assert_eq!(parsed.payloads[0].blob_index, 0);
    assert_eq!(parsed.payloads[0].logical_len, 14);
    assert_eq!(parsed.payloads[0].source, ProjectionSource::PhysicalDeflate);

    // 36..54 crosses 3 skeleton bytes, all 14 raw Deflate bytes, then 1 skeleton byte.
    let plan = parsed.plan_range(36, 18).expect("cross-boundary range");
    assert_eq!(plan.len(), 3);
    assert_eq!(plan[0].source, ProjectionSource::LogicalBlob);
    assert_eq!(plan[0].length, 3);
    assert_eq!(plan[1].source, ProjectionSource::PhysicalDeflate);
    assert_eq!(plan[1].blob_index, 0);
    assert_eq!(plan[1].blob_offset, 0);
    assert_eq!(plan[1].length, 14);
    assert_eq!(plan[2].source, ProjectionSource::LogicalBlob);
    assert_eq!(plan[2].length, 1);

    // A central-directory-only request must not touch the compressed payload at all.
    let tail = parsed.plan_range(53, 20).expect("tail-only range");
    assert_eq!(tail.len(), 1);
    assert_eq!(tail[0].source, ProjectionSource::LogicalBlob);
    assert_eq!(tail[0].blob_index, 1);
}
