from __future__ import annotations
from pathlib import Path
import hashlib

import pytest

from experiments.entropygraph_v030_r24_process_shipping import R24ProcessPrebuildRegistry


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(root: Path) -> None:
    root.mkdir()
    (root / "a.txt").write_text("alpha beta gamma\n" * 200)
    (root / "b.bin").write_bytes(bytes(range(256)) * 32)


def test_registry_consumes_exact_promoted_r24_once(tmp_path: Path):
    from experiments import entropygraph_v030_release_product as product

    root = tmp_path / "src"
    _source(root)
    direct = tmp_path / "direct.cmpct"
    product._locality_bounded_r24_build(root, direct)

    td = tmp_path / "work"
    staging = td / "profile"
    staging.mkdir(parents=True)
    out = td / "canonical-r24.cmpct"
    registry = R24ProcessPrebuildRegistry(timeout_s=30)
    registry.start(root, staging)
    stats = registry.consume(out)

    assert stats is not None
    assert stats["r24_prebuild_reused"] is True
    assert stats["r24_prebuild_owner"] == "child-process-v1"
    assert out.stat().st_size == direct.stat().st_size
    assert _sha(out) == _sha(direct)
    assert registry.consume(out) is None


def test_registry_duplicate_key_fails_without_replacing_owner(tmp_path: Path):
    root = tmp_path / "src"
    _source(root)
    td = tmp_path / "work"
    staging = td / "profile"
    staging.mkdir(parents=True)
    registry = R24ProcessPrebuildRegistry(timeout_s=30)
    registry.start(root, staging)
    with pytest.raises(RuntimeError, match="duplicate canonical r24 prebuild key"):
        registry.start(root, staging)
    assert registry.discard(staging) is True
    assert registry.discard(staging) is False


def test_registry_discard_removes_candidate_and_kills_owner(tmp_path: Path):
    root = tmp_path / "src"
    _source(root)
    td = tmp_path / "work"
    staging = td / "profile"
    staging.mkdir(parents=True)
    candidate = td / "prebuilt-canonical-r24.cmpct"
    registry = R24ProcessPrebuildRegistry(timeout_s=30)
    registry.start(root, staging)
    assert registry.discard(staging) is True
    assert not candidate.exists()


def test_registry_missing_prebuild_preserves_parent_fallback(tmp_path: Path):
    registry = R24ProcessPrebuildRegistry(timeout_s=30)
    out = tmp_path / "work" / "canonical-r24.cmpct"
    assert registry.consume(out) is None
