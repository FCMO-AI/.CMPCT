from __future__ import annotations

"""Exact r24 A/B for release-only .bin micro-packing versus dictionary training.

The v0.30 r24 product intentionally admits <=256 KiB ``.bin`` members to the existing S_PACK micro-pack path.
That admission currently reuses the builder's historical ``TEXT_EXT`` view.  The same view also controls Zstd
*dictionary training*, so a release-only packing hint can accidentally turn high-entropy binary chunks into
training samples and publish a dictionary that no physical payload actually uses.

This oracle separates those two decisions without changing revision-24 grammar: .bin remains eligible for S_PACK,
but dictionary training sees only the mature text-extension set.  The target A/B is repeated and strong-verified;
the full 15-workload campaign fails promotion on any byte regression or semantic-tree mismatch.  Historical v0.29
source-tree identities are retained strictly as frozen corpus provenance: canonical r24 strong verification uses a
product semantic-tree domain that is intentionally not byte-identical to that historical source digest.  The
candidate therefore earns semantic-equivalence credit only from shipping-vs-candidate canonical tree equality.
It is research evidence only and cannot authorize release by itself.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import statistics
import tempfile
import time

from benchmarks import v030_r24_compact_control_oracle as CONTROL
from benchmarks import v030_r24_medium_binary_pack_generalization as PACKGEN
from experiments import entropygraph_v030_release_product as P

ROUNDS = 5
TARGET = CONTROL.TARGET_NAME


class _PackingOnlyBinaryBuilder(P.C.Builder):
    """Keep release .bin S_PACK admission out of the historical dictionary-training policy."""

    def _train_dictionary(self):
        previous = getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)
        P._R24_CDC_POLICY.medium_binary_pack = False
        try:
            return super()._train_dictionary()
        finally:
            P._R24_CDC_POLICY.medium_binary_pack = previous


def _regular_shape(root: Path) -> tuple[int, int]:
    count = 0
    largest = 0
    for dirpath, dirnames, filenames in os.walk(Path(root), followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                count += 1
                largest = max(largest, int(st.st_size))
    return count, largest


def _candidate_build(root: Path, out: Path) -> dict:
    root = Path(root)
    out = Path(out)
    started = time.perf_counter()
    builder = _PackingOnlyBinaryBuilder(root, deflate_reuse_min=P.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.micro_pack_max_file = P.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular_files, largest_member = _regular_shape(root)
    if largest_member > 0:
        builder.micro_pack_target = min(P.R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member)
    wide_single = regular_files == 1 and largest_member >= P.R24_RELEASE_WIDE_CHUNK_BYTES
    old_wide = getattr(P._R24_CDC_POLICY, "wide_single_file", False)
    old_medium = getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)
    P._R24_CDC_POLICY.wide_single_file = wide_single
    P._R24_CDC_POLICY.medium_binary_pack = True
    try:
        stats = dict(builder.build(out))
    finally:
        P._R24_CDC_POLICY.wide_single_file = old_wide
        P._R24_CDC_POLICY.medium_binary_pack = old_medium
    build_s = time.perf_counter() - started
    verify_started = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - verify_started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"candidate r24 verification failed: {verified!r}")
    index, physical = CONTROL._read_index(out)
    return {
        "archive_bytes": int(physical["archive_bytes"]),
        "tree_sha256": verified["tree_sha256"],
        "complete_create_s": build_s + verify_s,
        "build_s": build_s,
        "verify_s": verify_s,
        "dict_blob_present": index.get("dict_blob") is not None,
        "unique_blobs": int(stats["unique_blobs"]),
    }


def _shipping_build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = dict(P._locality_bounded_r24_build(root, out))
    build_s = time.perf_counter() - started
    verify_started = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - verify_started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"shipping r24 verification failed: {verified!r}")
    index, physical = CONTROL._read_index(out)
    return {
        "archive_bytes": int(physical["archive_bytes"]),
        "tree_sha256": verified["tree_sha256"],
        "complete_create_s": build_s + verify_s,
        "build_s": build_s,
        "verify_s": verify_s,
        "dict_blob_present": index.get("dict_blob") is not None,
        "unique_blobs": int(stats["unique_blobs"]),
    }


def _target_evidence(work_root: Path) -> dict:
    sources = CONTROL._build_sources(work_root / "sources")
    root = sources[TARGET]
    samples = {"shipping": [], "candidate": []}
    bytes_seen = {"shipping": set(), "candidate": set()}
    trees = {"shipping": set(), "candidate": set()}
    dict_flags = {"shipping": set(), "candidate": set()}
    for round_index in range(ROUNDS):
        order = ("shipping", "candidate") if round_index % 2 == 0 else ("candidate", "shipping")
        for side in order:
            out = work_root / f"target-{side}-{round_index}.cmpct"
            row = _shipping_build(root, out) if side == "shipping" else _candidate_build(root, out)
            samples[side].append(float(row["complete_create_s"]))
            bytes_seen[side].add(int(row["archive_bytes"]))
            trees[side].add(str(row["tree_sha256"]))
            dict_flags[side].add(bool(row["dict_blob_present"]))
    if any(len(values) != 1 for values in bytes_seen.values()) or any(len(values) != 1 for values in trees.values()):
        raise RuntimeError("target archive/tree identity was not deterministic")
    shipping_bytes = next(iter(bytes_seen["shipping"]))
    candidate_bytes = next(iter(bytes_seen["candidate"]))
    same_tree = trees["shipping"] == trees["candidate"]
    return {
        "label": f"neutral_hostile_v1/{TARGET}",
        "rounds": ROUNDS,
        "shipping": {
            "archive_bytes": shipping_bytes,
            "median_complete_create_s": statistics.median(samples["shipping"]),
            "dict_blob_flags": sorted(dict_flags["shipping"]),
        },
        "candidate": {
            "archive_bytes": candidate_bytes,
            "median_complete_create_s": statistics.median(samples["candidate"]),
            "dict_blob_flags": sorted(dict_flags["candidate"]),
        },
        "same_verified_tree": same_tree,
        "saving_bytes": shipping_bytes - candidate_bytes,
        "candidate_not_slower_median": statistics.median(samples["candidate"]) <= statistics.median(samples["shipping"]),
    }


def _all15(work_root: Path) -> dict:
    accepted = PACKGEN.GENERAL._accepted_v029_rows()
    neutral = PACKGEN.GENERAL.V029._load(
        PACKGEN.GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_bindict_neutral",
    )
    hostile = PACKGEN.GENERAL.V029._load(
        PACKGEN.GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_bindict_hostile",
    )
    repair = PACKGEN.GENERAL.V029._load(PACKGEN.GENERAL.V029.REPAIR_PATH, "cmpct_v030_bindict_repair")
    repair.install_generation_hooks(neutral)
    rows = []
    for suite, module, root in (
        ("neutral_hostile_v1", neutral, work_root / "neutral"),
        ("resemblance_hostile_v1", hostile, work_root / "resemblance"),
    ):
        module.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(path for path in root.iterdir() if path.is_dir()):
            expected = accepted[(suite, workload.name)]["tree_sha256"]
            with tempfile.TemporaryDirectory(prefix="cmpct-v030-bindict-", dir=work_root) as td:
                td_path = Path(td)
                shipping = _shipping_build(workload, td_path / "shipping.cmpct")
                candidate = _candidate_build(workload, td_path / "candidate.cmpct")
            canonical_equal = shipping["tree_sha256"] == candidate["tree_sha256"]
            row = {
                "label": f"{suite}/{workload.name}",
                "frozen_source_tree_sha256": expected,
                "shipping_bytes": int(shipping["archive_bytes"]),
                "candidate_bytes": int(candidate["archive_bytes"]),
                "delta_bytes": int(candidate["archive_bytes"]) - int(shipping["archive_bytes"]),
                "shipping_tree_sha256": shipping["tree_sha256"],
                "candidate_tree_sha256": candidate["tree_sha256"],
                "same_verified_tree": canonical_equal,
                "frozen_source_digest_role": "corpus-provenance-only",
                "shipping_candidate_digest_role": "canonical-r24-product-semantic-equivalence",
                "shipping_dict_blob_present": shipping["dict_blob_present"],
                "candidate_dict_blob_present": candidate["dict_blob_present"],
            }
            rows.append(row)
            print(json.dumps({"label": row["label"], "delta_bytes": row["delta_bytes"]}), flush=True)
    gate = {
        "exact_workload_count": len(rows) == 15,
        "all_source_and_candidate_trees_match": all(row["same_verified_tree"] for row in rows),
        "historical_source_digest_not_misused_as_product_digest": all(
            row["frozen_source_digest_role"] == "corpus-provenance-only" for row in rows
        ),
        "zero_byte_regressions": all(row["delta_bytes"] <= 0 for row in rows),
        "at_least_one_strict_improvement": any(row["delta_bytes"] < 0 for row in rows),
    }
    gate["promotion_candidate"] = (
        gate["exact_workload_count"]
        and gate["all_source_and_candidate_trees_match"]
        and gate["historical_source_digest_not_misused_as_product_digest"]
        and gate["zero_byte_regressions"]
        and gate["at_least_one_strict_improvement"]
    )
    return {
        "rows": rows,
        "gate": gate,
        "shipping_total_bytes": sum(row["shipping_bytes"] for row in rows),
        "candidate_total_bytes": sum(row["candidate_bytes"] for row in rows),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    target = _target_evidence(work_root / "target")
    all15_root = work_root / "all15"
    all15_root.mkdir(parents=True)
    campaign = _all15(all15_root)
    return {
        "schema": "cmpct-v030-r24-binary-dictionary-isolation-v1",
        "hypothesis": "release-only .bin micro-pack admission must not automatically broaden Zstd dictionary training",
        "target": target,
        "all15": campaign,
        "identity_domain_repair": {
            "historical_source_digest_role": "frozen corpus provenance only",
            "canonical_product_digest_role": "shipping-vs-candidate semantic tree equivalence",
            "threshold_changed": False,
        },
        "contract": {
            "format_revision": 24,
            "archive_grammar_changed": False,
            "micro_pack_binary_admission_changed": False,
            "dictionary_training_policy_only": "medium-binary release hint suppressed during dictionary training",
            "strong_verification_required": True,
            "promotion_requires_zero_byte_regressions_all_15": True,
            "release_effect": "none; evidence only until ordinary product promotion and authority",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-binary-dict-isolation-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-binary-dict-isolation.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target": result["target"], "all15_gate": result["all15"]["gate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
