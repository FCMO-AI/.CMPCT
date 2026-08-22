from __future__ import annotations

"""Productization gate for the dedicated office/analytics federated r25 candidate.

This lane advances beyond the earlier CMPNX5 budget proof: the measured archive has a distinct r25-candidate
identity, canonical filesystem restoration, mandatory strong verification, exact primary/tail recovery, and an
operation-derived per-member locality audit.  It still cannot receive release credit until its grammar is owned by
production Python/native/Android readers and the ordinary all-15 authority admits it.
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

TARGETS = ("02_office_workspace", "04_analytics_and_database")
ROUNDS = 3


def _recovery(archive: Path, work: Path) -> dict:
    raw = archive.read_bytes()
    primary = bytearray(raw)
    primary[0] ^= 0x01
    primary_path = work / "primary-damaged.cmpct"
    primary_path.write_bytes(primary)
    primary_ok = bool(CAND.strong_verify(primary_path).get("ok"))

    tail = bytearray(raw)
    tail[-CAND.V25.FTR.size] ^= 0x01
    tail_path = work / "tail-damaged.cmpct"
    tail_path.write_bytes(tail)
    tail_ok = bool(CAND.strong_verify(tail_path).get("ok"))

    both = bytearray(primary)
    both[-CAND.V25.FTR.size] ^= 0x01
    both_path = work / "both-damaged.cmpct"
    both_path.write_bytes(both)
    both_failed = False
    try:
        CAND.strong_verify(both_path)
    except Exception:
        both_failed = True
    return {"primary_recovers_from_tail": primary_ok, "tail_recovers_from_primary": tail_ok, "both_fail_closed": both_failed}


def _one(label: str, source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg01-productization-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized")
        expected_external_tree = EXT._tree(stage)
        expected_user_tree = CAND._treehash(stage)
        names = ["candidate", "zip", "zstd19"]
        samples = {name: [] for name in names}
        sizes = {name: set() for name in names}
        candidate_runs = []
        recovery = None

        for round_index in range(ROUNDS):
            order = names[round_index:] + names[:round_index]
            round_root = root / f"round-{round_index}"
            round_root.mkdir()
            for name in order:
                case = round_root / name
                case.mkdir()
                if name == "candidate":
                    archive = case / "candidate.cmpct"
                    started = time.perf_counter()
                    result = CAND.build(stage, archive)
                    elapsed = time.perf_counter() - started
                    if archive.read_bytes()[:8] != CAND.MAGIC:
                        raise RuntimeError("candidate did not publish dedicated r25 identity")
                    if archive.read_bytes()[:8] == CAND.V25.MAG:
                        raise RuntimeError("research CMPNX5 identity escaped into candidate bytes")
                    if result["verified"]["canonical_user_tree_sha256"] != expected_user_tree:
                        raise RuntimeError("candidate canonical user-tree drift")
                    if not result["locality"]["within_release_bounds"]:
                        raise RuntimeError("candidate violates frozen locality/decode ceilings")
                    samples[name].append(elapsed)
                    sizes[name].add(int(result["archive_bytes"]))
                    candidate_runs.append({
                        "create_s": elapsed,
                        "max_member_read_amplification": float(result["locality"]["max_member_read_amplification"]),
                        "max_decode_unit_bytes": int(result["locality"]["max_decode_unit_bytes"]),
                        "archive_bytes": int(result["archive_bytes"]),
                    })
                    if recovery is None:
                        recovery = _recovery(archive, case)
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
            raise RuntimeError(f"nondeterministic archive sizes: {sizes!r}")
        bytes_ = {name: next(iter(values)) for name, values in sizes.items()}
        median = {name: statistics.median(values) for name, values in samples.items()}
        strict = {
            "smaller_than_zip": bytes_["candidate"] < bytes_["zip"],
            "smaller_than_zstd19": bytes_["candidate"] < bytes_["zstd19"],
            "verified_create_faster_than_zip": median["candidate"] < median["zip"],
            "verified_create_faster_than_zstd19": median["candidate"] < median["zstd19"],
        }
        strict["four_way"] = all(strict.values())
        return {
            "label": label,
            "canonical_user_tree_sha256": expected_user_tree,
            "candidate": {"archive_bytes": bytes_["candidate"], "median_complete_create_s": median["candidate"], "runs": candidate_runs},
            "zip": {"archive_bytes": bytes_["zip"], "median_create_s": median["zip"]},
            "zstd19": {"archive_bytes": bytes_["zstd19"], "median_create_s": median["zstd19"]},
            "recovery": recovery,
            "strict": strict,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_eg01_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg01_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    rows = [_one(f"neutral_hostile_v1/{name}", corpus / name, work_root) for name in TARGETS]
    gate = {
        "exact_target_count": len(rows) == len(TARGETS),
        "all_four_way": all(row["strict"]["four_way"] for row in rows),
        "all_locality_bounded": all(max(run["max_member_read_amplification"] for run in row["candidate"]["runs"]) <= CAND.MAX_MEMBER_AMPLIFICATION for row in rows),
        "all_decode_units_bounded": all(max(run["max_decode_unit_bytes"] for run in row["candidate"]["runs"]) <= CAND.MAX_DECODE_UNIT for row in rows),
        "all_two_way_recovery": all(all(row["recovery"].values()) for row in rows),
        "dedicated_candidate_identity": CAND.MAGIC != CAND.V25.MAG,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-federated-eg01-productization-v1",
        "rows": rows,
        "gate": gate,
        "claim_boundary": "candidate-profile productization proof only; no selector, release receipt, native or Android promotion credit",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-productization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-productization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": result["gate"], "rows": [{"label": r["label"], "strict": r["strict"]} for r in result["rows"]]}, indent=2))
    if not result["gate"]["passed"]:
        raise SystemExit("federated r25 candidate productization gate failed")


if __name__ == "__main__":
    main()
