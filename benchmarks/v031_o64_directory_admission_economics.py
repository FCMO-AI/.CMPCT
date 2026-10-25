"""O64-E: fresh-process *genuine-product* Windows directory admission economics.

Same source tree and environment; compare separately installed real wheels
from exact O57 and O64 Git source, including their package-owned native libraries.
No change to official benchmark/corpus/policy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _prepare(workspace: Path) -> dict:
    trees = workspace / "trees"
    trees.mkdir(parents=True, exist_ok=True)
    configurations = (
        ("empty256", 256, False),
        ("empty2048", 2048, False),
        ("mixed512", 512, True),
    )
    output = {}
    for name, n, with_files in configurations:
        root = trees / name
        root.mkdir()
        for index in range(n):
            directory = root / f"entry-{index:05d}"
            directory.mkdir()
            if with_files:
                (directory / "tiny.dat").write_bytes(
                    (f"o64e-positional-deterministic-content-{index:05d}\n" * 5).encode()
                )
        output[name] = str(root)
    return output


def _tree_witness(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            h.update(b"D")
        elif path.is_file():
            data = path.read_bytes()
            h.update(b"F" + len(data).to_bytes(8, "big") + hashlib.sha256(data).digest())
        else:
            raise AssertionError("unsupported test input: " + str(path))
        h.update(rel.encode() + b"\0")
    return h.hexdigest()


def _sample(args: argparse.Namespace) -> None:
    # No cmpct imports at module level: PYTHONPATH selects actual Git checkout
    # and every observation occurs in a fresh process.
    import psutil
    import cmpct.builder
    from cmpct.builder import Builder

    module_path = Path(cmpct.builder.__file__).resolve()
    expected = (Path(args.source).resolve() / "cmpct" / "builder.py")
    assert module_path == expected, (module_path, expected)
    source_root = Path(args.tree).resolve()
    archive = Path(args.output).resolve()
    started_cpu = time.process_time_ns()
    started_wall = time.perf_counter_ns()
    result = Builder(
        source_root, workers=1, reproducible=True, reproducible_epoch_ns=0
    ).build(archive)
    wall_ms = (time.perf_counter_ns() - started_wall) / 1e6
    cpu_ms = (time.process_time_ns() - started_cpu) / 1e6
    digest = _sha(archive.read_bytes())
    after_rss_kib = psutil.Process().memory_info().rss // 1024
    assert result["bytes"] == archive.stat().st_size
    print(json.dumps({
        "source": args.label, "scenario": args.scenario,
        "build_wall_ms": wall_ms, "build_cpu_ms": cpu_ms,
        "rss_post_kib": after_rss_kib, "archive_bytes": result["bytes"],
        "archive_sha256": digest, "module": str(module_path),
    }, sort_keys=True), flush=True)


def _drive(args: argparse.Namespace) -> None:
    if os.name != "nt":
        raise SystemExit("O64-E hosted economics must run on native Windows")
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    cases = _prepare(workspace)
    expected = {name: _tree_witness(Path(tree)) for name, tree in cases.items()}
    rows = []
    script = str(Path(__file__).resolve())
    outputs = workspace / "outputs"
    outputs.mkdir()
    for name, root in cases.items():
        for block in range(2):
            # ABBA blocks; reverse adjacent run ordering to expose time drift.
            order = ("base", "candidate", "candidate", "base") if block == 0 else (
                "candidate", "base", "base", "candidate"
            )
            for label in order:
                serial = sum(1 for x in rows if x["scenario"] == name)
                out = outputs / f"{name}-{label}-{serial}.cmpct"
                src = args.baseline if label == "base" else args.candidate
                env = os.environ.copy()
                env["PYTHONPATH"] = str(Path(src).resolve())
                cmd = [
                    sys.executable, script, "--sample", "--tree", str(root),
                    "--output", str(out), "--label", label,
                    "--scenario", name, "--source", str(src),
                ]
                t0 = time.perf_counter_ns()
                run = subprocess.run(cmd, env=env, text=True, capture_output=True)
                process_ms = (time.perf_counter_ns() - t0) / 1e6
                if run.returncode:
                    raise RuntimeError(
                        f"source={label} case={name} returncode={run.returncode}\n"
                        f"stdout={run.stdout[-4000:]}\nstderr={run.stderr[-4000:]}"
                    )
                receipt = json.loads(run.stdout.strip().splitlines()[-1])
                receipt.update(
                    {"process_wall_ms": process_ms, "rep": serial,
                     "tree_sha256": expected[name]}
                )
                rows.append(receipt)
                print("O64E_SAMPLE " + json.dumps(receipt, sort_keys=True), flush=True)
        observed_tree = _tree_witness(Path(root))
        assert observed_tree == expected[name], (name, observed_tree, expected[name])
        actual = {(row["archive_bytes"], row["archive_sha256"]) for row in rows
                  if row["scenario"] == name}
        assert len(actual) == 1, ("complete CMPCT artifact mismatch", name, actual)

    summary = {}
    for name in cases:
        groups = {
            label: [x for x in rows if x["scenario"] == name and x["source"] == label]
            for label in ("base", "candidate")
        }
        assert all(len(group) == 4 for group in groups.values())
        medians = {}
        for label, group in groups.items():
            medians[label] = {
                key: statistics.median(row[key] for row in group)
                for key in ("build_wall_ms", "build_cpu_ms",
                            "process_wall_ms", "rss_post_kib")
            }
        delta = {
            key: medians["candidate"][key] - medians["base"][key]
            for key in medians["base"]
        }
        signal = (delta["build_wall_ms"] >= 3
                  and delta["build_wall_ms"] >= 0.05 * medians["base"]["build_wall_ms"])
        summary[name] = {
            "medians": medians, "candidate_minus_base": delta,
            "promotion_timing_debt_signal": bool(signal),
            "tree_sha256": expected[name],
        }
        print("O64E_MEDIAN " + name + " " + json.dumps(summary[name], sort_keys=True),
              flush=True)

    output = {
        "scope": "Windows 2025 exact-source experimental product economics, not release",
        "baseline_commit": "d9f9fa724c139c6281f0e2a92c66601bee912618",
        "baseline_builder_blob": "7a13545c7dc22ea973f90930fae6cf053f13f1f2",
        "candidate_builder_blob": "b02a30d4ad1b26ea8eea49e11159113caebd6006",
        "candidate_helper_blob": "61d8cab1545c491da76b23ea89d4ca85d3030c5d",
        "python": sys.version,
        "cases": summary, "raw_samples": rows,
    }
    destination = Path(args.report)
    destination.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print("O64E_EXACT_PRODUCT_BYTES=PASS raw_samples=" + str(len(rows)), flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    p.add_argument("--source")
    p.add_argument("--label")
    p.add_argument("--scenario")
    p.add_argument("--tree")
    p.add_argument("--output")
    p.add_argument("--baseline")
    p.add_argument("--candidate")
    p.add_argument("--workspace")
    p.add_argument("--report")
    args = p.parse_args()
    if args.sample:
        _sample(args)
    else:
        _drive(args)


if __name__ == "__main__":
    main()
