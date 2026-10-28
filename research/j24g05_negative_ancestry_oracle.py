#!/usr/bin/env python3
"""J24G05 scientific oracle: reuse unchanged genuine Reader replay, memoize FAILED ancestor facts.

Does not modify shipping source. The wrapper runs only within a single synchronous test
Reader open and is discarded after the controlled experiment. Not a product patch.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import msgpack

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import FMAGIC, FTR, sha
from cmpct.transactions import append_rename

from j24g04_false_footer_recovery_court import (
    PAYLOAD, append_orphan_deltas, digest,
)

N_CASES = (32, 128, 256)
ROUNDS = 3


def flat_orphans(pristine: bytes, count: int) -> bytes:
    """SHA-valid no-op delta footers with no parent link, physical bytes matched."""
    raw = bytearray(pristine)
    payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
    for _ in range(count):
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC, 1, 0, 0, 0, len(payload), len(payload), 0, sha(payload)))
    return bytes(raw)


def actual_reader_open(path: Path, *, member: str, oracle: bool) -> dict:
    """Use authentic CMPCT._index_from_footer and authentic decoder for BOTH variants.

    In the oracle, record every original decoder position visited by the original
    index replay and cache all of them ONLY if the full index result was None.
    """
    decoder_positions = []
    invalid_positions = set()
    original_decoder = CMPCT._decode_generation_payload
    original_index = CMPCT._index_from_footer

    def counted_decoder(self, footer_pos):
        decoder_positions.append(footer_pos)
        return original_decoder(self, footer_pos)

    def cached_failed_index(self, footer_pos):
        if footer_pos in invalid_positions:
            return None
        visited = []

        def observed_decode(self, pos):
            visited.append(pos)
            return counted_decoder(self, pos)

        # Exact original replay; no duplicate algorithm or altered decoder semantics.
        with patch.object(CMPCT, "_decode_generation_payload", observed_decode):
            original_result = original_index(self, footer_pos)
        if original_result is None:
            invalid_positions.update(visited)
        return original_result

    a = time.perf_counter()
    b = time.process_time()
    with patch.object(CMPCT, "_decode_generation_payload", counted_decoder):
        if oracle:
            with patch.object(CMPCT, "_index_from_footer", cached_failed_index):
                with CMPCT(path) as ar:
                    assert ar.read(member) == PAYLOAD
                    assert ar.read_range(member, 0, 17) == PAYLOAD[:17]
                    assert ar.read_range(member, len(PAYLOAD)-7, 7) == PAYLOAD[-7:]
                    ar.verify()
                    selected_footer = ar.latest_footer_pos
                    depth = ar.delta_depth
        else:
            with CMPCT(path) as ar:
                assert ar.read(member) == PAYLOAD
                assert ar.read_range(member, 0, 17) == PAYLOAD[:17]
                assert ar.read_range(member, len(PAYLOAD)-7, 7) == PAYLOAD[-7:]
                ar.verify()
                selected_footer = ar.latest_footer_pos
                depth = ar.delta_depth
    return {
        "mode": "oracle" if oracle else "original",
        "decoder_calls": len(decoder_positions),
        "decoder_unique_positions": len(set(decoder_positions)),
        "negative_cache_positions": len(invalid_positions),
        "selected_footer_pos": selected_footer,
        "delta_depth": depth,
        "wall_s": time.perf_counter() - a,
        "cpu_s": time.process_time() - b,
        "logical_sha256": digest(PAYLOAD),
    }


def abba_court(path: Path, *, member: str, expected_footer: int, expected_depth: int,
               original_calls: int, oracle_calls: int) -> dict:
    original = []
    cached = []
    for repeat in range(ROUNDS):
        sequence = (False, True) if repeat % 2 == 0 else (True, False)
        for mode in sequence:
            row = actual_reader_open(path, member=member, oracle=mode)
            assert row["selected_footer_pos"] == expected_footer, (member, row)
            assert row["delta_depth"] == expected_depth, (member, row)
            assert row["logical_sha256"] == digest(PAYLOAD), (member, row)
            assert row["decoder_calls"] == (oracle_calls if mode else original_calls), row
            (cached if mode else original).append(row)
    original_median = statistics.median(x["wall_s"] for x in original)
    oracle_median = statistics.median(x["wall_s"] for x in cached)
    return {
        "original": original,
        "oracle": cached,
        "original_wall_median_s": original_median,
        "oracle_wall_median_s": oracle_median,
        "median_wall_ratio_original_over_oracle": original_median/oracle_median,
        "original_cpu_median_s": statistics.median(x["cpu_s"] for x in original),
        "oracle_cpu_median_s": statistics.median(x["cpu_s"] for x in cached),
    }


def main():
    out = Path(os.environ.get("J24G05_ARTIFACTS", "j24g05-artifacts"))
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g05-") as tmp:
        td = Path(tmp)
        source = td/"tree"
        source.mkdir()
        (source/"owner.bin").write_bytes(PAYLOAD)
        pristine = td/"baseline.cmpct"
        Builder(source).build(pristine)
        base = pristine.read_bytes()
        baseline_unrecorded = actual_reader_open(pristine, member="owner.bin", oracle=False)
        footer = baseline_unrecorded["selected_footer_pos"]
        assert footer > 0 and baseline_unrecorded["decoder_calls"] == 1

        control = abba_court(
            pristine, member="owner.bin", expected_footer=footer, expected_depth=0,
            original_calls=1, oracle_calls=1,
        )

        committed = td/"committed.cmpct"
        committed.write_bytes(base)
        append_rename(committed, "owner.bin", "renamed.bin")
        committed_head = actual_reader_open(committed, member="renamed.bin", oracle=False)
        assert committed_head["delta_depth"] == 1 and committed_head["selected_footer_pos"] > footer
        valid_control = abba_court(
            committed, member="renamed.bin",
            expected_footer=committed_head["selected_footer_pos"],
            expected_depth=1, original_calls=2, oracle_calls=2,
        )

        results = []
        for n in N_CASES:
            nested_bytes = append_orphan_deltas(base, n)
            flat_bytes = flat_orphans(base, n)
            assert len(nested_bytes) == len(flat_bytes) == len(base) + n*81
            nested = td/f"linked-invalid-{n}.cmpct"
            flat = td/f"flat-invalid-{n}.cmpct"
            nested.write_bytes(nested_bytes)
            flat.write_bytes(flat_bytes)
            # All source-open semantics and all original oracle counts are pinned.
            nested_court = abba_court(
                nested, member="owner.bin", expected_footer=footer, expected_depth=0,
                original_calls=1+n*(n+1)//2, oracle_calls=1+n,
            )
            flat_court = abba_court(
                flat, member="owner.bin", expected_footer=footer, expected_depth=0,
                original_calls=1+n, oracle_calls=1+n,
            )
            results.append({
                "n":n,
                "physical_bytes":len(nested_bytes),
                "same_full_physical_bytes": len(nested_bytes)==len(flat_bytes),
                "nested_sha256":digest(nested_bytes),
                "flat_sha256":digest(flat_bytes),
                "nested":nested_court,
                "flat":flat_court,
            })

        final = results[-1]["nested"]
        assert final["median_wall_ratio_original_over_oracle"] >= 2.0, (
            "Prospective 2x oracle headroom absent", final["median_wall_ratio_original_over_oracle"]
        )
        result = {
            "question":"J24G05-bounded-orphan-failure-ancestry-science-oracle",
            "status":"FAILED_ANCESTRY_MEMOIZATION_ORACLE_PASSED_WITHIN_SCOPED_INPUTS",
            "published_reader_unmodified":True,
            "product_release_credit":0,
            "hypothesis_owner":"draft-only scientific runtime wrapper",
            "source_primary_archive_sha256":digest(base),
            "source_primary_bytes":len(base),
            "logical_sha256":digest(PAYLOAD),
            "original_builder_footer_pos":footer,
            "comparison_rounds":ROUNDS,
            "valid_baseline":control,
            "valid_committed_rename":valid_control,
            "orphaned_cases":results,
        }
        (out/"oracle.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("J24G05_SOURCE_EXACT_ORACLE="+json.dumps(result,sort_keys=True))
        print("J24G05_DECISION=FAILED_ANCESTRY_MEMOIZATION_ORACLE_PASSED_WITHIN_SCOPED_INPUTS")

if __name__=="__main__":
    main()
