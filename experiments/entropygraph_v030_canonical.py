"""Canonical CMPCT v0.30 / revision-25 release facade.

Research established two new complete archive representations with temporary experiment magics.  Shipping those
identifiers would make v0.30 an experiment bundle rather than a format revision, so the release assigns stable
revision-25 profile magics of the same width:

- ``CMP25G4\0`` — revision 25 Geometry-over-Mosaic G0-G4 profile;
- ``CMP25PG\0`` — revision 25 PrefixGraph depth-1 profile.

Their duplicate-tail identifiers are likewise canonicalized.  The header/footer structs, metadata, payloads,
selection thresholds and archive lengths are unchanged.  The owning writers resolve magic constants at call
time, so installing the profile constants *before build* emits canonical bytes directly—there is no post-build
archive rewrite or extra payload copy.

If the exact tournament falls back to accepted v0.29, the output remains the byte-identical inherited r24
archive.  Therefore the v0.30 engine may lawfully emit r24 for an inherited representation or r25 for a new
representation; it never wraps r24 merely to claim a new revision and therefore creates no fallback regression.

Footnote: revision identifies the on-disk grammar actually used by an archive, not the marketing version of the
encoder that happened to create it.  That distinction is what lets exact fallback stay exact.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_authoritative as AUTH
from experiments import entropygraph_v030_geometry_overlay_g04 as G04_RESEARCH
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader as STREAM
from experiments import entropygraph_v030_shared_portfolio as SHARED

REVISION = 25
G04_MAGIC = b"CMP25G4\0"
G04_TAIL = b"C25G4TL\0"
PG_MAGIC = b"CMP25PG\0"
PG_TAIL = b"C25PGTL\0"

if not all(len(value) == 8 for value in (G04_MAGIC, G04_TAIL, PG_MAGIC, PG_TAIL)):
    raise RuntimeError("revision-25 profile magics must remain exactly eight bytes")


def install_revision25_profiles() -> None:
    """Bind canonical profile identities into the single-sourced research writers/readers."""
    G04_RESEARCH.MAG = G04_MAGIC
    G04_RESEARCH.TAIL = G04_TAIL
    SHARED.MAG = G04_MAGIC
    SHARED.TAIL = G04_TAIL
    PG.MAGIC = PG_MAGIC
    PG.TAIL = PG_TAIL
    # STREAM imports the same module objects, but these explicit assignments make the contract obvious during
    # review and protect against a future refactor that snapshots constants locally.
    STREAM.G04.MAG = G04_MAGIC
    STREAM.G04.TAIL = G04_TAIL
    STREAM.PG.MAGIC = PG_MAGIC
    STREAM.PG.TAIL = PG_TAIL


install_revision25_profiles()


def _revision_for_archive(archive: Path) -> tuple[int, str]:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic == G04_MAGIC:
        return REVISION, "geometry-g04"
    if magic == PG_MAGIC:
        return REVISION, "prefixgraph-depth1"
    return 24, "inherited-r24"


def build(root: Path, out: Path) -> dict:
    install_revision25_profiles()
    stats = dict(AUTH.build(root, out))
    revision, profile = _revision_for_archive(out)
    stats.update(
        {
            "encoder_version": "0.30.0",
            "format_revision": revision,
            "format_profile": profile,
            "canonical_profile_magic": (
                G04_MAGIC.decode("ascii", errors="replace")
                if profile == "geometry-g04"
                else PG_MAGIC.decode("ascii", errors="replace")
                if profile == "prefixgraph-depth1"
                else None
            ),
            "canonical_release_facade": "cmpct-v030-r25-v1",
        }
    )
    return stats


def strong_verify(archive: Path) -> dict:
    install_revision25_profiles()
    result = dict(AUTH.strong_verify(archive))
    if result.get("ok"):
        revision, profile = _revision_for_archive(archive)
        result["format_revision"] = revision
        result["format_profile"] = profile
        result["canonical_release_facade"] = "cmpct-v030-r25-v1"
    return result


def extract(archive: Path, dst: Path, *, max_output_bytes: int = STREAM.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    install_revision25_profiles()
    AUTH.extract(archive, dst, max_output_bytes=max_output_bytes)


def treehash(root: Path) -> str:
    return AUTH.treehash(root)
