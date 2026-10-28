#!/usr/bin/env python3
"""J24G06c: deterministic cross-scanner-window same-inode footer refresh court.

This is science only. Uses the genuine installed candidate, unchanged released Reader
compiled from its immutable Git blob, and Builder-originated revision-24 archives.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import msgpack
from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, sha
from j24g04_false_footer_recovery_court import PAYLOAD, append_orphan_deltas, digest
from j24g06_bounded_footer_product_court import exact_historical_reader
from j24g06b_live_footer_mutation_court import read_case
from cmpct.reader import CMPCT as Candidate

MIB = 1 << 20
TOTALS = (2 * MIB, 3 * MIB)


def window_separated_archive(base: bytes, total: int) -> tuple[bytes, int, int]:
    """SHA-authentic orphan A->0 and B->A with a scanner boundary between them."""
    payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
    ftr_a = FTR.pack(FMAGIC, 1, 0, 0, 0, len(payload), len(payload), 0, sha(payload))
    a_pos = len(base) + len(payload)
    ftr_b = FTR.pack(FMAGIC, 1, 0, 0, 0, len(payload), len(payload), a_pos, sha(payload))
    padding_size = total - (len(base) + 2 * len(payload) + len(ftr_a) + len(ftr_b))
    assert padding_size > MIB and len(ftr_a) == FTR.size
    raw = base + payload + ftr_a + bytes(padding_size) + payload + ftr_b
    b_pos = total - FTR.size
    assert len(raw) == total
    assert a_pos < MIB
    assert b_pos >= (total - MIB)
    assert b_pos - a_pos > MIB
    assert FTR.unpack(raw[a_pos:a_pos + FTR.size])[-2] == 0
    assert FTR.unpack(raw[b_pos:b_pos + FTR.size])[-2] == a_pos
    return raw, a_pos, b_pos


def inspect_mutation(path: Path, base_footer: int, a_pos: int, raw: bytes) -> dict:
    current = path.read_bytes()
    assert len(current) == len(raw)
    assert current[:a_pos] == raw[:a_pos]
    assert current[a_pos + FTR.size:] == raw[a_pos + FTR.size:]
    header = FTR.unpack(current[a_pos:a_pos + FTR.size])
    old_header = FTR.unpack(raw[a_pos:a_pos + FTR.size])
    assert header[:-2] == old_header[:-2], (header, old_header)
    assert header[-2] == base_footer, (header, base_footer)
    assert header[-1] == old_header[-1], "signed payload hash changed"
    return {
        "before_sha256": digest(raw),
        "after_sha256": digest(current),
        "physical_bytes": len(raw),
        "reparented_prev": header[-2],
        "sha_payload_unchanged": header[-1] == old_header[-1],
    }


def main() -> None:
    artifacts = Path(os.environ.get("J24G06C_ARTIFACTS", "j24g06c-artifacts"))
    artifacts.mkdir(parents=True, exist_ok=True)
    Historical = exact_historical_reader()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g06c-") as temp:
        root = Path(temp)
        src = root / "source"
        src.mkdir()
        (src / "owner.bin").write_bytes(PAYLOAD)
        clean = root / "clean.cmpct"
        Builder(src).build(clean)
        base = clean.read_bytes()
        with Historical(clean) as reader:
            base_footer = reader.latest_footer_pos
            assert reader.read("owner.bin") == PAYLOAD

        # Retain original J24G06b compact-source result as a true control.
        # It is not rewritten to make the new hypothesis succeed.
        adjacent = append_orphan_deltas(base, 2)
        payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
        aa = len(base) + len(payload)
        bb = aa + FTR.size + len(payload)
        control = {
            "old": read_case(Historical, adjacent, base_footer, aa, bb, False, root, "adjacent-old-unmutated"),
            "candidate": read_case(Candidate, adjacent, base_footer, aa, bb, False, root, "adjacent-candidate-unmutated"),
            "historical_mutated": read_case(Historical, adjacent, base_footer, aa, bb, True, root, "adjacent-old-mutated"),
            "candidate_mutated": read_case(Candidate, adjacent, base_footer, aa, bb, True, root, "adjacent-candidate-mutated"),
        }
        assert control["old"]["selected_footer"] == control["candidate"]["selected_footer"] == base_footer

        cases = []
        for total in TOTALS:
            raw, a_pos, b_pos = window_separated_archive(base, total)
            label = str(total // MIB) + "mib"
            before_old = read_case(Historical, raw, base_footer, a_pos, b_pos, False, root, label + "-historical-control")
            before_new = read_case(Candidate, raw, base_footer, a_pos, b_pos, False, root, label + "-candidate-control")
            assert before_old["selected_footer"] == before_new["selected_footer"] == base_footer
            assert before_old["delta_depth"] == before_new["delta_depth"] == 0

            old = read_case(Historical, raw, base_footer, a_pos, b_pos, True, root, label + "-historical-mutation")
            new = read_case(Candidate, raw, base_footer, a_pos, b_pos, True, root, label + "-candidate-mutation")
            old_physical = inspect_mutation(root / (label + "-historical-mutation.cmpct"), base_footer, a_pos, raw)
            new_physical = inspect_mutation(root / (label + "-candidate-mutation.cmpct"), base_footer, a_pos, raw)
            assert old_physical == new_physical
            assert old["archive_sha256_after"] == new["archive_sha256_after"] == old_physical["after_sha256"]
            assert old["logical_sha256"] == new["logical_sha256"] == digest(PAYLOAD)
            # The preregistered discriminator: immutable source Readers must differ in
            # generation selection only if the historic buffered Reader really refreshes.
            verdict = (
                "GENERATION_SELECTION_DIVERGENCE"
                if old["selected_footer"] == a_pos and old["delta_depth"] == 1
                and new["selected_footer"] == base_footer and new["delta_depth"] == 0
                else "NONCONFIRMING"
            )
            cases.append({
                "total_bytes": total,
                "a_footer": a_pos,
                "b_footer": b_pos,
                "control_historical": before_old,
                "control_candidate": before_new,
                "mutated_historical": old,
                "mutated_candidate": new,
                "physical_mutation": old_physical,
                "verdict": verdict,
            })
        results = {
            "question": "J24G06c scanner-window buffered I/O confound and mutable-footer memo",
            "release_credit": 0,
            "product_source_changed": False,
            "original_git_reader": "e716233403dabd0966863c45635e18fa5ac6afb8",
            "candidate_git_reader": "bead2ea6a09a6daaadc3ec2389cfb8853e3dd172",
            "source_builder_sha256": digest(base),
            "logical_sha256": digest(PAYLOAD),
            "adjacent_control": control,
            "window_cases": cases,
            "decision": (
                "CROSS_WINDOW_TEMPORAL_DIVERGENCE_CONFIRMED"
                if all(c["verdict"] == "GENERATION_SELECTION_DIVERGENCE" for c in cases)
                else "MIXED_OR_NONCONFIRMING_KEEP_EVIDENCE"
            ),
        }
        (artifacts / "court.json").write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
        print("J24G06C_RECEIPT=" + json.dumps(results, sort_keys=True))
        print("J24G06C_DECISION=" + results["decision"])
        # An honest failing scientific hypothesis remains a documented failure,
        # not a lower acceptance bar or a false positive.
        assert results["decision"] == "CROSS_WINDOW_TEMPORAL_DIVERGENCE_CONFIRMED", results["decision"]


if __name__ == "__main__":
    main()
