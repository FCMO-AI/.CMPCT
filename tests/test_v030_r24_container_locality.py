from __future__ import annotations

from pathlib import Path
import random
import zipfile

from cmpct.builder import Builder
from cmpct.codec import K_FILE, S_PACK
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_release_product as PRODUCT


def _nested_zip_tree(root: Path, *, count: int = 14) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(0xC030D3F1)
    for archive_index in range(count):
        archive = root / f"bundle-{archive_index:02d}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for member_index in range(12):
                # Related framing/text plus a deterministic noisy tail gives realistic nested-container bytes
                # while keeping the fixture small enough for the ordinary Python suite.
                text = (
                    f"bundle={archive_index};member={member_index};\n".encode()
                    + (b"shared nested archive business row\n" * 120)
                    + bytes(rng.getrandbits(8) for _ in range(192))
                )
                info = zipfile.ZipInfo(f"member-{member_index:02d}.txt", date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, text, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def _pack_hashes(archive: Path) -> set[bytes]:
    with CMPCT(archive) as reader:
        return {
            bytes(row[6][1])
            for row in reader.files
            if row[1] == K_FILE and row[6] and row[6][0] == S_PACK
        }


def _all_member_amplifications(archive: Path) -> list[float]:
    original = PRODUCT.CMPCT

    class TrackingR24(original):
        def __init__(self, path):
            super().__init__(path)
            self.observed_blob_ids: set[int] = set()

        def _blob(self, idx):
            self.observed_blob_ids.add(int(idx))
            return super()._blob(idx)

    amplifications = []
    with TrackingR24(archive) as reader:
        for row in reader.files:
            if row[1] != K_FILE:
                continue
            rel, _kind, _mode, _mtime, size, _digest, _storage = row
            reader.observed_blob_ids.clear()
            raw = bytes(reader.read(rel))
            assert len(raw) == int(size)
            decoded = sum(int(reader.blobs[idx][1]) for idx in reader.observed_blob_ids)
            amplifications.append(max(len(raw), decoded) / max(1, len(raw)))
    return amplifications


def test_default_r24_nested_container_policy_remains_historical(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _nested_zip_tree(source)
    archive = tmp_path / "default.cmpct"
    Builder(source).build(archive)

    # The generic/historical encoder still owns its previous one-cohort heuristic.  The release repair must not
    # silently rewrite accepted v0.29 evidence or ordinary r24 bytes merely because release_product was imported.
    assert len(_pack_hashes(archive)) == 1
    with CMPCT(archive) as reader:
        assert reader.verify() == 14


def test_shipping_r24_splits_nested_container_pack_to_all_member_8x(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _nested_zip_tree(source)
    archive = tmp_path / "release.cmpct"

    stats = PRODUCT._locality_bounded_r24_build(source, archive)
    assert stats["format_revision"] == 24
    assert len(_pack_hashes(archive)) >= 2

    verified = PRODUCT.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["format_revision"] == 24
    assert verified["tree_sha256"] == PRODUCT.treehash(source)

    amplifications = _all_member_amplifications(archive)
    assert len(amplifications) == 14
    assert max(amplifications) <= 8.0
