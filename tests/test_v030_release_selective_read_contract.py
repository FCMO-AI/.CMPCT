from __future__ import annotations

"""Fast policy tests for the canonical selective-read evidence harness."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from benchmarks import v030_perf_worker_canonical as W
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_release_selective_read_canonical as S


def test_selective_read_reuses_frozen_runtime_targets_and_locality_ceiling() -> None:
    assert S.MAX_MEMBER_READ_AMP == 8.0
    assert PERF.TARGETS == (
        ("resemblance_hostile_v1", "01_shifted_versions"),
        ("neutral_hostile_v1", "05_logs_and_telemetry"),
        ("neutral_hostile_v1", "09_ml_artifacts"),
    )
    assert S.OPERATION_ORDER == (("member", "extract"), ("extract", "member"))


def test_missing_locality_can_never_default_to_zero() -> None:
    with pytest.raises(RuntimeError, match="did not prove observed locality"):
        S._observed_amp({})
    with pytest.raises(RuntimeError, match="omitted max_member_read_amplification"):
        S._observed_amp({"locality_observed_from_actual_product_operation": True})
    with pytest.raises(RuntimeError, match="invalid locality amplification"):
        S._observed_amp(
            {
                "locality_observed_from_actual_product_operation": True,
                "max_member_read_amplification": 0.0,
            }
        )


def test_r24_fallback_is_observed_through_public_product_read_member(tmp_path: Path) -> None:
    payload = b"canonical-r24-member"
    calls = []

    class DummySession:
        pass

    class FakeCMPCT:
        def __init__(self, _archive):
            self.blobs = [[0, len(payload) * 2, 0, 0, 0]]
            self._observed = False

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

        def _blob(self, idx):
            self._observed = True
            return payload + payload

        def read(self, rel):
            calls.append(rel)
            return self._blob(0)[: len(payload)]

        def close(self):
            return None

    class FakeEngine:
        POLICY = SimpleNamespace(R=SimpleNamespace(_G04Session=DummySession, _PGSession=DummySession))
        CMPCT = FakeCMPCT

        def read_member(self, archive, rel):
            with self.CMPCT(archive) as reader:
                return bytes(reader.read(rel))

        def list_members(self, _archive):
            return [{"path": "payload.bin", "kind": "file", "size": len(payload)}]

    engine = FakeEngine()
    raw, stats = W._observed_product_member(engine, tmp_path / "fake.cmpct", "payload.bin")
    assert raw == payload
    assert calls == ["payload.bin"]
    assert stats["representation"] == "canonical-r24"
    assert stats["locality_observed_from_actual_product_operation"] is True
    assert stats["max_member_read_amplification"] == 2.0

    # Footnote: the fake engine deliberately exposes only the public product method. If the worker bypasses
    # ``read_member`` and benchmarks a research adapter, this test stops observing the call and fails.


def test_member_target_uses_public_regular_file_rows_and_ignores_aliases(tmp_path: Path) -> None:
    regular = tmp_path / "large.bin"
    regular.write_bytes(b"x" * 20)
    small = tmp_path / "small.bin"
    small.write_bytes(b"y" * 3)
    members = [
        {"path": ".__cmpct_r25_internal__/filesystem-v1.msgpack", "kind": "file", "size": 999},
        {"path": "alias.bin", "kind": "hardlink", "size": 1000},
        {"path": "large.bin", "kind": "file", "size": 20},
        {"path": "small.bin", "kind": "file", "size": 3},
    ]
    rel, size, digest = S._member_target(tmp_path, members)
    assert rel == "large.bin"
    assert size == 20
    assert len(digest) == 64


def test_selective_ratio_is_measurement_not_post_hoc_release_threshold() -> None:
    assert S._ratio(2.0, 4.0) == 0.5
    assert not hasattr(S, "MAX_SELECTIVE_TIME_RATIO")
    assert not hasattr(S, "MAX_SELECTIVE_RSS_RATIO")

    # Footnote: adding a threshold after observing CI would convert diagnostic timing into benchmark gaming.
    # A future numeric selective-read speed gate must be preregistered in release policy before its first run.
