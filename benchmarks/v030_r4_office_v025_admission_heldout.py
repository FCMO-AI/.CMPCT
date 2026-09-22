from __future__ import annotations

"""Generator-distinct hostile transfer for the inherited v0.25 admission law.

This file is deliberately frozen before result-bearing execution.  It does not use the
neutral Office generator.  Two populations are predicted from structure alone:

* exact-shared: four ZIPs contain the same three exact stored-information roots and the
  source tree also contains exact loose views; a fifth ZIP is independent.  The mature
  v0.25 law should admit the four useful containers and reject the independent one.
* near-equal: the existing resemblance-hostile deflate_family generator creates related
  text archives whose members change by version.  Similarity alone is not exact stream
  federation evidence, so the mature exact admission law should reject these containers.

No threshold or codec parameter is tuned here.  The inherited law remains 512 KiB local
exact duplication OR 32 KiB shared exact stream OR 32 KiB external exact view.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import time
import zipfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_admission_transfer as TRANSFER
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-v025-admission-heldout-v1"


def _rand(tag: str, n: int) -> bytes:
    seed = int.from_bytes(hashlib.sha256(tag.encode()).digest()[:8], "little")
    r = random.Random(seed)
    return bytes(r.getrandbits(8) for _ in range(n))


def _zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name, body in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 2, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, body, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def build_exact_shared(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    loose = root / "materialized"
    loose.mkdir()
    shared = {
        "alpha.bin": _rand("heldout-alpha", 48 * 1024),
        "beta.bin": _rand("heldout-beta", 48 * 1024),
        "gamma.bin": _rand("heldout-gamma", 48 * 1024),
    }
    for name, body in shared.items():
        (loose / name).write_bytes(body)
    for i in range(4):
        members = dict(shared)
        members[f"unique-{i}.txt"] = ((f"tenant={i};generation=heldout\n").encode() * 420)
        _zip(root / f"packet-{i}.zip", members)
    # Deliberately large enough to make accidental federation carrying cost visible.
    _zip(root / "isolated.zip", {"only.bin": _rand("heldout-isolated", 384 * 1024)})
    (root / "ordinary.txt").write_text("heldout admission transfer\n" * 200, encoding="utf-8")


def _full_transfer(root: Path, work: Path) -> dict:
    expected = PRODUCT.treehash(root)
    sfv4_dir = work / "sfv4"
    t0c = time.process_time(); t0w = time.perf_counter()
    sfv4 = SFV4.build_candidate(root, sfv4_dir, work / "sfv4-work")
    sfv4_cpu = time.process_time() - t0c; sfv4_wall = time.perf_counter() - t0w
    sv = SFV4.extract_candidate(sfv4_dir, work / "sfv4-extract")
    if sv["tree_sha256"] != expected:
        raise RuntimeError("heldout SFV4 tree mismatch")

    cand_dir = work / "admission"
    t0c = time.process_time(); t0w = time.perf_counter()
    cand = TRANSFER._build_candidate(root, cand_dir, work / "admission-work")
    cand_cpu = time.process_time() - t0c; cand_wall = time.perf_counter() - t0w
    cv = SFV4.extract_candidate(cand_dir, work / "admission-extract")
    if cv["tree_sha256"] != expected:
        raise RuntimeError("heldout admission tree mismatch")

    return {
        "tree_sha256": expected,
        "sfv4_stored_bytes": int(sfv4["stored_bytes"]),
        "candidate_stored_bytes": int(cand["stored_bytes"]),
        "saving_bytes": int(sfv4["stored_bytes"]) - int(cand["stored_bytes"]),
        "sfv4_create_cpu_s": sfv4_cpu,
        "sfv4_create_wall_s": sfv4_wall,
        "candidate_create_cpu_s": cand_cpu,
        "candidate_create_wall_s": cand_wall,
        "candidate_containers": cand["candidate_containers"],
        "admitted_containers": cand["admitted_containers"],
        "rejected_containers": cand["rejected_containers"],
        "rejected_source_bytes_retained_in_base_input": cand[
            "rejected_source_bytes_retained_in_base_input"
        ],
        "derived_files": cand["derived_file_count"],
        "derived_logical_bytes": cand["derived_logical_bytes"],
        "admission_rows": cand["admission_rows"],
        "exact_tree": cv["tree_sha256"] == expected,
    }


def _near_equal_negative(root: Path) -> dict:
    HOSTILE.deflate_family(root)
    discovered, _ = SFV2.discover(root)
    admitted, rows = TRANSFER._admission(root, discovered)
    return {
        "tree_sha256": PRODUCT.treehash(root),
        "candidate_containers": len(discovered),
        "admitted_containers": len(admitted),
        "rejected_containers": len(discovered) - len(admitted),
        "admission_rows": rows,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    pos = work / "exact-shared-source"
    build_exact_shared(pos)
    positive = _full_transfer(pos, work / "positive")
    negative = _near_equal_negative(work / "near-equal-source")

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "positive_exact_shared": positive,
        "negative_near_equal": negative,
        "hypothesis": {
            "positive_mixed_admission_exact": positive["candidate_containers"] == 5
            and positive["admitted_containers"] == 4
            and positive["rejected_containers"] == 1,
            "positive_exact_tree": positive["exact_tree"],
            "positive_complete_bytes_improve": positive["saving_bytes"] > 0,
            "positive_derived_views_present": positive["derived_files"] >= 3,
            "near_equal_exact_law_rejects_all": negative["candidate_containers"] == 14
            and negative["admitted_containers"] == 0,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "generator_distinct_from_neutral_office": True,
            "positive_prediction_frozen_before_execution": True,
            "negative_prediction_frozen_before_execution": True,
            "thresholds_inherited_without_sweep": {
                "local_duplicate_bytes": 512 * 1024,
                "shared_stream_bytes": 32 * 1024,
                "external_exact_view_stream_bytes": 32 * 1024,
            },
            "no_workload_path_hash_dispatch": True,
            "near_equal_control_is_existing_resemblance_hostile_generator": True,
            "production_format_changed": False,
            "production_selector_changed": False,
        },
        "next_if_supported": (
            "admission law has generator-distinct causal support; next attack the still-unpaid derived-view "
            "locality/auth/index cost before any product selector integration"
        ),
        "next_if_falsified": (
            "preserve the transfer negative and do not promote inherited v0.25 admission thresholds as a "
            "general v0.30 mechanism"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-v025-admission-heldout-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-v025-admission-heldout.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({
        "positive_exact_shared": {k:v for k,v in d["positive_exact_shared"].items() if k != "admission_rows"},
        "negative_near_equal": {k:v for k,v in d["negative_near_equal"].items() if k != "admission_rows"},
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
