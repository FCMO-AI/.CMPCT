from __future__ import annotations

from experiments import entropygraph_v030_hierarchical_geometry as HG
from experiments import v030_hierarchical_bounded_screen_probe as PROBE


def _cases() -> list[bytes]:
    # Structured enough to exercise the hierarchical screen, plus a small direct-path control.
    rows = [f"{i:05d}|alpha-{i % 17:02d}|beta-{i % 7:02d}|payload-{i % 31:02d}".encode() for i in range(4096)]
    shifted = b"\n".join(rows)
    semicolon = b";".join(
        f"k={i % 97:02d},v={i:06d},group={i % 13:02d},tail={i % 5}".encode() for i in range(4096)
    )
    return [b"small-control", shifted, semicolon]


def test_bounded_screen_probe_is_exact_audition_equivalent() -> None:
    for raw in _cases():
        incumbent = HG.audition(raw)
        bounded = PROBE.audition(raw)
        assert bounded == incumbent


def test_bounded_screen_probe_preserves_resource_counts() -> None:
    raw = _cases()[1]
    incumbent = HG.audition(raw)
    bounded = PROBE.audition(raw)
    assert bounded["screened_candidates"] == incumbent["screened_candidates"]
    assert bounded["exact_finalists"] == incumbent["exact_finalists"]
