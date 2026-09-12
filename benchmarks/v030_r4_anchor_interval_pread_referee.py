from __future__ import annotations

"""Use existing sparse anchors as the refill geometry for direct physical reads.

Mission Lock / Referee
======================
The direct-pread referee proved that the unchanged sparse DEFLATE reader can decode byte-exactly from
physical ``os.pread`` I/O, but its fixed 8-byte refill policy paid thousands of syscalls. The separate
anchor-bulk referee proved that already-persisted page anchors + Huffman block state delimit every
compressed interval consumed by the unchanged reader with essentially zero overfetch on the frozen
mixed literal/copy stream.

Hypothesis
----------
Replacing only the physical byte-source refill policy with those pre-existing anchor intervals will
preserve exact output and logical payload accounting while reducing physical read calls materially
versus the frozen 8-byte source, without adding persisted metadata or reading the whole payload eagerly.

Disproof
--------
Any byte mismatch, uncovered byte that requires a fallback read, logical-range coverage failure,
physical-byte accounting failure, or non-reduction in total pread calls falsifies the mechanism.
Timing is diagnostic: a noisy single hosted run cannot by itself grant a speed win.

This is a mechanism referee, not Office/release authority. Office transfer must independently charge
its exact group/locator/root/auth bytes and <=8x locality budget.
"""

import argparse
import bisect
import json
import os
import tempfile
import time
from pathlib import Path

from benchmarks import v030_r4_anchor_bulk_prefetch_referee as PREF
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_pread_bit_source_referee as SRC

SCHEMA = "cmpct-v030-r4-anchor-interval-pread-referee-v1"
PAGE = 4096


class AnchorIntervalSource:
    """Lazy physical source: one cached pread per anchor interval actually touched."""

    __slots__ = ("fd", "size", "intervals", "starts", "cache", "ranges", "calls", "fallbacks")

    def __init__(self, fd: int, size: int, intervals: list[tuple[int, int]]):
        self.fd = fd
        self.size = size
        self.intervals = intervals
        self.starts = [a for a, _ in intervals]
        self.cache: dict[int, bytes] = {}
        self.ranges: list[tuple[int, int]] = []
        self.calls = 0
        self.fallbacks = 0

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, index: int) -> int:
        if index < 0:
            index += self.size
        if not 0 <= index < self.size:
            raise IndexError(index)
        slot = bisect.bisect_right(self.starts, index) - 1
        if slot < 0:
            self.fallbacks += 1
            raise RuntimeError(f"compressed byte {index} precedes first anchor interval")
        a, b = self.intervals[slot]
        if not a <= index < b:
            self.fallbacks += 1
            raise RuntimeError(f"compressed byte {index} is outside anchor intervals")
        data = self.cache.get(slot)
        if data is None:
            data = os.pread(self.fd, b - a, a)
            if len(data) != b - a:
                raise RuntimeError("short pread")
            self.cache[slot] = data
            self.ranges.append((a, b))
            self.calls += 1
        return data[index - a]


def _timed(fn):
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    out = fn()
    return out, time.process_time() - cpu0, time.perf_counter() - wall0


