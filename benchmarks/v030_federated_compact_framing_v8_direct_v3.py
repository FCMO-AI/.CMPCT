from __future__ import annotations

"""Single-pass-boundary C25EG08 office frontier.

The v2 direct proof established exact byte identity for the parallel final-pack schedule, but intentionally paid
for every final pack twice: once at level 1 during the inherited EG07 build and again at its selected final effort.
That conservative boundary measured 5,953,922 B with full integrity/locality, yet missed ZIP creation wall-clock.

This v3 proof removes only that duplicated *final physical-pack* compression.  The historical graph/search path is
unchanged.  Audition/probe compression requests below the final-pack level still execute at level 1 exactly as in
v2; final physical-pack requests return their raw bytes, allowing the ordinary builder to emit authenticated raw
packs.  Those independent raw packs are then compressed once, concurrently, with the exact per-pack levels already
proved by the serial selected-policy reference.  The resulting EG08 archive must remain byte-for-byte and
SHA-256-identical to that serial reference before any timing receives credit.

No product selector, archive grammar, metadata, recovery copy, digest, locality rule, comparator or historical
floor is changed.  This is research evidence for a production single-pass scheduler, not release authorization.
"""

from contextlib import contextmanager
import json
from pathlib import Path
import time

from benchmarks import v030_federated_compact_framing_v8_direct as BASE
from benchmarks import v030_federated_embedded_fs_v7_effort_oracle as EG07_EFFORT
from benchmarks import v030_federated_selective_effort_oracle as EFFORT
from experiments import entropygraph_v025 as V25


@contextmanager
def _raw_final_build_patch():
    original = BASE._build_level1_eg07

    def build_raw_final(stage: Path, root: Path):
        """Build the identical EG07 graph while skipping only duplicated final-pack compression."""
        started = time.perf_counter()
        profile, _ = EG07_EFFORT._prepare(stage, root / "profile-stage")
        archive = root / "baseline.c25eg07"
        original_zc = V25.zc

        def raw_final(raw: bytes, requested: int = 19) -> bytes:
            requested = int(requested)
            if requested < 19:
                # Preserve every graph/search audition exactly at the current level-1 policy.
                return original_zc(raw, min(requested, 1))
            # Final physical packs are independently authenticated by raw SHA/CRC and will be compressed exactly
            # once by the proved selected-effort schedule below.
            return raw

        with BASE._eg07_effort_bindings():
            with EFFORT._engine(archive, profile, raw_final):
                V25.build()
        return archive, time.perf_counter() - started

    BASE._build_level1_eg07 = build_raw_final
    try:
        yield
    finally:
        BASE._build_level1_eg07 = original


def run(work_root: Path) -> dict:
    with _raw_final_build_patch():
        result = dict(BASE.run(work_root))
    result["schema"] = "cmpct-v030-eg08-direct-office-v3"
    result["schedule"] = "raw-final-build-plus-exact-parallel-selected-pack-compression"
    result["single_pass_boundary"] = {
        "graph_search_changed": False,
        "probe_compression_changed": False,
        "final_pack_compressed_once": True,
        "exact_serial_archive_identity_required": True,
    }
    result["claim_boundary"] = (
        "Research-only direct C25EG08 office single-pass scheduling evidence. The historical graph/search path and "
        "all probe compression remain unchanged; only duplicated level-1 compression of final physical packs is "
        "removed. Final packs are compressed once in parallel with the exact selected levels, and timing receives "
        "credit only after byte-for-byte/SHA identity with the ordinary serial selected-effort archive. Native/" 
        "Android parity, selector admission, all-15 external/generalization/runtime authorities and the strict "
        "release lock remain mandatory before promotion."
    )
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-v3-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-v3.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "minimum_modeled_effort": result["minimum_modeled_effort"],
        "measured_candidate": result["measured_candidate"],
        "single_pass_boundary": result["single_pass_boundary"],
        "measurement_gate": result["measurement_gate"],
    }, indent=2), flush=True)
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("single-pass C25EG08 office frontier failed")


if __name__ == "__main__":
    main()
