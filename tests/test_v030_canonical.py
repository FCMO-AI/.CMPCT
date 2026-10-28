from __future__ import annotations

import os
from pathlib import Path
import stat

from experiments import entropygraph_v030_canonical as canonical
from experiments import entropygraph_v030_geometry_overlay_g04 as g04
from experiments import entropygraph_v030_prefixgraph as pg
from experiments import entropygraph_v030_product_fs as product_fs


def _prefix_fixture(root: Path) -> dict[str, bytes]:
    root.mkdir(parents=True)
    nested = root / "nested"
    nested.mkdir()
    base = (b'{"id":1,"name":"alpha","values":[' + b"1234567890," * 140 + b"]}\n") * 25
    expected = {}
    for index in range(5):
        raw = base.replace(b'"id":1', f'"id":{index + 1}'.encode(), 1)
        rel = f"nested/version-{index:02d}.json"
        (root / rel).write_bytes(raw)
        expected[rel] = raw
    (root / "empty-dir").mkdir()
    return expected


def test_revision25_profile_magics_are_fixed_width_distinct_and_r24_is_exact() -> None:
    assert canonical.REVISION == 25
    assert len(canonical.G04_MAGIC) == 8
    assert len(canonical.G04_TAIL) == 8
    assert len(canonical.PG_MAGIC) == 8
    assert len(canonical.PG_TAIL) == 8
    assert canonical.G04_MAGIC != canonical.PG_MAGIC
    assert canonical.G04_MAGIC.startswith(b"CMP25")
    assert canonical.PG_MAGIC.startswith(b"CMP25")
    assert canonical.R24_MAGIC == b"CMPCT24\x00"


def test_profile_installation_updates_single_sourced_writer_reader_constants() -> None:
    canonical.install_revision25_profiles()
    assert g04.MAG == canonical.G04_MAGIC
    assert g04.TAIL == canonical.G04_TAIL
    assert pg.MAGIC == canonical.PG_MAGIC
    assert pg.TAIL == canonical.PG_TAIL
    assert canonical.POLICY.R.G04.MAG == canonical.G04_MAGIC
    assert canonical.POLICY.R.PG.MAGIC == canonical.PG_MAGIC


def test_profile_detection_never_launders_research_bytes_as_r24(tmp_path: Path) -> None:
    r24 = tmp_path / "r24.cmpct"
    research = tmp_path / "research.cmpct"
    unknown = tmp_path / "unknown.cmpct"
    r24.write_bytes(canonical.R24_MAGIC + b"rest")
    research.write_bytes(b"CMPNX11\x00" + b"research")
    unknown.write_bytes(b"NOTCMPCT" + b"unknown")

    assert canonical._profile_for_archive(r24) == (24, "canonical-r24")
    assert canonical._profile_for_archive(research) == (None, "research-only")
    assert canonical._profile_for_archive(unknown) == (None, "unknown")
    assert canonical.strong_verify(research)["ok"] is False
    assert canonical.strong_verify(research)["format_revision"] is None

    # Footnote: this regression gate exists because the first convergence facade treated every non-r25 magic as
    # "inherited-r24". Accepted v0.29 actually emits CMPNX research grammars, so that shortcut could overstate
    # interoperability without changing a single archive byte.


def test_filesystem_manifest_is_bounded_deterministic_and_preserves_relationships(tmp_path: Path) -> None:
    source = tmp_path / "source"
    expected = _prefix_fixture(source)
    owner = source / "nested" / "version-00.json"
    owner.chmod(0o640)

    hardlink = source / "nested" / "version-hardlink.json"
    symlink = source / "version-link.json"
    try:
        os.link(owner, hardlink)
        os.symlink("nested/version-00.json", symlink)
    except OSError:
        hardlink = None
        symlink = None

    raw, regular_sources, stats = product_fs.capture_filesystem_manifest(
        source,
        max_path_bytes=canonical.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=canonical.MAX_PROFILE_FILES,
        max_profile_logical_bytes=canonical.MAX_PROFILE_LOGICAL_BYTES,
    )
    decoded = product_fs.decode_manifest(
        raw,
        max_path_bytes=canonical.POLICY.R.MAX_PATH_BYTES,
        max_entries=canonical.MAX_MANIFEST_ENTRIES,
    )
    rows = product_fs.entry_map(decoded)

    assert stats["manifest_bytes"] == len(raw)
    assert stats["manifest_sha256"]
    assert rows["empty-dir"][1] == "d"
    assert rows["nested/version-00.json"][1] == "f"
    assert rows["nested/version-00.json"][2] == 0o640
    assert rows["nested/version-00.json"][7][0] == len(expected["nested/version-00.json"])
    assert product_fs.FILESYSTEM_MANIFEST not in rows
    assert all(rel != product_fs.FILESYSTEM_MANIFEST for _path, rel in regular_sources)

    if hardlink is not None and symlink is not None:
        assert rows["nested/version-hardlink.json"][1] == "h"
        assert rows["nested/version-hardlink.json"][7] == "nested/version-00.json"
        assert rows["version-link.json"][1] == "l"
        assert rows["version-link.json"][7] == "nested/version-00.json"


