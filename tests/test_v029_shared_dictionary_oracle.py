from __future__ import annotations

"""Focused invariants for the detached shared-dictionary record-context oracle."""

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "entropygraph_v029_shared_dictionary_oracle.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_shared_dictionary_oracle_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_libzstd_dictionary_roundtrip_is_exact() -> None:
    mod = _module()
    api = mod.ZstdDictionaryAPI()
    dictionary = (b"common-prefix:alpha-beta-gamma;" * 256)[:8192]
    raw = (b"common-prefix:alpha-beta-gamma;record=42;payload=hello-world\n" * 256)
    payload = api.compress_verify(raw, dictionary, 9)
    assert payload
    assert len(payload) < len(raw)


def test_node_record_dependencies_remain_depth_one() -> None:
    mod = _module()
    meta = {
        "nodes": [
            ["direct", 10, 0, 1000, b"a" * 32],
            ["direct", 11, 0, 1000, b"b" * 32],
            ["delta", 0, 20, 1000, b"c" * 32],
            ["delta_pack", 1, 21, 0, 10, 1000, b"d" * 32],
            ["mosaic", [0, 1], 22, 1000, b"e" * 32],
            ["pack_mosaic", 23, 0, 10, [0, 1], 1000, b"f" * 32],
        ]
    }
    assert mod._node_record_dependencies(meta, 0) == {10}
    assert mod._node_record_dependencies(meta, 2) == {10, 20}
    assert mod._node_record_dependencies(meta, 3) == {11, 21}
    assert mod._node_record_dependencies(meta, 4) == {10, 11, 22}
    assert mod._node_record_dependencies(meta, 5) == {10, 11, 23}


def test_locality_filter_rejects_dictionary_too_large_for_cold_target() -> None:
    mod = _module()
    meta = {
        "nodes": [
            ["direct", 0, 0, 4096, b"a" * 32],
            ["direct", 1, 0, 256 * 1024, b"b" * 32],
        ]
    }
    records = [
        {"record_id": 0, "logical_bytes": 4096},
        {"record_id": 1, "logical_bytes": 256 * 1024},
    ]
    allowed, locality = mod._locality_filter(meta, records, {0, 1}, 16 * 1024)
    assert 0 not in allowed  # 16 KiB dictionary alone is 4x a 4 KiB cold target.
    assert 1 in allowed
    assert locality["max_additional_dictionary_read_amp"] <= mod.MAX_ADDITIONAL_DICT_AMP


def test_training_samples_are_bounded_and_deterministic() -> None:
    mod = _module()
    raw = bytes(range(256)) * 1024
    records = [{"record_id": 7, "codec": mod.CODEC_RAW, "raw": raw}]
    samples = mod._training_samples(records, {7})
    assert len(samples) == 2
    assert all(len(sample) == mod.TRAIN_SAMPLE_SLICE for sample in samples)
    assert samples[0] == raw[:mod.TRAIN_SAMPLE_SLICE]
    assert samples[1] == raw[-mod.TRAIN_SAMPLE_SLICE:]
