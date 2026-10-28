from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_r24_compact_control_direct_extract as DIRECT
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT


def _tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(96):
        p = root / "records" / f"g-{i // 16:02d}" / f"row-{i:04d}.bin"
        p.parent.mkdir(parents=True, exist_ok=True)
        seed = f"row={i:04d}\n".encode()
        p.write_bytes((seed * ((32 * 1024 + len(seed) - 1) // len(seed)))[: 32 * 1024])


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_direct_extract_matches_compatibility_path_without_rebuilding_r24(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "src"
    _tree(src)
    archive = tmp_path / "candidate.cmpct"
    stats = CC.build(src, archive)
    assert stats["format_profile"] == CC.PROFILE
    assert CC.strong_verify(archive)["ok"] is True

    legacy = tmp_path / "legacy"
    CC.extract(archive, legacy)

    # The direct experiment must never synthesize the compatibility archive. If that helper is reached the test
    # fails immediately, making the removed whole-pass/materialization boundary explicit.
    monkeypatch.setattr(
        CC,
        "_rebuild_r24_bytes",
        lambda parsed: (_ for _ in ()).throw(AssertionError("compatibility r24 rebuild must not run")),
    )
    direct = tmp_path / "direct"
    DIRECT.extract(archive, direct)
    assert _snapshot(direct) == _snapshot(legacy) == _snapshot(src)


def test_direct_extract_preserves_budget_failure_and_existing_destination(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    archive = tmp_path / "candidate.cmpct"
    CC.build(src, archive)

    dst = tmp_path / "existing"
    dst.mkdir()
    sentinel = dst / "sentinel.txt"
    sentinel.write_text("preserve-me")
    with pytest.raises(Exception):
        DIRECT.extract(archive, dst, max_output_bytes=1024)
    assert sentinel.read_text() == "preserve-me"
    assert list(dst.iterdir()) == [sentinel]


def test_direct_extract_rejects_invalid_output_budget(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        DIRECT.extract(tmp_path / "missing.cmpct", tmp_path / "dst", max_output_bytes=0)
    with pytest.raises(ValueError):
        DIRECT.extract(tmp_path / "missing.cmpct", tmp_path / "dst", max_output_bytes=True)
