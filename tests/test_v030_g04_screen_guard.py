from __future__ import annotations

from experiments import entropygraph_v030_hierarchical_geometry as HG


def _install_one_pair(monkeypatch):
    monkeypatch.setattr(HG, "primary_candidates", lambda raw: [1])
    monkeypatch.setattr(HG, "secondary_candidates", lambda rows, primary: [2])
    monkeypatch.setattr(
        HG,
        "hierarchy_forward",
        lambda raw, primary, secondary, *, prefix_planes=False: b"T" + raw[1:],
    )
    monkeypatch.setattr(HG, "hierarchy_inverse", lambda transformed, logical_size: b"R" * logical_size)


def test_zero_headroom_screen_skips_exact_finalists(monkeypatch):
    raw = b"R" * HG.MIN_NODE_BYTES
    _install_one_pair(monkeypatch)
    exact_calls = []

    def exact(value):
        exact_calls.append(value)
        return HG.G.CODEC_ZSTD, b"x" * 100

    monkeypatch.setattr(HG.G, "_compress_physical", exact)
    monkeypatch.setattr(HG, "_compressed_size", lambda value, level: 100)

    got = HG.audition(raw)
    assert got["kind"] == "direct"
    assert got["screened_candidates"] == 2
    assert got["exact_finalists"] == 0
    assert exact_calls == [raw]


def test_positive_screen_still_prices_exact_finalists(monkeypatch):
    raw = b"R" * HG.MIN_NODE_BYTES
    _install_one_pair(monkeypatch)
    exact_calls = []

    def exact(value):
        exact_calls.append(value)
        return HG.G.CODEC_ZSTD, b"x" * (80 if value.startswith(b"T") else 200)

    monkeypatch.setattr(HG.G, "_compress_physical", exact)
    monkeypatch.setattr(HG, "_compressed_size", lambda value, level: 90 if value.startswith(b"T") else 100)

    got = HG.audition(raw)
    assert got["kind"] == "hierarchical"
    assert got["screened_candidates"] == 2
    assert got["exact_finalists"] == 2
    assert len(exact_calls) == 3


def test_no_primary_candidates_preserve_zero_screen_compression_fast_path(monkeypatch):
    raw = b"R" * HG.MIN_NODE_BYTES
    monkeypatch.setattr(HG, "primary_candidates", lambda value: [])
    monkeypatch.setattr(
        HG,
        "_compressed_size",
        lambda value, level: (_ for _ in ()).throw(AssertionError("unexpected screen compression")),
    )
    got = HG.audition(raw)
    assert got["kind"] == "direct"
    assert got["screened_candidates"] == 0
    assert got["exact_finalists"] == 0
