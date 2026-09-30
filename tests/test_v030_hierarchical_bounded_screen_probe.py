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
    below = bytes(rng.randrange(256) for _ in range(HG.MIN_NODE_BYTES - 1))
    boundary = bytes(rng.randrange(256) for _ in range(HG.MIN_NODE_BYTES))
    randomish = bytes(rng.randrange(256) for _ in range(16 * 1024))
    rows = [f"{i:05d}|alpha-{i % 17:02d}|beta-{i % 7:02d}|payload-{i % 31:02d}".encode() for i in range(4096)]
    shifted = b"\n".join(rows)
    semicolon = b";".join(
        f"k={i % 97:02d},v={i:06d},group={i % 13:02d},tail={i % 5}".encode() for i in range(4096)
    )
    return [b"small-control", below, boundary, randomish, shifted, semicolon, _known_hierarchical_win()]


def _semantic_result(result: dict) -> dict:
    # The productized zero-threshold discriminator intentionally changes exact-finalist work accounting
    # when the level-6 screen rejects a transform. Compare the selected representation and stored bytes,
    # not the amount of speculative work used to reach that decision.
    return {key: value for key, value in result.items() if key != "exact_finalists"}


def test_productized_bounded_screen_preserves_probe_selected_representation() -> None:
    # The older bounded-retention probe is an independent control for candidate construction/tie semantics.
    # Productization may price fewer exact finalists, but must not alter the selected representation here.
    for raw in _cases():
        assert _semantic_result(HG.audition(raw)) == _semantic_result(PROBE.audition(raw))


def test_productized_bounded_screen_never_adds_exact_finalist_work() -> None:
    for raw in _cases():
        shipping = HG.audition(raw)
        probe = PROBE.audition(raw)
        assert shipping["screened_candidates"] == probe["screened_candidates"]
        assert shipping["exact_finalists"] <= probe["exact_finalists"]


def test_productized_bounded_screen_preserves_known_hierarchical_winner() -> None:
    raw = _known_hierarchical_win()
    shipping = HG.audition(raw)
    probe = PROBE.audition(raw)
    assert shipping["kind"] == "hierarchical"
    assert shipping == probe
