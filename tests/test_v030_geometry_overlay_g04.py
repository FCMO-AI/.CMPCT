from __future__ import annotations

import binascii

from experiments import entropygraph_v030_geometry_overlay_g04 as g04


def _raw_record(raw: bytes):
    """Create an authenticated uncompressed Mosaic physical record for focused transform tests."""
    return (
        g04.O.CODEC_RAW,
        len(raw),
        raw,
        binascii.crc32(raw) & 0xFFFFFFFF,
        g04.H(raw),
    )


def _hierarchy_candidate(raw: bytes, *, prefix_planes: bool):
    transformed = g04.HG.hierarchy_forward(
        raw,
        ord("\n"),
        ord(","),
        prefix_planes=prefix_planes,
    )
    compressed = g04.O.zc(transformed, 19)
    if len(compressed) < len(transformed):
        codec, payload = g04.O.CODEC_ZSTD, compressed
    else:
        codec, payload = g04.O.CODEC_RAW, transformed
    return {
        "kind": "hierarchical",
        "primary": ord("\n"),
        "secondary": ord(","),
        "prefix_planes": prefix_planes,
        "physical": transformed,
        "codec": codec,
        "payload": payload,
        "payload_bytes": len(payload),
        "saving_bytes": len(raw) - len(payload),
        "screened_candidates": 4,
        "exact_finalists": 2,
    }


def test_g04_overlay_can_select_hierarchical_prefix_planes(monkeypatch) -> None:
    raw = b"user-000001,region-us-east,metric-0000000001\n" * 800
    record = _raw_record(raw)

    # Keep the flat stage as an explicit incumbent.  The test isolates the integration law; flat Geometry's
    # own vectors live in test_v030_geometry_overlay.py and must not be duplicated here.
    def fake_flat(record_id, candidate, member_lengths):
        return candidate, None, {
            "record_id": record_id,
            "raw_bytes": len(raw),
            "baseline_payload_bytes": len(candidate[2]),
            "max_member_read_amplification": 1.0,
            "selected": "none",
            "payload_saving_bytes": 0,
        }

    hierarchy = _hierarchy_candidate(raw, prefix_planes=True)
    assert hierarchy["payload_bytes"] < len(record[2]) - g04.HG.MIN_PAYLOAD_SAVING
    monkeypatch.setattr(g04.O, "_audition_record", fake_flat)
    monkeypatch.setattr(g04.HG, "audition", lambda candidate: hierarchy)

    chosen, descriptor, stats = g04._audition_record(7, record, [len(raw)])
    assert descriptor == ["hierarchical", ord("\n"), ord(","), 1, len(raw)]
    assert stats["selected"] == "hierarchical-prefix"
    assert stats["hierarchical_incremental_saving_bytes"] > 0

    codec, usize, payload, crc, logical_sha = chosen
    if codec == g04.O.CODEC_ZSTD:
        physical = g04.O.zd(payload, usize)
    else:
        physical = payload
    assert physical[:4] == g04.HG.MAGIC_PREFIX
    restored = g04.HG.hierarchy_inverse(physical, len(raw))
    assert restored == raw
    assert (binascii.crc32(restored) & 0xFFFFFFFF) == crc
    assert g04.H(restored) == logical_sha


def test_g04_hierarchy_cannot_displace_smaller_flat_incumbent(monkeypatch) -> None:
    raw = b"user-000001,region-us-east,metric-0000000001\n" * 800
    record = _raw_record(raw)
    hierarchy = _hierarchy_candidate(raw, prefix_planes=False)

    flat_payload = b"f" * max(1, hierarchy["payload_bytes"] - 1)
    flat_record = (
        g04.O.CODEC_RAW,
        len(flat_payload),
        flat_payload,
        record[3],
        record[4],
    )
    flat_descriptor = ["lane", 4, len(raw)]

    def fake_flat(record_id, candidate, member_lengths):
        return flat_record, flat_descriptor, {
            "record_id": record_id,
            "raw_bytes": len(raw),
            "baseline_payload_bytes": len(candidate[2]),
            "max_member_read_amplification": 1.0,
            "selected": "lane",
            "payload_saving_bytes": len(candidate[2]) - len(flat_payload),
        }

    monkeypatch.setattr(g04.O, "_audition_record", fake_flat)
    monkeypatch.setattr(g04.HG, "audition", lambda candidate: hierarchy)
    chosen, descriptor, stats = g04._audition_record(0, record, [len(raw)])
    assert chosen == flat_record
    assert descriptor == flat_descriptor
    assert stats["selected"] == "lane"


def test_g04_overlay_preserves_eight_x_locality_rejection(monkeypatch) -> None:
    raw = b"field-a,field-b,field-c\n" * 1000
    record = _raw_record(raw)
    called = {"hierarchy": False}

    def fake_flat(record_id, candidate, member_lengths):
        return candidate, None, {
            "record_id": record_id,
            "raw_bytes": len(raw),
            "baseline_payload_bytes": len(candidate[2]),
            "max_member_read_amplification": g04.MAX_MEMBER_READ_AMP + 0.01,
            "selected": "none",
            "payload_saving_bytes": 0,
        }

    def fake_hierarchy(candidate):
        called["hierarchy"] = True
        raise AssertionError("hierarchy must not run after locality rejection")

    monkeypatch.setattr(g04.O, "_audition_record", fake_flat)
    monkeypatch.setattr(g04.HG, "audition", fake_hierarchy)
    chosen, descriptor, stats = g04._audition_record(0, record, [1])
    assert chosen == record
    assert descriptor is None
    assert not called["hierarchy"]
    assert stats["max_member_read_amplification"] > g04.MAX_MEMBER_READ_AMP


def test_g04_codec_identity_is_explicit() -> None:
    # Footnote: a cross-module codec-number drift would produce a syntactically valid archive that the wrong
    # physical decoder interprets differently.  The integration layer treats that as an import-time contract.
    g04._assert_codec_identity()
