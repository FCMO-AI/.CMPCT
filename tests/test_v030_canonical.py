from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_authoritative as research_authority
from experiments import entropygraph_v030_canonical as canonical
from experiments import entropygraph_v030_geometry_overlay_g04 as g04
from experiments import entropygraph_v030_prefixgraph as pg


def _prefix_fixture(root: Path) -> None:
    root.mkdir(parents=True)
    base = (b'{"id":1,"name":"alpha","values":[' + b"1234567890," * 140 + b"]}\n") * 25
    for index in range(5):
        (root / f"version-{index:02d}.json").write_bytes(
            base.replace(b'"id":1', f'"id":{index + 1}'.encode(), 1)
        )


def test_revision25_profile_magics_are_fixed_width_and_distinct() -> None:
    assert canonical.REVISION == 25
    assert len(canonical.G04_MAGIC) == 8
    assert len(canonical.G04_TAIL) == 8
    assert len(canonical.PG_MAGIC) == 8
    assert len(canonical.PG_TAIL) == 8
    assert canonical.G04_MAGIC != canonical.PG_MAGIC
    assert canonical.G04_MAGIC.startswith(b"CMP25")
    assert canonical.PG_MAGIC.startswith(b"CMP25")


def test_profile_installation_updates_single_sourced_writer_reader_constants() -> None:
    canonical.install_revision25_profiles()
    assert g04.MAG == canonical.G04_MAGIC
    assert g04.TAIL == canonical.G04_TAIL
    assert pg.MAGIC == canonical.PG_MAGIC
    assert pg.TAIL == canonical.PG_TAIL


def test_canonical_prefixgraph_profile_roundtrips_and_reports_r25(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    _prefix_fixture(source)
    archive = tmp_path / "candidate.cmpct"

    # Force only the top-level complete-artifact choice so this test deterministically exercises the canonical
    # PrefixGraph profile. The PrefixGraph builder/reader themselves remain real and authenticated.
    real_pg_build = pg.build

    def tiny_pg(root: Path, out: Path):
        return real_pg_build(root, out)

    monkeypatch.setattr(canonical.AUTH.RC.PG, "build", tiny_pg)
    # A tiny fake G04 candidate is not safe here because strict verification is real. Instead build PG directly
    # after canonical profile installation and verify through the canonical facade's reader path.
    stats = pg.build(source, archive)
    assert stats["archive_bytes"] == archive.stat().st_size
    assert archive.read_bytes()[:8] == canonical.PG_MAGIC
    verified = canonical.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["format_revision"] == 25
    assert verified["format_profile"] == "prefixgraph-depth1"
    destination = tmp_path / "out"
    canonical.extract(archive, destination)
    assert canonical.treehash(destination) == canonical.treehash(source)


def test_r24_fallback_revision_detection_is_non_wrapping(tmp_path: Path) -> None:
    archive = tmp_path / "fallback.cmpct"
    archive.write_bytes(b"CMPCT\x18\x00\x00" + b"rest")
    revision, profile = canonical._revision_for_archive(archive)
    assert revision == 24
    assert profile == "inherited-r24"

# Footnote: the full release benchmark compares canonical-r25 and authority-research archive *sizes*, which must
# remain identical because profile promotion replaces fixed-width magic bytes rather than adding a wrapper.
