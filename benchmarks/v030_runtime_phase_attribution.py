from __future__ import annotations

"""Research-only phase attribution for the exact-head v0.30 runtime blockers.

This instrument does not alter the frozen release gate. It runs the real promoted product front door on the
three authority-v2 runtime targets, records wall time owned by product-level semantic phases, and verifies exact
user-tree identity after every operation. The goal is to decide whether the current runtime debt is large enough
inside a local owner to justify optimization, or whether Forge should escalate architecture instead.
"""

import argparse
import contextlib
import json
import shutil
import statistics
import time
from pathlib import Path

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_product_base as BASE
from experiments import entropygraph_v030_release_product_logs_candidate as LOGS_PRODUCT
from experiments import entropygraph_v030_logs_fused_extract as LOGS_FUSED

TARGETS = (
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("neutral_hostile_v1", "05_logs_and_telemetry"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)
ROUNDS = 3


class PhaseRecorder:
    def __init__(self) -> None:
        self.samples: dict[str, list[float]] = {}

    def wrap(self, owner, name: str, label: str):
        original = getattr(owner, name)

        def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                self.samples.setdefault(label, []).append(time.perf_counter() - started)

        setattr(owner, name, timed)
        return original

    def summary(self) -> dict:
        return {
            key: {
                "calls": len(values),
                "total_s": float(sum(values)),
                "median_call_s": float(statistics.median(values)),
                "max_call_s": float(max(values)),
            }
            for key, values in sorted(self.samples.items())
            if values
        }


@contextlib.contextmanager
def instrumented_phases(recorder: PhaseRecorder):
    patches = []
    # Parent phases plus inner canonical owners. Nested timers intentionally overlap; they are ownership
    # attribution, not additive accounting. PrefixGraph.build itself is deliberately not monkeypatched: the
    # shipping one-shot process executor validates that callable's module/name identity before dispatch, so
    # replacing it would mutate execution semantics instead of merely observing them. The enclosing r25
    # release-candidate timer still prices the complete PrefixGraph/G0-G4 tournament honestly.
    #
    # v3 additionally splits the now-proven dominant G04 owner at stable semantic seams. In particular, record
    # audition is timed as an aggregate of real calls rather than replaced with a different scheduler. This lets
    # the next causal A/B distinguish inherited-v0.29 construction, attempt-5 graph construction, transform
    # search, overlay materialization and verification without changing any candidate bytes or selection law.
    G04 = BASE.C.RC.G04
    for owner, name, label in (
        (PRODUCT, "_shared_frontdoor_preflight", "build.frontdoor_preflight"),
        (LOGS_PRODUCT, "_parallel_candidates", "build.logs_parallel_candidates"),
        (BASE.C, "build", "build.canonical_final"),
        (BASE.C, "_prepare_profile_tree", "build.canonical.prepare_profile_tree"),
        (BASE.C, "_r24_build", "build.canonical.r24_floor"),
        (BASE.C, "_r25_build", "build.canonical.r25_tournament"),
        (BASE.C.RC, "build", "build.canonical.r25.release_candidate"),
        (G04, "build", "build.canonical.r25.g04"),
        (G04.BASE, "build", "build.canonical.r25.g04.v029_floor"),
        (G04.A5, "build_graph", "build.canonical.r25.g04.attempt5_graph"),
        (G04, "_audition_record", "build.canonical.r25.g04.record_audition"),
        (G04, "_write_overlay", "build.canonical.r25.g04.overlay_write"),
        (G04, "strong_verify", "build.canonical.r25.g04.overlay_verify"),
        (BASE, "_locality_bounded_r24_build", "build.r24_candidate"),
        (BASE.POLICY, "extract_verified_into_staging", "extract.r25_verified_stream"),
        (BASE.VERIFIED_RESTORE, "restore_verified_manifest_tree", "extract.r25_fs_restore"),
        (LOGS_FUSED, "_restore_filesystem_metadata", "extract.logs_fs_restore"),
    ):
        patches.append((owner, name, recorder.wrap(owner, name, label)))
    patches.append((LOGS_FUSED.LOGS.Archive, "_restore_session", recorder.wrap(LOGS_FUSED.LOGS.Archive, "_restore_session", "extract.logs_restore_session")))
    try:
        yield
    finally:
        for owner, name, original in reversed(patches):
            setattr(owner, name, original)


def _run_target(source: Path, work: Path) -> dict:
    source_tree = PRODUCT.treehash(source)
    archive = work / "archive.cmpct"
    build_rounds = []
    extract_rounds = []
    build_stats = None
    for index in range(ROUNDS):
        archive.unlink(missing_ok=True)
        recorder = PhaseRecorder()
        with instrumented_phases(recorder):
            started = time.perf_counter(); build_stats = PRODUCT.build(source, archive); wall = time.perf_counter() - started
        verified = PRODUCT.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError("instrumented build failed exact strong verification")
        build_rounds.append({"round": index, "wall_s": wall, "phases": recorder.summary()})

    for index in range(ROUNDS):
        dst = work / f"extract-{index}"
        shutil.rmtree(dst, ignore_errors=True)
        recorder = PhaseRecorder()
        with instrumented_phases(recorder):
            started = time.perf_counter(); PRODUCT.extract(archive, dst); wall = time.perf_counter() - started
        if PRODUCT.treehash(dst) != source_tree:
            raise RuntimeError("instrumented extraction failed exact tree identity")
        extract_rounds.append({"round": index, "wall_s": wall, "phases": recorder.summary()})

    return {
        "source_tree_sha256": source_tree,
        "archive_bytes": archive.stat().st_size,
        "selected": build_stats.get("selected") if isinstance(build_stats, dict) else None,
        "format_profile": build_stats.get("format_profile") if isinstance(build_stats, dict) else None,
        "build_rounds": build_rounds,
        "extract_rounds": extract_rounds,
        "build_wall_median_s": float(statistics.median(row["wall_s"] for row in build_rounds)),
        "extract_wall_median_s": float(statistics.median(row["wall_s"] for row in extract_rounds)),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpora = PERF._build_corpora(work_root / "corpus")
    rows = []
    for suite, name in TARGETS:
        target_work = work_root / f"{suite}-{name}"
        target_work.mkdir(parents=True)
        row = _run_target(corpora[(suite, name)], target_work)
        rows.append({"suite": suite, "name": name, **row})
    return {
        "schema": "cmpct-v030-runtime-phase-attribution-v3",
        "release_credit": False,
        "rounds": ROUNDS,
        "targets": rows,
        "claim_boundary": (
            "Research-only in-process semantic-phase ownership on the exact promoted product front door. "
            "Nested phase times overlap and are not additive. v3 splits G04 into inherited-floor, attempt-5 graph, "
            "record-audition, overlay-write and overlay-verification owners without changing scheduler or bytes. "
            "It preserves exact archive/tree semantics but is not fresh-process release timing and cannot unlock v0.30."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
