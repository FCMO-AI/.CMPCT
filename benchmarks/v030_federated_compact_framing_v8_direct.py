from __future__ import annotations

"""Direct measured C25EG08 office frontier.

The structural EG08 proof establishes an exact 92-byte physical-framing reduction over the measured EG07
representation, enough to turn EG07's 42-byte office miss into a 51-byte strict win over accepted v0.29 at the
same payload floor.  This lane closes the remaining evidence gap: derive the *minimum modeled compression-effort
selection* needed after that framing reduction, rebuild that selection as real EG07 bytes, compact those bytes to
C25EG08, and charge the complete build + compaction + mandatory EG08 strong-verification wall-clock against fresh
ZIP/Deflate-9 and solid Zstd-19 comparators.

No shipping selector, native/Android dispatch, compressor default, locality limit, v0.29 byte, or comparator is
changed.  A red timing result is valid negative evidence; this file exists specifically to prevent arithmetic-only
promotion of the compact framing win.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_federated_embedded_fs_v7_effort_oracle as EG07_EFFORT
from benchmarks import v030_federated_selective_effort_oracle as EFFORT
from benchmarks import v030_federated_selective_effort_oracle_v3 as EFFORT_V3
from benchmarks import v030_federated_selective_effort_oracle_v4 as EFFORT_V4
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EXPECTED_OFFICE_V029 = 5_954_026
EXPECTED_EG07_ALL_BEST = 5_954_067
EXPECTED_FRAMING_SAVING = 92
ROUNDS = 3


def _h(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def _eg07_effort_bindings():
    """Bind the inherited selective-effort builder to EG07 and restore every process-global owner afterward."""
    old_candidate = EFFORT.CAND
    old_prepare = EFFORT._prepare
    old_build = EFFORT.V25.build

    def finalized_build():
        stats = old_build()
        EG07.finalize_research_archive(Path(EFFORT.V25.OUT), Path(EFFORT.V25.ROOT))
        return stats

    EFFORT.CAND = EG07
    EFFORT._prepare = EG07_EFFORT._prepare
    EFFORT.V25.build = finalized_build
    try:
        yield
    finally:
        EFFORT.V25.build = old_build
        EFFORT._prepare = old_prepare
        EFFORT.CAND = old_candidate
        EG07._PENDING_CONTROL.clear()


def _minimum_selection(packs: list[dict], required_saving: int) -> dict:
    model = EFFORT._dp(packs, max_extra_ms=EFFORT.MAX_MODEL_EXTRA_MS)
    for used_ms in sorted(model["states"]):
        saving, selection = model["states"][used_ms]
        if int(saving) >= int(required_saving):
            return {
                "modeled_extra_ms": int(used_ms),
                "modeled_saving_bytes": int(saving),
                "selection": dict(selection),
            }
    raise RuntimeError(f"EG08 office floor is unreachable by measured pack effort: need {required_saving} bytes")


def _build_selected(stage: Path, root: Path, selection: dict[str, int]) -> dict:
    """Build selected EG07 payloads, compact to EG08, then verify only the final candidate."""
    profile, _ = EG07_EFFORT._prepare(stage, root / "profile-stage")
    eg07_archive = root / "selected.c25eg07"
    eg08_archive = root / "selected.c25eg08"
    original_zc = V25.zc

    def selective(raw: bytes, requested: int = 19) -> bytes:
        requested = int(requested)
        if requested < 19:
            return original_zc(raw, min(requested, 1))
        return original_zc(raw, int(selection.get(_h(raw), 1)))

    started = time.perf_counter()
    with _eg07_effort_bindings():
        # _engine observes the bindings above and therefore emits a finalized EG07 archive with the chosen final
        # pack effort while preserving the exact inherited candidate/reconstruction graph.
        with EFFORT._engine(eg07_archive, profile, selective):
            V25.build()
        framing = EG08.compact_existing(eg07_archive, eg08_archive)
    build_and_compact_s = time.perf_counter() - started

    started = time.perf_counter()
    verified = EG08.strong_verify(eg08_archive, expected_tree=EG07._treehash(stage))
    verify_s = time.perf_counter() - started
    locality = EG08.locality_report(eg08_archive)
    if not verified.get("ok"):
        raise RuntimeError("direct EG08 candidate failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("direct EG08 candidate exceeded frozen locality/decode limits")

    return {
        "archive_bytes": eg08_archive.stat().st_size,
        "archive_sha256": hashlib.sha256(eg08_archive.read_bytes()).hexdigest(),
        "build_and_compact_s": build_and_compact_s,
        "strong_verify_s": verify_s,
        "verified_create_s": build_and_compact_s + verify_s,
        "framing": framing,
        "verified": verified,
        "locality": locality,
    }


def _comparators(stage: Path, root: Path) -> dict:
    expected_tree = EXT._tree(stage)
    samples = {"zip": [], "zstd19": []}
    sizes = {"zip": set(), "zstd19": set()}
    for round_index in range(ROUNDS):
        order = ("zip", "zstd19") if round_index % 2 == 0 else ("zstd19", "zip")
        for name in order:
            lane = root / f"cmp-{round_index}-{name}"
            lane.mkdir(parents=True)
            if name == "zip":
                result = EXT._zip(stage, lane / "archive.zip", lane / "out")
            else:
                result = EXT._tar_zstd(stage, lane / "archive.tar.zst", lane / "out", lane)
                if not result.get("available"):
                    raise RuntimeError(f"solid Zstd-19 unavailable: {result!r}")
            EXT._verify_extracted(lane / "out", expected_tree, name)
            samples[name].append(float(result["create_s"]))
            sizes[name].add(int(result["archive_bytes"]))
    if any(len(value) != 1 for value in sizes.values()):
        raise RuntimeError(f"nondeterministic comparator size: {sizes!r}")
    return {
        name: {
            "archive_bytes": next(iter(sizes[name])),
            "median_create_s": statistics.median(samples[name]),
            "raw_create_s": samples[name],
        }
        for name in ("zip", "zstd19")
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    # Reuse the audited EG07 pack frontier, extended through levels 20-22 and adapted to the authoritative repaired
    # accepted-v0.29 schema.  This profiles the exact payload inputs whose bytes EG08 intentionally leaves unchanged.
    old_levels = EFFORT.LEVELS
    EFFORT.LEVELS = EFFORT_V3.EXTENDED_LEVELS
    try:
        eg07 = EG07_EFFORT.run(work_root / "eg07-frontier")
    finally:
        EFFORT.LEVELS = old_levels
    office = next(row for row in eg07["rows"] if row["label"] == "neutral_hostile_v1/02_office_workspace")
    if int(office["accepted_v029_bytes"]) != EXPECTED_OFFICE_V029:
        raise RuntimeError("direct EG08 evidence drifted from immutable office v0.29 bytes")
    eg07_all_best = int(office["compression_effort_upper_bound"]["all_best_archive_floor_bytes"])
    if eg07_all_best != EXPECTED_EG07_ALL_BEST:
        raise RuntimeError(f"direct EG08 evidence drifted from EG07 floor: {eg07_all_best}")
    pack_count = int(office["baseline_level1"]["physical_pack_count"])
    framing_saving = 20 + 8 * pack_count
    if framing_saving != EXPECTED_FRAMING_SAVING:
        raise RuntimeError(f"direct EG08 framing delta drifted: {framing_saving}")

    eg07_level1 = int(office["baseline_level1"]["archive_bytes"])
    eg08_level1 = eg07_level1 - framing_saving
    required_saving = max(0, eg08_level1 - EXPECTED_OFFICE_V029 + 1)
    minimum = _minimum_selection(office["pack_frontier"], required_saving)

    # Rebuild the exact frozen office source independently of the profile run above.
    accepted = EFFORT_V4._accepted_rows_with_legacy_alias()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_eg08_direct_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg08_direct_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    key = ("neutral_hostile_v1", "02_office_workspace")
    if EXT._tree(source) != accepted[key]["tree_sha256"]:
        raise RuntimeError("direct EG08 frozen office source identity drifted")

    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-direct-", dir=work_root) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "normalized-root")
        comparators = _comparators(stage, root / "comparators")
        samples = []
        sizes = set()
        shas = set()
        locality = None
        framing = None
        verified_tree = None
        for round_index in range(ROUNDS):
            lane = root / f"candidate-{round_index}"
            lane.mkdir()
            result = _build_selected(stage, lane, minimum["selection"])
            samples.append(float(result["verified_create_s"]))
            sizes.add(int(result["archive_bytes"]))
            shas.add(str(result["archive_sha256"]))
            locality = result["locality"]
            framing = result["framing"]
            verified_tree = result["verified"].get("tree_sha256") or result["verified"].get("tree")
        if len(sizes) != 1 or len(shas) != 1:
            raise RuntimeError("direct EG08 candidate is not deterministic")
        candidate_bytes = next(iter(sizes))
        median_create = statistics.median(samples)

    strict = {
        "beats_accepted_v029_size": candidate_bytes < EXPECTED_OFFICE_V029,
        "beats_zip_size": candidate_bytes < int(comparators["zip"]["archive_bytes"]),
        "beats_zstd19_size": candidate_bytes < int(comparators["zstd19"]["archive_bytes"]),
        "verified_create_beats_zip": median_create < float(comparators["zip"]["median_create_s"]),
        "verified_create_beats_zstd19": median_create < float(comparators["zstd19"]["median_create_s"]),
        "within_release_locality_bounds": bool(locality and locality.get("within_release_bounds")),
    }
    strict["passed"] = all(strict.values())
    gate = {
        "eg07_frontier_valid": bool(eg07["measurement_gate"]["passed"]),
        "exact_framing_saving": framing_saving == EXPECTED_FRAMING_SAVING,
        "minimum_selection_found": bool(minimum["selection"]),
        "candidate_rounds_complete": len(samples) == ROUNDS,
        "comparator_rounds_complete": all(len(comparators[name]["raw_create_s"]) == ROUNDS for name in comparators),
        "candidate_deterministic": len(sizes) == 1 and len(shas) == 1,
        "strict_four_way_and_v029": strict["passed"],
    }
    gate["passed"] = all(gate.values())

    return {
        "schema": "cmpct-v030-eg08-direct-office-v1",
        "candidate": "C25EG08",
        "accepted_v029_bytes": EXPECTED_OFFICE_V029,
        "eg07_all_best_floor_bytes": eg07_all_best,
        "physical_pack_count": pack_count,
        "framing_saving_bytes": framing_saving,
        "eg08_level1_bytes": eg08_level1,
        "required_payload_saving_bytes": required_saving,
        "minimum_modeled_effort": minimum,
        "measured_candidate": {
            "archive_bytes": candidate_bytes,
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": median_create,
            "raw_verified_create_s": samples,
            "locality": locality,
            "framing": framing,
            "verified_tree": verified_tree,
            "strict": strict,
        },
        "comparators": comparators,
        "measurement_gate": gate,
        "claim_boundary": (
            "Research-only direct C25EG08 office productization evidence. A green result proves the candidate itself, "
            "not arithmetic, clears v0.29/ZIP/Zstd size and ZIP/Zstd verified-creation requirements. Native/Android "
            "parity, selector admission, all-15 generalization/external/runtime authorities and final release lock "
            "remain mandatory before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "minimum_modeled_effort": result["minimum_modeled_effort"],
        "measured_candidate": result["measured_candidate"],
        "measurement_gate": result["measurement_gate"],
    }, indent=2), flush=True)
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("direct C25EG08 office frontier failed")


if __name__ == "__main__":
    main()
