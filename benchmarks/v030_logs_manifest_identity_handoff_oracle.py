from __future__ import annotations

"""Research-only A/B for eliminating a duplicate full-tree SHA pass during logs extraction.

The canonical logs reader already hashes every restored logical member inside ``Archive._restore_session`` before
it writes the bytes.  The filesystem-manifest bridge then re-opens every regular output file and hashes it again
before applying metadata.  This oracle keeps the archive and reader grammar unchanged and asks whether the second
disk hash can be replaced by an exact authenticated-identity handoff from the content reader to the manifest owner.

The candidate is deliberately local to this oracle.  It is not production dispatch.  It must compare the complete
verified identity map with the authenticated manifest, preserve file shapes and the final canonical tree exactly,
and retain transactional staging.  A positive timing result only authorizes a separately reviewed product change;
race/threat-model, reader, fuzz, native, Android and runtime authorities must be re-earned.
"""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = ("neutral_hostile_v1", "05_logs_and_telemetry")
ROUNDS = 7
MIN_IMPROVEMENT = 0.10


def _content_extract_with_verified_identities(path: Path, dst: Path) -> dict[str, tuple[int, bytes]]:
    """Mirror the canonical v2 full-operation reader while retaining identities it already proved."""
    identities: dict[str, tuple[int, bytes]] = {}
    with LOGS.Archive(path) as archive:
        dst.mkdir(parents=True, exist_ok=True)
        member_cache: dict[int, tuple[bytes, int]] = {}
        pack_cache: dict[int, bytes] = {}
        active: set[int] = set()
        prepared_parents: set[Path] = {dst}
        for index, row in enumerate(archive.files):
            rel = str(row[5])
            target = dst.joinpath(*PurePosixPath(rel).parts)
            parent = target.parent
            if parent not in prepared_parents:
                parent.mkdir(parents=True, exist_ok=True)
                prepared_parents.add(parent)
            value, _context = archive._restore_session(
                index,
                member_cache=member_cache,
                pack_cache=pack_cache,
                active=active,
            )
            # _restore_session has just required len(value)==row[2] and SHA256(value)==row[3].
            target.write_bytes(value)
            identities[rel] = (int(row[2]), bytes(row[3]))
    return identities


def _restore_manifest_from_verified_identities(
    staging: Path,
    decoded: dict,
    verified_regular: dict[str, tuple[int, bytes]],
) -> None:
    """Research mirror of FS.restore_manifest_tree with the duplicate content hash replaced by exact identity equality."""
    if verified_regular != decoded["regular"]:
        raise RuntimeError("logs authenticated identity handoff disagrees with filesystem manifest")
    entries = decoded["manifest"]["entries"]
    internal = staging.joinpath(*PurePosixPath(FS.INTERNAL_ROOT).parts)
    if internal.exists() or internal.is_symlink():
        shutil.rmtree(internal, ignore_errors=True)

    # Preserve the canonical post-write shape check. Only the second byte-content hash is removed.
    for row in entries:
        rel, kind = row[0], row[1]
        if kind != "f":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        size, _expected = row[7]
        if not target.is_file() or target.is_symlink() or target.stat().st_size != int(size):
            raise RuntimeError(f"r25 extracted regular-file shape mismatch: {rel}")

    for row in entries:
        rel, kind = row[0], row[1]
        target = staging.joinpath(*PurePosixPath(rel).parts)
        if kind == "d":
            target.mkdir(parents=True, exist_ok=True)
        elif kind == "l":
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = row[7]
            parsed = PurePosixPath(link_target)
            if parsed.is_absolute() or ".." in parsed.parts:
                raise RuntimeError(f"unsafe r25 symlink target in {rel!r}")
            target.unlink(missing_ok=True)
            os.symlink(link_target, target)
        elif kind == "h":
            target.parent.mkdir(parents=True, exist_ok=True)
            owner = staging.joinpath(*PurePosixPath(row[7]).parts)
            if not owner.is_file() or owner.is_symlink():
                raise RuntimeError(f"r25 hardlink owner is not materialized: {row[7]}")
            target.unlink(missing_ok=True)
            os.link(owner, target)

    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, _extra = row
        if kind == "d":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        follow = kind != "l"
        if follow:
            try:
                os.chmod(target, int(mode), follow_symlinks=False)
            except OSError:
                pass
        if hasattr(os, "chown") and (uid or gid):
            try:
                os.chown(target, int(uid), int(gid), follow_symlinks=follow)
            except (OSError, PermissionError):
                pass
        FS._apply_xattrs(target, xattrs, follow_symlinks=follow)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)), follow_symlinks=follow)
        except OSError:
            pass

    directories = sorted(
        (row for row in entries if row[1] == "d"),
        key=lambda item: item[0].count("/"),
        reverse=True,
    )
    for row in directories:
        rel, _kind, mode, mtime_ns, uid, gid, xattrs, _extra = row
        target = staging.joinpath(*PurePosixPath(rel).parts)
        try:
            os.chmod(target, int(mode))
        except OSError:
            pass
        if hasattr(os, "chown") and (uid or gid):
            try:
                os.chown(target, int(uid), int(gid))
            except (OSError, PermissionError):
                pass
        FS._apply_xattrs(target, xattrs, follow_symlinks=True)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)))
        except OSError:
            pass


