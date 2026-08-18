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

    # MessagePack cannot represent MIN_I64 - 1 at all, so the hostile boundary must use the representable
    # unsigned side of the wire domain. MAX_I64 + 1 encodes as uint64 and therefore actually reaches the reader's
    # signed-i64 admission check instead of failing inside the test fixture's packer.
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
