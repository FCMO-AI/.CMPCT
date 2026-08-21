from __future__ import annotations

from pathlib import Path
import random

from experiments import entropygraph_v030_release_product as P


def _random_bins(root: Path, *, count: int = 32, size: int = 32 * 1024, seed: int = 9001) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    for index in range(count):
        (root / f"member-{index:04d}.bin").write_bytes(bytes(rng.getrandbits(8) for _ in range(size + index % 7)))


def test_medium_terminal_shipping_skips_r25_only_after_real_r24_ratio(tmp_path, monkeypatch):
    root = tmp_path / "high-entropy"
    _random_bins(root)
    called = {"r25": False}

    def forbidden(*args, **kwargs):
        called["r25"] = True
        raise AssertionError("proven terminal envelope must not construct r25")

    monkeypatch.setattr(P.C, "build", forbidden)
    out = tmp_path / "terminal.cmpct"
    stats = P.build(root, out)
    assert called["r25"] is False
    assert stats["terminal_r24"] is True
    assert stats["r25_attempted"] is False
    assert stats["terminal_r24_archive_to_logical_ratio"] >= P.R24_TERMINAL_MEDIUM_MIN_ARCHIVE_TO_LOGICAL_RATIO
    assert P.strong_verify(out)["ok"] is True


def test_compressible_medium_binary_fails_closed_to_exact_tournament(tmp_path, monkeypatch):
    root = tmp_path / "compressible"
    root.mkdir()
    for index in range(32):
        (root / f"member-{index:04d}.bin").write_bytes((b"cmpct-v030" * 4096)[: 32 * 1024])
    sentinel = {"selected": "sentinel-r25-tournament"}
    called = {"r25": 0}

    def exact_tournament(*args, **kwargs):
        called["r25"] += 1
        return sentinel

    monkeypatch.setattr(P.C, "build", exact_tournament)
    result = P.build(root, tmp_path / "fallback.cmpct")
    assert result is sentinel
    assert called["r25"] == 1


def test_medium_terminal_source_predicate_rejects_mixed_suffix_and_small_members(tmp_path):
    root = tmp_path / "mixed"
    _random_bins(root)
    (root / "member-0000.bin").rename(root / "member-0000.dat")
    shape = P._medium_binary_terminal_shape(root)
    assert P._medium_binary_terminal_source_eligible(shape) is False

    small = tmp_path / "small"
    _random_bins(small)
    (small / "member-0001.bin").write_bytes(b"x" * (32 * 1024 - 1))
    shape = P._medium_binary_terminal_shape(small)
    assert P._medium_binary_terminal_source_eligible(shape) is False


def test_medium_terminal_source_predicate_rejects_symlink(tmp_path):
    root = tmp_path / "symlink"
    _random_bins(root)
    link = root / "link.bin"
    try:
        link.symlink_to(root / "member-0000.bin")
    except OSError:
        return
    shape = P._medium_binary_terminal_shape(root)
    assert shape["has_nonregular_entries"] is True
    assert P._medium_binary_terminal_source_eligible(shape) is False
