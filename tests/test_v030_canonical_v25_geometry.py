from __future__ import annotations

import os
from pathlib import Path
import zipfile

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from experiments import canonical_v25_geometry as V25


def _fixture(root: Path) -> None:
    (root / "nested").mkdir(parents=True)
    rows = []
    for i in range(24000):
        rows.append(
            f"2026-08-17T12:{(i // 60) % 60:02d}:{i % 60:02d} INFO worker={i % 32:02d} "
            f"tenant=T{i % 380:04d} route={('/api/a','/api/b','/health')[i % 3]} latency={8 + (i * 13) % 820}\n"
        )
    (root / "nested" / "events.log").write_text("".join(rows), encoding="utf-8")
    (root / "small.txt").write_text("alpha beta gamma\n" * 300, encoding="utf-8")

    # Preserve non-byte semantics through the canonical r24 logical index.  The r25 compiler is forbidden to
    # rescan/reinterpret these objects; it may only change physical blob codecs.
    if hasattr(os, "symlink"):
        try:
            os.symlink("small.txt", root / "link-to-small")
        except OSError:
            pass
    if hasattr(os, "link"):
        try:
            os.link(root / "small.txt", root / "hard-small")
        except OSError:
            pass
    sparse = root / "sparse.bin"
    with sparse.open("wb") as fh:
        fh.write(b"head")
        fh.seek(2 * 1024 * 1024)
        fh.write(b"tail")
    if hasattr(os, "setxattr"):
        try:
            os.setxattr(root / "small.txt", "user.cmpct_test", b"r25")
        except OSError:
            pass
    with zipfile.ZipFile(root / "nested.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("inside.txt", "nested exact zip payload\n" * 200)


def _logical_sections(index: dict) -> tuple:
    return (
        index["files"],
        index.get("recipes"),
        index.get("dict_blob"),
        index.get("fsmeta"),
    )


def test_r25_physical_compile_preserves_canonical_logical_semantics(tmp_path: Path) -> None:
    root = tmp_path / "src"; root.mkdir(); _fixture(root)
    r24 = tmp_path / "base.cmpct"; r25 = tmp_path / "candidate.cmpct"
    Builder(root, workers=1, reproducible=False).build(r24)
    stats = V25.compile_r24_to_r25(r24, r25)
    with CMPCT(r24) as before, V25.CMPCTV25(r25) as after:
        assert _logical_sections(before.index) == _logical_sections(after.index)
        assert after.index["v"] == V25.V25_VERSION
        assert "geometry-ir-physical-codec" in after.index["features"]
        for row in before.files:
            if row[1] == 1:  # directory
                continue
            assert before.read(row[0]) == after.read(row[0])
            size = row[4]
            if row[1] == 0 and size >= 32:
                start = min(7, size)
                length = min(23, size - start)
                assert before.read_range(row[0], start, length) == after.read_range(row[0], start, length)
    assert stats["geometry_blobs"] > 0


def test_r25_tail_index_recovers_corrupted_primary_index_payload(tmp_path: Path) -> None:
    root = tmp_path / "src"; root.mkdir(); _fixture(root)
    r24 = tmp_path / "base.cmpct"; r25 = tmp_path / "candidate.cmpct"
    Builder(root, workers=1, reproducible=True).build(r24)
    V25.compile_r24_to_r25(r24, r25)
    data = bytearray(r25.read_bytes())
    _m, _v, _fl, cs, _us, _ds, _ih = V25.HDR.unpack_from(data, 0)
    assert cs > 8
    data[V25.HDR.size + cs // 2] ^= 0x5A
    damaged = tmp_path / "damaged.cmpct"; damaged.write_bytes(data)
    with V25.CMPCTV25(damaged) as reader:
        assert reader.index["v"] == 25
        assert reader.read("small.txt") == (root / "small.txt").read_bytes()


def test_geometry_metadata_rejects_noncanonical_inner_codec_and_sizes() -> None:
    raw = b"a" * 20000
    candidate = V25.encode_geometry_blob(raw)
    assert candidate is not None
    comp, meta, _stats = candidate
    rows = V25._unpack_geometry_meta(meta)
    broken = [list(row) for row in rows]
    broken[0][4] = 99
    bad_meta = V25._pack_geometry_meta(broken)
    with pytest.raises(IOError, match="inner payload"):
        V25.decode_geometry_blob(comp, bad_meta, len(raw))

    broken = [list(row) for row in rows]
    broken[0][2] = V25.RC.G.MAX_CHUNK + 1
    bad_meta = V25._pack_geometry_meta(broken)
    with pytest.raises(IOError, match="logical chunk"):
        V25.decode_geometry_blob(comp, bad_meta, len(raw))


def test_r25_complete_candidate_never_regresses_r24_bytes(tmp_path: Path) -> None:
    root = tmp_path / "src"; root.mkdir(); _fixture(root)
    out = tmp_path / "portfolio.cmpct"
    stats = V25.build_candidate(root, out, workers=1, reproducible=True)
    assert stats["archive_bytes"] <= stats["r24_bytes"]
    if stats["selected"] == "r25-geometry":
        with V25.CMPCTV25(out) as reader:
            assert reader.read("small.txt") == (root / "small.txt").read_bytes()
    else:
        with CMPCT(out) as reader:
            assert reader.read("small.txt") == (root / "small.txt").read_bytes()
