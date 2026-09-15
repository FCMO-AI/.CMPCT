from __future__ import annotations

import pytest

from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments.v030_g04_delimiter_inverse_ab import delimiter_inverse_banded


def _round_trip(raw: bytes, delimiter: int) -> None:
    encoded = G04.O.delimiter_forward(raw, delimiter)
    historical = G04.O.delimiter_inverse(encoded, len(raw))
    candidate = delimiter_inverse_banded(encoded, len(raw))
    assert historical == raw
    assert candidate == raw
    assert candidate == historical


@pytest.mark.parametrize(
    ("raw", "delimiter"),
    [
        (b"", 0),
        (b"single-member", 0),
        (b"a,b,c,d", ord(",")),
        (b",leading,,empty,trailing,", ord(",")),
        (b"x" * 4096 + b"|" + b"y" * 3 + b"|" + b"z" * 1024, ord("|")),
        (b"\x00".join(bytes((index,)) * (index % 17) for index in range(1, 128)), 0),
        (b"\xff".join(bytes((index % 251,)) * (1 + (index * 37) % 257) for index in range(512)), 255),
    ],
)
def test_banded_delimiter_inverse_matches_historical_oracle(raw: bytes, delimiter: int) -> None:
    _round_trip(raw, delimiter)


def test_banded_delimiter_inverse_handles_empty_segment_that_disables_dense_prefix() -> None:
    # Canonical bulk-v1 uses min(lengths) as its rectangular-prefix width. One empty member therefore makes the
    # whole payload fall back to byte-at-a-time Python loops. This shape is the causal performance target for the
    # banded inverse; exact bytes must remain identical to the historical oracle.
    raw = b"alpha\x00\x00" + b"beta" * 4096 + b"\x00gamma\x00"
    _round_trip(raw, 0)


def test_banded_delimiter_inverse_rejects_trailing_body() -> None:
    raw = b"a,b,c"
    encoded = G04.O.delimiter_forward(raw, ord(",")) + b"x"
    with pytest.raises(RuntimeError, match="body-size mismatch|trailing body"):
        delimiter_inverse_banded(encoded, len(raw))
