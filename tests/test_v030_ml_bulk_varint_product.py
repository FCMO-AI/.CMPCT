import pytest

from experiments import entropygraph_v030_verified_restore as R


def _descriptor(raw: bytes):
    encoded = R.C.SHARED.G.O.delimiter_forward(raw)
    assert encoded is not None
    return encoded


def test_bulk_one_byte_table_matches_historical_inverse() -> None:
    raw = b"aa,b,ccc,,dddd,e"
    encoded = _descriptor(raw)
    assert R.release_single_buffer_delimiter_inverse(encoded, len(raw)) == raw
    assert R._PRE_RELEASE_DELIMITER_INVERSE(encoded, len(raw)) == raw


def test_multibyte_lengths_fall_back_without_grammar_change() -> None:
    raw = (b"a" * 130) + b"," + (b"b" * 257) + b",tail"
    encoded = _descriptor(raw)
    assert R.release_single_buffer_delimiter_inverse(encoded, len(raw)) == raw
    assert R._PRE_RELEASE_DELIMITER_INVERSE(encoded, len(raw)) == raw


def test_truncated_descriptor_rejection_matches_historical_reader() -> None:
    raw = b"alpha,beta,gamma,delta"
    encoded = _descriptor(raw)
    for cut in (1, 2, 3, max(1, len(encoded) // 2)):
        damaged = encoded[:-cut]
        with pytest.raises(RuntimeError):
            R.release_single_buffer_delimiter_inverse(damaged, len(raw))
        with pytest.raises(RuntimeError):
            R._PRE_RELEASE_DELIMITER_INVERSE(damaged, len(raw))
