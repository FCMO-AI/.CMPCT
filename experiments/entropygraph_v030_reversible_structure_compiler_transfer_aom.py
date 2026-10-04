"""F-01 structural transfer + initial AOM/carrying-cost oracle.

Research-only. The O0.1 grammar/serialization remains unchanged. This instrument generates post-causal-freeze
structural variations, prices the exact full grammar, then A/Bs the causally scoped lane-width pruning {2,4}.
Search wall time is gifted; all selected program bytes and exact reconstruction remain fully charged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from experiments import entropygraph_v030_reversible_structure_compiler_o01 as O

SCHEMA = "cmpct-v030-foundry-f01-transfer-aom-v1"
CAUSAL_SOURCE = "2876698d311b13f296a6f11f23d89eaab51cd09c"
CAUSAL_ARTIFACT_DIGEST = "sha256:e910165ad51b2501f44a8531dab39ccbd697a1a1b150f9d958fb03290d33f2b6"


def _lane_region(size: int, width: int, salt: int, noise_stride: int = 0) -> bytes:
    if size % width:
        raise ValueError("lane transfer region must align to width")
    out = bytearray(size)
    rows = size // width
    pos = 0
    for row in range(rows):
        phase = (row >> 5) & 7
        for col in range(width):
            out[pos] = ((row // (11 + col % 4)) + col * 37 + phase * (col + 3) + salt) & 0xFF
            pos += 1
    if noise_stride:
        for i in range(noise_stride // 2, size, noise_stride):
            out[i] ^= ((i // max(1, noise_stride)) * 29 + salt) & 0xFF
    return bytes(out)


def _record_region(size: int, sep: int, salt: int, noise_stride: int = 0) -> bytes:
    out = bytearray()
    row = 0
    while len(out) < size:
        # Generator-distinct from the frozen O0.1 record helper: mixed binary/ascii fields,
        # variable record lengths and slowly moving grouped values.
        rec = (
            f"k{(row + salt) % 97:02d}|g{(row // 13 + salt) % 211:03d}|"
            f"v{(row * 17 + salt * 5) % 100003:05d}|p{(row // 7) % 41:02d}"
        ).encode("ascii")
        out.extend(rec)
        out.append(sep)
        row += 1
    raw = bytearray(out[:size])
    if noise_stride:
        for i in range(noise_stride // 3, len(raw), noise_stride):
            if raw[i] != sep:
                raw[i] ^= ((i // max(1, noise_stride)) * 11 + salt) & 0x0F
    return bytes(raw)


def _false_delimiter(size: int, sep: int, salt: int) -> bytes:
    raw = bytearray(hashlib.shake_256(f"f01-false-delim-{salt}".encode()).digest(size))
    for i in range(31, size, 37):
        raw[i] = sep
    return bytes(raw)


def _cases() -> list[dict]:
    kib = 1024
    cases: list[dict] = []

    def add(name: str, family: str, positive: bool, raw: bytes, *, scale_kib: int, variant: str, aligned: bool) -> None:
        cases.append({
            "name": name,
            "family": family,
            "positive": positive,
            "scale_kib": scale_kib,
            "variant": variant,
            "aligned_boundary": aligned,
            "raw": raw,
        })

    add("tr_lr_32_a", "lane+record", True,
        _lane_region(16*kib, 8, 19) + _record_region(16*kib, 0x1E, 31),
        scale_kib=32, variant="lane8-record-clean", aligned=True)
    add("tr_lr_64_b", "lane+record", True,
        _lane_region(24*kib, 16, 43) + _record_region(40*kib, 0x1F, 47),
        scale_kib=64, variant="lane16-record-unequal", aligned=True)
    add("tr_lr_128_n", "lane+record", True,
        _lane_region(64*kib, 8, 59, 997) + _record_region(64*kib, 0x1D, 61, 1201),
        scale_kib=128, variant="lane8-record-noisy", aligned=True)

    add("tr_ll_64_ab", "lane+lane", True,
        _lane_region(24*kib, 8, 71) + _lane_region(40*kib, 16, 73),
        scale_kib=64, variant="8-to-16", aligned=True)
    add("tr_ll_96_ba", "lane+lane", True,
        _lane_region(48*kib, 16, 79, 1151) + _lane_region(48*kib, 8, 83, 887),
        scale_kib=96, variant="16-to-8-noisy", aligned=True)
    add("tr_ll_128_u", "lane+lane", True,
        _lane_region(32*kib, 8, 89) + _lane_region(96*kib, 16, 97, 1531),
        scale_kib=128, variant="8-to-16-unequal", aligned=True)

    add("hn_random_64", "hostile-random", False,
        hashlib.shake_256(b"f01-transfer-random-64").digest(64*kib),
        scale_kib=64, variant="random", aligned=False)
    add("hn_false_delim_64", "hostile-false-delimiter", False,
        _false_delimiter(64*kib, 0x1E, 101),
        scale_kib=64, variant="false-delimiter", aligned=False)
    add("hn_single_lane_64", "hostile-single-lane", False,
        _lane_region(64*kib, 8, 103),
        scale_kib=64, variant="single-lane", aligned=False)
    # Deliberately off the frozen 4 KiB split grid: reach-limit evidence, not a reason to move the grid post-result.
    add("hn_offgrid_lr_64", "hostile-offgrid-positive-structure", False,
        _lane_region(18*kib, 8, 107) + _record_region(46*kib, 0x1C, 109),
        scale_kib=64, variant="offgrid-lane-record", aligned=False)
    return cases


def _fingerprint(cases: list[dict]) -> str:
    manifest = [
        {
            "name": c["name"], "family": c["family"], "positive": c["positive"],
            "bytes": len(c["raw"]), "sha256": hashlib.sha256(c["raw"]).hexdigest(),
            "scale_kib": c["scale_kib"], "variant": c["variant"], "aligned_boundary": c["aligned_boundary"],
        }
        for c in cases
    ]
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _search_with_widths(raw: bytes, widths: tuple[int, ...]) -> dict:
    original = O.L.LANE_WIDTHS
    O.L.LANE_WIDTHS = widths
    try:
        return O.search(raw)
    finally:
        O.L.LANE_WIDTHS = original


def run(source_commit: str) -> dict:
    cases = _cases()
    fp = _fingerprint(cases)
    rows = []
    full_generated = full_costed = full_prunes = 0
    pruned_generated = pruned_costed = pruned_prunes = 0
    positive_bytes = material_positive_bytes = hostile_material_bytes = 0
    material_manual_bytes = material_saving_bytes = 0
    positive_winners: list[dict] = []
    hostile_winners: list[dict] = []
    pruning_preserves_all = True

    for c in cases:
        raw = c["raw"]
        full = _search_with_widths(raw, (2, 4, 8, 16))
        pruned = _search_with_widths(raw, (8, 16))
        if not full["exact_reconstruction"] or not pruned["exact_reconstruction"]:
            raise RuntimeError("F-01 transfer lost exact reconstruction")
        same_optimum = (
            full["synthesized_bytes"] == pruned["synthesized_bytes"]
            and full["synthesized_motif"] == pruned["synthesized_motif"]
        )
        pruning_preserves_all = pruning_preserves_all and same_optimum
        material = bool(full["material_composed_win"])
        full_generated += int(full["search"]["generated"])
        full_costed += int(full["search"]["costed"])
        full_prunes += int(full["search"]["exact_bound_prunes"])
        pruned_generated += int(pruned["search"]["generated"])
        pruned_costed += int(pruned["search"]["costed"])
        pruned_prunes += int(pruned["search"]["exact_bound_prunes"])
        if c["positive"]:
            positive_bytes += len(raw)
            if material:
                material_positive_bytes += len(raw)
                material_manual_bytes += int(full["manual_bytes"])
                material_saving_bytes += int(full["saving_vs_manual_bytes"])
                positive_winners.append(c)
        elif material:
            hostile_material_bytes += len(raw)
            hostile_winners.append(c)
        rows.append({
            **{k: v for k, v in c.items() if k != "raw"},
            "sha256": hashlib.sha256(raw).hexdigest(),
            "logical_bytes": len(raw),
            "manual_bytes": full["manual_bytes"],
            "synthesized_bytes": full["synthesized_bytes"],
            "synthesized_motif": full["synthesized_motif"],
            "saving_vs_manual_bytes": full["saving_vs_manual_bytes"],
            "saving_vs_manual_ratio": full["saving_vs_manual_ratio"],
            "material_transfer_win": material,
            "full_search": full["search"],
            "pruned_bytes": pruned["synthesized_bytes"],
            "pruned_motif": pruned["synthesized_motif"],
            "pruned_search": pruned["search"],
            "pruning_preserves_exact_optimum": same_optimum,
        })

    addressable_fraction = material_positive_bytes / positive_bytes if positive_bytes else 0.0
    conditional_saving_fraction = material_saving_bytes / material_manual_bytes if material_manual_bytes else 0.0
    families = {c["family"] for c in positive_winners}
    scales = {c["scale_kib"] for c in positive_winners}
    variants = {c["variant"] for c in positive_winners}
    pruning_reduces = pruned_generated < full_generated and pruned_costed < full_costed

    if hostile_winners or not positive_winners:
        decision = "TRANSFER_FAIL"
    elif (
        len(positive_winners) >= 4
        and {"lane+record", "lane+lane"}.issubset(families)
        and len(scales) >= 2
        and len(variants) >= 2
        and addressable_fraction >= 0.25
        and conditional_saving_fraction >= 0.02
        and pruning_preserves_all
        and pruning_reduces
    ):
        decision = "TRANSFER_ADVANCE"
    else:
        decision = "TRANSFER_NARROW"

    return {
        "schema": SCHEMA,
        "source_commit": source_commit,
        "causal_source": CAUSAL_SOURCE,
        "causal_artifact_digest": CAUSAL_ARTIFACT_DIGEST,
        "corpus_fingerprint": fp,
        "decision": decision,
        "cases": rows,
        "aom": {
            "confidence": "low-synthetic-transfer-corpus",
            "positive_structural_logical_bytes": positive_bytes,
            "material_winner_logical_bytes": material_positive_bytes,
            "addressable_byte_fraction": addressable_fraction,
            "material_winner_manual_bytes": material_manual_bytes,
            "material_saving_bytes": material_saving_bytes,
            "conditional_saving_fraction": conditional_saving_fraction,
            "addressable_gain_bytes": material_positive_bytes * conditional_saving_fraction,
            "hostile_material_false_win_count": len(hostile_winners),
            "hostile_material_false_win_bytes": hostile_material_bytes,
            "corpus_bias": "deterministic post-freeze synthetic structures; independent/public real-data AOM remains deferred",
        },
        "carrying_cost": {
            "full_lane_widths": [2, 4, 8, 16],
            "pruned_lane_widths": [8, 16],
            "full_generated_states": full_generated,
            "full_costed_states": full_costed,
            "full_exact_bound_prunes": full_prunes,
            "pruned_generated_states": pruned_generated,
            "pruned_costed_states": pruned_costed,
            "pruned_exact_bound_prunes": pruned_prunes,
            "pruning_preserves_every_exact_optimum": pruning_preserves_all,
            "pruning_reduces_generated_and_costed_states": pruning_reduces,
            "full_nominations_per_logical_mib": full_generated / (sum(len(c["raw"]) for c in cases) / (1024*1024)),
            "pruned_nominations_per_logical_mib": pruned_generated / (sum(len(c["raw"]) for c in cases) / (1024*1024)),
        },
        "transfer": {
            "positive_material_win_count": len(positive_winners),
            "winning_families": sorted(families),
            "winning_scales_kib": sorted(scales),
            "winning_variants": sorted(variants),
        },
        "oracle_gift_ledger": {
            "gifted": ["search/discovery wall time"],
            "never_gifted": ["program/control/terminal bytes", "exact reconstruction", "structural AOM labels"],
            "deferred": [
                "independent/public real-data AOM", "generic admission economics", "canonical framing/index",
                "locality/recovery/integrity", "native/platform", "product runtime", "full release matrix",
            ],
        },
        "strongest_surviving_objection": (
            "A synthetic transfer advance can still indicate only a compact mixed-region primitive; it does not justify "
            "shipping the research compiler or its search grammar."
        ),
        "next_decisive_test": (
            "If TRANSFER_ADVANCE, perform independent/public real-data AOM plus a cheap necessary-condition admission study "
            "before HANDOFF_READY; otherwise narrow/retire without adding operators."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-commit", default=os.environ.get("EVIDENCE_HEAD", ""))
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if not args.source_commit or len(args.source_commit) < 12:
        raise SystemExit("F-01 transfer/AOM requires exact source commit")
    result = run(args.source_commit)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
