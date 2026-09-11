import random
import zlib

import pytest

from experiments.one.native_observe import observe_native
from experiments.one.observe import observe


def _assert_equal(data: bytes, **kwargs) -> None:
    expected = observe(data, **kwargs)
    actual = observe_native(data, **kwargs)
    assert actual.runs == expected.runs
    assert actual.reuse == expected.reuse
    assert actual.stats == expected.stats


def _structured(size: int) -> bytes:
    motif = b"ONE-law-surprise:" + bytes(range(32))
    out = bytearray()
    while len(out) < size:
        out.extend(motif * 3)
        out.extend(b"A" * 96)
        out.extend(motif)
        out.extend(b"BC" * 37)
    return bytes(out[:size])


def _random(size: int, seed: int = 0xC0A57) -> bytes:
    rng = random.Random(seed + size)
    return rng.randbytes(size)


def _compressed_like(size: int) -> bytes:
    seed = zlib.compress(_structured(max(size * 2, 1024)), level=9)
    return (seed * ((size + len(seed) - 1) // len(seed)))[:size]


def _long_runs(size: int) -> bytes:
    pattern = b"A" * 257 + b"B" * 64 + b"C" * 7 + b"D" * 129 + bytes(range(64))
    return (pattern * ((size + len(pattern) - 1) // len(pattern)))[:size]


def _near_repeats(size: int) -> bytes:
    chunks = []
    for i in range(max(1, (size + 63) // 64)):
        chunk = bytearray(b"near-repeat-pattern" * 4)
        chunk = chunk[:64]
        chunk[-1] ^= i & 0xFF
        chunks.append(bytes(chunk))
    return b"".join(chunks)[:size]


@pytest.mark.parametrize("size", [0, 1, 7, 8, 9, 63, 64, 65, 127, 128, 129, 4095, 4096, 4097])
def test_native_observer_tail_and_boundary_semantics(size: int) -> None:
    data = _structured(size)
    _assert_equal(data)


@pytest.mark.parametrize("builder", [_structured, _random, _compressed_like, _long_runs, _near_repeats])
@pytest.mark.parametrize("size", [64 << 10, 256 << 10])
def test_native_observer_family_semantics(builder, size: int) -> None:
    _assert_equal(builder(size))


def test_native_observer_bounded_index_exhaustion_matches_reference() -> None:
    data = _near_repeats(128 << 10)
    _assert_equal(data, max_index_entries=3)
    _assert_equal(data, max_index_entries=17)


def test_native_observer_seeded_parameter_fuzz_matches_reference() -> None:
    rng = random.Random(0x0B5E12E)
    for _ in range(96):
        size = rng.randrange(0, 2049)
        data = rng.randbytes(size)
        # Inject deterministic run/reuse structure into a subset of otherwise random
        # roots so the fuzz surface exercises both nomination and no-opportunity cases.
        if size >= 192 and rng.randrange(2):
            buf = bytearray(data)
            buf[32:96] = b"Q" * 64
            buf[128:192] = buf[0:64]
            data = bytes(buf)
        _assert_equal(
            data,
            min_run=rng.choice((2, 3, 8, 17, 64)),
            chunk_size=rng.choice((8, 16, 32, 64, 128)),
            max_index_entries=rng.choice((1, 2, 3, 7, 17, 257)),
        )


def test_native_observer_parameter_validation_matches_contract() -> None:
    with pytest.raises(TypeError):
        observe_native(bytearray(b"x"))  # type: ignore[arg-type]
    for kwargs in ({"min_run": 0}, {"chunk_size": 0}, {"max_index_entries": 0}):
        with pytest.raises(ValueError):
            observe_native(b"x", **kwargs)
