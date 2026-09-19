from __future__ import annotations

"""Research-only exact fast-path oracle for G04 delimiter inversion.

The runtime attribution chain localized the ML G04 regression to one delimiter-transformed physical record.
This oracle extracts that exact stored record from one shipping archive, reconstructs its transformed physical
bytes with the unchanged shipping codec, and compares the current inverse against a block/strided-slice inverse.
The candidate preserves the grammar and resource checks and receives zero product/release credit until promoted
and re-measured through the real product.
"""

import argparse
import binascii
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from benchmarks import v030_release_performance as PERF

ENGINE = "v030-g04-delimiter-inverse-oracle-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPS = 15


def _json_child(cmd: list[str]) -> dict:
    env = dict(os.environ); env["PYTHONHASHSEED"] = "0"
    p = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"child failed {p.returncode}: {p.stderr}\n{p.stdout}")
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])


def candidate_inverse(O, encoded: bytes, logical_size: int) -> bytes:
    if not encoded.startswith(b"DGO1") or len(encoded) < 6 or logical_size < 0 or logical_size > O.MAX_OVERLAY_RECORD:
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")
    lengths: list[int] = []
    logical_members = 0
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length); logical_members += length
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    if count * max(lengths, default=0) > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    rows = [bytearray(length) for length in lengths]
    active = [index for index, length in enumerate(lengths) if length]
    cursor = 0
    previous = 0
    for boundary in sorted({length for length in lengths if length}):
        span = boundary - previous
        width = len(active)
        if span <= 0 or width <= 0:
            raise RuntimeError("Geometry overlay delimiter block shape")
        block_bytes = span * width
        end = cursor + block_bytes
        if end > len(body):
            raise RuntimeError("Geometry overlay delimiter short body")
        block = body[cursor:end]
        for rank, index in enumerate(active):
            rows[index][previous:boundary] = block[rank:block_bytes:width]
        cursor = end
        previous = boundary
        active = [index for index in active if lengths[index] > boundary]
    if cursor != len(body) or active:
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return bytes((delimiter,)).join(bytes(row) for row in rows)


def run(work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as CANON
    R = CANON.POLICY.R; O = R.G04.O
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora"); source = roots[(SUITE, TARGET)]
    archive = work_root / "v030.cmpct"
    pack = _json_child([sys.executable, str(PERF.WORKER), "--engine", "v030", "--op", "pack", "--source", str(source), "--archive", str(archive)])
    if pack.get("build_stats", {}).get("selected") != "g04-overlay":
        raise RuntimeError("ML target no longer selects g04-overlay")

    with CANON.C._revision25_profile_context():
        session = R._G04Session(archive)
        try:
            ids = [i for i, transform in enumerate(session.transforms) if transform and transform[0] == "delimiter"]
            if len(ids) != 1:
                raise RuntimeError(f"expected exactly one delimiter record, got {ids}")
            rid = ids[0]; rel = session.offsets[rid]
            session.stream.seek(session.record_start + rel)
            header = session.stream.read(R.PH.size)
            codec, usize, csize, crc, expected_sha = R.PH.unpack(header)
            payload = session.stream.read(csize)
            if R.H(payload) != session.leaves[rid]:
                raise RuntimeError("payload authentication drift")
            if codec != R.G04.O.CODEC_ZSTD:
                raise RuntimeError(f"delimiter record codec drift: {codec}")
            encoded = R.G04.O.zd(payload, usize)
            descriptor = session.transforms[rid]
            logical_size = int(descriptor[2])
        finally:
            session.close()

    baseline = O.delimiter_inverse(encoded, logical_size)
    candidate = candidate_inverse(O, encoded, logical_size)
    if candidate != baseline:
        raise RuntimeError("candidate inverse byte mismatch")
    if (binascii.crc32(candidate) & 0xFFFFFFFF) != crc or R.H(candidate) != expected_sha:
        raise RuntimeError("candidate inverse integrity mismatch")

    def bench(fn):
        times=[]
        for _ in range(REPS):
            t=time.perf_counter(); got=fn(); times.append(time.perf_counter()-t)
            if got != baseline: raise RuntimeError("timed inverse mismatch")
        return times
    # Alternate order to reduce thermal/order bias.
    current_times=[]; candidate_times=[]
    for rep in range(REPS):
        order=(("current", lambda: O.delimiter_inverse(encoded, logical_size)), ("candidate", lambda: candidate_inverse(O, encoded, logical_size)))
        if rep % 2: order=tuple(reversed(order))
        for name, fn in order:
            t=time.perf_counter(); got=fn(); dt=time.perf_counter()-t
            if got != baseline: raise RuntimeError("timed inverse mismatch")
            (current_times if name=="current" else candidate_times).append(dt)

    # Parse shape for explanatory evidence.
    count,pos=O._get_varint(encoded,5); lengths=[]
    for _ in range(count): length,pos=O._get_varint(encoded,pos); lengths.append(length)
    cm=statistics.median(current_times); nm=statistics.median(candidate_times)
    return {
      "engine":ENGINE,"status":"PASS","evidence_class":"research-oracle","product_release_credit":False,
      "contract":{"suite":SUITE,"workload":TARGET,"record_id":rid,"codec":"zstd","logical_size":logical_size,
        "encoded_bytes":len(encoded),"compressed_payload_bytes":len(payload),"delimiter":int(descriptor[1]),
        "segment_count":count,"max_segment_length":max(lengths,default=0),"unique_segment_lengths":len(set(lengths)),
        "repetitions_each":REPS,"same_exact_encoded_bytes":True,"candidate_bytes_equal_current":True,
        "candidate_crc_sha_match_archive":True,"product_code_changed":False,"release_thresholds_changed":False},
      "comparison":{"current_median_s":cm,"candidate_median_s":nm,"speedup_x":cm/max(nm,1e-12),
        "saved_s":cm-nm,"current_samples_s":current_times,"candidate_samples_s":candidate_times}}


def _write(p:Path,d:dict): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2)+"\n")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/g04-delimiter-oracle-work")); ap.add_argument("--output",type=Path,default=Path("benchmark-artifacts/g04-delimiter-oracle.json")); a=ap.parse_args()
    try: d=run(a.work_root)
    except BaseException as e:
        _write(a.output,{"engine":ENGINE,"status":"HARNESS_FAILURE","evidence_class":"research-oracle","product_release_credit":False,"error":{"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc(limit=32)}}); raise
    _write(a.output,d); print(json.dumps(d["comparison"],indent=2))
if __name__=="__main__": main()
