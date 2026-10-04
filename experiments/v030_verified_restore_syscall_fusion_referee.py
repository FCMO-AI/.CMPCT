from __future__ import annotations

"""Research-only A/B for fusing verified r25 shape checks into metadata restore.

The release product currently traverses every authenticated regular file once for a
path/type/size guard and then traverses non-directories again to apply metadata.
This referee asks the narrower causal question from issue #99: can the regular-file
shape guard reuse the metadata pass's one ``lstat`` and skip a redundant ``chmod``
when the stored mode is already present, without changing any archive bytes,
authentication, link semantics, metadata, rollback, or publication behavior?

The shipping helper is not edited by this experiment.  A fresh subprocess patches
only its in-memory function for the fused arm.  Baseline and fused arms extract the
same already-built archive.  Timings stop before the independently computed output
identity signature, so verification work cannot make one arm appear slower.

Frozen before measurement:
* five fresh-process repetitions per arm and workload;
* primary ML median must improve by at least 10%;
* Logs and Shifted controls may regress by at most 2%;
* every baseline/fused output signature must be identical.

This is research evidence only and grants no product/release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
ROUNDS = 5
ML_MIN_IMPROVEMENT = 0.10
CONTROL_MAX_REGRESSION = 0.02
TARGETS = PERF.TARGETS


def _fused_restore_verified_manifest_tree(staging: Path, decoded: dict, *, safe_symlinks: bool = True) -> None:
    """Candidate: one regular-file lstat inside the existing metadata pass.

    This deliberately mirrors ``entropygraph_v030_verified_restore`` except for the
    two operations under test: the standalone regular-file shape traversal is gone,
    and regular files reuse one ``lstat`` for type/size/mode and avoid ``chmod`` when
    the current mode already equals the authenticated manifest mode.
    """
    from experiments import entropygraph_v030_verified_restore as R

    FS = R.FS
    staging = Path(staging)
    entries = decoded["manifest"]["entries"]
    internal = staging.joinpath(*PurePosixPath(FS.INTERNAL_ROOT).parts)
    if internal.exists() or internal.is_symlink():
        shutil.rmtree(internal, ignore_errors=True)

    for row in entries:
        rel, kind = row[0], row[1]
        target = staging.joinpath(*PurePosixPath(rel).parts)
        if kind == "d":
            target.mkdir(parents=True, exist_ok=True)
        elif kind == "l":
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = row[7]
            parsed = PurePosixPath(link_target)
            if safe_symlinks and (parsed.is_absolute() or ".." in parsed.parts):
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

    # Children before directories, exactly as the shipping helper.  For regular
    # files this is now also the structural guard, so one lstat owns type/size/mode.
    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        if kind == "d":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        follow = kind != "l"
        mode_matches = False
        if kind == "f":
            st = os.lstat(target)
            expected_size, _expected_digest = extra
            if not stat.S_ISREG(st.st_mode) or int(st.st_size) != int(expected_size):
                raise RuntimeError(f"r25 extracted regular-file shape mismatch: {rel}")
            mode_matches = stat.S_IMODE(st.st_mode) == int(mode)
        if follow and not mode_matches:
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


def _xattrs(path: Path, *, follow: bool) -> list[tuple[str, str]]:
    if not hasattr(os, "listxattr") or not hasattr(os, "getxattr"):
        return []
    try:
        names = sorted(os.listxattr(path, follow_symlinks=follow))
    except (OSError, NotImplementedError):
        return []
    out: list[tuple[str, str]] = []
    for name in names:
        try:
            value = os.getxattr(path, name, follow_symlinks=follow)
        except (OSError, NotImplementedError):
            continue
        out.append((name, value.hex()))
    return out


def _output_signature(root: Path) -> str:
    """Hash content plus filesystem semantics relevant to this restore change."""
    h = hashlib.sha256()
    inode_owner: dict[tuple[int, int], str] = {}
    paths = [root] + sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix())
    for path in paths:
        rel = "." if path == root else path.relative_to(root).as_posix()
        st = os.lstat(path)
        mode = stat.S_IMODE(st.st_mode)
        if stat.S_ISREG(st.st_mode):
            kind = "f"
        elif stat.S_ISDIR(st.st_mode):
            kind = "d"
        elif stat.S_ISLNK(st.st_mode):
            kind = "l"
        else:
            kind = "o"
        record = {
            "rel": rel,
            "kind": kind,
            "mode": mode,
            "uid": int(st.st_uid),
            "gid": int(st.st_gid),
            "mtime_ns": int(st.st_mtime_ns),
            "xattrs": _xattrs(path, follow=kind != "l"),
        }
        if kind == "f":
            content = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    content.update(chunk)
            record["size"] = int(st.st_size)
            record["sha256"] = content.hexdigest()
            inode = (int(st.st_dev), int(st.st_ino))
            owner = inode_owner.setdefault(inode, rel)
            record["hardlink_owner"] = owner
        elif kind == "l":
            record["target"] = os.readlink(path)
        h.update(json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _worker(arm: str, archive: Path, destination: Path) -> None:
    from experiments import entropygraph_v030_release_product as PRODUCT
    from experiments import entropygraph_v030_verified_restore as RESTORE

    if arm == "fused":
        RESTORE.restore_verified_manifest_tree = _fused_restore_verified_manifest_tree
    elif arm != "baseline":
        raise ValueError(arm)

    shutil.rmtree(destination, ignore_errors=True)
    started = time.perf_counter()
    PRODUCT.extract(archive, destination)
    elapsed = time.perf_counter() - started
    # Deliberately outside the measured interval.
    signature = _output_signature(destination)
    print(json.dumps({"arm": arm, "wall_s": elapsed, "signature": signature}, separators=(",", ":")))


def _run_worker(arm: str, archive: Path, destination: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(THIS), "--worker", arm, "--archive", str(archive), "--destination", str(destination)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"worker emitted no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def _measure(work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as PRODUCT

    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    rows = []
    for suite, name in TARGETS:
        source = roots[(suite, name)]
        archive = work_root / "archives" / f"{suite}-{name}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        build_stats = PRODUCT.build(source, archive)
        verified = PRODUCT.strong_verify(archive)
        if not verified.get("ok"):
            raise RuntimeError(f"strong verification failed before A/B for {suite}/{name}: {verified!r}")

        samples = {"baseline": [], "fused": []}
        signatures = {"baseline": [], "fused": []}
        # ABBA-like alternation across five paired rounds prevents fixed ordering from
        # handing either arm all early/late runner conditions.
        for rep in range(ROUNDS):
            order = ("baseline", "fused") if rep % 2 == 0 else ("fused", "baseline")
            for arm in order:
                destination = work_root / "extract" / f"{suite}-{name}-r{rep}-{arm}"
                result = _run_worker(arm, archive, destination)
                samples[arm].append(float(result["wall_s"]))
                signatures[arm].append(result["signature"])

        all_signatures = signatures["baseline"] + signatures["fused"]
        identity_ok = len(set(all_signatures)) == 1
        baseline_median = statistics.median(samples["baseline"])
        fused_median = statistics.median(samples["fused"])
        ratio = fused_median / max(baseline_median, 1e-12)
        rows.append({
            "suite": suite,
            "name": name,
            "archive_bytes": archive.stat().st_size,
            "build_stats": build_stats,
            "baseline_wall_s": samples["baseline"],
            "fused_wall_s": samples["fused"],
            "baseline_median_s": baseline_median,
            "fused_median_s": fused_median,
            "fused_over_baseline": ratio,
            "improvement_fraction": 1.0 - ratio,
            "identity_ok": identity_ok,
            "identity_sha256": all_signatures[0] if identity_ok else None,
        })

    by_name = {row["name"]: row for row in rows}
    ml = by_name["09_ml_artifacts"]
    controls = (by_name["05_logs_and_telemetry"], by_name["01_shifted_versions"])
    exact_identity = all(row["identity_ok"] for row in rows)
    ml_pass = ml["improvement_fraction"] >= ML_MIN_IMPROVEMENT
    controls_pass = all(row["fused_over_baseline"] <= 1.0 + CONTROL_MAX_REGRESSION for row in controls)
    decision = "ADVANCE_SYSCALL_FUSION" if exact_identity and ml_pass and controls_pass else "RETIRE_SYSCALL_FUSION"
    return {
        "schema": "cmpct-v030-verified-restore-syscall-fusion-v1",
        "release_credit": False,
        "evidence_head": os.environ.get("EVIDENCE_HEAD"),
        "rounds_per_arm": ROUNDS,
        "frozen_gate": {
            "ml_min_median_improvement_fraction": ML_MIN_IMPROVEMENT,
            "control_max_median_regression_fraction": CONTROL_MAX_REGRESSION,
            "exact_output_identity_required": True,
        },
        "rows": rows,
        "decision": decision,
        "gate": {
            "exact_identity": exact_identity,
            "ml_pass": ml_pass,
            "controls_pass": controls_pass,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", choices=("baseline", "fused"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()

    if args.worker:
        if args.archive is None or args.destination is None:
            raise SystemExit("--archive and --destination required in worker mode")
        _worker(args.worker, args.archive, args.destination)
        return
    if args.work_root is None or args.output is None:
        raise SystemExit("--work-root and --output required")
    result = _measure(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
