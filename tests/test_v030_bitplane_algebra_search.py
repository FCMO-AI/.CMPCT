from __future__ import annotations

from experiments import entropygraph_v030_bitplane_algebra as BPA
from experiments import entropygraph_v030_bitplane_algebra_safe as SAFE


def test_safe_search_thresholds_every_finalist_against_original_incumbent(monkeypatch) -> None:
    raw = b"x" * (16 * 1024)
    incumbent = b"i" * 1000
    monkeypatch.setattr(SAFE.G, "_encode_node", lambda _: {
        "payload": incumbent,
        "payload_bytes": len(incumbent),
        "physical": incumbent,
        "kind": "direct",
    })
    monkeypatch.setattr(BPA, "WORD_WIDTHS", (2,))
    monkeypatch.setattr(BPA, "PREDICTORS", ("first", "second"))
    monkeypatch.setattr(BPA, "rank_alignments", lambda _raw, _width: [0])
    monkeypatch.setattr(BPA, "_basis_options", lambda _bits: (("none", 0),))

    def fake_forward(_raw, _width, _alignment, predictor, _basis):
        # Both candidates clear the 64-byte threshold versus Geometry. The second is only five bytes better
        # than the first; an order-dependent implementation would wrongly reject it after choosing `first`.
        # Footnote: transformed mocks intentionally remain larger than the mocked compressed payloads.
        # Production BPA legitimately falls back to an uncompressed transform when compression expands it;
        # a one-byte mock would test that independent fallback law instead of the search-order invariant.
        marker = b"A" if predictor == "first" else b"B"
        return marker * 1200

    monkeypatch.setattr(BPA, "forward", fake_forward)
    monkeypatch.setattr(BPA, "inverse", lambda _encoded, _logical_size: raw[:_logical_size])
    monkeypatch.setattr(BPA, "_screen_size", lambda transformed: 1 if transformed[:1] == b"A" else 2)

    def fake_zc(transformed, _level):
        return b"1" * 900 if transformed[:1] == b"A" else b"2" * 895

    monkeypatch.setattr(SAFE.G, "zc", fake_zc)
    result = SAFE.audition(raw)
    assert result["kind"] == "bitplane-algebra"
    assert result["payload_bytes"] == 895
    assert result["saving_vs_incumbent_bytes"] == 105
    assert result["predictor"] == "second"
