from __future__ import annotations

import importlib.util
import lzma
from pathlib import Path
import sys


PATH = Path(__file__).resolve().parents[1] / "experiments" / "entropygraph_v029_lzma2_backend_oracle.py"
SPEC = importlib.util.spec_from_file_location("cmpct_test_v029_lzma2_backend", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def test_bounded_lzma2_roundtrip_is_exact() -> None:
    raw = (b"cmpct-reference-record\x00" * 8192) + bytes(range(256)) * 16
    payload, encode_s, decode_s = MOD._compress_verify(raw, 1 << 20)
    assert payload
    assert encode_s >= 0
    assert decode_s >= 0
    filters = [{"id": lzma.FILTER_LZMA2, "dict_size": 1 << 20, "preset": 6}]
    assert lzma.decompress(payload, format=lzma.FORMAT_RAW, filters=filters) == raw


def test_backend_oracle_policy_is_bounded_and_preregistered() -> None:
    assert MOD.DICT_SIZES == (1 << 20, 4 << 20, 8 << 20)
    assert MOD.MAX_DICT_BYTES == 8 << 20
    assert MOD.MIN_NET_SAVING == 128 * 1024
    assert MOD.MIN_IMPROVED_RECORDS == 4
    assert MOD.TRANSITION_METADATA_CHARGE > 0
