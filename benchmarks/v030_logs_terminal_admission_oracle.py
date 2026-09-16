from __future__ import annotations

"""Post-promotion structural ratchet for the canonical logs-inverse terminal path.

The shipping selector must never dispatch on a benchmark name. This harness rebuilds all 15 frozen workloads and
replays the generic structural/measured admission predicate that earned logs promotion. For every admitted tree it
constructs independent r24 and logs candidates, then builds the *actual shipping product* and requires that the
selector publishes the independently measured logs representation exactly.

An admitted shipping row receives credit only when the complete product boundary is strictly smaller than accepted
v0.29, ZIP/Deflate-9 and solid tar+Zstd-19, strictly faster to create than ZIP and Zstd-19, strongly verifies, and
retains <=8x member-read amplification plus <=8 MiB decode context. Equality is failure. Non-admitted rows remain
negative evidence. This lane is a regression ratchet; the ordinary all-15 external/release authorities remain the
release decision makers.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product as PRODUCT

MIN_SIDECAR_PAIRS = 2
MIN_INVERSE_EDGES = 2
MIN_SAVING_BYTES = 1024 * 1024
MAX_LOGS_TO_R24_RATIO = 0.80
MAX_MEMBER_AMPLIFICATION = 8.0
MAX_DECODE_UNIT_BYTES = 8 * 1024 * 1024


def _regular_paths(root: Path) -> set[str]:
    root = Path(root)
    out: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_file() and not path.is_symlink():
                out.add(path.relative_to(root).as_posix())
    return out


def source_prefilter(root: Path) -> dict:
    paths = _regular_paths(root)
    pairs: list[tuple[str, str]] = []
    for rel in sorted(paths):
        for suffix in (".gz", ".zst"):
            if rel.endswith(suffix):
                sibling = rel[: -len(suffix)]
                if sibling in paths:
                    pairs.append((rel, sibling))
                break
    return {
        "sidecar_pairs": len(pairs),
        "pair_examples": pairs[:8],
        "eligible": len(pairs) >= MIN_SIDECAR_PAIRS,
    }


def _build_r24(stage: Path, archive: Path) -> dict:
    stats = dict(PRODUCT._locality_bounded_r24_build(stage, archive))
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"r24 admission candidate failed strong verification: {verified!r}")
    stats["archive_bytes"] = archive.stat().st_size
    stats["strong_verify"] = True
    return stats


def _build_logs(stage: Path, archive: Path) -> dict:
    stats = dict(LOGS.build(stage, archive))
    verified = LOGS.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"logs admission candidate failed strong verification: {verified!r}")
    if "max_member_read_amplification" not in stats or "max_decode_unit_bytes" not in stats:
        raise RuntimeError("logs profile did not expose required locality evidence")
    stats["archive_bytes"] = archive.stat().st_size
    stats["strong_verify"] = True
    stats["tree_sha256"] = verified.get("tree_sha256") or verified.get("user_tree_sha256")
    return stats


def _parallel_candidates(stage: Path, work: Path) -> tuple[dict, dict, float]:
    r24_path = work / "candidate-r24.cmpct"
    logs_path = work / "candidate-logs.cmpct"
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="cmpct-v030-logs-terminal-ratchet") as pool:
        r24_future = pool.submit(_build_r24, stage, r24_path)
        logs_future = pool.submit(_build_logs, stage, logs_path)
        r24 = r24_future.result()
        logs = logs_future.result()
    return r24, logs, time.perf_counter() - started


def _admitted(r24: dict, logs: dict) -> tuple[bool, dict]:
    r24_bytes = int(r24["archive_bytes"])
    logs_bytes = int(logs["archive_bytes"])
    saving = r24_bytes - logs_bytes
    ratio = logs_bytes / max(1, r24_bytes)
    edges = int(logs.get("edge_detection", {}).get("inverse_edges") or 0)
    amp = float(logs["max_member_read_amplification"])
    decode = int(logs["max_decode_unit_bytes"])
    facts = {
        "inverse_edges": edges,
        "saving_vs_r24_bytes": saving,
        "logs_to_r24_ratio": ratio,
        "max_member_read_amplification": amp,
        "max_decode_unit_bytes": decode,
    }
    admitted = (
        edges >= MIN_INVERSE_EDGES
        and saving >= MIN_SAVING_BYTES
        and ratio <= MAX_LOGS_TO_R24_RATIO
        and amp <= MAX_MEMBER_AMPLIFICATION
        and decode <= MAX_DECODE_UNIT_BYTES
    )
    return admitted, facts


def _one(label: str, source: Path, work: Path, accepted_v029_bytes: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-logs-terminal-ratchet-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "stage-root")
        prefilter = source_prefilter(stage)
        row = {
            "label": label,
            "prefilter": prefilter,
            "accepted_v029_bytes": int(accepted_v029_bytes),
            "admitted": False,
        }
        if not prefilter["eligible"]:
            return row

        candidate_root = root / "candidates"
        candidate_root.mkdir()
        try:
            r24, logs, pair_wall_s = _parallel_candidates(stage, candidate_root)
        except Exception as exc:
            row["candidate_error"] = f"{type(exc).__name__}: {exc}"
            return row

        admitted, admission = _admitted(r24, logs)
        row.update({
            "candidate_pair_create_verify_s": pair_wall_s,
            "r24_bytes": int(r24["archive_bytes"]),
            "logs_bytes": int(logs["archive_bytes"]),
            "logs_tree_sha256": logs.get("tree_sha256"),
            "admission": admission,
            "admitted": admitted,
        })
        if not admitted:
            return row

        full_path = root / "shipping-product.cmpct"
        full_started = time.perf_counter()
        full_stats = PRODUCT.build(stage, full_path)
        full_create_s = time.perf_counter() - full_started
        full_verified = PRODUCT.strong_verify(full_path)
        if not full_verified.get("ok"):
            raise RuntimeError(f"shipping product failed logs ratchet verification: {full_verified!r}")

        zip_root = root / "zip"
        zip_root.mkdir()
        zip_result = EXT._zip(stage, zip_root / "archive.zip", zip_root / "out")
        EXT._verify_extracted(zip_root / "out", EXT._tree(stage), "zip_deflate9")
        zstd_root = root / "zstd"
        zstd_root.mkdir()
        zstd_result = EXT._tar_zstd(stage, zstd_root / "archive.tar.zst", zstd_root / "out", zstd_root)
        if not zstd_result.get("available"):
            raise RuntimeError(f"solid Zstd-19 unavailable in logs ratchet: {zstd_result!r}")
        EXT._verify_extracted(zstd_root / "out", EXT._tree(stage), "tar_zstd19_solid")

        product_bytes = int(full_path.stat().st_size)
        logs_bytes = int(logs["archive_bytes"])
        zip_bytes = int(zip_result["archive_bytes"])
        zstd_bytes = int(zstd_result["archive_bytes"])
        selected_amp = float(
            full_stats.get("r25", {}).get("max_selected_member_read_amplification", float("inf"))
        )
        selected_decode = int(full_stats.get("r25", {}).get("max_decode_unit_bytes", MAX_DECODE_UNIT_BYTES + 1))
        verified_tree = full_verified.get("tree_sha256") or full_verified.get("user_tree_sha256")
        strict = {
            "shipping_selects_logs_inverse": full_stats.get("selected") == "logs-inverse"
            and full_stats.get("format_profile") == PRODUCT.LOGS_PROFILE,
            "shipping_matches_independent_logs_bytes": product_bytes == logs_bytes,
            "shipping_matches_independent_logs_tree": verified_tree == logs.get("tree_sha256"),
            "shipping_beats_accepted_v029_size": product_bytes < int(accepted_v029_bytes),
            "shipping_beats_zip_size": product_bytes < zip_bytes,
            "shipping_beats_zstd19_size": product_bytes < zstd_bytes,
            "shipping_beats_zip_create": full_create_s < float(zip_result["create_s"]),
            "shipping_beats_zstd19_create": full_create_s < float(zstd_result["create_s"]),
            "shipping_locality_le_8x": selected_amp <= MAX_MEMBER_AMPLIFICATION,
            "shipping_decode_unit_le_8mib": selected_decode <= MAX_DECODE_UNIT_BYTES,
        }
        strict["passed"] = all(strict.values())
        row.update({
            "shipping_product_bytes": product_bytes,
            "shipping_product_create_s": full_create_s,
            "shipping_product_selected": full_stats.get("selected"),
            "shipping_product_profile": full_stats.get("format_profile"),
            "shipping_product_max_member_read_amplification": selected_amp,
            "shipping_product_max_decode_unit_bytes": selected_decode,
            "zip_bytes": zip_bytes,
            "zip_create_s": float(zip_result["create_s"]),
            "zstd19_bytes": zstd_bytes,
            "zstd19_create_s": float(zstd_result["create_s"]),
            "strict": strict,
        })
        return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_logs_terminal_neutral"
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_logs_terminal_hostile"
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_logs_terminal_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    for suite, builder, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected = accepted[key]
            if EXT._tree(workload) != expected["tree_sha256"]:
                raise RuntimeError(f"source drift: {suite}/{workload.name}")
            row = _one(
                f"{suite}/{workload.name}", workload, work_root, int(expected["accepted_v029_bytes"])
            )
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            print(
                json.dumps(
                    {"label": row["label"], "prefilter": row["prefilter"], "admitted": row["admitted"], "strict": row.get("strict")},
                    separators=(",", ":"),
                ),
                flush=True,
            )

    admitted = [row for row in rows if row["admitted"]]
    gate = {
        "exact_workload_count": len(rows) == 15,
        "at_least_one_structural_admission": bool(admitted),
        "all_admitted_shipping_strictly_safe": bool(admitted)
        and all(row.get("strict", {}).get("passed") is True for row in admitted),
        "logs_workload_admitted": any(row["name"] == "05_logs_and_telemetry" for row in admitted),
        "no_candidate_errors": not any("candidate_error" in row for row in rows if row["prefilter"]["eligible"]),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-logs-terminal-ratchet-v2",
        "contract": {
            "workloads": 15,
            "source_prefilter": f">={MIN_SIDECAR_PAIRS} .gz/.zst sibling sidecar pairs",
            "measured_admission": f">={MIN_INVERSE_EDGES} proven inverse edges, >={MIN_SAVING_BYTES} B saving vs r24, logs/r24 <= {MAX_LOGS_TO_R24_RATIO}",
            "shipping_requirements": "selector must publish independent logs bytes/tree, beat accepted v0.29 + ZIP + Zstd size, beat ZIP + Zstd complete creation time, <=8x locality, <=8 MiB decode unit",
            "release_boundary": "regression evidence only; ordinary external/generalization/final authority remains decisive",
        },
        "rows": rows,
        "summary": {
            "prefilter_rows": [row["label"] for row in rows if row["prefilter"]["eligible"]],
            "admitted_rows": [row["label"] for row in admitted],
        },
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-terminal-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-terminal-admission.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("promoted logs terminal regression ratchet failed")


if __name__ == "__main__":
    main()
