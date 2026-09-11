from __future__ import annotations

"""Transfer-only hosted probe for the frozen historical product measurement worker."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from benchmarks.one.one_genesis_historical_product_worker import FROZEN
from benchmarks.one.one_genesis_historical_metric_normalization import (
    normalize_missing_v029_selective_surface,
    normalize_v030_read_member_stats,
)


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _write_tree(root: Path) -> dict[str, bytes]:
    root.mkdir()
    files = {
        "alpha.bin": _hash_stream(48 * 1024, b"historical-worker-alpha"),
        "nested/beta.bin": _hash_stream(32 * 1024, b"historical-worker-beta"),
        "nested/tiny.txt": b"frozen product transfer fixture\n" * 17,
        "empty": b"",
    }
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return files


def _run_worker(
    *, current: Path, contender: str, mode: str, checkout: Path, root: Path,
    archive: Path, output: Path, member: str | None = None,
) -> dict:
    cmd = [
        sys.executable,
        str(current / "benchmarks/one/one_genesis_historical_product_worker.py"),
        "--contender", contender,
        "--mode", mode,
        "--checkout", str(checkout),
        "--root", str(root),
        "--archive", str(archive),
        "--output", str(output),
        "--transfer-fixture",
    ]
    if member is not None:
        cmd.extend(["--member", member])
    env = dict(os.environ)
    env["PYTHONPATH"] = str(current)
    completed = subprocess.run(cmd, cwd=current, env=env, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"historical worker failed contender={contender} mode={mode}:\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return json.loads(output.read_text(encoding="utf-8"))


def probe(current: Path, v029: Path, v030: Path) -> dict:
    current = current.resolve()
    v029 = v029.resolve()
    v030 = v030.resolve()
    with tempfile.TemporaryDirectory(prefix="cmpct-genesis-historical-worker-probe-") as td:
        base = Path(td)
        root = base / "external-tree"
        files = _write_tree(root)
        logical = sum(map(len, files.values()))
        checkouts = {"v029": v029, "v030": v030}
        rows: dict[str, dict] = {}

        for contender in ("v029", "v030"):
            archive = base / f"{contender}.cmpct"
            build = _run_worker(
                current=current, contender=contender, mode="build", checkout=checkouts[contender],
                root=root, archive=archive, output=base / f"{contender}-build.json",
            )
            whole = _run_worker(
                current=current, contender=contender, mode="whole", checkout=checkouts[contender],
                root=root, archive=archive, output=base / f"{contender}-whole.json",
            )
            if build["frozen_source_sha"] != FROZEN[contender]["sha"]:
                raise AssertionError(f"{contender}: source binding changed")
            if build["stored_bytes"] != archive.stat().st_size or build["stored_bytes"] <= 0:
                raise AssertionError(f"{contender}: persistent stored bytes invalid")
            if whole.get("exact") is not True or whole.get("returned_bytes") != logical:
                raise AssertionError(f"{contender}: independent whole reconstruction not exact")
            for phase in (build, whole):
                if phase["authorization"] != {
                    "transfer_fixture": True,
                    "production_authorized": False,
                    "frozen_source_sha": FROZEN[contender]["sha"],
                }:
                    raise AssertionError(f"{contender}: transfer authorization boundary changed")
                if phase["comparison_executed"] or phase["scoring_executed"] or phase["winner_selected"]:
                    raise AssertionError(f"{contender}: worker crossed no-scoring boundary")
            rows[contender] = {"creation": build, "whole_read": whole}

        selective = _run_worker(
            current=current, contender="v030", mode="selective", checkout=v030,
            root=root, archive=base / "v030.cmpct", output=base / "v030-selective.json",
            member="alpha.bin",
        )
        if selective.get("exact") is not True or selective.get("returned_bytes") != len(files["alpha.bin"]):
            raise AssertionError("v030 selective bytes are not exact")
        normalized_v030 = normalize_v030_read_member_stats(
            selective.get("product_access_stats", {}),
            requested_bytes=int(selective["requested_bytes"]),
        )
        rows["v030"]["selective_access"] = selective
        rows["v030"]["selective_normalized"] = normalized_v030
        rows["v029"]["selective_normalized"] = normalize_missing_v029_selective_surface()

        return {
            "schema": "cmpct-one-genesis-historical-product-worker-probe-v1",
            "claim_boundary": "transfer-only raw product measurement evidence; no Genesis 15-workload corpus, comparisons, scoring, or winner",
            "external_tree": {"files": len(files), "logical_bytes": logical},
            "rows": rows,
            "v029_selective_fabricated": False,
            "genesis_15_workloads_touched": False,
            "comparisons_executed": False,
            "scoring_executed": False,
            "winner_selected": False,
            "decision": "ADVANCE_HISTORICAL_PRODUCT_WORKER",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--v029", type=Path, required=True)
    parser.add_argument("--v030", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.current, args.v029, args.v030)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
