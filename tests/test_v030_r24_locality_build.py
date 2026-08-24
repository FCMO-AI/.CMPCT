from __future__ import annotations

from pathlib import Path
import threading

import pytest

from experiments import entropygraph_v030_release_product as product


@pytest.fixture(autouse=True)
def _isolate_dead_dictionary_postpass(monkeypatch):
    """These tests exercise r24 locality/packing policy with deliberately fake archive bytes.

    Dead-dictionary elision has its own real-r24 all-15 proof.  Stub only that orthogonal post-selection pass here so
    the fake Builder payloads remain valid test doubles instead of being parsed as revision-24 archives.
    """
    monkeypatch.setattr(
        product._R24_DEAD_DICT,
        "elide_dead_dictionary_in_place",
        lambda _path: {"reason": "test-isolated", "saving_bytes": 0},
    )


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
            seen["max_file"] = int(self.micro_pack_max_file)
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
    assert seen["max_file"] == product.R24_RELEASE_MICRO_MAX_FILE_BYTES == 256 * 1024
    assert seen["deflate_reuse_min"] == product.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES
    assert stats["micro_pack_target_default_bytes"] == 256 * 1024
    assert stats["micro_pack_target_release_bytes"] == 24_000
    assert stats["micro_pack_max_file_release_bytes"] == 256 * 1024
    assert stats["micro_pack_medium_binary_extension"] == ".bin"
    assert stats["locality_selected_member_bytes"] == 3000
    assert stats["locality_ceiling"] == 8.0
    assert stats["verified_files"] is None
    assert stats["verification_state"] == "deferred-to-selected-artifact"
    assert stats["large_file_chunk_policy"] == "mature-cdc"


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
    assert stats["large_file_chunk_policy"] == "mature-cdc"


def test_shipping_r24_enables_medium_binary_pack_only_during_build(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "medium.bin").write_bytes(b"x" * (96 * 1024))
    out = tmp_path / "out.cmpct"
    seen: dict[str, object] = {}

    class FakeBuilder:
        def __init__(self, _root: Path, *, deflate_reuse_min: int):
            self.micro_pack_target = 256 * 1024
            self.micro_pack_max_file = 32 * 1024

        def build(self, target: Path):
            seen["medium_enabled"] = product.R24_RELEASE_MEDIUM_BINARY_EXT in product.R24_BUILDER_MODULE.TEXT_EXT
            seen["max_file"] = self.micro_pack_max_file
            target.write_bytes(b"fake-r24")
            return {}

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    stats = product._locality_bounded_r24_build(root, out)

    assert seen["medium_enabled"] is True
    assert seen["max_file"] == 256 * 1024
    assert stats["micro_pack_medium_binary_policy"] == "shipping-r24-thread-local-existing-s-pack"
    assert product.R24_RELEASE_MEDIUM_BINARY_EXT not in product.R24_BUILDER_MODULE.TEXT_EXT
    assert getattr(product._R24_CDC_POLICY, "medium_binary_pack", False) is False


def test_shipping_r24_admits_wide_chunks_only_for_one_large_regular_file(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "large.bin").write_bytes(b"x" * (product.R24_RELEASE_WIDE_CHUNK_BYTES + 17))
    out = tmp_path / "out.cmpct"
    seen: dict[str, object] = {}

    class FakeBuilder:
        def __init__(self, _root: Path, *, deflate_reuse_min: int):
            self.micro_pack_target = 256 * 1024
            self.micro_pack_max_file = 32 * 1024

        def build(self, target: Path):
            seen["wide"] = getattr(product._R24_CDC_POLICY, "wide_single_file", False)
            chunks = product._release_cdc_chunks(b"z" * (product.R24_RELEASE_WIDE_CHUNK_BYTES + 17))
            seen["chunk_lengths"] = [len(chunk) for chunk in chunks]
            target.write_bytes(b"fake-r24")
            return {}

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    stats = product._locality_bounded_r24_build(root, out)

    assert seen["wide"] is True
    assert seen["chunk_lengths"] == [product.R24_RELEASE_WIDE_CHUNK_BYTES, 17]
    assert stats["regular_user_files"] == 1
    assert stats["large_file_chunk_policy"] == "fixed-8mib"
    assert stats["large_file_chunk_bytes"] == product.R24_RELEASE_WIDE_CHUNK_BYTES
    assert getattr(product._R24_CDC_POLICY, "wide_single_file", False) is False


def test_shipping_r24_does_not_widen_multi_file_tree(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "large.bin").write_bytes(b"x" * product.R24_RELEASE_WIDE_CHUNK_BYTES)
    (root / "peer.bin").write_bytes(b"y")
    out = tmp_path / "out.cmpct"
    seen: dict[str, object] = {}

    class FakeBuilder:
        def __init__(self, _root: Path, *, deflate_reuse_min: int):
            self.micro_pack_target = 256 * 1024
            self.micro_pack_max_file = 32 * 1024

        def build(self, target: Path):
            seen["wide"] = getattr(product._R24_CDC_POLICY, "wide_single_file", False)
            target.write_bytes(b"fake-r24")
            return {}

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    stats = product._locality_bounded_r24_build(root, out)

    assert seen["wide"] is False
    assert stats["regular_user_files"] == 2
    assert stats["large_file_chunk_policy"] == "mature-cdc"
    assert stats["large_file_chunk_bytes"] is None


def test_wide_chunk_dispatch_is_thread_local(monkeypatch) -> None:
    monkeypatch.setattr(product, "_R24_ORIGINAL_CDC_CHUNKS", lambda data: [b"original", bytes(str(len(data)), "ascii")])
    barrier = threading.Barrier(2)
    seen: dict[str, list[int] | list[bytes]] = {}

    def wide_worker() -> None:
        product._R24_CDC_POLICY.wide_single_file = True
        barrier.wait()
        chunks = product._release_cdc_chunks(b"x" * (product.R24_RELEASE_WIDE_CHUNK_BYTES + 3))
        seen["wide"] = [len(chunk) for chunk in chunks]
        product._R24_CDC_POLICY.wide_single_file = False

    def normal_worker() -> None:
        product._R24_CDC_POLICY.wide_single_file = False
        barrier.wait()
        seen["normal"] = product._release_cdc_chunks(b"abc")

    first = threading.Thread(target=wide_worker)
    second = threading.Thread(target=normal_worker)
    first.start(); second.start(); first.join(); second.join()

    assert seen["wide"] == [product.R24_RELEASE_WIDE_CHUNK_BYTES, 3]
    assert seen["normal"] == [b"original", b"3"]


def test_medium_binary_pack_dispatch_is_thread_local() -> None:
    barrier = threading.Barrier(2)
    seen: dict[str, bool] = {}

    def r24_worker() -> None:
        product._R24_CDC_POLICY.medium_binary_pack = True
        barrier.wait()
        seen["r24"] = product.R24_RELEASE_MEDIUM_BINARY_EXT in product.R24_BUILDER_MODULE.TEXT_EXT
        product._R24_CDC_POLICY.medium_binary_pack = False

    def research_worker() -> None:
        product._R24_CDC_POLICY.medium_binary_pack = False
        barrier.wait()
        seen["research"] = product.R24_RELEASE_MEDIUM_BINARY_EXT in product.R24_BUILDER_MODULE.TEXT_EXT

    first = threading.Thread(target=r24_worker)
    second = threading.Thread(target=research_worker)
    first.start(); second.start(); first.join(); second.join()

    assert seen == {"r24": True, "research": False}
    assert product.R24_RELEASE_MEDIUM_BINARY_EXT not in product.R24_BUILDER_MODULE.TEXT_EXT


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
