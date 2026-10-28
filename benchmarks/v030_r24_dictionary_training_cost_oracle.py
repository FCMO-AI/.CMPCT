from __future__ import annotations

"""All-15 exact-byte diagnostic for r24 dictionary-training cost.

Shipping r24 can train a Zstd dictionary and later remove it when no selected physical record uses
CODEC_ZSTDDICT. Post-selection elision recovers bytes but not training CPU. This research-only A/B
rebuilds every frozen workload with training disabled and reports only rows whose final verified archive
is byte-for-byte identical to shipping r24. It deliberately does not define a production skip rule.

The accepted-v0.29 corpus tree hash and the canonical r24 strong-verification tree hash are intentionally
distinct evidence domains. The accepted hash binds the generated input to the frozen corpus. Promotion
evidence compares shipping-r24 and no-dictionary *canonical product trees to each other*; it never equates
a historical source-identity hash with a canonical product semantic-tree hash.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import statistics
import time

from benchmarks import v030_r24_binary_dictionary_isolation_oracle as PRIOR
from benchmarks import v030_r24_medium_binary_pack_generalization as PACKGEN
from experiments import entropygraph_v030_release_product as P

ROUNDS = 3


class _NoDictionaryBuilder(P.C.Builder):
    def _train_dictionary(self):
        self.dictionary = b""
        self.dict_hash = None
        return None


def _shape(root: Path) -> tuple[int, int]:
    count = largest = 0
    for dirpath, dirnames, filenames in os.walk(Path(root), followlinks=False):
        dirnames[:] = [n for n in dirnames if not os.path.islink(Path(dirpath) / n)]
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


def _no_dictionary_build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    builder = _NoDictionaryBuilder(root, deflate_reuse_min=P.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.micro_pack_max_file = P.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular_files, largest = _shape(root)
    if largest:
        builder.micro_pack_target = min(P.R24_RELEASE_PACK_CAP_BYTES, 8 * largest)
    old_wide = getattr(P._R24_CDC_POLICY, "wide_single_file", False)
    old_medium = getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)
    P._R24_CDC_POLICY.wide_single_file = regular_files == 1 and largest >= P.R24_RELEASE_WIDE_CHUNK_BYTES
    P._R24_CDC_POLICY.medium_binary_pack = True
    try:
        builder.build(out)
    finally:
        P._R24_CDC_POLICY.wide_single_file = old_wide
        P._R24_CDC_POLICY.medium_binary_pack = old_medium
    build_s = time.perf_counter() - started
    verify_started = time.perf_counter()
    verified = P.strong_verify(out)
    verify_s = time.perf_counter() - verify_started
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"no-dictionary r24 verification failed: {verified!r}")
    raw = out.read_bytes()
    return {
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "tree_sha256": str(verified["tree_sha256"]),
        "complete_create_s": build_s + verify_s,
    }


def _shipping_build(root: Path, out: Path) -> dict:
    row = PRIOR._shipping_build(root, out)
    return {**row, "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}


def _measure(root: Path, work: Path, accepted_source_tree: str) -> dict:
    samples = {"shipping": [], "no_dictionary": []}
    identities = {"shipping": set(), "no_dictionary": set()}
    trees = {"shipping": set(), "no_dictionary": set()}
    sizes = {"shipping": set(), "no_dictionary": set()}
    for rep in range(ROUNDS):
        order = ["shipping", "no_dictionary"] if rep % 2 == 0 else ["no_dictionary", "shipping"]
        for side in order:
            out = work / f"{side}-{rep}.cmpct"
            row = _shipping_build(root, out) if side == "shipping" else _no_dictionary_build(root, out)
            samples[side].append(float(row["complete_create_s"]))
            identities[side].add(str(row["archive_sha256"]))
            trees[side].add(str(row["tree_sha256"]))
            sizes[side].add(int(row["archive_bytes"]))
    deterministic = all(len(v) == 1 for v in (*identities.values(), *trees.values(), *sizes.values()))
    exact_bytes = deterministic and identities["shipping"] == identities["no_dictionary"]
    product_tree_equal = deterministic and trees["shipping"] == trees["no_dictionary"]
    ship_t = statistics.median(samples["shipping"])
    nodict_t = statistics.median(samples["no_dictionary"])
    saved_s = ship_t - nodict_t
    saved_ratio = saved_s / max(ship_t, 1e-12)
    return {
        "rounds": ROUNDS,
        "accepted_source_tree_sha256": accepted_source_tree,
        "source_identity_domain": "accepted-v0.29 frozen corpus provenance",
        "product_tree_domain": "canonical r24 strong-verification semantic tree",
        "shipping_verified_tree_sha256": next(iter(trees["shipping"])) if len(trees["shipping"]) == 1 else None,
        "no_dictionary_verified_tree_sha256": next(iter(trees["no_dictionary"])) if len(trees["no_dictionary"]) == 1 else None,
        "shipping_bytes": next(iter(sizes["shipping"])) if len(sizes["shipping"]) == 1 else None,
        "no_dictionary_bytes": next(iter(sizes["no_dictionary"])) if len(sizes["no_dictionary"]) == 1 else None,
        "shipping_median_complete_create_s": ship_t,
        "no_dictionary_median_complete_create_s": nodict_t,
        "saved_s": saved_s,
        "saved_ratio": saved_ratio,
        "deterministic": deterministic,
        "exact_archive_bytes_and_sha": exact_bytes,
        "canonical_product_tree_equal": product_tree_equal,
        "material_exact_opportunity": exact_bytes and product_tree_equal and saved_s >= 0.005 and saved_ratio >= 0.10,
    }


def _sources(work_root: Path) -> list[tuple[str, Path, str]]:
    accepted = PACKGEN.GENERAL._accepted_v029_rows()
    neutral = PACKGEN.GENERAL.V029._load(PACKGEN.GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_dictcost_neutral")
    hostile = PACKGEN.GENERAL.V029._load(PACKGEN.GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_dictcost_hostile")
    repair = PACKGEN.GENERAL.V029._load(PACKGEN.GENERAL.V029.REPAIR_PATH, "cmpct_v030_dictcost_repair")
    repair.install_generation_hooks(neutral)
    rows = []
    for suite, module, root in (("neutral_hostile_v1", neutral, work_root / "neutral"), ("resemblance_hostile_v1", hostile, work_root / "resemblance")):
        module.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(p for p in root.iterdir() if p.is_dir()):
            rows.append((f"{suite}/{workload.name}", workload, accepted[(suite, workload.name)]["tree_sha256"]))
    return rows


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows = []
    for label, root, accepted_source_tree in _sources(work_root / "corpus"):
        work = work_root / "rows" / label.replace("/", "__")
        work.mkdir(parents=True, exist_ok=True)
        row = _measure(root, work, accepted_source_tree)
        row["label"] = label
        rows.append(row)
        print(json.dumps({"label": label, "exact": row["exact_archive_bytes_and_sha"], "product_tree_equal": row["canonical_product_tree_equal"], "saved_s": row["saved_s"], "saved_ratio": row["saved_ratio"]}), flush=True)
    opportunities = [r["label"] for r in rows if r["material_exact_opportunity"]]
    return {
        "schema": "cmpct-v030-r24-dictionary-training-cost-v2",
        "contract": {
            "workloads": 15,
            "format_revision": 24,
            "production_change": False,
            "release_credit": False,
            "dictionary_training_disabled_only_in_research_candidate": True,
            "exact_archive_identity_required_for_opportunity": True,
            "canonical_product_tree_equality_required_for_opportunity": True,
            "accepted_source_hash_is_provenance_not_product_tree": True,
            "minimum_material_saved_ratio": 0.10,
            "minimum_material_saved_s": 0.005,
            "future_skip_requires_separate_content_agnostic_admission_proof": True,
        },
        "rows": rows,
        "summary": {
            "exact_workload_count": len(rows) == 15,
            "all_candidates_match_shipping_product_tree": all(r["canonical_product_tree_equal"] for r in rows),
            "exact_byte_identity_rows": sum(bool(r["exact_archive_bytes_and_sha"]) for r in rows),
            "material_exact_opportunities": opportunities,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
