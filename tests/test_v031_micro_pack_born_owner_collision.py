"""Real-product regression: newly created micro-pack SHA shares a later S_BLOB owner.

Known-red on v0.31 Builder blob 663ef0922992; do not claim candidate acceptance
until this is executed against the installed exact-head Builder and Reader.
"""
from pathlib import Path
from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _assert_roundtrip(src: Path, dst: Path):
    Builder(src, workers=1, reproducible=True).build(dst)
    with CMPCT(dst) as archive:
        for path in sorted(src.iterdir()):
            assert archive.read(path.name) == path.read_bytes()
        assert archive.verify() == len(list(src.iterdir()))


def test_new_micro_pack_content_matches_later_regular_file(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.md").write_bytes(b"alpha ")
    (src / "b.md").write_bytes(b"beta")
    # The first bucket sorts beta then alpha-space, producing this exact hash.
    (src / "alias.txt").write_bytes(b"betaalpha ")
    (src / "other.txt").write_bytes(b"gamma")
    _assert_roundtrip(src, tmp_path / "cross_extension.cmpct")


def test_safe_singleton_alias_remains_reconstructible(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.md").write_bytes(b"alpha ")
    (src / "b.md").write_bytes(b"beta")
    (src / "alias.txt").write_bytes(b"betaalpha ")
    _assert_roundtrip(src, tmp_path / "singleton.cmpct")
