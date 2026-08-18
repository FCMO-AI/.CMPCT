from __future__ import annotations

from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_canonical_final as canonical


def _manifest_raw(*, mtime_ns: int = 0) -> bytes:
    return msgpack.packb(
        {
            "v": canonical.FS.FILESYSTEM_MANIFEST_VERSION,
            "profile": "cmpct-r25-filesystem-manifest-v1",
            "internal_path": canonical.FS.FILESYSTEM_MANIFEST,
            "entries": [["a.txt", "f", 0o644, mtime_ns, 0, 0, [], [1, b"x" * 32]]],
        },
        use_bin_type=True,
    )


def test_signed_mtime_manifest_domain_matches_writer() -> None:
    decoded = canonical._decode_manifest(_manifest_raw(mtime_ns=-1_000_000_000))
    assert decoded["manifest"]["entries"][0][3] == -1_000_000_000

    # MessagePack cannot encode MIN_I64 - 1, so use the representable uint64 side of the wire domain to exercise
    # the reader's signed-i64 admission boundary rather than failing inside the test fixture's packer.
    hostile = msgpack.unpackb(_manifest_raw(), raw=False)
    hostile["entries"][0][3] = canonical.MAX_I64 + 1
    with pytest.raises(RuntimeError, match="mtime declaration"):
        canonical._decode_manifest(msgpack.packb(hostile, use_bin_type=True))

    # Footnote: ``st_mtime_ns`` is signed on real filesystems. The reader must accept every bounded value the
    # writer can emit instead of creating archives that become unreadable merely because a timestamp predates 1970.


@pytest.mark.parametrize(
    "target",
    ["../x", "..\\x", "/x", "C:\\x", "C:/x", "\\\\server\\share", "\\rooted"],
)
def test_safe_symlink_policy_is_cross_platform(target: str) -> None:
    assert canonical._safe_symlink_target(target) is False


def test_safe_symlink_policy_accepts_benign_relative_target() -> None:
    assert canonical._safe_symlink_target("folder/file.txt") is True

    # Footnote: an archive accepted on Linux must not acquire a new traversal interpretation when the exact same
    # symlink bytes are later extracted on Windows, where backslashes, drives and UNC roots have path semantics.


def test_revision25_profile_context_restores_every_mutated_owner() -> None:
    before = canonical._snapshot_profile_globals()
    with canonical._revision25_profile_context():
        assert canonical.G04_RESEARCH.MAG == canonical.G04_MAGIC
        assert canonical.SHARED.MAG == canonical.G04_MAGIC
        assert canonical.PG.MAGIC == canonical.PG_MAGIC
        assert canonical.POLICY.R.G04.MAG == canonical.G04_MAGIC
        assert canonical.POLICY.R.PG.MAGIC == canonical.PG_MAGIC
    after = canonical._snapshot_profile_globals()
    assert after == before

    # Footnote: canonical identity is an operation-scoped descriptor. Import order must never permanently rewrite
    # the research grammars or leave the process in a different archive dialect after a canonical operation.


def _fake_product_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    r24_bytes: int,
    r25_bytes: int,
    v029_bytes: int,
) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_bytes(b"x")
    archive = tmp_path / "out.cmpct"

    prepared_raw = _manifest_raw()

    def fake_prepare(_root: Path, staged: Path) -> dict:
        staged.mkdir(parents=True, exist_ok=True)
        return {
            "manifest_raw": prepared_raw,
            "manifest_sha256": "m" * 64,
            "manifest_bytes": len(prepared_raw),
            "entries": 1,
            "regular_graph_members": 1,
        }

    def fake_r24(_root: Path, out: Path) -> dict:
        out.write_bytes(canonical.R24_MAGIC + b"r" * (r24_bytes - 8))
        return {"archive_bytes": r24_bytes, "format_revision": 24}

    def fake_r25(_staged: Path, out: Path) -> dict:
        out.write_bytes(canonical.PG_MAGIC + b"p" * (r25_bytes - 8))
        return {"archive_bytes": r25_bytes, "v029_bytes": v029_bytes, "selected": "prefixgraph"}

    monkeypatch.setattr(canonical, "_prepare_profile_tree", fake_prepare)
    monkeypatch.setattr(canonical, "_r24_build", fake_r24)
    monkeypatch.setattr(canonical, "_r25_build", fake_r25)
    monkeypatch.setattr(canonical, "_semantic_tree_sha", lambda _decoded: "tree")
    monkeypatch.setattr(
        canonical,
        "strong_verify",
        lambda path: {
            "ok": True,
            "tree_sha256": "tree" if Path(path).read_bytes().startswith(canonical.PG_MAGIC) else None,
        },
    )
    return source, archive


def test_r25_that_beats_research_floor_but_loses_product_floor_cannot_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, archive = _fake_product_environment(
        tmp_path,
        monkeypatch,
        r24_bytes=100,
        r25_bytes=110,
        v029_bytes=120,
    )
    result = canonical.build(source, archive)
    assert archive.read_bytes().startswith(canonical.R24_MAGIC)
    assert result["format_revision"] == 24
    assert result["r25_strictly_smaller_than_v029_research_floor"] is True
    assert result["r25_strictly_smaller_than_r24"] is False
    assert result["r24_product_bytes"] == 100
    assert result["r25_product_bytes"] == 110

    # Footnote: staged research accounting is causal evidence, not the product floor. Revision 25 must pay its
    # filesystem framing and beat the genuine revision-24 artifact for the same source tree before publication.


def test_exact_product_size_tie_conservatively_keeps_r24(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, archive = _fake_product_environment(
        tmp_path,
        monkeypatch,
        r24_bytes=100,
        r25_bytes=100,
        v029_bytes=120,
    )
    result = canonical.build(source, archive)
    assert archive.read_bytes().startswith(canonical.R24_MAGIC)
    assert result["selected"] == "r24-fallback"
    assert result["tie_policy"] == "r24-wins"


def test_r24_member_stats_do_not_invent_one_x_locality(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "r24.cmpct"
    archive.write_bytes(canonical.R24_MAGIC)

    class FakeReader:
        def __init__(self, _path: Path):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _rel: str) -> bytes:
            return b"payload"

    monkeypatch.setattr(canonical, "CMPCT", FakeReader)
    raw, stats = canonical.read_member_with_stats(archive, "a.txt")
    assert raw == b"payload"
    assert stats["decoded_context_bytes"] is None
    assert stats["decoded_context_amplification"] is None

    # Footnote: r24 may decode shared/compressed context larger than the requested member. Unknown is truthful;
    # reporting a fabricated precise 1.0x would let an unmeasured locality claim pass a release gate.
