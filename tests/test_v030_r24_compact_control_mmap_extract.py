from __future__ import annotations

from pathlib import Path

import pytest

from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_direct_extract as DIRECT
from experiments import entropygraph_v030_r24_compact_control_mmap_extract as MMAP
from experiments import entropygraph_v030_r24_compact_control_profile as CC


def _tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(128):
        p = root / "records" / f"g-{i // 16:02d}" / f"row-{i:04d}.bin"
        p.parent.mkdir(parents=True, exist_ok=True)
        seed = f"row={i:04d};stable=1\n".encode()
        p.write_bytes((seed * ((32 * 1024 + len(seed) - 1) // len(seed)))[: 32 * 1024])


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _flip(path: Path, offset: int) -> None:
    payload = bytearray(path.read_bytes())
    payload[offset] ^= 0x5A
    path.write_bytes(payload)


def test_mmap_extract_matches_direct_without_payload_bytes_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "src"
    _tree(src)
    archive = tmp_path / "candidate.cmpct"
    CC.build(src, archive)
    assert CC.strong_verify(archive)["ok"] is True

    direct = tmp_path / "direct"
    DIRECT.extract(archive, direct)

    # The mmap path owns parsing itself.  Reaching the bytes-backed parser would reintroduce the full payload copy.
    monkeypatch.setattr(CC, "_parse", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("bytes parser must not run")))
    mapped = tmp_path / "mapped"
    MMAP.extract(archive, mapped)
    assert _snapshot(mapped) == _snapshot(direct) == _snapshot(src)


def test_mmap_extract_preserves_recovery_copy_and_budget_rollback(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    archive = tmp_path / "candidate.cmpct"
    CC.build(src, archive)
    pristine = archive.read_bytes()

    _magic, _version, _flags, primary_cbytes, _raw_bytes, _data_bytes, _sha = R24.HDR.unpack_from(pristine, 0)
    primary_offset = R24.HDR.size + max(0, int(primary_cbytes) // 2)
    primary_bad = tmp_path / "primary-bad.cmpct"
    primary_bad.write_bytes(pristine)
    _flip(primary_bad, primary_offset)

    recovered = tmp_path / "recovered"
    MMAP.extract(primary_bad, recovered)
    assert _snapshot(recovered) == _snapshot(src)

    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "sentinel.txt"
    sentinel.write_text("preserve-me")
    with pytest.raises(Exception):
        MMAP.extract(archive, existing, max_output_bytes=1024)
    assert sentinel.read_text() == "preserve-me"
    assert list(existing.iterdir()) == [sentinel]


def test_mmap_extract_fails_closed_when_both_controls_are_damaged(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _tree(src)
    archive = tmp_path / "candidate.cmpct"
    CC.build(src, archive)
    payload = archive.read_bytes()
    _magic, _version, _flags, primary_cbytes, _raw_bytes, _data_bytes, _sha = R24.HDR.unpack_from(payload, 0)
    footer_off = len(payload) - R24.FTR.size
    _fm, _a, _b, _c, _d, tail_cbytes, _tail_raw, _res, _tail_sha = R24.FTR.unpack_from(payload, footer_off)
    primary_offset = R24.HDR.size + max(0, int(primary_cbytes) // 2)
    tail_start = footer_off - int(tail_cbytes)
    tail_offset = tail_start + max(0, int(tail_cbytes) // 2)

    bad = tmp_path / "both-bad.cmpct"
    bad.write_bytes(payload)
    _flip(bad, primary_offset)
    _flip(bad, tail_offset)
    with pytest.raises(Exception):
        MMAP.extract(bad, tmp_path / "dst")
    assert not (tmp_path / "dst").exists()
