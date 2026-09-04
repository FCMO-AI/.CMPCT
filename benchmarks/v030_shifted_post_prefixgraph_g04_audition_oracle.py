from __future__ import annotations

"""Frozen O0 headroom instrument for post-PrefixGraph G0-G4 audition on Shifted.

This benchmark implements only the experiment frozen in
``docs/v030-rnd/R25_SHIFTED_POST_PREFIXGRAPH_G04_AUDITION_ORACLE_PREREG.md``.
The oracle gifts family nomination only: it still builds the exact profile tree, a genuine
shipping r24 floor, the shipping level-15 PrefixGraph child, exact PrefixGraph bytes/locality,
publication and final canonical strong verification. It earns zero release credit.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ACCEPTED_V029_BYTES = 1_723_056
PAIRS = (("control", "oracle"), ("oracle", "control"), ("control", "oracle"), ("oracle", "control"), ("control", "oracle"))
SUPPORTED_RATIO = 0.80
SUPPORTED_SAVING_S = 5.0
AMBIGUOUS_RATIO = 0.90
AMBIGUOUS_SAVING_S = 2.0
LOCALITY_CEILING = 8.0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _oracle_build(root: Path, out: Path) -> dict:
    """Build the exact shipping PrefixGraph winner without executing G0-G4.

    This is deliberately not a product API. The only gifted fact is that PrefixGraph wins this
    frozen target. Every representation byte and every outer product obligation is still paid.
    """
    from experiments import entropygraph_v030_release_product as product
    from experiments.entropygraph_v030_prefixgraph_process_executor import PrefixGraphProcessExecutor

    C = product._BASE_IMPL.C
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-shifted-pg-oracle-", dir=out.parent) as td:
        temp = Path(td)
        staged = temp / "profile-tree"
        r24_path = temp / "canonical-r24.cmpct"
        pg_path = temp / "prefixgraph.cmpct"

        # The promoted C._prepare_profile_tree starts the exact shipping r24 prebuild before
        # manifest capture. C._r24_build below consumes that exact prebuild, preserving the
        # production overlap boundary rather than serializing a cost outside the oracle.
        prepared = C._prepare_profile_tree(root, staged)
        source_tree_sha = C._semantic_tree_sha(C._decode_manifest(prepared["manifest_raw"]))

        with C._revision25_profile_context():
            expected_graph_tree = C.RC.treehash(staged)
            eligible, reason = C.RC._prefixgraph_eligibility(staged, expected_graph_tree)
            if not eligible:
                raise RuntimeError(f"frozen Shifted target lost PrefixGraph eligibility: {reason}")
            with PrefixGraphProcessExecutor() as executor:
                pg_stats = dict(executor.submit(C.RC.PG.build, staged, pg_path).result())
                receipt = dict(executor.last_receipt or {})
            # subprocess.run in PrefixGraphProcessExecutor has returned here, therefore its only
            # child is dead before locality, r24 selection, publication and final verification.
            locality = dict(C.RC._prefixgraph_locality(pg_path))

        if receipt.get("schema") != "cmpct-v030-prefixgraph-process-executor-v1":
            raise RuntimeError(f"invalid PrefixGraph semantic-owner receipt: {receipt!r}")
        if receipt.get("semantic_owner") != "experiments._v030_canonical_prefixgraph":
            raise RuntimeError(f"PrefixGraph semantic owner drift: {receipt!r}")
        if int(receipt.get("prefix_level", -1)) != 15:
            raise RuntimeError(f"PrefixGraph level drift: {receipt!r}")
        if not locality.get("passed") or float(locality["max_member_read_amplification"]) > LOCALITY_CEILING:
            raise RuntimeError(f"PrefixGraph locality law failed: {locality!r}")

        r24_stats = dict(C._r24_build(root, r24_path))
        r24_bytes = r24_path.stat().st_size
        pg_bytes = pg_path.stat().st_size
        pg_sha = _sha256(pg_path)
        if int(receipt.get("archive_bytes", -1)) != pg_bytes or receipt.get("archive_sha256") != pg_sha:
            raise RuntimeError("PrefixGraph executor receipt does not bind the oracle archive")
        if pg_bytes >= ACCEPTED_V029_BYTES:
            raise RuntimeError("oracle PrefixGraph no longer strictly beats accepted v0.29")
        if pg_bytes >= r24_bytes:
            raise RuntimeError("oracle PrefixGraph no longer strictly beats genuine canonical r24")

        os.replace(pg_path, out)
        if out.stat().st_size != pg_bytes or _sha256(out) != pg_sha:
            raise RuntimeError("oracle publication changed PrefixGraph physical bytes")

    verify_started = time.perf_counter()
    verified = dict(product.strong_verify(out))
    verify_s = time.perf_counter() - verify_started
    if not verified.get("ok"):
        raise RuntimeError(f"oracle publication failed strong verification: {verified!r}")
    if verified.get("tree_sha256") != source_tree_sha:
        raise RuntimeError("oracle publication user-tree identity differs from source")
    if int(verified.get("format_revision", -1)) != 25 or verified.get("format_profile") != "prefixgraph-depth1":
        raise RuntimeError(f"oracle did not publish canonical PrefixGraph: {verified!r}")

    return {
        "selected": "prefixgraph",
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "format_revision": 25,
        "format_profile": "prefixgraph-depth1",
        "r24_product_bytes": r24_bytes,
        "accepted_v029_bytes": ACCEPTED_V029_BYTES,
        "tree_sha256": source_tree_sha,
        "filesystem_manifest_sha256": prepared["manifest_sha256"],
        "filesystem_manifest_bytes": prepared["manifest_bytes"],
        "r24": r24_stats,
        "prefixgraph": pg_stats,
        "prefixgraph_process_receipt": receipt,
        "prefixgraph_locality": locality,
        "max_selected_member_read_amplification": float(locality["max_member_read_amplification"]),
        "prefixgraph_child_exited_before_publication": True,
        "g04_executed": False,
        "final_strong_verify": verified,
        "final_strong_verify_s": verify_s,
        "portfolio_create_s": time.perf_counter() - started,
        "oracle_gift": "exact-winning-r25-family-nomination-only",
        "release_credit": False,
    }


def _worker(arm: str, source: Path, archive: Path) -> dict:
    from experiments import entropygraph_v030_release_product as product

    archive = Path(archive)
    archive.unlink(missing_ok=True)
    started = time.perf_counter()
    if arm == "control":
        stats = dict(product.build(source, archive))
        elapsed = time.perf_counter() - started
        verified = dict(stats.get("final_strong_verify") or product.strong_verify(archive))
        r25 = stats.get("r25") or {}
        locality = r25.get("max_selected_member_read_amplification")
        receipt = r25.get("prefixgraph_process_receipt") or {}
        g04 = r25.get("g04") or {}
        row = {
            "selected": stats.get("selected"),
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": _sha256(archive),
            "format_revision": stats.get("format_revision"),
            "format_profile": stats.get("format_profile"),
            "r24_product_bytes": int(stats.get("r24_product_bytes", -1)),
            "accepted_v029_bytes": ACCEPTED_V029_BYTES,
            "tree_sha256": stats.get("tree_sha256"),
            "prefixgraph_process_receipt": receipt,
            "max_selected_member_read_amplification": locality,
            "prefixgraph_child_exited_before_publication": bool(receipt),
            "g04_executed": True,
            "g04_portfolio_create_s": g04.get("portfolio_create_s"),
            "g04_shared_build_s": (g04.get("shared") or {}).get("create_s") if isinstance(g04.get("shared"), dict) else None,
            "final_strong_verify": verified,
            "final_strong_verify_s": None,
            "portfolio_create_s": elapsed,
            "release_credit": False,
        }
    elif arm == "oracle":
        row = _oracle_build(source, archive)
    else:
        raise ValueError(arm)

    if not row["final_strong_verify"].get("ok"):
        raise RuntimeError(f"{arm} did not strong-verify")
    row["arm"] = arm
    return row


def _run_fresh_worker(arm: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, __file__, "--worker", arm, "--source", os.fspath(source), "--archive", os.fspath(archive)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or not lines:
        raise RuntimeError(
            f"fresh {arm} worker failed rc={completed.returncode} stdout={completed.stdout[-2000:]!r} stderr={completed.stderr[-4000:]!r}"
        )
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]

    pairs = []
    invalid_reasons: list[str] = []
    for pair_index, order in enumerate(PAIRS, start=1):
        arms = {}
        for arm in order:
            archive = work_root / f"pair-{pair_index}-{arm}.cmpct"
            arms[arm] = _run_fresh_worker(arm, source, archive)
        control = arms["control"]
        oracle = arms["oracle"]

        checks = {
            "control_prefixgraph": control.get("selected") == "prefixgraph" and control.get("format_profile") == "prefixgraph-depth1",
            "oracle_prefixgraph": oracle.get("selected") == "prefixgraph" and oracle.get("format_profile") == "prefixgraph-depth1",
            "same_archive_bytes": int(control.get("archive_bytes", -1)) == int(oracle.get("archive_bytes", -2)),
            "same_archive_sha256": control.get("archive_sha256") == oracle.get("archive_sha256"),
            "same_tree_sha256": control.get("tree_sha256") == oracle.get("tree_sha256"),
            "control_verify": bool((control.get("final_strong_verify") or {}).get("ok")),
            "oracle_verify": bool((oracle.get("final_strong_verify") or {}).get("ok")),
            "control_locality": float(control.get("max_selected_member_read_amplification") or 1e9) <= LOCALITY_CEILING,
            "oracle_locality": float(oracle.get("max_selected_member_read_amplification") or 1e9) <= LOCALITY_CEILING,
            "control_r24_paid": int(control.get("r24_product_bytes", -1)) > int(control.get("archive_bytes", 1 << 62)),
            "oracle_r24_paid": int(oracle.get("r24_product_bytes", -1)) > int(oracle.get("archive_bytes", 1 << 62)),
            "control_child_receipt": (control.get("prefixgraph_process_receipt") or {}).get("schema") == "cmpct-v030-prefixgraph-process-executor-v1",
            "oracle_child_receipt": (oracle.get("prefixgraph_process_receipt") or {}).get("schema") == "cmpct-v030-prefixgraph-process-executor-v1",
            "oracle_child_exited": oracle.get("prefixgraph_child_exited_before_publication") is True,
            "oracle_g04_not_executed": oracle.get("g04_executed") is False,
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            invalid_reasons.append(f"pair-{pair_index}:" + ",".join(failed))
        control_s = float(control["portfolio_create_s"])
        oracle_s = float(oracle["portfolio_create_s"])
        pairs.append({
            "pair": pair_index,
            "order": list(order),
            "control": control,
            "oracle": oracle,
            "checks": checks,
            "oracle_control_ratio": oracle_s / max(control_s, 1e-9),
            "absolute_saving_s": control_s - oracle_s,
        })

    ratios = [float(row["oracle_control_ratio"]) for row in pairs]
    savings = [float(row["absolute_saving_s"]) for row in pairs]
    median_ratio = statistics.median(ratios)
    median_saving = statistics.median(savings)
    if invalid_reasons:
        decision = "INVALID"
    elif median_ratio <= SUPPORTED_RATIO and median_saving >= SUPPORTED_SAVING_S:
        decision = "SHIFTED_POST_PG_G04_AUDITION_HEADROOM_SUPPORTED"
    elif median_ratio > AMBIGUOUS_RATIO or median_saving < AMBIGUOUS_SAVING_S:
        decision = "SHIFTED_POST_PG_G04_AUDITION_HEADROOM_NOT_SUPPORTED"
    else:
        decision = "SHIFTED_POST_PG_G04_AUDITION_HEADROOM_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-shifted-post-prefixgraph-g04-audition-o0-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": "/".join(TARGET),
        "accepted_v029_bytes": ACCEPTED_V029_BYTES,
        "pairs": pairs,
        "median_oracle_control_ratio": median_ratio,
        "median_absolute_saving_s": median_saving,
        "decision": decision,
        "invalid_reasons": invalid_reasons,
        "contract": {
            "pairs": 5,
            "supported_max_ratio": SUPPORTED_RATIO,
            "supported_min_saving_s": SUPPORTED_SAVING_S,
            "ambiguous_max_ratio": AMBIGUOUS_RATIO,
            "not_supported_below_saving_s": AMBIGUOUS_SAVING_S,
            "locality_ceiling": LOCALITY_CEILING,
            "oracle_gift": "exact-winning-r25-family-nomination-only",
            "representation_bytes_gifted": False,
            "r24_bytes_gifted": False,
            "release_credit": False,
        },
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", choices=("control", "oracle"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if args.worker:
        if args.source is None or args.archive is None:
            parser.error("--worker requires --source and --archive")
        print(json.dumps(_worker(args.worker, args.source, args.archive), separators=(",", ":"), default=str))
        return
    if args.work_root is None or args.output is None:
        parser.error("oracle mode requires --work-root and --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": result["decision"],
        "median_oracle_control_ratio": result["median_oracle_control_ratio"],
        "median_absolute_saving_s": result["median_absolute_saving_s"],
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
