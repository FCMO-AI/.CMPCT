from __future__ import annotations

import random

from experiments import entropygraph_v030_hierarchical_geometry as HG
from experiments import v030_hierarchical_bounded_screen_probe as PROBE


def _known_hierarchical_win() -> bytes:
    rows = []
    for index in range(3_000):
        rows.append(
            f"step={index} account=A{index % 19000:05d} region={['n','s','e','w'][index % 4]} "
            f"product=P{(index * 7) % 1200:04d} qty={1 + index % 13} value={2.75 + (index % 191) * .91:.2f}"
        )
    return ("\n".join(rows) + "\n").encode()


def _cases() -> list[bytes]:
    rng = random.Random(0xC0A0C7)
    # Cover direct-path boundary, incompressible-like control, delimiter-rich families, and the incumbent's
    # independent golden workload that is known to select a real hierarchical transform.
    below = bytes(rng.randrange(256) for _ in range(HG.MIN_NODE_BYTES - 1))
    boundary = bytes(rng.randrange(256) for _ in range(HG.MIN_NODE_BYTES))
    randomish = bytes(rng.randrange(256) for _ in range(16 * 1024))
    rows = [f"{i:05d}|alpha-{i % 17:02d}|beta-{i % 7:02d}|payload-{i % 31:02d}".encode() for i in range(4096)]
    shifted = b"\n".join(rows)
    semicolon = b";".join(
        f"k={i % 97:02d},v={i:06d},group={i % 13:02d},tail={i % 5}".encode() for i in range(4096)
    )
    return [b"small-control", below, boundary, randomish, shifted, semicolon, _known_hierarchical_win()]


def test_bounded_screen_probe_is_exact_audition_equivalent() -> None:
    for raw in _cases():
        incumbent = HG.audition(raw)
        bounded = PROBE.audition(raw)
        assert bounded == incumbent


def test_bounded_screen_probe_preserves_resource_counts() -> None:
    raw = _cases()[-2]
    incumbent = HG.audition(raw)
    bounded = PROBE.audition(raw)
    assert bounded["screened_candidates"] == incumbent["screened_candidates"]
    assert bounded["exact_finalists"] == incumbent["exact_finalists"]


def test_bounded_screen_probe_preserves_known_hierarchical_winner() -> None:
    raw = _known_hierarchical_win()
    incumbent = HG.audition(raw)
    bounded = PROBE.audition(raw)
    assert incumbent["kind"] == "hierarchical"
    assert bounded == incumbent
