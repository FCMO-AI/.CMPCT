from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_gir_rehab as rehab


def _rows(count: int) -> bytes:
    return (
        "\n".join(
            f"2026-08-17T14:{index % 60:02d}:00Z level=INFO worker={index % 32:02d} "
            f"tenant=T{index % 380:04d} route=/api/jobs latency={8 + index % 820} request={index:012x}"
            for index in range(count)
        )
        + "\n"
    ).encode()


def test_small_node_pays_raw_direct_floor_once(monkeypatch) -> None:
    raw = (b"opaque-rehab-probe-" * 200) + bytes(range(256))
    assert len(raw) < rehab.HG.MIN_NODE_BYTES

    original = rehab.G._compress_physical
    calls: list[bytes] = []

    def counted(candidate: bytes):
        calls.append(candidate)
        return original(candidate)

    monkeypatch.setattr(rehab.G, "_compress_physical", counted)
    chosen = rehab._encode_node(raw)

    assert chosen["kind"] == "direct"
    assert calls == [raw]


def test_rehab_and_legacy_encoder_emit_identical_complete_gir_bytes(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "structured.log").write_bytes(_rows(4_000))
    (source / "opaque.bin").write_bytes(bytes((index * 73 + 19) & 255 for index in range(90_000)))

    legacy_archive = tmp_path / "legacy.cmpct"
    with monkeypatch.context() as scoped:
        scoped.setattr(rehab.gir, "_encode_node", rehab.LEGACY_ENCODE_NODE)
        legacy_stats = rehab.gir._build_gir(source, legacy_archive)

    optimized_archive = tmp_path / "optimized.cmpct"
    optimized_stats = rehab._build_gir(source, optimized_archive)

    # Footnote: byte equality is the core rehabilitation contract.  A timing optimization that perturbs one
    # transform choice, descriptor, metadata byte, payload frame or recovery copy is not admissible here.
    assert optimized_archive.read_bytes() == legacy_archive.read_bytes()
    assert optimized_stats["graph_bytes"] == legacy_stats["graph_bytes"]
    assert optimized_stats["node_kind_counts"] == legacy_stats["node_kind_counts"]
    assert optimized_stats["transform_payload_saving_bytes"] == legacy_stats["transform_payload_saving_bytes"]
    assert rehab.strong_verify(optimized_archive)["ok"] is True


def test_reused_direct_floor_preserves_hierarchical_saving_accounting() -> None:
    raw = _rows(2_500)
    incumbent = rehab.G._encode_node(raw)
    direct_bytes = int(incumbent["payload_bytes"]) + int(incumbent.get("saving", 0))
    optimized = rehab._audition_hierarchy_with_direct_bytes(raw, direct_bytes)
    legacy = rehab.HG.audition(raw)

    assert optimized["kind"] == legacy["kind"]
    assert optimized["payload_bytes"] == legacy["payload_bytes"]
    assert optimized["saving_bytes"] == legacy["saving_bytes"]
    assert optimized["primary"] == legacy["primary"]
    assert optimized["secondary"] == legacy["secondary"]
    assert optimized["prefix_planes"] == legacy["prefix_planes"]
