from __future__ import annotations

from experiments import entropygraph_v030_canonical_final as C


def test_parallel_overlay_preserves_deferred_verification_contract(monkeypatch, tmp_path):
    """Canonical scheduling may parallelize auditions, never move logical verify before byte/locality admission."""

    monkeypatch.setattr(
        C.SHARED.strict,
        "_read_source_records",
        lambda _path: ("test-source", None, {"meta": "kept"}, [b"record"]),
    )
    monkeypatch.setattr(C.SHARED.O, "_record_member_lengths", lambda _meta, _count: [1])
    monkeypatch.setattr(
        C.SHARED.G,
        "_audition_record",
        lambda record_id, record, users: (record, {"record_id": record_id}, {"selected": "none"}),
    )
    monkeypatch.setattr(
        C.SHARED.G,
        "_write_overlay",
        lambda meta, records, transforms, path: {
            "meta_raw_bytes": 1,
            "meta_comp_bytes": 1,
            "overlay_source_format": meta["overlay_source_format"],
        },
    )

    def forbidden_eager_verify(_path):
        raise AssertionError("parallel overlay wrapper must not verify before byte/locality admission")

    monkeypatch.setattr(C.SHARED.G, "strong_verify", forbidden_eager_verify)

    result = C._parallel_overlay_retained_graph(tmp_path / "graph", tmp_path / "overlay")

    assert result["source_format"] == "test-source"
    assert result["verified"] is None
    assert result["verification_state"] == "deferred-until-byte-and-locality-win"
    assert result["audition_workers"] == 1
    assert result["audition_scheduler"] == "bounded-ordered-thread-pool-v1"
    assert result["delimiter_transpose"] == "bulk-rectangular-prefix-v1"
