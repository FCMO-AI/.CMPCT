from __future__ import annotations

from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_canonical as canonical
from experiments import entropygraph_v030_prefixgraph as pg
from experiments import entropygraph_v030_product_fs as product_fs


def _prefix_tree(root: Path) -> None:
    root.mkdir(parents=True)
    shared = (b'{"schema":"v25","values":[' + b"1234567890," * 180 + b"]}\n") * 24
    for index in range(4):
        (root / f"version-{index:02d}.json").write_bytes(
            shared.replace(b'"v25"', f'"v25-{index}"'.encode(), 1)
        )


def test_real_r25_winner_does_not_pay_for_redundant_r24_encode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    _prefix_tree(source)
    archive = tmp_path / "winner.cmpct"

    def forbidden_r24(*_args, **_kwargs):
        raise AssertionError("a successful r25 winner must not perform a full r24 compatibility encode")

    def forced_prefixgraph_tournament(staged_root: Path, out: Path) -> dict:
        stats = dict(pg.build(staged_root, out))
        # The accepted-v0.29 floor is deliberately one byte larger so this test isolates publication scheduling
        # rather than depending on whatever corpus happens to make the real research selector choose a profile.
        return {
            **stats,
            "selected": "prefixgraph",
            "v029_bytes": out.stat().st_size + 1,
        }

    monkeypatch.setattr(canonical, "_r24_build", forbidden_r24)
    monkeypatch.setattr(canonical.RC, "build", forced_prefixgraph_tournament)

    result = canonical.build(source, archive)

    assert archive.read_bytes()[:8] == canonical.PG_MAGIC
    assert result["format_revision"] == 25
    assert result["format_profile"] == "prefixgraph-depth1"
    assert result["r24_built"] is False
    assert result["r24"] is None
    assert result["r25_smaller_than_v029_research_floor"] is True
    assert canonical.strong_verify(archive)["ok"] is True

    # Footnote: canonical r24 is still the exact compatibility fallback when r25 cannot publish. Building it on
    # every r25 success would add a whole archive creation pass to the hot path solely to discard its result.


def test_manifest_hardlinks_must_target_an_earlier_regular_owner() -> None:
    hostile = {
        "v": product_fs.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": product_fs.FILESYSTEM_MANIFEST,
        "entries": [
            ["directory", "d", 0o755, 0, 0, 0, [], None],
            ["alias", "h", 0o644, 0, 0, 0, [], "directory"],
        ],
    }
    raw = msgpack.packb(hostile, use_bin_type=True)

    with pytest.raises(RuntimeError, match="regular-file owner"):
        product_fs.decode_manifest(
            raw,
            max_path_bytes=canonical.POLICY.R.MAX_PATH_BYTES,
            max_entries=canonical.MAX_MANIFEST_ENTRIES,
        )

    # Footnote: merely requiring a backward path is insufficient: a hardlink could otherwise point to another
    # hardlink or a directory. Direct-to-regular ownership makes cycles/chains impossible and keeps depth at one.


def test_manifest_entry_bound_is_enforced_during_capture(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_bytes(b"a")
    (source / "b.txt").write_bytes(b"b")

    with pytest.raises(canonical.ProfileNotEligible, match="entry count"):
        product_fs.capture_filesystem_manifest(
            source,
            max_path_bytes=canonical.POLICY.R.MAX_PATH_BYTES,
            max_profile_files=canonical.MAX_PROFILE_FILES,
            max_profile_logical_bytes=canonical.MAX_PROFILE_LOGICAL_BYTES,
            max_entries=1,
        )

    # Footnote: hostile-input bounds are creation-time rules too. Rejecting the second entry while walking avoids
    # first allocating an arbitrarily large Python manifest and only discovering the limit after serialization.
