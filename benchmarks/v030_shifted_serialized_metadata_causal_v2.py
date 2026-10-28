from __future__ import annotations

"""Frozen D2/Custody causal check for Shifted serialized-metadata drift.

Evidence-only. This instrument changes no production, benchmark, or release behavior.
"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_SHIFTED_SERIALIZED_METADATA_CAUSAL_V2_PREREG.md"
FIXED_MTIME_NS = 1_767_225_600_000_000_000
REPETITIONS = 3


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _xattrs(path: Path) -> list[list[str]]:
    if not hasattr(os, "listxattr"):
        return []
    rows: list[list[str]] = []
    try:
        names = os.listxattr(path, follow_symlinks=False)
    except OSError:
        return []
    for name in names:
        try:
            value = os.getxattr(path, name, follow_symlinks=False)
        except OSError:
            continue
        raw_name = os.fsencode(name)
        rows.append([_b64(raw_name), _b64(value)])
    rows.sort()
    return rows


def _projection(root: Path) -> dict:
    """Capture the stable filesystem facts consumed by canonical Builder.scan()."""
    prior_inode: dict[tuple[int, int], str] = {}
    full: list[dict] = []
    no_mtime: list[dict] = []
    mtimes: list[int] = []
    paths = sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix())
    for path in paths:
        st = path.lstat()
        rel = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(st.st_mode)
        hardlink_to = None
        symlink_target = None
        if stat.S_ISLNK(st.st_mode):
            kind = "symlink"
            target = os.readlink(path).encode()
            symlink_target = _b64(target)
            canonical_size = len(target)
        elif stat.S_ISDIR(st.st_mode):
            kind = "dir"
            canonical_size = 0
        elif stat.S_ISREG(st.st_mode):
            inode_key = (int(st.st_dev), int(st.st_ino))
            if int(st.st_nlink) > 1 and inode_key in prior_inode:
                kind = "hardlink"
                hardlink_to = prior_inode[inode_key]
            else:
                kind = "file"
                if int(st.st_nlink) > 1:
                    prior_inode[inode_key] = rel
            canonical_size = int(st.st_size)
        else:
            # Builder ignores unsupported entry types; the projection records them so an unexpected
            # fixture mutation cannot silently disappear from the causal experiment.
            kind = "ignored-other"
            canonical_size = int(st.st_size)
        row = {
            "path": rel,
            "type": kind,
            "mode": int(mode),
            "mtime_ns": int(st.st_mtime_ns),
            "size": canonical_size,
            "uid": int(getattr(st, "st_uid", 0)),
            "gid": int(getattr(st, "st_gid", 0)),
            "xattrs": _xattrs(path),
            "hardlink_to": hardlink_to,
            "symlink_target_b64": symlink_target,
        }
        full.append(row)
        no_mtime.append({k: v for k, v in row.items() if k != "mtime_ns"})
        mtimes.append(int(st.st_mtime_ns))

    def digest(rows: list[dict]) -> str:
        payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    return {
        "entries": len(full),
        "full_projection_sha256": digest(full),
        "projection_without_mtime_sha256": digest(no_mtime),
        "mtime_min_ns": min(mtimes) if mtimes else None,
        "mtime_max_ns": max(mtimes) if mtimes else None,
        "unique_mtimes": len(set(mtimes)),
        "all_mtimes_fixed": bool(mtimes) and all(value == FIXED_MTIME_NS for value in mtimes),
    }


def _fix_mtimes(root: Path) -> None:
    # Descendants first, root last: traversal and directory updates cannot perturb the normalized values.
    paths = sorted([root, *root.rglob("*")], key=lambda p: len(p.relative_to(root).parts), reverse=True)
    for path in paths:
        os.utime(path, ns=(FIXED_MTIME_NS, FIXED_MTIME_NS), follow_symlinks=False)
    for path in [root, *root.rglob("*")]:
        if int(path.lstat().st_mtime_ns) != FIXED_MTIME_NS:
            raise RuntimeError(f"mtime normalization did not stick: {path}")


def _one(work_root: Path, arm: str, rep: int, expected_historical: str) -> dict:
    slot = work_root / f"{arm}-r{rep}"
    source = PERF._build_corpora(slot / "corpus")[TARGET]
    historical_before = GENERAL._historical_treehash(source)
    if historical_before != expected_historical:
        raise RuntimeError(f"historical Shifted identity drift before intervention: {historical_before}")
    before_projection = _projection(source)
    if arm == "fixed-mtime":
        _fix_mtimes(source)
    elif arm != "fresh":
        raise RuntimeError(f"unknown arm: {arm}")
    historical_after = GENERAL._historical_treehash(source)
    if historical_after != expected_historical:
        raise RuntimeError("metadata arm changed accepted historical content identity")
    projection = _projection(source)
    if arm == "fixed-mtime" and before_projection["projection_without_mtime_sha256"] != projection["projection_without_mtime_sha256"]:
        raise RuntimeError("mtime normalization changed a non-mtime serialized filesystem fact")

    r24 = slot / "genuine-r24.cmpct"
    PRODUCT._locality_bounded_r24_build(source, r24)
    product_tree = str(PRODUCT.treehash(source))
    verify = dict(PRODUCT.strong_verify(r24))
    if not verify.get("ok") or str(verify.get("tree_sha256") or "") != product_tree:
        raise RuntimeError(f"genuine r24 strong verification failed for {arm}/r{rep}")
    return {
        "arm": arm,
        "rep": rep,
        "historical_tree_sha256": historical_after,
        "logical_tree_sha256": product_tree,
        "projection": projection,
        "r24_bytes": r24.stat().st_size,
        "r24_sha256": _sha(r24),
        "strong_verify_ok": bool(verify.get("ok")),
        "verified_tree_sha256": verify.get("tree_sha256"),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    expected_historical = str(GENERAL._accepted_v029_rows()[TARGET]["tree_sha256"])
    rows: list[dict] = []
    failures: list[str] = []
    try:
        for arm in ("fresh", "fixed-mtime"):
            for rep in range(REPETITIONS):
                rows.append(_one(work_root, arm, rep, expected_historical))
    except Exception as exc:
        failures.append(f"{type(exc).__name__}:{exc}")

    fresh = [r for r in rows if r["arm"] == "fresh"]
    fixed = [r for r in rows if r["arm"] == "fixed-mtime"]

    def values(group: list[dict], path: tuple[str, ...]) -> set:
        out = set()
        for row in group:
            value = row
            for key in path:
                value = value[key]
            out.add(value)
        return out

    valid = (
        not failures
        and len(fresh) == REPETITIONS
        and len(fixed) == REPETITIONS
        and all(r["historical_tree_sha256"] == expected_historical for r in rows)
        and len(values(rows, ("logical_tree_sha256",))) == 1
        and all(r["strong_verify_ok"] and r["verified_tree_sha256"] == r["logical_tree_sha256"] for r in rows)
        and all(r["projection"]["all_mtimes_fixed"] for r in fixed)
    )
    decision = "INVALID_EXPERIMENT"
    if valid:
        fresh_without = values(fresh, ("projection", "projection_without_mtime_sha256"))
        fixed_without = values(fixed, ("projection", "projection_without_mtime_sha256"))
        supported = (
            len(values(fresh, ("r24_bytes",))) > 1
            and len(values(fresh, ("r24_sha256",))) > 1
            and len(values(fresh, ("projection", "full_projection_sha256"))) > 1
            and len(fresh_without) == 1
            and len(values(fixed, ("projection", "full_projection_sha256"))) == 1
            and len(fixed_without) == 1
            and fresh_without == fixed_without
            and len(values(fixed, ("r24_bytes",))) == 1
            and len(values(fixed, ("r24_sha256",))) == 1
        )
        decision = "SHIFTED_MTIME_SERIALIZED_METADATA_CAUSAL_SUPPORTED" if supported else "SHIFTED_MTIME_SERIALIZED_METADATA_NOT_SUFFICIENT"

    observed = {
        "fresh_r24_bytes": sorted(values(fresh, ("r24_bytes",))) if fresh else [],
        "fresh_r24_sha256": sorted(values(fresh, ("r24_sha256",))) if fresh else [],
        "fresh_full_projection_sha256": sorted(values(fresh, ("projection", "full_projection_sha256"))) if fresh else [],
        "fresh_projection_without_mtime_sha256": sorted(values(fresh, ("projection", "projection_without_mtime_sha256"))) if fresh else [],
        "fixed_r24_bytes": sorted(values(fixed, ("r24_bytes",))) if fixed else [],
        "fixed_r24_sha256": sorted(values(fixed, ("r24_sha256",))) if fixed else [],
        "fixed_full_projection_sha256": sorted(values(fixed, ("projection", "full_projection_sha256"))) if fixed else [],
        "fixed_projection_without_mtime_sha256": sorted(values(fixed, ("projection", "projection_without_mtime_sha256"))) if fixed else [],
    }
    return {
        "schema": "cmpct-v030-shifted-serialized-metadata-causal-v2",
        "source_commit": _head(),
        "preregistration": PREREG,
        "target": list(TARGET),
        "expected_historical_tree_sha256": expected_historical,
        "fixed_mtime_ns": FIXED_MTIME_NS,
        "repetitions_per_arm": REPETITIONS,
        "rows": rows,
        "experiment_valid": valid,
        "failures": failures,
        "decision": decision,
        "observed_sets": observed,
        "contract": {
            "metadata_intervention": "atime+mtime only",
            "historical_content_identity_must_not_change": True,
            "canonical_projection_fields": ["path", "type", "mode", "mtime_ns", "size", "uid", "gid", "xattrs", "hardlink_to", "symlink_target_b64"],
            "release_thresholds_changed": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shifted-serialized-metadata-causal-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shifted-serialized-metadata-causal-v2.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"experiment_valid": data["experiment_valid"], "decision": data["decision"], "observed_sets": data["observed_sets"]}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("Shifted serialized-metadata causal v2 experiment invalid")


if __name__ == "__main__":
    main()
