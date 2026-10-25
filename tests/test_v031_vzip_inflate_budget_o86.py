"""O86: authentic r24 Builder control for bounded *speculative* ZIP inflation.

The physical ZIP is never truncated, modified or rejected: the fallback is exact opaque storage.
Tests are designed to disprove early admission, total-budget accounting and unchanged
under-budget behavior independently of release/benchmark gates.
"""
from __future__ import annotations

import hashlib
import io
import time
import zipfile
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import S_BLOB, make_vzip_recipe
from cmpct.reader import CMPCT


def _zip(path: Path, lengths: tuple[int, ...]) -> bytes:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for i, n in enumerate(lengths):
            z.writestr(f"payload-{i}.bin", bytes((65 + i % 20,)) * n)
    return path.read_bytes()


def _capture(*, root: Path, out: Path, monkeypatch, budget: int):
    monkeypatch.setenv("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES", str(budget))
    t0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    result = Builder(root, workers=1, reproducible=True).build(out)
    return {
        "result": result, "archive_bytes": out.stat().st_size,
        "create_wall_ns": time.perf_counter_ns() - t0,
        "create_cpu_ns": time.process_time_ns() - cpu0,
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    }


def test_o86_over_budget_never_inflates_or_publishes_candidate(tmp_path, monkeypatch):
    path = tmp_path / "large.zip"
    original = _zip(path, (2 * 1024 * 1024,))
    calls = []
    def forbidden_read(self, *args, **kwargs):
        raise AssertionError("over-budget VZIP must not inflate member")
    monkeypatch.setattr(zipfile.ZipFile, "read", forbidden_read)
    recipe = make_vzip_recipe(
        path, lambda *args: calls.append(args), original=original,
        max_inflated_bytes=1024 * 1024,
    )
    assert recipe is None
    assert calls == []


def test_o86_budget_is_cumulative_across_zip_members(tmp_path, monkeypatch):
    path = tmp_path / "multi.zip"
    original = _zip(path, (700_000, 700_000))
    calls = []
    def forbidden_read(self, *args, **kwargs):
        raise AssertionError("cumulative 1.4MB exceeds 1MB before any inflate")
    monkeypatch.setattr(zipfile.ZipFile, "read", forbidden_read)
    assert make_vzip_recipe(
        path, lambda *args: calls.append(args), original=original,
        max_inflated_bytes=1_000_000,
    ) is None
    assert not calls


@pytest.mark.parametrize("bad", [0, -1, True, "large"])
def test_o86_invalid_direct_probe_budget_rejected(tmp_path, bad):
    path = tmp_path / "tiny.zip"
    raw = _zip(path, (32,))
    with pytest.raises(ValueError, match="max_inflated_bytes"):
        make_vzip_recipe(path, lambda *args: None, original=raw, max_inflated_bytes=bad)


def test_o86_large_zip_falls_back_and_roundtrips_real_builder(tmp_path, monkeypatch):
    root = tmp_path / "source"; root.mkdir()
    path = root / "large.zip"
    original = _zip(path, (24 * 1024 * 1024,))
    limited = tmp_path / "limited.cmpct"
    receipt = _capture(root=root, out=limited, monkeypatch=monkeypatch, budget=1024 * 1024)
    with CMPCT(limited) as reader:
        assert len(reader.files) == 1
        assert reader.files[0][6][0] == S_BLOB, "over-budget ZIP must use exact fallback"
        assert reader.read("large.zip") == original
        assert reader.verify() == 1
        extracted = tmp_path / "extracted"
        reader.extractall(extracted)
        assert (extracted / "large.zip").read_bytes() == original
    print("O86_LIMITED_RECEIPT", receipt)
    # Immutable input physical content: even an extreme ZIP is reconstructed byte-for-byte.
    assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(original).digest()


def test_o86_small_zip_same_complete_archive_as_permissive_o63(tmp_path, monkeypatch):
    root = tmp_path / "source"; root.mkdir()
    original = _zip(root / "small.zip", (128 * 1024, 100 * 1024))
    small = tmp_path / "small-budget.cmpct"
    wide = tmp_path / "wide-budget.cmpct"
    limited = _capture(root=root, out=small, monkeypatch=monkeypatch, budget=1024 * 1024)
    reference = _capture(root=root, out=wide, monkeypatch=monkeypatch, budget=64 * 1024 * 1024)
    assert small.read_bytes() == wide.read_bytes(), "sub-budget output must remain byte-identical"
    with CMPCT(small) as reader:
        assert reader.read("small.zip") == original
        assert reader.verify() == 1
    print("O86_UNDER_BUDGET_RECEIPT", limited, reference)


def test_o86_builder_rejects_invalid_environment_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES", "0")
    with pytest.raises(ValueError, match="CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES"):
        Builder(tmp_path)
