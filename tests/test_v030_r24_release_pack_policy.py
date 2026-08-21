from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as product


class _FakeReader:
    def __init__(self, path: Path):
        self.path = Path(path)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def verify(self):
        raise AssertionError("r24 floor candidate must not be eagerly verified")


class _FakeBuilder:
    instances = []

    def __init__(self, root: Path, deflate_reuse_min=None, **_kwargs):
        import os

        self.root = Path(root)
        self.deflate_reuse_min = deflate_reuse_min
        self.micro_pack_target = int(os.environ.get("CMPCT_MICRO_PACK_TARGET", str(256 * 1024)))
        self.micro_pack_max_file = int(os.environ.get("CMPCT_MICRO_PACK_MAX_FILE", str(32 * 1024)))
        self.__class__.instances.append(self)

    def build(self, out: Path):
        Path(out).write_bytes(b"r24")
        return {"built": True}


def _exercise(monkeypatch, tmp_path: Path, *, largest_bytes: int):
    root = tmp_path / "root"
    root.mkdir()
    (root / "largest.log").write_bytes(b"x" * largest_bytes)
    out = tmp_path / "candidate.cmpct"

    _FakeBuilder.instances.clear()
    monkeypatch.setenv("CMPCT_MICRO_PACK_TARGET", "4096")
    monkeypatch.setenv("CMPCT_MICRO_PACK_MAX_FILE", "1024")
    monkeypatch.setenv("CMPCT_DEFLATE_REUSE_MIN", "1")
    monkeypatch.setattr(product.C, "Builder", _FakeBuilder)
    monkeypatch.setattr(product, "CMPCT", _FakeReader)

    stats = product._locality_bounded_r24_build(root, out)
    builder = _FakeBuilder.instances[-1]
    return builder, stats


def test_release_r24_spends_locality_budget_up_to_reader_cache_cap(monkeypatch, tmp_path: Path):
    builder, stats = _exercise(monkeypatch, tmp_path, largest_bytes=300 * 1024)

    assert builder.micro_pack_target == 2 * 1024 * 1024
    assert stats["micro_pack_target_release_bytes"] == 2 * 1024 * 1024
    assert stats["locality_selected_member_bytes"] == 300 * 1024
    assert stats["locality_ceiling"] == 8.0
    assert stats["locality_pack_policy"] == "min-2mib-cache-cap-or-8x-largest-regular-member-plus-exact-deflate-retention"
    assert stats["verification_state"] == "deferred-to-selected-artifact"
    assert stats["verified_files"] is None


def test_release_r24_still_shrinks_for_tiny_selected_member(monkeypatch, tmp_path: Path):
    builder, stats = _exercise(monkeypatch, tmp_path, largest_bytes=3 * 1024)

    assert builder.micro_pack_target == 24 * 1024
    assert stats["micro_pack_target_release_bytes"] == 24 * 1024


def test_release_r24_byte_knobs_ignore_ambient_environment(monkeypatch, tmp_path: Path):
    builder, stats = _exercise(monkeypatch, tmp_path, largest_bytes=300 * 1024)

    assert builder.deflate_reuse_min == 0
    assert builder.micro_pack_max_file == 32 * 1024
    assert stats["deflate_reuse_min_release_bytes"] == 0
    assert stats["micro_pack_max_file_release_bytes"] == 32 * 1024
    assert stats["release_byte_knobs"] == "environment-independent-r24-v3"
