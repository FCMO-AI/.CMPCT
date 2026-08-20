from __future__ import annotations

from pathlib import Path
import threading

from experiments import entropygraph_v030_release_product as product


def test_shipping_r24_micro_pack_target_is_bounded_by_largest_member(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "largest.txt").write_bytes(b"a" * 3000)
    (root / "tiny.txt").write_bytes(b"b" * 17)
    out = tmp_path / "out.cmpct"
    seen: dict[str, int] = {}

    class FakeBuilder:
        def __init__(self, _root: Path, *, deflate_reuse_min: int):
            seen["deflate_reuse_min"] = int(deflate_reuse_min)
            self.micro_pack_target = 256 * 1024
            self.micro_pack_max_file = 32 * 1024

        def build(self, target: Path):
            seen["target"] = int(self.micro_pack_target)
            target.write_bytes(b"fake-r24")
            return {"bytes": target.stat().st_size}

    class FakeReader:
        def __init__(self, _path: Path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def verify(self):
            raise AssertionError("r24 floor candidate must not be eagerly verified")

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    monkeypatch.setattr(product, "CMPCT", FakeReader)

    stats = product._locality_bounded_r24_build(root, out)

    assert seen["target"] == 24_000
    assert seen["deflate_reuse_min"] == product.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES
    assert stats["micro_pack_target_default_bytes"] == 256 * 1024
    assert stats["micro_pack_target_release_bytes"] == 24_000
    assert stats["locality_selected_member_bytes"] == 3000
    assert stats["locality_ceiling"] == 8.0
    assert stats["verified_files"] is None
    assert stats["verification_state"] == "deferred-to-selected-artifact"


def test_shipping_r24_uses_reader_cache_cap_for_large_members(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "large.bin").write_bytes(b"x" * (1024 * 1024))
    out = tmp_path / "out.cmpct"
    seen: dict[str, int] = {}

    class FakeBuilder:
        def __init__(self, _root: Path, *, deflate_reuse_min: int):
            seen["deflate_reuse_min"] = int(deflate_reuse_min)
            self.micro_pack_target = 256 * 1024
            self.micro_pack_max_file = 32 * 1024

        def build(self, target: Path):
            seen["target"] = int(self.micro_pack_target)
            target.write_bytes(b"fake-r24")
            return {}

    class FakeReader:
        def __init__(self, _path: Path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def verify(self):
            raise AssertionError("r24 floor candidate must not be eagerly verified")

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    monkeypatch.setattr(product, "CMPCT", FakeReader)

    stats = product._locality_bounded_r24_build(root, out)

    # For a 1 MiB selected member the 8x locality allowance is 8 MiB, but the mature reader's decoded-blob
    # cache ceiling is 2 MiB. The shipping encoder intentionally uses that tighter cache cap; 256 KiB was only
    # the historical encoder heuristic and is no longer the release policy for this source shape.
    assert seen["target"] == product.R24_RELEASE_PACK_CAP_BYTES == 2 * 1024 * 1024
    assert seen["deflate_reuse_min"] == product.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES
    assert stats["micro_pack_target_release_bytes"] == product.R24_RELEASE_PACK_CAP_BYTES
    assert stats["locality_selected_member_bytes"] == 1024 * 1024
    assert stats["verification_state"] == "deferred-to-selected-artifact"


def test_r24_prebuild_overlaps_filesystem_manifest_capture(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "payload.bin").write_bytes(b"payload")
    job_root = tmp_path / "job"
    job_root.mkdir()
    staging = job_root / "profile-tree"
    output = job_root / "canonical-r24.cmpct"
    started = threading.Event()
    release = threading.Event()
    capture_observed_prebuild = []

    def fake_r24(_root: Path, target: Path) -> dict:
        started.set()
        assert release.wait(2.0)
        target.write_bytes(b"prebuilt-r24")
        return {"archive_bytes": len(b"prebuilt-r24"), "format_revision": 24}

    def fake_prepare(_root: Path, _staging: Path) -> dict:
        capture_observed_prebuild.append(started.wait(1.0))
        return {"manifest_raw": b"manifest"}

    monkeypatch.setattr(product, "_locality_bounded_r24_build", fake_r24)
    monkeypatch.setattr(product, "_ORIGINAL_PREPARE_PROFILE_TREE", fake_prepare)

    prepared = product._prepare_profile_tree_with_r24_overlap(root, staging)
    assert prepared == {"manifest_raw": b"manifest"}
    assert capture_observed_prebuild == [True]

    release.set()
    stats = product._consume_or_build_locality_bounded_r24(root, output)

    assert output.read_bytes() == b"prebuilt-r24"
    assert stats["r24_prebuild_overlap"] == "filesystem-manifest-capture"
    assert stats["r24_prebuild_reused"] is True


def test_release_product_rebinds_canonical_build_hooks() -> None:
    assert product.C._r24_build is product._consume_or_build_locality_bounded_r24
    assert product.C._prepare_profile_tree is product._prepare_profile_tree_with_r24_overlap
