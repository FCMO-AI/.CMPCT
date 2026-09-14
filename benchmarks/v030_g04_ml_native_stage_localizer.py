from __future__ import annotations

"""Research-only localization of canonical ML native G0-G4 runtime.

This diagnostic intentionally does not run the multi-round performance oracle. It builds the exact
canonical ML archive once, proves shipping strong identity, then times metadata-only native open/list
and each member's native reconstruction independently behind a fixed timeout. A timeout is reported as
censored evidence, never converted into a fabricated duration. No release credit or product mutation.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
MEMBER_TIMEOUT_S = 30.0
METADATA_TIMEOUT_S = 10.0


def _run(cli: Path, args: list[str], timeout_s: float) -> dict:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [str(cli), *args], capture_output=True, text=True, timeout=timeout_s, check=False
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "elapsed_s_lower_bound": float(time.perf_counter() - started),
            "timeout_s": float(timeout_s),
            "stdout_tail": (exc.stdout or "")[-1000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-1000:] if isinstance(exc.stderr, str) else "",
        }
    elapsed = time.perf_counter() - started
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "elapsed_s": float(elapsed),
        "returncode": int(completed.returncode),
        "stdout": completed.stdout,
        "stderr_tail": completed.stderr[-2000:],
    }


def run(work_root: Path, native_cli: Path) -> dict:
    native_cli = native_cli.resolve()
    if not native_cli.is_file():
        raise RuntimeError(f"native CLI not found: {native_cli}")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
    if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
        raise RuntimeError("shipping strong verification failed before native localization")

    info = _run(native_cli, ["info", str(archive)], METADATA_TIMEOUT_S)
    listing = _run(native_cli, ["list", str(archive)], METADATA_TIMEOUT_S)
    if info["status"] != "ok" or listing["status"] != "ok":
        return {
            "schema": "cmpct-v030-g04-ml-native-stage-localizer-v1",
            "target": "/".join(TARGET),
            "shipping_build": built,
            "archive_bytes": archive.stat().st_size,
            "info": info,
            "list": listing,
            "members": [],
            "release_credit": False,
            "claim_boundary": "Censored stage-localization diagnostic only; metadata/open failure prevents member attribution.",
        }

    members = []
    for line in listing["stdout"].splitlines():
        if not line.strip():
            continue
        fields = line.split("\t", 3)
        if len(fields) != 4:
            raise RuntimeError(f"malformed native list row: {line!r}")
        index, kind, size, path = fields
        row = {"index": int(index), "kind": int(kind), "logical_bytes": int(size), "path": path}
        if int(kind) == 0:
            row["native_member_stats"] = _run(
                native_cli, ["member-stats", str(archive), path], MEMBER_TIMEOUT_S
            )
        members.append(row)

    return {
        "schema": "cmpct-v030-g04-ml-native-stage-localizer-v1",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "source_tree_sha256": source_tree,
        "metadata_timeout_s": METADATA_TIMEOUT_S,
        "member_timeout_s": MEMBER_TIMEOUT_S,
        "info": info,
        "list": {k: v for k, v in listing.items() if k != "stdout"},
        "members": members,
        "release_credit": False,
        "claim_boundary": "Research-only per-member localization of current native G0-G4 execution. Timeouts are lower bounds, not completed timings; no release or performance-promotion credit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-cli", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-native-stage-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-native-stage.json"))
    args = parser.parse_args()
    result = run(args.work_root, args.native_cli)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
