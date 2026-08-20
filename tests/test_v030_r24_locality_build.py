from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as product


def test_shipping_r24_micro_pack_target_is_bounded_by_largest_member(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "largest.txt").write_bytes(b"a" * 3000)
    (root / "tiny.txt").write_bytes(b"b" * 17)
    out = tmp_path / "out.cmpct"
    seen: dict[str, int] = {}

    class FakeBuilder:
        def __init__(self, _root: Path):
            self.micro_pack_target = 256 * 1024

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
            return 2

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    monkeypatch.setattr(product, "CMPCT", FakeReader)

    stats = product._locality_bounded_r24_build(root, out)

    assert seen["target"] == 24_000
    assert stats["micro_pack_target_default_bytes"] == 256 * 1024
    assert stats["micro_pack_target_release_bytes"] == 24_000
    assert stats["locality_selected_member_bytes"] == 3000
    assert stats["locality_ceiling"] == 8.0
    assert stats["verified_files"] == 2


def test_shipping_r24_keeps_default_pack_cap_for_large_members(tmp_path, monkeypatch) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "large.bin").write_bytes(b"x" * (1024 * 1024))
    out = tmp_path / "out.cmpct"
    seen: dict[str, int] = {}

    class FakeBuilder:
        def __init__(self, _root: Path):
            self.micro_pack_target = 256 * 1024

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
            return 1

    monkeypatch.setattr(product.C, "Builder", FakeBuilder)
    monkeypatch.setattr(product, "CMPCT", FakeReader)

    stats = product._locality_bounded_r24_build(root, out)

    assert seen["target"] == 256 * 1024
    assert stats["micro_pack_target_release_bytes"] == 256 * 1024
    assert stats["locality_selected_member_bytes"] == 1024 * 1024


def test_release_product_rebinds_canonical_r24_builder_to_locality_bounded_policy() -> None:
    assert product.C._r24_build is product._locality_bounded_r24_build
