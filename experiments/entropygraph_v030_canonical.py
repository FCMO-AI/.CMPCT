"""Canonical CMPCT v0.30 product surface for provisional revision 25.

The v0.30 research campaign proved two useful content representations, but a canonical archive cannot silently
throw away filesystem semantics or relabel an inherited ``CMPNX*`` research artifact as revision 24. This
module owns the product boundary and publishes only one of three truthful archive states:

- ``CMP25G4\0`` — revision-25 G0-G4 Geometry-over-Mosaic content profile;
- ``CMP25PG\0`` — revision-25 bounded depth-1 PrefixGraph content profile;
- ``CMPCT24\0`` — genuine canonical revision-24 fallback.

Revision-25 profiles carry an authenticated reserved filesystem manifest as an ordinary graph member. The
manifest is implemented in ``entropygraph_v030_product_fs`` and restores the semantics the research content
graphs intentionally did not model: directories, mode/time/ownership/xattrs, symlinks, and hardlinks. Sparse
or special-file trees currently fall back to r24 rather than being flattened into a weaker representation.

PrefixGraph is promoted as an alternative canonical *content* profile instead of being inserted into Mosaic's
node grammar. Its depth-1 raw-prefix relationship has independent complete-artifact evidence, while no current
ablation proves that splicing that relation into Mosaic preserves or improves final bytes after locality,
metadata, reader, and portability costs. Canonical selection therefore prices complete G0-G4 and PrefixGraph
artifacts and never adds their independent savings arithmetically.

Accepted v0.29 remains an exact research/ablation floor. It can emit ``CMPNX11`` or an inherited research
fallback, so those bytes are never described or published as r24 by this module.

Footnote: the reader is deliberately simpler than the encoder. It never repeats Geometry nomination, separator
search, PrefixGraph anchor search, or portfolio heuristics. It dispatches one selected profile, validates its
bounded authenticated metadata plus the filesystem manifest, and reconstructs the declared tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from cmpct import codec as R24_CODEC
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_geometry_overlay_g04 as G04_RESEARCH
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_admission as ADMISSION
from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader_policy as POLICY
from experiments import entropygraph_v030_shared_portfolio as SHARED

REVISION = 25
G04_MAGIC = b"CMP25G4\0"
G04_TAIL = b"C25G4TL\0"
PG_MAGIC = b"CMP25PG\0"
PG_TAIL = b"C25PGTL\0"
R24_MAGIC = R24_CODEC.MAGIC

MAX_PROFILE_FILES = min(POLICY.R.MAX_FILES - 1, 65_535)
MAX_PROFILE_LOGICAL_BYTES = POLICY.R.MAX_DECLARED_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = POLICY.R.MAX_FILES

if not all(len(value) == 8 for value in (G04_MAGIC, G04_TAIL, PG_MAGIC, PG_TAIL, R24_MAGIC)):
    raise RuntimeError("canonical CMPCT profile magics must remain exactly eight bytes")


class UnsupportedArchiveProfile(RuntimeError):
    """Input bytes are not a canonical r24/r25 product archive."""


# Preserve the narrow exception as part of the product-facing API while keeping filesystem grammar ownership in
# one module. Callers can distinguish "valid input, r25 not eligible" from corruption/programming failures.
ProfileNotEligible = FS.ProfileNotEligible


def install_revision25_profiles() -> None:
    """Bind stable r25 identities into the single-sourced content writers/readers.

    The research modules remain useful causal implementations. Canonical publication changes only fixed-width
    profile identities; transform/reference semantics continue to live in one owner. These assignments are
    intentionally explicit so a reviewer can see every module object participating in r25 dispatch.
    """
    G04_RESEARCH.MAG = G04_MAGIC
    G04_RESEARCH.TAIL = G04_TAIL
    SHARED.MAG = G04_MAGIC
    SHARED.TAIL = G04_TAIL
    PG.MAGIC = PG_MAGIC
    PG.TAIL = PG_TAIL
    POLICY.R.G04.MAG = G04_MAGIC
    POLICY.R.G04.TAIL = G04_TAIL
    POLICY.R.PG.MAGIC = PG_MAGIC
    POLICY.R.PG.TAIL = PG_TAIL


install_revision25_profiles()
POLICY.install_policy()

# The exact complete-artifact tournament resolves these globals at runtime. Canonical product code binds the
# selected semantic owners directly instead of routing through the now-historical ``authoritative`` facade.
RC.G04 = SHARED
RC._prefixgraph_eligibility = ADMISSION.prefixgraph_eligibility
RC._prefixgraph_locality = ADMISSION.prefixgraph_locality


def _prepare_profile_tree(root: Path, staging_root: Path) -> dict:
    prepared = FS.prepare_profile_tree(
        root,
        staging_root,
        max_path_bytes=POLICY.R.MAX_PATH_BYTES,
        max_profile_files=MAX_PROFILE_FILES,
        max_profile_logical_bytes=MAX_PROFILE_LOGICAL_BYTES,
    )
    if int(prepared["entries"]) > MAX_MANIFEST_ENTRIES:
        raise ProfileNotEligible("r25 filesystem manifest entry count exceeds reader policy")
    return prepared


def _magic(archive: Path) -> bytes:
    with Path(archive).open("rb") as stream:
        return stream.read(8)


def _profile_for_archive(archive: Path) -> tuple[int | None, str]:
    """Classify bytes without ever laundering a research grammar into a canonical revision."""
    magic = _magic(archive)
    if magic == G04_MAGIC:
        return REVISION, "geometry-g04"
    if magic == PG_MAGIC:
        return REVISION, "prefixgraph-depth1"
    if magic == R24_MAGIC:
        return 24, "canonical-r24"
    if magic.startswith(b"CMPNX"):
        return None, "research-only"
    return None, "unknown"


def _revision_for_archive(archive: Path) -> tuple[int | None, str]:
    """Compatibility alias retained for callers of the earlier facade."""
    return _profile_for_archive(archive)


def _read_g04_member(archive: Path, rel: str) -> bytes:
    session = POLICY.R._G04Session(archive)
    try:
        desc = session.meta["files"].get(rel)
        if desc is None:
            raise KeyError(rel)
        if desc[0] == "preflate":
            raw = session.record(int(desc[1]))
        elif desc[0] == "nodes":
            raw = b"".join(session.node(int(node_id)) for node_id in desc[1])
        else:  # pragma: no cover - strict reader policy rejects this before product dispatch.
            raise RuntimeError("unknown G0-G4 file descriptor")
        if len(raw) != int(desc[2]) or hashlib.sha256(raw).digest() != bytes(desc[3]):
            raise RuntimeError("G0-G4 member integrity mismatch")
        return raw
    finally:
        session.close()


def _read_pg_member(archive: Path, rel: str) -> bytes:
    session = POLICY.R._PGSession(archive)
    try:
        try:
            index = session.meta["files"].index(rel)
        except ValueError as exc:
            raise KeyError(rel) from exc
        return session.file(index)
    finally:
        session.close()


def _read_profile_content_member(archive: Path, rel: str) -> bytes:
    revision, profile = _profile_for_archive(archive)
    if revision != REVISION:
        raise UnsupportedArchiveProfile(f"not a revision-25 content profile: {profile}")
    if profile == "geometry-g04":
        return _read_g04_member(archive, rel)
    if profile == "prefixgraph-depth1":
        return _read_pg_member(archive, rel)
    raise UnsupportedArchiveProfile(profile)


def _profile_content_identities(archive: Path) -> dict[str, tuple[int, bytes]]:
    """Return authenticated logical content identities without decoding every regular member."""
    revision, profile = _profile_for_archive(archive)
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    if profile == "geometry-g04":
        session = POLICY.R._G04Session(archive)
        try:
            return {
                rel: (int(desc[2]), bytes(desc[3]))
                for rel, desc in session.meta["files"].items()
            }
        finally:
            session.close()
    session = POLICY.R._PGSession(archive)
    try:
        return {
            rel: (int(desc[2]), bytes(desc[5]))
            for rel, desc in zip(session.meta["files"], session.records, strict=True)
        }
    finally:
        session.close()


def _validated_manifest(archive: Path) -> dict:
    raw = _read_profile_content_member(archive, FS.FILESYSTEM_MANIFEST)
    decoded = FS.decode_manifest(
        raw,
        max_path_bytes=POLICY.R.MAX_PATH_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    )
    content = _profile_content_identities(archive)
    expected_paths = set(decoded["regular"]) | {FS.FILESYSTEM_MANIFEST}
    if set(content) != expected_paths:
        raise RuntimeError("r25 content profile and filesystem manifest disagree on logical members")
    if content[FS.FILESYSTEM_MANIFEST] != (len(raw), hashlib.sha256(raw).digest()):
        raise RuntimeError("r25 filesystem manifest graph identity mismatch")
    for rel, identity in decoded["regular"].items():
        if content.get(rel) != identity:
            raise RuntimeError(f"r25 manifest/content identity mismatch: {rel}")
    return decoded


def _r24_build(root: Path, out: Path) -> dict:
    """Build and strongly verify the genuine canonical revision-24 semantic floor."""
    stats = dict(Builder(Path(root)).build(Path(out)))
    with CMPCT(out) as reader:
        verified_files = reader.verify()
    return {
        **stats,
        "archive_bytes": Path(out).stat().st_size,
        "format_revision": 24,
        "format_profile": "canonical-r24",
        "verified_files": verified_files,
    }


def _publish_atomic(source: Path, out: Path) -> None:
    size = source.stat().st_size
    os.replace(source, out)
    if out.stat().st_size != size:
        raise RuntimeError("canonical publication changed selected archive size")


def _build_ablation_prepared(staged_root: Path, out: Path, mode: str) -> dict:
    """Build one causal representation over an already charged filesystem-manifest tree."""
    install_revision25_profiles()
    if mode == "v029":
        stats = dict(G04_RESEARCH.BASE.build(staged_root, out))
        return {**stats, "ablation": "v029", "canonical_publication": False}
    if mode == "geometry":
        stats = dict(SHARED.build(staged_root, out))
        return {**stats, "ablation": "geometry", "canonical_publication": False}
    if mode == "prefixgraph":
        expected_tree = PG.treehash(staged_root)
        eligible, reason = ADMISSION.prefixgraph_eligibility(staged_root, expected_tree)
        if not eligible:
            raise ProfileNotEligible(f"PrefixGraph ablation rejected: {reason}")
        stats = dict(PG.build(staged_root, out))
        locality = ADMISSION.prefixgraph_locality(out)
        if not locality.get("passed"):
            raise ProfileNotEligible("PrefixGraph ablation exceeded locality ceiling")
        verified = POLICY.strong_verify(out)
        if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
            raise RuntimeError("PrefixGraph ablation failed strict verification")
        return {
            **stats,
            "ablation": "prefixgraph",
            "prefixgraph_locality": locality,
            "canonical_publication": False,
        }
    if mode == "combined":
        stats = dict(RC.build(staged_root, out))
        return {
            **stats,
            "ablation": "combined-complete-artifact-tournament",
            "canonical_publication": False,
        }
    raise ValueError(f"unknown v0.30 ablation mode: {mode}")


def build_ablation(root: Path, out: Path, mode: str) -> dict:
    """Build exact v0.29 / Geometry / PrefixGraph / combined causal artifacts.

    All graph ablations consume the same staged filesystem manifest, so metadata cost is charged rather than
    borrowed from the product wrapper. ``combined`` means a complete-artifact tournament, not arithmetic
    addition of Geometry and PrefixGraph savings.
    """
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-ablation-", dir=out.parent) as td:
        staged = Path(td) / "tree"
        prepared = _prepare_profile_tree(root, staged)
        stats = _build_ablation_prepared(staged, out, mode)
        stats["filesystem_manifest_sha256"] = prepared["manifest_sha256"]
        stats["filesystem_manifest_bytes"] = prepared["manifest_bytes"]
        return stats


def build(root: Path, out: Path) -> dict:
    """Build one canonical r25 winner or a genuine revision-24 compatibility fallback.

    The r25 tournament is evaluated first because a *real* r25 output already proves strict improvement over
    the accepted-v0.29 research floor: G0-G4 emits r25 only when its complete artifact beats v0.29, and the
    PrefixGraph selector can replace that result only with a still-smaller complete archive. Building r24 before
    that decision would add an avoidable full encode to every successful r25 creation and violate the release
    campaign's create-time discipline.

    A genuine r24 archive is built only when r25 cannot lawfully cross the product boundary: unsupported
    filesystem semantics or an internal ``CMPNX*`` research fallback. This keeps the compatibility fallback exact
    without charging its creation cost to successful r25 winners.
    """
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-canonical-", dir=out.parent) as td:
        temp = Path(td)
        candidate_path = temp / "candidate-r25-or-research.cmpct"
        r24_path = temp / "canonical-r24.cmpct"

        try:
            staged = temp / "profile-tree"
            prepared = _prepare_profile_tree(root, staged)
        except ProfileNotEligible as exc:
            r24_stats = _r24_build(root, r24_path)
            _publish_atomic(r24_path, out)
            verified = strong_verify(out)
            return {
                "selected": "r24-fallback",
                "archive_bytes": out.stat().st_size,
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "r24_built": True,
                "r24_bytes": out.stat().st_size,
                "r25_attempted": False,
                "r25_reject_reason": str(exc),
                "r24": r24_stats,
                "final_strong_verify": verified,
                "release_facade": "cmpct-v030-canonical-product-v2",
            }

        research = _build_ablation_prepared(staged, candidate_path, "combined")
        research_revision, research_profile = _profile_for_archive(candidate_path)
        research_bytes = candidate_path.stat().st_size
        v029_floor = int(research.get("v029_bytes", research_bytes))

        if research_revision == REVISION:
            # A canonical r25 winner must have earned its identity through the complete-artifact tournament. A
            # non-improving r25 profile here would mean an upstream selector invariant regressed.
            if research_bytes >= v029_floor:
                raise RuntimeError("r25 candidate did not strictly beat accepted-v0.29 complete bytes")
            _publish_atomic(candidate_path, out)
            selected = str(research.get("selected", research_profile))
            r24_stats = None
        else:
            # Accepted-v0.29 bytes are valuable evidence but remain CMPNX research grammar. Product fallback is
            # therefore created by the real r24 builder rather than by changing eight magic bytes or wrapping the
            # research artifact in a cosmetic container.
            r24_stats = _r24_build(root, r24_path)
            _publish_atomic(r24_path, out)
            selected = "r24-fallback"

        final_revision, final_profile = _profile_for_archive(out)
        verified = strong_verify(out)
        if not verified.get("ok"):
            raise RuntimeError(f"canonical v0.30 publication failed strong verification: {verified!r}")
        if final_revision not in (24, REVISION):
            raise RuntimeError("canonical v0.30 product published a non-canonical profile")

        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "format_revision": final_revision,
            "format_profile": final_profile,
            "r24_built": final_revision == 24,
            "r24_bytes": out.stat().st_size if final_revision == 24 else None,
            "r25_attempted": True,
            "r25_candidate_bytes": research_bytes if research_revision == REVISION else None,
            "r25_candidate_profile": research_profile if research_revision == REVISION else None,
            "research_tournament_selected": research.get("selected"),
            "research_tournament_profile": research_profile,
            "research_tournament_bytes": research_bytes,
            "v029_research_floor_bytes": v029_floor,
            "r25_smaller_than_v029_research_floor": bool(
                research_revision == REVISION and research_bytes < v029_floor
            ),
            "filesystem_manifest_sha256": prepared["manifest_sha256"],
            "filesystem_manifest_bytes": prepared["manifest_bytes"],
            "filesystem_manifest_entries": prepared["entries"],
            "regular_graph_members": prepared["regular_graph_members"],
            "r24": r24_stats,
            "research_tournament": research,
            "final_strong_verify": verified,
            "release_facade": "cmpct-v030-canonical-product-v2",
            "claim_boundary": (
                "real r25 winner strictly improves accepted-v0.29 complete bytes; otherwise canonical publication "
                "uses a freshly built genuine r24 compatibility archive and never relabels CMPNX research bytes"
            ),
        }


def strong_verify(archive: Path) -> dict:
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision == REVISION:
        base = dict(POLICY.strong_verify(archive))
        if not base.get("ok"):
            return {**base, "format_revision": revision, "format_profile": profile}
        try:
            manifest = _validated_manifest(archive)
        except Exception as exc:
            return {
                "ok": False,
                "error": repr(exc),
                "format_revision": revision,
                "format_profile": profile,
                "reader": "cmpct-v030-canonical-product-v2",
            }
        return {
            **base,
            "format_revision": revision,
            "format_profile": profile,
            "filesystem_manifest_sha256": hashlib.sha256(manifest["raw"]).hexdigest(),
            "filesystem_entries": len(manifest["manifest"]["entries"]),
            "filesystem_semantics_verified": True,
            "canonical_release_facade": "cmpct-v030-canonical-product-v2",
        }
    if revision == 24:
        try:
            with CMPCT(archive) as reader:
                files = reader.verify()
            return {
                "ok": True,
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "verified_files": files,
                "reader": "cmpct-r24-reference-reader",
                "canonical_release_facade": "cmpct-v030-canonical-product-v2",
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": repr(exc),
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "reader": "cmpct-r24-reference-reader",
            }
    return {
        "ok": False,
        "error": (
            "research-only CMPNX bytes are not canonical r24/r25"
            if profile == "research-only"
            else "unknown CMPCT profile"
        ),
        "format_revision": None,
        "format_profile": profile,
        "reader": "cmpct-v030-canonical-product-v2",
    }


def read_member(archive: Path, rel: str) -> bytes:
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision == 24:
        with CMPCT(archive) as reader:
            return bytes(reader.read(rel))
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)

    decoded = _validated_manifest(archive)
    row = FS.entry_map(decoded).get(rel)
    if row is None:
        raise KeyError(rel)
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        return row[7].encode("utf-8", "surrogateescape")
    if kind == "h":
        return read_member(archive, row[7])
    return _read_profile_content_member(archive, rel)


def list_members(archive: Path) -> list[dict]:
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision == 24:
        with CMPCT(archive) as reader:
            kind_names = {
                R24_CODEC.K_FILE: "file",
                R24_CODEC.K_DIR: "directory",
                R24_CODEC.K_SYMLINK: "symlink",
                R24_CODEC.K_HARDLINK: "hardlink",
            }
            return [
                {"path": row[0], "kind": kind_names.get(row[1], "unknown"), "size": int(row[4])}
                for row in reader.files
            ]
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    decoded = _validated_manifest(archive)
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    rows = []
    for row in decoded["manifest"]["entries"]:
        size = int(row[7][0]) if row[1] == "f" else 0
        rows.append({"path": row[0], "kind": names[row[1]], "size": size})
    return rows


def _remove_backup_best_effort(backup: Path) -> None:
    try:
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink(missing_ok=True)
    except OSError:
        # Footnote: once a fully verified staged tree is installed, stale-backup cleanup is housekeeping rather
        # than archive integrity. Keeping a uniquely named backup is safer than pretending publication failed.
        pass


def _publish_tree(staging: Path, dst: Path) -> None:
    backup = dst.parent / f".{dst.name}.cmpct-v030-backup-{uuid.uuid4().hex}"
    moved_old = False
    installed = False
    try:
        if dst.exists() or dst.is_symlink():
            os.replace(dst, backup)
            moved_old = True
        os.replace(staging, dst)
        installed = True
    except Exception:
        if moved_old and not (dst.exists() or dst.is_symlink()) and (backup.exists() or backup.is_symlink()):
            os.replace(backup, dst)
        raise
    else:
        if moved_old:
            _remove_backup_best_effort(backup)
    finally:
        if not installed and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    """Extract canonical r24/r25 transactionally without exposing the reserved r25 manifest."""
    archive = Path(archive)
    dst = Path(dst)
    revision, profile = _profile_for_archive(archive)
    if revision not in (24, REVISION):
        raise UnsupportedArchiveProfile(profile)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    dst.parent.mkdir(parents=True, exist_ok=True)
    wrapper = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-stage-", dir=dst.parent))
    publish_root = wrapper
    try:
        if revision == 24:
            with CMPCT(archive) as reader:
                reader.extractall(wrapper, max_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
        else:
            decoded = _validated_manifest(archive)
            content_root = wrapper / "tree"
            # The content extractor accounts the internal manifest as a logical member. Add only its bounded
            # maximum to the caller's user-visible budget; the final restored tree still cannot exceed the
            # caller's requested regular-file bytes by silently materializing archive metadata.
            internal_budget = min(
                POLICY.R.MAX_DECLARED_LOGICAL_BYTES,
                max_output_bytes + FS.MAX_MANIFEST_BYTES,
            )
            POLICY.extract(archive, content_root, max_output_bytes=internal_budget)
            FS.restore_manifest_tree(content_root, decoded, safe_symlinks=safe_symlinks)
            user_bytes = sum(int(identity[0]) for identity in decoded["regular"].values())
            if user_bytes > max_output_bytes:
                raise RuntimeError("r25 extraction exceeds caller output budget")
            publish_root = content_root
        _publish_tree(publish_root, dst)
    except Exception:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)
        raise
    else:
        # r25 moves ``wrapper/tree`` and leaves an empty wrapper directory behind; r24 moves wrapper itself.
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)


def treehash(root: Path) -> str:
    """Return the historical v0.30 content-tree hash used by graph ablations.

    Canonical filesystem identity additionally lives in ``filesystem_manifest_sha256`` because r25 binds
    metadata/directories/links that the historical research tree hash intentionally did not model.
    """
    return G04_RESEARCH.treehash(Path(root))


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.30 canonical r25/r24 product surface")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pack")
    p.add_argument("source", type=Path)
    p.add_argument("archive", type=Path)

    p = sub.add_parser("verify")
    p.add_argument("archive", type=Path)

    p = sub.add_parser("list")
    p.add_argument("archive", type=Path)

    p = sub.add_parser("read")
    p.add_argument("archive", type=Path)
    p.add_argument("member")
    p.add_argument("--output", type=Path)

    p = sub.add_parser("extract")
    p.add_argument("archive", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("--max-output-bytes", type=int, default=POLICY.DEFAULT_MAX_EXTRACT_BYTES)
    p.add_argument("--unsafe-symlinks", action="store_true")

    p = sub.add_parser("ablate")
    p.add_argument("mode", choices=("v029", "geometry", "prefixgraph", "combined"))
    p.add_argument("source", type=Path)
    p.add_argument("archive", type=Path)

    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    elif args.cmd == "list":
        print(json.dumps(list_members(args.archive), indent=2, default=str))
    elif args.cmd == "read":
        raw = read_member(args.archive, args.member)
        if args.output is None:
            os.write(1, raw)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(raw)
    elif args.cmd == "extract":
        extract(
            args.archive,
            args.destination,
            max_output_bytes=args.max_output_bytes,
            safe_symlinks=not args.unsafe_symlinks,
        )
        print(json.dumps({"ok": True}, indent=2))
    else:
        print(json.dumps(build_ablation(args.source, args.archive, args.mode), indent=2, default=str))


if __name__ == "__main__":
    _main()
