from __future__ import annotations

"""All-15 structural/measured admission proof for the C25EG01 federated candidate.

The office/analytics productization gate proves two high-value rows.  This harness asks the harder selector-design
question without changing production: if the dedicated candidate is cheaply attempted on every frozen workload,
which rows earn a generic measured admission against the shipping r24 floor, and do *all* admitted rows still beat
accepted v0.29, ZIP and solid Zstd-19 on complete size while beating ZIP and Zstd-19 on verified creation time?

Admission never uses a benchmark name.  A candidate must save at least 1 MiB versus the genuine shipping r24
artifact, be at most 90% of r24 bytes, strongly verify the canonical user tree, and satisfy <=8x / <=8 MiB locality.
Only admitted rows pay repeated external-comparator timing.  A single admitted counterexample makes the gate red;
aggregate wins cannot hide it.  Candidate construction must also complete on all 15 rows so an exception cannot
silently turn a counterexample into an apparent non-admission.  This is selector research only: native/Android
parity and ordinary release authority remain mandatory before C25EG01 can be dispatched by the shipping product.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_federated_candidate as CAND
from experiments import entropygraph_v030_release_product_base as BASE

MIN_SAVING_VS_R24_BYTES = 1024 * 1024
MAX_CANDIDATE_TO_R24_RATIO = 0.90
ROUNDS = 3


def _r24(stage: Path, archive: Path) -> dict:
    archive.parent.mkdir(parents=True, exist_ok=True)
    stats = dict(BASE._locality_bounded_r24_build(stage, archive))
    verified = BASE.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"shipping r24 floor failed strong verification: {verified!r}")
    stats["archive_bytes"] = archive.stat().st_size
    return stats


def _candidate(stage: Path, archive: Path) -> dict:
    archive.parent.mkdir(parents=True, exist_ok=True)
    result = dict(CAND.build(stage, archive))
    if not result["verified"].get("ok"):
        raise RuntimeError("federated candidate did not strongly verify")
    if result["verified"]["canonical_user_tree_sha256"] != CAND._treehash(stage):
        raise RuntimeError("federated candidate canonical tree drift")
    if not result["locality"]["within_release_bounds"]:
        raise RuntimeError("federated candidate locality/decode bounds")
    return result


def _internal_admission(stage: Path, work: Path) -> tuple[bool, dict]:
    work.mkdir(parents=True, exist_ok=True)
    candidate_path = work / "candidate.cmpct"
    r24_path = work / "r24.cmpct"
    started = time.perf_counter()
    candidate = _candidate(stage, candidate_path)
    candidate_s = time.perf_counter() - started
    started = time.perf_counter()
    r24 = _r24(stage, r24_path)
    r24_s = time.perf_counter() - started

    candidate_bytes = int(candidate["archive_bytes"])
    r24_bytes = int(r24["archive_bytes"])
    saving = r24_bytes - candidate_bytes
    ratio = candidate_bytes / max(1, r24_bytes)
    locality = candidate["locality"]
    admitted = (
        saving >= MIN_SAVING_VS_R24_BYTES
        and ratio <= MAX_CANDIDATE_TO_R24_RATIO
        and float(locality["max_member_read_amplification"]) <= CAND.MAX_MEMBER_AMPLIFICATION
        and int(locality["max_decode_unit_bytes"]) <= CAND.MAX_DECODE_UNIT
    )
    return admitted, {
        "candidate_bytes": candidate_bytes,
        "candidate_complete_create_s": candidate_s,
        "r24_bytes": r24_bytes,
        "r24_complete_create_s": r24_s,
        "saving_vs_r24_bytes": saving,
        "candidate_to_r24_ratio": ratio,
        "max_member_read_amplification": float(locality["max_member_read_amplification"]),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
    }


def _external_strict(stage: Path, work: Path, accepted_v029_bytes: int) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    names = ["candidate", "zip", "zstd19"]
    samples = {name: [] for name in names}
    sizes = {name: set() for name in names}
    expected_external_tree = EXT._tree(stage)
    expected_user_tree = CAND._treehash(stage)

    for round_index in range(ROUNDS):
        order = names[round_index:] + names[:round_index]
        round_root = work / f"round-{round_index}"
        round_root.mkdir()
        for name in order:
            case = round_root / name
            case.mkdir()
            if name == "candidate":
                archive = case / "candidate.cmpct"
                started = time.perf_counter()
                result = _candidate(stage, archive)
                elapsed = time.perf_counter() - started
                if result["verified"]["canonical_user_tree_sha256"] != expected_user_tree:
                    raise RuntimeError("candidate tree drift during repeated frontier")
                samples[name].append(elapsed)
                sizes[name].add(int(result["archive_bytes"]))
            elif name == "zip":
                result = EXT._zip(stage, case / "archive.zip", case / "out")
                EXT._verify_extracted(case / "out", expected_external_tree, "zip_deflate9")
                samples[name].append(float(result["create_s"]))
                sizes[name].add(int(result["archive_bytes"]))
            else:
                result = EXT._tar_zstd(stage, case / "archive.tar.zst", case / "out", case)
                if not result.get("available"):
                    raise RuntimeError("solid Zstd-19 unavailable")
                EXT._verify_extracted(case / "out", expected_external_tree, "tar_zstd19_solid")
                samples[name].append(float(result["create_s"]))
                sizes[name].add(int(result["archive_bytes"]))

    if any(len(values) != 1 for values in sizes.values()):
        raise RuntimeError(f"nondeterministic federated/comparator bytes: {sizes!r}")
    bytes_ = {name: next(iter(values)) for name, values in sizes.items()}
    medians = {name: statistics.median(values) for name, values in samples.items()}
    strict = {
        "beats_accepted_v029_size": bytes_["candidate"] < int(accepted_v029_bytes),
        "beats_zip_size": bytes_["candidate"] < bytes_["zip"],
        "beats_zstd19_size": bytes_["candidate"] < bytes_["zstd19"],
        "verified_create_beats_zip": medians["candidate"] < medians["zip"],
        "verified_create_beats_zstd19": medians["candidate"] < medians["zstd19"],
    }
    strict["passed"] = all(strict.values())
    return {
        "candidate_bytes": bytes_["candidate"],
        "candidate_median_verified_create_s": medians["candidate"],
        "zip_bytes": bytes_["zip"],
        "zip_median_create_s": medians["zip"],
        "zstd19_bytes": bytes_["zstd19"],
        "zstd19_median_create_s": medians["zstd19"],
        "strict": strict,
    }


def _one(label: str, source: Path, work: Path, accepted_v029_bytes: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg01-generalize-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized")
        try:
            admitted, admission = _internal_admission(stage, root / "admission")
        except Exception as exc:
            return {
                "label": label,
                "admitted": False,
                "candidate_error": f"{type(exc).__name__}: {exc}",
            }
        row = {"label": label, "admitted": admitted, "admission": admission}
        if admitted:
            row["external"] = _external_strict(stage, root / "external", accepted_v029_bytes)
        return row


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_eg01_generalize_neutral",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_eg01_generalize_hostile",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg01_generalize_repair")
    repair.install_generation_hooks(neutral)

    rows = []
    for suite, builder, corpus in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "hostile"),
    ):
        builder.build(corpus)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(corpus)
        for workload in sorted(path for path in corpus.iterdir() if path.is_dir()):
            key = (suite, workload.name)
            expected = accepted[key]
            if EXT._tree(workload) != expected["tree_sha256"]:
                raise RuntimeError(f"source drift: {suite}/{workload.name}")
            row = _one(
                f"{suite}/{workload.name}",
                workload,
                work_root,
                int(expected["accepted_v029_bytes"]),
            )
            row["suite"] = suite
            row["name"] = workload.name
            rows.append(row)
            print(
                json.dumps(
                    {
                        "label": row["label"],
                        "admitted": row["admitted"],
                        "admission": row.get("admission"),
                        "strict": row.get("external", {}).get("strict"),
                        "candidate_error": row.get("candidate_error"),
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )

    admitted = [row for row in rows if row["admitted"]]
    candidate_errors = [row for row in rows if "candidate_error" in row]
    gate = {
        "exact_workload_count": len(rows) == 15,
        "at_least_two_measured_admissions": len(admitted) >= 2,
        "all_admitted_strictly_safe": bool(admitted)
        and all(row["external"]["strict"]["passed"] for row in admitted),
        "all_15_candidate_attempts_completed": not candidate_errors,
        "dedicated_candidate_identity": CAND.MAGIC != CAND.V25.MAG,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-federated-eg01-generalization-admission-v1",
        "contract": {
            "workloads": 15,
            "internal_admission": {
                "minimum_saving_vs_r24_bytes": MIN_SAVING_VS_R24_BYTES,
                "maximum_candidate_to_r24_ratio": MAX_CANDIDATE_TO_R24_RATIO,
                "maximum_member_read_amplification": CAND.MAX_MEMBER_AMPLIFICATION,
                "maximum_decode_unit_bytes": CAND.MAX_DECODE_UNIT,
                "benchmark_name_dispatch": False,
            },
            "external_credit": "every admitted row must beat accepted v0.29 + ZIP + Zstd size and ZIP + Zstd verified creation time; ties fail",
            "promotion_boundary": "selector research only; production Python/native/Android dispatch and ordinary release authority remain mandatory",
        },
        "rows": rows,
        "summary": {
            "admitted_rows": [row["label"] for row in admitted],
            "candidate_error_rows": [row["label"] for row in candidate_errors],
        },
        "gate": gate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("federated C25EG01 all-15 admission gate failed")


if __name__ == "__main__":
    main()
