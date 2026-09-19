from __future__ import annotations

"""Mechanism referee: remove redundant canonical-uvarint re-encoding from streaming LOC1 parse.

The streaming parser cut near-ceiling fresh-process RSS materially but its validation CPU was ~2.2x the
legacy table parser. v4 proves uvarint canonicity by slicing the original bytes and allocating a freshly
re-encoded copy for every integer. For unsigned LEB128 under the same 10-byte decoder, the equivalent
local rule is: a multi-byte integer is non-canonical iff its final 7-bit payload is zero.

Hypothesis: the direct rule is decision-equivalent to the reference on deterministic boundary/canonical/
overlong controls, preserves exact record count on the same 899,982 B locator, retains the streaming RSS
advantage, and reduces fresh-process parse CPU versus v4 streaming. No archive bytes or locality budget move.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4

SCHEMA = "cmpct-v030-r4-compact-locator-parser-resource-v2"
TARGET_RAW_BYTES = 900_000


def _read_canonical_uvarint_fast(buf: bytes, off: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for i in range(10):
        if off >= len(buf):
            raise ValueError("truncated uvarint")
        b = buf[off]
        off += 1
        payload = b & 0x7F
        value |= payload << shift
        if not (b & 0x80):
            if i and payload == 0:
                raise ValueError("non-canonical locator uvarint")
            return value, off
        shift += 7
    raise ValueError("overlong uvarint")


def _semantic_controls() -> dict:
    vals = [0,1,2,126,127,128,129,255,256,16383,16384,(1<<21)-1,1<<21,(1<<35)+17,(1<<63)-1,(1<<69)-1]
    canonical_ok = True
    for value in vals:
        enc = DEP.uvarint(value)
        ref = V4._read_canonical_uvarint(enc, 0)
        fast = _read_canonical_uvarint_fast(enc, 0)
        canonical_ok &= ref == fast == (value, len(enc))
    # Add a zero high group to valid one- through nine-byte spellings; semantics stay the same but bytes are overlong.
    overlong_ok = True
    for value in vals:
        enc = DEP.uvarint(value)
        if len(enc) >= 10:
            continue
        bad = enc[:-1] + bytes([enc[-1] | 0x80, 0])
        ref_reject = fast_reject = False
        try: V4._read_canonical_uvarint(bad, 0)
        except ValueError: ref_reject = True
        try: _read_canonical_uvarint_fast(bad, 0)
        except ValueError: fast_reject = True
        overlong_ok &= ref_reject and fast_reject
    return {"canonical_boundaries_match":canonical_ok,"overlong_controls_match":overlong_ok}


def worker(mode: str, raw_path: Path) -> dict:
    raw=raw_path.read_bytes()
    original=V4._read_canonical_uvarint
    if mode == "fast": V4._read_canonical_uvarint=_read_canonical_uvarint_fast
    elif mode != "reference": raise ValueError(mode)
    cpu0=time.process_time(); wall0=time.perf_counter()
    try:
        view=V4._parse_locator_streaming(raw)
    finally:
        V4._read_canonical_uvarint=original
    return {"mode":mode,"raw_bytes":len(raw),"records":int(view.record_count),
            "parse_cpu_s":time.process_time()-cpu0,"parse_wall_s":time.perf_counter()-wall0,
            "peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}


def _fresh(mode: str, raw_path: Path) -> dict:
    cp=subprocess.run([sys.executable,__file__,"--worker-mode",mode,"--raw",str(raw_path)],check=True,capture_output=True,text=True)
    return json.loads(cp.stdout.strip().splitlines()[-1])


def run(work: Path) -> dict:
    work.mkdir(parents=True,exist_ok=True)
    raw=V4._large_valid_locator(TARGET_RAW_BYTES); raw_path=work/'near-ceiling.loc1'; raw_path.write_bytes(raw)
    controls=_semantic_controls(); ref=_fresh('reference',raw_path); fast=_fresh('fast',raw_path)
    same=ref['raw_bytes']==fast['raw_bytes']==len(raw) and ref['records']==fast['records']
    return {"schema":SCHEMA,"source_commit":os.environ.get('EVIDENCE_HEAD'),"input":{"raw_bytes":len(raw),"records":ref['records']},
            "controls":controls,"reference_streaming":ref,"fast_streaming":fast,
            "comparison":{"same_input_and_cardinality":same,
                          "cpu_saved_s":ref['parse_cpu_s']-fast['parse_cpu_s'],
                          "cpu_ratio_fast_over_reference":fast['parse_cpu_s']/ref['parse_cpu_s'],
                          "wall_ratio_fast_over_reference":fast['parse_wall_s']/ref['parse_wall_s'],
                          "rss_delta_kib_fast_minus_reference":fast['peak_rss_kib']-ref['peak_rss_kib']},
            "hypothesis":{"direct_canonical_rule_preserves_decisions_and_reduces_cpu":same and all(controls.values()) and fast['parse_cpu_s'] < ref['parse_cpu_s']},
            "contract":{"diagnostic_only":True,"release_credit":False,"representation_unchanged":True,"fresh_process_per_contender":True}}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--worker-mode',choices=['reference','fast']); p.add_argument('--raw',type=Path)
    p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-locator-parser-resource-v2-work'))
    p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-locator-parser-resource-v2.json')); a=p.parse_args()
    if a.worker_mode:
        print(json.dumps(worker(a.worker_mode,a.raw),sort_keys=True)); return
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n'); print(json.dumps(d,sort_keys=True))

if __name__=='__main__': main()