def test_canonical_prefixgraph_profile_roundtrips_filesystem_semantics(tmp_path: Path) -> None:
    source = tmp_path / "source"
    expected = _prefix_fixture(source)
    (source / "nested" / "version-00.json").chmod(0o640)

    hardlink = source / "nested" / "version-hardlink.json"
    symlink = source / "version-link.json"
    links_supported = True
    try:
        os.link(source / "nested" / "version-00.json", hardlink)
        os.symlink("nested/version-00.json", symlink)
    except OSError:
        links_supported = False

    staged = tmp_path / "profile-tree"
    prepared = canonical._prepare_profile_tree(source, staged)
    archive = tmp_path / "candidate.cmpct"
    stats = pg.build(staged, archive)

    assert stats["archive_bytes"] == archive.stat().st_size
    assert archive.read_bytes()[:8] == canonical.PG_MAGIC
    assert prepared["manifest_bytes"] > 0

    verified = canonical.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["format_revision"] == 25
    assert verified["format_profile"] == "prefixgraph-depth1"
    assert verified["filesystem_semantics_verified"] is True

    listing = {row["path"]: row for row in canonical.list_members(archive)}
    assert product_fs.FILESYSTEM_MANIFEST not in listing
    assert listing["empty-dir"]["kind"] == "directory"
    assert canonical.read_member(archive, "nested/version-01.json") == expected["nested/version-01.json"]

    destination = tmp_path / "out"
    canonical.extract(archive, destination)
    for rel, raw in expected.items():
        assert (destination / rel).read_bytes() == raw
    assert (destination / "empty-dir").is_dir()
    assert stat.S_IMODE((destination / "nested" / "version-00.json").stat().st_mode) == 0o640
    assert not (destination / product_fs.INTERNAL_ROOT).exists()

    if links_supported:
        assert (destination / "version-link.json").is_symlink()
        assert os.readlink(destination / "version-link.json") == "nested/version-00.json"
        assert os.stat(destination / "nested" / "version-hardlink.json").st_ino == os.stat(
            destination / "nested" / "version-00.json"
        ).st_ino

    # Footnote: the content profile does not gain a parallel metadata parser. The graph authenticates the
    # reserved manifest as ordinary content; product_fs alone turns that manifest back into filesystem state.


def test_product_build_never_publishes_research_fallback_bytes(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "hello.txt").write_text("hello canonical fallback\n", encoding="utf-8")
    archive = tmp_path / "product.cmpct"

    def fake_research_tournament(root: Path, out: Path):
        del root
        raw = b"CMPNX11\x00" + b"research-only-fallback"
        out.write_bytes(raw)
        return {
            "selected": "v029-fallback",
            "archive_bytes": len(raw),
            "v029_bytes": len(raw),
        }

    monkeypatch.setattr(canonical.RC, "build", fake_research_tournament)
    result = canonical.build(source, archive)

    assert archive.read_bytes()[:8] == canonical.R24_MAGIC
    assert result["selected"] == "r24-fallback"
    assert result["format_revision"] == 24
    assert result["format_profile"] == "canonical-r24"
    assert result["research_tournament_profile"] == "research-only"
    assert result["r25_candidate_bytes"] is None
    assert canonical.strong_verify(archive)["ok"] is True
    assert canonical.read_member(archive, "hello.txt") == b"hello canonical fallback\n"


def test_reserved_r25_namespace_falls_back_to_genuine_r24(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    reserved = source / product_fs.INTERNAL_ROOT
    reserved.mkdir(parents=True)
    (reserved / "user-file.txt").write_text("must remain user data\n", encoding="utf-8")
    archive = tmp_path / "fallback.cmpct"

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("r25 research tournament should not run after manifest-namespace rejection")

    monkeypatch.setattr(canonical.RC, "build", should_not_run)
    result = canonical.build(source, archive)

    assert result["r25_attempted"] is False
    assert result["format_revision"] == 24
    assert archive.read_bytes()[:8] == canonical.R24_MAGIC
    assert canonical.read_member(archive, f"{product_fs.INTERNAL_ROOT}/user-file.txt") == b"must remain user data\n"

    # Footnote: reserving an internal path is safe only because collision is an explicit admission failure. The
    # user file is preserved through r24 instead of being renamed, hidden, or overwritten by product metadata.
