from __future__ import annotations

"""Prefetch only the existing-anchor compressed ranges predicted for one logical request.

Mission Lock / Referee
======================
The lazy anchor-interval source cut physical syscalls by 97.72% but falsified its own physical-byte
bound on 6/8 probes: crossing an anchor boundary caused the source to fetch the *whole next page
interval* even when the decoder needed only a few boundary bytes. It was also slower than 8-byte pread.
The earlier bulk-range referee already established a stronger fact: for a requested output page, existing
anchors + Huffman block state predict the complete compressed interval (including recursive dependency
pages) with 0--2 B overfetch on this frozen stream.

Hypothesis
----------
Planning those already-proven intervals from the logical request *before* decode, merging overlaps, and
preading exactly the merged ranges will preserve byte-exact output and logical payload accounting while
(a) requiring no fallback reads, (b) touching no more than actual logical payload + 2 B per requested
output page, and (c) materially reducing physical read calls versus the frozen 8-byte source.

Disproof
--------
Any mismatch, cache miss/fallback, uncovered logical payload range, excess physical bytes, or failure to
reduce syscalls falsifies the mechanism. Timing remains diagnostic; one hosted observation cannot grant a
speed claim.

No new persisted metadata is introduced. This remains a synthetic mechanism referee; Office must repeat
the proof under the exact v7 644-byte group+locator/root economics and <=8x product locality accounting.
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

SCHEMA = "cmpct-v030-r4-planned-anchor-pread-referee-v1"
PAGE = 4096


def _merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[list[int]] = []
    for a, b in sorted(ranges):
        if not out or a > out[-1][1]:
            out.append([a, b])
        else:
            out[-1][1] = max(out[-1][1], b)
    return [(a, b) for a, b in out]


class PlannedRangeSource:
    __slots__ = ("size", "ranges", "starts", "buffers", "calls", "fallbacks")

    def __init__(self, fd: int, size: int, ranges: list[tuple[int, int]]):
        self.size = size
        self.ranges = ranges
        self.starts = [a for a, _ in ranges]
        self.buffers = []
        self.calls = 0
        self.fallbacks = 0
        for a, b in ranges:
            data = os.pread(fd, b - a, a)
            if len(data) != b - a:
                raise RuntimeError("short pread")
            self.buffers.append(data)
            self.calls += 1

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
            raise RuntimeError(f"compressed byte {index} before planned ranges")
        a, b = self.ranges[slot]
        if not a <= index < b:
            self.fallbacks += 1
            raise RuntimeError(f"compressed byte {index} outside planned ranges")
        return self.buffers[slot][index - a]


def _timed(fn):
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    out = fn()
    return out, time.process_time() - cpu0, time.perf_counter() - wall0


def _plan(comp: bytes, anchors, blocks, start: int, end: int) -> tuple[list[tuple[int, int]], int]:
    if end <= start:
        return [], 0
    first = start // PAGE
    last = (end - 1) // PAGE
    pages = list(range(first, last + 1))
    ranges = [PREF._predict(comp, anchors, blocks, p) for p in pages]
    return _merge(ranges), len(pages)


def run() -> dict:
    raw, comp = SRC._stream()
    parsed = DEP.parse_tokens(comp)
    anchors, blocks, _ = COLD._build_metadata(parsed)
    starts = sorted(set([0, 1, 4095, 4096, max(0, len(raw)//3-37), len(raw)//2,
                         max(0, len(raw)-PAGE-17), max(0, len(raw)-PAGE)]))
    rows=[]; failures=0
    totals={"resident_cpu_s":0.0,"resident_wall_s":0.0,"pread8_cpu_s":0.0,"pread8_wall_s":0.0,
            "planned_cpu_s":0.0,"planned_wall_s":0.0,"pread8_calls":0,"planned_calls":0}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"payload.deflate"; path.write_bytes(comp); fd=os.open(path,os.O_RDONLY)
        try:
            for start in starts:
                end=min(len(raw),start+PAGE)
                def resident_decode():
                    r=COLD.ColdReader(comp,anchors,blocks,len(raw)); return r,r.read(start,end)
                (rr,rg),rcpu,rwall=_timed(resident_decode)

                src8=SRC.PreadByteSource(fd,len(comp))
                def p8_decode():
                    r=COLD.ColdReader(src8,anchors,blocks,len(raw)); return r,r.read(start,end)
                (r8,g8),p8cpu,p8wall=_timed(p8_decode)

                plan,page_count=_plan(comp,anchors,blocks,start,end)
                planned=PlannedRangeSource(fd,len(comp),plan)
                err=None
                try:
                    def planned_decode():
                        r=COLD.ColdReader(planned,anchors,blocks,len(raw)); return r,r.read(start,end)
                    (rp,gp),pcpu,pwall=_timed(planned_decode)
                except Exception as exc:
                    rp=None; gp=b""; pcpu=pwall=0.0; err=repr(exc)

                logical=r8.payload_bytes(); p8bytes=SRC._bytes(src8.ranges); planned_bytes=SRC._bytes(plan)
                exact=rg==g8==gp==raw[start:end]
                covered=rp is not None and SRC._covers(plan,rp.payload_ranges)
                logical_equal=rp is not None and rp.payload_bytes()==logical
                physical_bound=planned_bytes <= logical + 2*page_count
                call_reduction=planned.calls < src8.calls
                ok=(err is None and exact and covered and logical_equal and physical_bound and
                    planned.fallbacks==0 and call_reduction)
                if not ok: failures+=1
                for k,v in (("resident_cpu_s",rcpu),("resident_wall_s",rwall),("pread8_cpu_s",p8cpu),
                            ("pread8_wall_s",p8wall),("planned_cpu_s",pcpu),("planned_wall_s",pwall)):
                    totals[k]+=v
                totals["pread8_calls"]+=src8.calls; totals["planned_calls"]+=planned.calls
                rows.append({"start":start,"end":end,"requested_pages":page_count,"exact":exact,
                             "logical_payload_bytes":logical,"pread8_bytes":p8bytes,"planned_bytes":planned_bytes,
                             "pread8_calls":src8.calls,"planned_calls":planned.calls,"planned_ranges":plan,
                             "planned_fallbacks":planned.fallbacks,"planned_ranges_cover_logical":covered,
                             "logical_accounting_equal":logical_equal,"physical_bound_ok":physical_bound,
                             "call_reduction":call_reduction,"resident_wall_s":rwall,"pread8_wall_s":p8wall,
                             "planned_wall_s":pwall,"planned_error":err,"pass":ok})
        finally:
            os.close(fd)
    ratio=totals["planned_calls"]/max(totals["pread8_calls"],1)
    supported=failures==0
    return {"schema":SCHEMA,"source_commit":os.environ.get("EVIDENCE_HEAD"),
            "input":{"raw_bytes":len(raw),"compressed_bytes":len(comp),"anchors":len(anchors),"probes":len(rows)},
            "failures":failures,"rows":rows,
            "summary":{**totals,"planned_vs_pread8_call_ratio":ratio,
                       "planned_call_reduction_pct":(1-ratio)*100.0,
                       "planned_vs_pread8_wall_ratio":totals["planned_wall_s"]/max(totals["pread8_wall_s"],1e-12),
                       "planned_vs_resident_wall_ratio":totals["planned_wall_s"]/max(totals["resident_wall_s"],1e-12),
                       "max_planned_bytes":max(r["planned_bytes"] for r in rows),
                       "max_planned_calls":max(r["planned_calls"] for r in rows),
                       "max_pread8_calls":max(r["pread8_calls"] for r in rows),
                       "max_planned_fallbacks":max(r["planned_fallbacks"] for r in rows),
                       "max_overfetch_bytes":max(r["planned_bytes"]-r["logical_payload_bytes"] for r in rows)},
            "hypothesis":{"existing_anchors_support_request_planned_pread_without_new_metadata":supported},
            "contract":{"diagnostic_only":True,"release_credit":False,"no_new_persisted_metadata":True,
                        "coldreader_unchanged":True,"same_anchor_block_metadata":True,"no_refill_sweep":True,
                        "timing_is_diagnostic_not_acceptance":True,
                        "remaining_debt":"Office transfer on exact v7 644B group+locator/root budget; <=8x physical locality; archive-root auth/recovery; fresh-process RSS; native/platform parity"}}


def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-planned-anchor-pread.json")); a=p.parse_args()
    d=run(); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"input":d["input"],"failures":d["failures"],"summary":d["summary"],"hypothesis":d["hypothesis"]},sort_keys=True))

if __name__=="__main__": main()
