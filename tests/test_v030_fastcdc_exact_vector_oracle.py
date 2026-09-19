from __future__ import annotations

import random

import pytest

from benchmarks.v030_fastcdc_exact_vector_oracle import vector_fastcdc
from cmpct.resemblance import fastcdc


PARAMS = [
    (16 * 1024, 64 * 1024, 256 * 1024),
    (32 * 1024, 128 * 1024, 512 * 1024),
    (4 * 1024, 16 * 1024, 64 * 1024),
]


def _assert_same(data: bytes, params: tuple[int, int, int]) -> None:
    minimum, average, maximum = params
    expected = fastcdc(data, min_size=minimum, avg_size=average, max_size=maximum)
    actual, scratch = vector_fastcdc(data, min_size=minimum, avg_size=average, max_size=maximum)
    assert actual == expected
    assert scratch >= 0


@pytest.mark.parametrize("params", PARAMS)
def test_vector_fastcdc_matches_scalar_on_boundary_shapes(params: tuple[int, int, int]) -> None:
    minimum, average, maximum = params
    cases = [
        b"",
        b"x",
        b"x" * (minimum - 1),
        b"x" * minimum,
        b"x" * (minimum + 1),
        b"x" * maximum,
        b"x" * (maximum + 1),
        bytes(range(256)) * max(1, (2 * maximum) // 256),
        bytes(3 * maximum),
    ]
    for data in cases:
        _assert_same(data, params)


@pytest.mark.parametrize("params", PARAMS)
def test_vector_fastcdc_matches_scalar_on_seeded_random_bytes(params: tuple[int, int, int]) -> None:
    rng = random.Random(0xC0DEC7)
    _minimum, _average, maximum = params
    for size in (63, 64, 65, 4095, 4096, maximum // 2, maximum, maximum + 137, 3 * maximum + 19):
        data = rng.randbytes(size)
        _assert_same(data, params)


def test_vector_fastcdc_rejects_invalid_bounds_like_scalar() -> None:
    for kwargs in (
        dict(min_size=0, avg_size=1, max_size=2),
        dict(min_size=4, avg_size=3, max_size=5),
        dict(min_size=4, avg_size=6, max_size=5),
    ):
        with pytest.raises(ValueError):
            fastcdc(b"payload", **kwargs)
        with pytest.raises(ValueError):
            vector_fastcdc(b"payload", **kwargs)
