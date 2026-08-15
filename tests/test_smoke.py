import hashlib
import os
from pathlib import Path

from cmpct.core import Builder, CMPCT


def digest_tree(root: Path):
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            out[rel] = ("L", os.readlink(p))
        elif p.is_dir():
            out[rel] = ("D", "")
        elif p.is_file():
            out[rel] = ("F", hashlib.sha256(p.read_bytes()).hexdigest())
    return out


def test_roundtrip_and_range(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "small.txt").write_text("shared text\n" * 200)
    big = (b"abcdefgh" * 200_000) + os.urandom(128 * 1024)
    (src / "big.bin").write_bytes(big)
    os.link(src / "small.txt", src / "small-hardlink.txt")
    os.symlink("small.txt", src / "small-link.txt")

    archive = tmp_path / "sample.cmpct"
    Builder(src).build(archive)

    with CMPCT(archive) as ar:
        assert ar.read("small.txt") == (src / "small.txt").read_bytes()
        assert ar.read_range("big.bin", 12345, 4096) == big[12345:12345 + 4096]
        assert ar.verify() >= 2
        restored = tmp_path / "restored"
        ar.extractall(restored)

    assert digest_tree(src) == digest_tree(restored)


def test_sparse_file_roundtrip(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    p = src / "disk.img"
    with p.open("wb") as f:
        f.truncate(16 * 1024 * 1024)
        f.seek(8 * 1024 * 1024)
        f.write(b"CMPCT" * 1000)

    archive = tmp_path / "sparse.cmpct"
    Builder(src).build(archive)
    with CMPCT(archive) as ar:
        assert ar.read_range("disk.img", 0, 4096) == b"\0" * 4096
        assert ar.read("disk.img") == p.read_bytes()


def test_cli_info(tmp_path: Path, capsys):
    from cmpct.cli import main
    import sys
    src = tmp_path / "src"
    src.mkdir()
    (src / "x.txt").write_text("hello")
    archive = tmp_path / "x.cmpct"
    Builder(src).build(archive)
    old = sys.argv
    try:
        sys.argv = ["cmpct", "info", str(archive)]
        main()
    finally:
        sys.argv = old
    assert '"version": 24' in capsys.readouterr().out