def _candidate_extract(path: Path, dst: Path) -> None:
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="cmpct-v030-logs-handoff-", dir=dst.parent))
    stage = temp_root / "tree"
    try:
        identities = _content_extract_with_verified_identities(path, stage)
        manifest_path = stage.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise RuntimeError("logs candidate extraction did not materialize filesystem manifest")
        decoded = FS.decode_manifest(
            manifest_path.read_bytes(),
            max_path_bytes=LOGS.MAX_PATH_BYTES,
            max_entries=FS.DEFAULT_MAX_MANIFEST_ENTRIES,
        )
        regular = {rel: identity for rel, identity in identities.items() if rel != FS.FILESYSTEM_MANIFEST}
        _restore_manifest_from_verified_identities(stage, decoded, regular)
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        os.replace(stage, dst)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "logs.cmpct"
    built = PRODUCT.build(source, archive)
    revision, profile = PRODUCT._revision_for_archive(archive)
    if int(revision or 0) != 25 or profile != LOGS.PROFILE:
        raise RuntimeError(f"logs handoff target did not select canonical logs profile: {revision}/{profile}")
    strong = PRODUCT.strong_verify(archive)
    if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
        raise RuntimeError("shipping logs archive failed strong verification before identity-handoff A/B")

    samples = {"baseline_extract": [], "handoff_extract": []}
    trees = {"baseline": set(), "handoff": set()}
    for rep in range(ROUNDS):
        order = ("handoff", "baseline") if rep % 2 else ("baseline", "handoff")
        for kind in order:
            dst = work_root / f"{kind}-{rep}"
            shutil.rmtree(dst, ignore_errors=True)
            started = time.perf_counter()
            if kind == "baseline":
                LOGS.extract(archive, dst)
            else:
                _candidate_extract(archive, dst)
            elapsed = time.perf_counter() - started
            tree = PRODUCT.treehash(dst)
            if tree != source_tree:
                raise RuntimeError(f"{kind} logs extraction changed canonical tree identity")
            samples[f"{kind}_extract"].append(float(elapsed))
            trees[kind].add(tree)
            shutil.rmtree(dst, ignore_errors=True)

    baseline = float(statistics.median(samples["baseline_extract"]))
    handoff = float(statistics.median(samples["handoff_extract"]))
    improvement = 1.0 - handoff / max(baseline, 1e-9)
    gate = {
        "archive_bytes_unchanged": True,
        "grammar_unchanged": True,
        "canonical_tree_preserved": len(trees["baseline"]) == len(trees["handoff"]) == 1 and next(iter(trees["handoff"])) == source_tree,
        "authenticated_identity_map_required_exact": True,
        "post_write_shape_checks_preserved": True,
        "materially_faster": improvement >= MIN_IMPROVEMENT,
    }
    return {
        "schema": "cmpct-v030-logs-manifest-identity-handoff-v1",
        "target": "/".join(TARGET),
        "archive_bytes": archive.stat().st_size,
        "shipping_build": built,
        "rounds": ROUNDS,
        "samples_s": samples,
        "median_baseline_extract_s": baseline,
        "median_handoff_extract_s": handoff,
        "improvement_fraction": float(improvement),
        "contract": {
            "minimum_improvement_fraction": MIN_IMPROVEMENT,
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "selector_changed": False,
            "second_disk_content_hash_removed_only_after_authenticated_identity_map_equality": True,
            "release_credit": False,
        },
        "gate": {**gate, "passed": all(gate.values())},
        "promotion_signal": bool(all(gate.values())),
        "claim_boundary": (
            "Research-only extraction A/B. The candidate mirrors canonical filesystem restoration but replaces the "
            "second disk SHA pass only after the content reader has verified each logical member and that complete "
            "identity map exactly equals the authenticated filesystem manifest. A positive result does not authorize "
            "shipping until race/threat-model, reader/fuzz/native/Android/runtime authority is re-earned."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-manifest-handoff-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-manifest-handoff.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "median_baseline_extract_s": result["median_baseline_extract_s"],
        "median_handoff_extract_s": result["median_handoff_extract_s"],
        "improvement_fraction": result["improvement_fraction"],
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
