from __future__ import annotations

"""H-ATTR v2: source-sealed Office v0.25 physical attribution.

v1 correctly failed closed because it compared two different tree-hash contracts: the
frozen v0.25 file-only hash and the modern product filesystem hash.  v2 preserves that
negative and repairs only the referee identity test.  Both contenders are now compared
with one neutral, engine-independent file manifest digest (relative path + length +
bytes), while both engine-specific hashes remain recorded diagnostically.

All physical-accounting, source-seal, no-selector/no-format/no-threshold and exact-role
closure requirements from v1 remain unchanged.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from benchmarks import v030_r4_office_v025_physical_attribution as V1

SCHEMA = "cmpct-v030-r4-office-v025-physical-attribution-v2"


def neutral_file_treehash(root: Path) -> str:
    """Engine-independent identity for the byte/path tree under comparison."""
    h = sha256()
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = p.relative_to(root).as_posix().encode()
        data = p.read_bytes()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update(len(data).to_bytes(8, "little"))
        h.update(data)
    return h.hexdigest()


def _orchestrate(work: Path, frozen_checkout: Path) -> dict[str, Any]:
    from benchmarks import mosaic_v029_generalization_bench as V029
    from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
    from experiments import entropygraph_v030_release_product as PRODUCT

    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_v025_attr_v2_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_v025_attr_v2_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    neutral_sha = neutral_file_treehash(source)
    product_tree_sha = PRODUCT.treehash(source)

    sfv4 = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")
    sfv4_sizes = dict(sfv4["component_bytes"])
    if sum(sfv4_sizes.values()) != int(sfv4["stored_bytes"]):
        raise RuntimeError("SFV4 component accounting mismatch")

    worker_json = work / "v025-attribution.json"
    archive = work / "frozen-v025.cmpct"
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--frozen-worker",
        "--frozen-checkout",
        str(frozen_checkout),
        "--source",
        str(source),
        "--archive",
        str(archive),
        "--output",
        str(worker_json),
    ]
    subprocess.run(cmd, check=True, env=os.environ.copy())
    hist = json.loads(worker_json.read_text())
    # Frozen v0.25 treehash is exactly the same neutral file/path/bytes contract.  Do not
    # compare it to PRODUCT.treehash(), whose newer filesystem contract is intentionally
    # different and was the v1 harness error.
    if hist["tree_sha256"] != neutral_sha:
        raise RuntimeError(f"neutral tree identity mismatch: frozen={hist['tree_sha256']} neutral={neutral_sha}")

    v025_phys = hist["physical_bytes_by_role"]
    v025_stream = int(v025_phys["stream_pool"])
    v025_nonstream = int(hist["archive_bytes"]) - v025_stream
    sfv4_stream = int(sfv4_sizes.get("streams.bin", 0))
    sfv4_nonstream = int(sfv4["stored_bytes"]) - sfv4_stream
    total_gap = int(sfv4["stored_bytes"]) - int(hist["archive_bytes"])
    stream_delta = sfv4_stream - v025_stream
    nonstream_delta = sfv4_nonstream - v025_nonstream
    if stream_delta + nonstream_delta != total_gap:
        raise RuntimeError("coarse role delta does not close")
    dominant = "stream_path" if abs(stream_delta) >= abs(nonstream_delta) else "nonstream_path"
    dominant_delta = stream_delta if dominant == "stream_path" else nonstream_delta
    concentration = abs(dominant_delta) / max(1, abs(total_gap))

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "identity": {
            "neutral_file_tree_sha256": neutral_sha,
            "frozen_v025_tree_sha256": hist["tree_sha256"],
            "modern_product_tree_sha256": product_tree_sha,
            "same_neutral_tree": True,
            "v1_harness_negative_preserved": {
                "frozen_hash": "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57",
                "modern_hash": "87bbe63fa864725f13011a14a8e81c0ec06fa54dee7881302cac9dd5b4b2f1c7",
                "cause": "different hash contracts, not different source bytes",
            },
        },
        "sfv4": {
            "stored_bytes": int(sfv4["stored_bytes"]),
            "component_bytes": sfv4_sizes,
            "all_member_stream_bytes": int(sfv4["all_member_stream_bytes"]),
            "literal_skeleton_bytes": int(sfv4["literal_skeleton_bytes"]),
            "derived_file_count": int(sfv4["derived_file_count"]),
            "derived_logical_bytes": int(sfv4["derived_logical_bytes"]),
        },
        "frozen_v025": hist,
        "comparison": {
            "same_tree": True,
            "accepted_v029_office_bytes": V1.ACCEPTED_V029_OFFICE,
            "frozen_v025_same_tree_bytes": int(hist["archive_bytes"]),
            "frozen_v025_delta_vs_accepted_v029_bytes": int(hist["archive_bytes"]) - V1.ACCEPTED_V029_OFFICE,
            "sfv4_minus_frozen_v025_bytes": total_gap,
            "stream_path_delta_bytes": stream_delta,
            "nonstream_path_delta_bytes": nonstream_delta,
            "dominant_coarse_role": dominant,
            "dominant_delta_bytes": dominant_delta,
            "dominant_abs_fraction_of_gap": concentration,
        },
        "hypothesis": {
            "physical_accounting_exact": int(hist["physical_bytes_sum"]) == int(hist["archive_bytes"]),
            "source_sealed": bool(hist["source_sealed"]),
            "same_neutral_tree": True,
            "role_concentration_ge_50pct": concentration >= 0.5,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "selector_changed": False,
            "format_changed": False,
            "thresholds_changed": False,
            "frozen_contender_executes_frozen_source": True,
            "note": "coarse stream/nonstream deltas are causal attribution guides, not interchangeable-format byte claims",
        },
        "next_if_stream_dominant": "measure frozen v0.25 hot/cold stream-slab codec/framing economics against SFV4/page-seed streams under the same locality law",
        "next_if_nonstream_dominant": "split v0.25 direct/micro/skeleton/control bytes against SFV4 base/control bytes and isolate one bounded packing/control primitive",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-v025-attribution-v2-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-v025-attribution-v2.json"))
    p.add_argument("--frozen-checkout", type=Path, required=True)
    p.add_argument("--frozen-worker", action="store_true")
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    a = p.parse_args()
    if a.frozen_worker:
        if a.source is None or a.archive is None:
            p.error("--frozen-worker requires --source and --archive")
        V1._frozen_worker(a.frozen_checkout, a.source, a.archive, a.output)
        return
    d = _orchestrate(a.work_root, a.frozen_checkout)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({
        "identity": d["identity"],
        "comparison": d["comparison"],
        "v025_roles": d["frozen_v025"]["physical_bytes_by_role"],
        "sfv4_components": d["sfv4"]["component_bytes"],
        "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()
