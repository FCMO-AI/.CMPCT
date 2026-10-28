from __future__ import annotations

import pytest

from cmpct.resemblance import (
    choose_central_bases,
    delta_decode,
    delta_encode,
    fastcdc,
    lsh_candidates,
    similarity_sketch,
)


def _prefix_offsets(lengths):
    offset = 0
    for length in lengths:
        yield offset
        offset += length


def test_fastcdc_is_deterministic_bounded_and_complete():
    data = (b"alpha-beta-gamma\n" * 20000) + bytes(range(256)) * 200
    a = fastcdc(data, min_size=4096, avg_size=16384, max_size=65536)
    b = fastcdc(data, min_size=4096, avg_size=16384, max_size=65536)
    assert a == b
    assert sum(c.length for c in a) == len(data)
    assert all(0 < c.length <= 65536 for c in a)
    assert [c.offset for c in a] == list(_prefix_offsets([c.length for c in a]))


def test_delta_survives_insertions_and_rejects_bad_references():
    base = b"A" * 9000 + b"B" * 10000 + b"C" * 11000
    target = base[:12345] + b"INSERTED-CONTENT" * 7 + base[12345:-91] + b"tail-change"
    encoded = delta_encode(base, target)
    assert delta_decode(base, encoded.payload, expected_size=len(target)) == target
    assert encoded.stats.copied_bytes > len(target) * 0.8
    # Footnote: malformed COPY references fail closed instead of relying on Python's forgiving slicing.
    with pytest.raises(ValueError):
        delta_decode(b"x", b"\x01\x7f\x7f", max_output=1024)


def test_lsh_is_bounded_and_only_a_candidate_oracle():
    base = b"header\n" + b"same semantic line\n" * 300 + b"footer\n"
    near = base.replace(b"semantic", b"SEMANTIC", 8) + b"new trailer"
    far = bytes((i * 73 + 19) & 255 for i in range(len(base)))
    sketches = [similarity_sketch(x) for x in (base, near, far)]
    edges = lsh_candidates(sketches, max_bucket=4, max_candidates=2)
    # Footnote: similarity never grants storage by itself. The close object only becomes a candidate;
    # actual acceptance is based on measured delta bytes in the research encoder.
    assert any(edge.target == 1 and edge.base == 0 for edge in edges)
    assert all(edge.target > edge.base for edge in edges)
    assert len([edge for edge in edges if edge.target == 2]) <= 2


def test_centrality_selection_never_creates_delta_chains():
    assignment = choose_central_bases(
        6,
        [
            (1, 0, 1000),
            (2, 0, 900),
            (3, 1, 5000),
            (4, 3, 800),
            (5, 0, 700),
        ],
    )
    assert all(base not in assignment for base in assignment.values())
    assert all(target != base for target, base in assignment.items())


def test_hostile_equal_sketch_population_has_bounded_fanout():
    sketch = similarity_sketch(b"x" * 8192)
    edges = lsh_candidates([sketch] * 500, max_bucket=7, max_candidates=3)
    per_target: dict[int, int] = {}
    for edge in edges:
        per_target[edge.target] = per_target.get(edge.target, 0) + 1
    assert max(per_target.values(), default=0) <= 3