def run() -> dict:
    raw, comp = SRC._stream()
    parsed = DEP.parse_tokens(comp)
    anchors, blocks, _ = COLD._build_metadata(parsed)
    intervals = [PREF._predict(comp, anchors, blocks, p) for p in range(len(anchors))]
    starts = sorted(
        set(
            [
                0,
                1,
                4095,
                4096,
                max(0, len(raw) // 3 - 37),
                len(raw) // 2,
                max(0, len(raw) - PAGE - 17),
                max(0, len(raw) - PAGE),
            ]
        )
    )
    rows = []
    failures = 0
    totals = {
        "resident_cpu_s": 0.0,
        "resident_wall_s": 0.0,
        "pread8_cpu_s": 0.0,
        "pread8_wall_s": 0.0,
        "bulk_cpu_s": 0.0,
        "bulk_wall_s": 0.0,
        "pread8_calls": 0,
        "bulk_calls": 0,
    }
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "payload.deflate"
        path.write_bytes(comp)
        fd = os.open(path, os.O_RDONLY)
        try:
            for start in starts:
                end = min(len(raw), start + PAGE)

                def resident_decode():
                    r = COLD.ColdReader(comp, anchors, blocks, len(raw))
                    return r, r.read(start, end)

                (resident_reader, resident_got), rcpu, rwall = _timed(resident_decode)

                src8 = SRC.PreadByteSource(fd, len(comp))

                def pread8_decode():
                    r = COLD.ColdReader(src8, anchors, blocks, len(raw))
                    return r, r.read(start, end)

                (reader8, got8), p8cpu, p8wall = _timed(pread8_decode)

                bulk = AnchorIntervalSource(fd, len(comp), intervals)
                bulk_error = None
                try:
                    def bulk_decode():
                        r = COLD.ColdReader(bulk, anchors, blocks, len(raw))
                        return r, r.read(start, end)

                    (bulk_reader, bulk_got), bcpu, bwall = _timed(bulk_decode)
                except Exception as exc:  # receipt owns the failure rather than hiding it in CI.
                    bulk_reader = None
                    bulk_got = b""
                    bcpu = bwall = 0.0
                    bulk_error = repr(exc)

                logical = reader8.payload_bytes()
                pread8_bytes = SRC._bytes(src8.ranges)
                bulk_bytes = SRC._bytes(bulk.ranges)
                exact = resident_got == got8 == bulk_got == raw[start:end]
                covered = bulk_reader is not None and SRC._covers(bulk.ranges, bulk_reader.payload_ranges)
                logical_equal = bulk_reader is not None and bulk_reader.payload_bytes() == logical
                physical_bound = bulk_bytes <= logical + max(0, bulk.calls) * 8
                call_reduction = bulk.calls < src8.calls
                ok = (
                    bulk_error is None
                    and exact
                    and covered
                    and logical_equal
                    and physical_bound
                    and bulk.fallbacks == 0
                    and call_reduction
                )
                if not ok:
                    failures += 1

                for key, value in (
                    ("resident_cpu_s", rcpu),
                    ("resident_wall_s", rwall),
                    ("pread8_cpu_s", p8cpu),
                    ("pread8_wall_s", p8wall),
                    ("bulk_cpu_s", bcpu),
                    ("bulk_wall_s", bwall),
                ):
                    totals[key] += value
                totals["pread8_calls"] += src8.calls
                totals["bulk_calls"] += bulk.calls

                rows.append(
                    {
                        "start": start,
                        "end": end,
                        "exact": exact,
                        "logical_payload_bytes": logical,
                        "pread8_bytes": pread8_bytes,
                        "bulk_bytes": bulk_bytes,
                        "pread8_calls": src8.calls,
                        "bulk_calls": bulk.calls,
                        "bulk_fallbacks": bulk.fallbacks,
                        "bulk_ranges_cover_logical": covered,
                        "logical_accounting_equal": logical_equal,
                        "physical_bound_ok": physical_bound,
                        "call_reduction": call_reduction,
                        "resident_wall_s": rwall,
                        "pread8_wall_s": p8wall,
                        "bulk_wall_s": bwall,
                        "bulk_error": bulk_error,
                        "pass": ok,
                    }
                )
        finally:
            os.close(fd)

    supported = failures == 0
    call_ratio = totals["bulk_calls"] / max(totals["pread8_calls"], 1)
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "input": {
            "raw_bytes": len(raw),
            "compressed_bytes": len(comp),
            "anchors": len(anchors),
            "probes": len(rows),
        },
        "failures": failures,
        "rows": rows,
        "summary": {
            **totals,
            "bulk_vs_pread8_call_ratio": call_ratio,
            "bulk_call_reduction_pct": (1.0 - call_ratio) * 100.0,
            "bulk_vs_pread8_wall_ratio": totals["bulk_wall_s"] / max(totals["pread8_wall_s"], 1e-12),
            "bulk_vs_resident_wall_ratio": totals["bulk_wall_s"] / max(totals["resident_wall_s"], 1e-12),
            "max_bulk_bytes": max(r["bulk_bytes"] for r in rows),
            "max_bulk_calls": max(r["bulk_calls"] for r in rows),
            "max_pread8_calls": max(r["pread8_calls"] for r in rows),
            "max_bulk_fallbacks": max(r["bulk_fallbacks"] for r in rows),
        },
        "hypothesis": {
            "existing_anchors_support_lazy_bulk_pread_without_new_metadata": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "no_new_persisted_metadata": True,
            "coldreader_unchanged": True,
            "same_anchor_block_metadata": True,
            "no_refill_sweep": True,
            "timing_is_diagnostic_not_acceptance": True,
            "remaining_debt": "Office transfer on the exact v7 644B group+locator/root budget; <=8x physical locality; auth/recovery; fresh-process RSS; native/platform parity",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r4-anchor-interval-pread.json"),
    )
    args = parser.parse_args()
    data = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "input": data["input"],
                "failures": data["failures"],
                "summary": data["summary"],
                "hypothesis": data["hypothesis"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
