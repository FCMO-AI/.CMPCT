#!/usr/bin/env python3
"""O227 operation-local physical-owner scatter oracle. Scientific adapter, not CMPCT code."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time

import o226_decoder_unit_ownership_court as base

READER_BLOB = "dbd4ac576a05a47eae97e1e40de89cf1de440516"
PREREG_COMMIT = "f34fe69211fe07e09a368fda9ade7c7233a77520"
PARENT = "12a8b08a661746653a4af1801dfe89c00a39dd85"
FAMILIES = ("zstd_entropy_twice", "deflate_entropy_twice",
            "zstd_pattern_twice", "deflate_pattern_twice",
            "zstd_entropy_once", "deflate_entropy_once")
KINDS = ("fixed", "cdc")
ARMS = ("eager", "serial", "scatter")
REPEATS = 3


def owner_scatter(reader, kind):
    """Index only this request. No extra decoded cache or another unverified archive source."""
    row = reader.by[base.NAME]
    refs = row[6][1]
    if kind == "fixed":
        pieces = [(int(idx), reader.blobs[idx][1]) for idx in refs]
    else:
        pieces = [(int(idx), int(length)) for length, idx in refs]
    positions = collections.defaultdict(list)
    offset = 0
    for idx, length in pieces:
        if length < 0 or offset + length > row[4]:
            raise IOError("invalid logical extent")
        positions[idx].append((offset, length))
        offset += length
    if offset != row[4]:
        raise IOError("invalid complete logical extent")
    out = bytearray(offset)
    for idx, target in positions.items():
        raw = reader._blob(idx)  # existing checksum/decoder, once per owner in this request
        for off, length in target:
            if len(raw) != length:
                raise IOError("physical/logical geometry mismatch")
            out[off:off+length] = raw
    got = bytes(out)  # second full-sized copy is charged in wall/CPU/RSS
    if len(got) != row[4] or hashlib.sha256(got).digest() != bytes(row[5]):
        raise IOError("scatter logical integrity failure")
    return got, len(pieces), len(positions)


def read_arm(reader, arm, kind):
    if arm == "scatter":
        return owner_scatter(reader, kind)
    if arm == "eager":
        got = reader.read(base.NAME)
    elif arm == "serial":
        row = reader.by[base.NAME]
        ids = row[6][1] if kind == "fixed" else [e[1] for e in row[6][1]]
        got = b"".join(reader._blob(i) for i in ids)
        if len(got) != row[4] or hashlib.sha256(got).digest() != bytes(row[5]):
            raise IOError("serial logical integrity failure")
    else:
        raise ValueError("unknown arm")
    row = reader.by[base.NAME]
    refs = row[6][1]
    return got, len(refs), len(refs)


def child(args):
    from cmpct.reader import CMPCT
    begin_wall, begin_cpu = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(Path(args.archive)) as reader:
        open_wall, open_cpu = time.perf_counter_ns(), time.process_time_ns()
        got, ref_calls, distinct_calls = read_arm(reader, args.arm, args.kind)
        if base.digest(got) != args.logical_sha or len(got) != args.logical_bytes:
            raise AssertionError("wrong complete bytes/SHA")
    end_wall, end_cpu = time.perf_counter_ns(), time.process_time_ns()
    print(json.dumps({
        "family": args.family, "kind": args.kind, "arm": args.arm,
        "pid": os.getpid(), "python": sys.version.split()[0],
        "archive_sha256": args.archive_sha,
        "archive_bytes": Path(args.archive).stat().st_size,
        "logical_sha256": base.digest(got), "logical_bytes": len(got),
        "requested_blob_calls": ref_calls,
        "unique_physical_owners": distinct_calls,
        "read_wall_ms": (end_wall-open_wall)/1e6,
        "read_cpu_ms": (end_cpu-open_cpu)/1e6,
        "session_wall_ms": (end_wall-begin_wall)/1e6,
        "session_cpu_ms": (end_cpu-begin_cpu)/1e6,
        "open_wall_ms": (open_wall-begin_wall)/1e6,
        "open_cpu_ms": (open_cpu-begin_cpu)/1e6,
        **base.own_memory(),
    }, sort_keys=True))


def controls(root):
    from cmpct.reader import CMPCT
    from cmpct.codec import CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE
    owners = [base.payload(i, 11+(i*i*19)%127) for i in range(13)]
    codecs = [CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE] * 4 + [CODEC_RAW]
    refs = [(i*i+7*i+3) % 13 for i in range(139)]
    positives, negatives = [], []
    for kind in KINDS:
        wire, logical = base.archive(owners, codecs, refs, kind)
        p = root/("heldout-"+kind+".cmpct")
        p.write_bytes(wire)
        with CMPCT(p) as reader:
            if reader.verify() != 1 or reader.read(base.NAME) != logical:
                raise AssertionError("inherited mixed fixture failed")
            random_ranges = random.Random(22713 if kind=="fixed" else 22731)
            for _ in range(1000):
                start = random_ranges.randrange(len(logical)+1)
                length = random_ranges.randrange(len(logical)-start+1)
                assert reader.read_range(base.NAME, start, length) == logical[start:start+length]
            for arm in ARMS:
                got, n, u = read_arm(reader, arm, kind)
                if got != logical:
                    raise AssertionError("wrong mixed-owner output")
                positives.append({"kind":kind,"arm":arm,"sha256":base.digest(got),
                                  "bytes":len(got),"calls":n,"owners":u})
        bad_wire, _ = base.archive(owners, codecs, refs, kind, corrupt_crc=True)
        bad_p = root/("hostile-"+kind+".cmpct")
        bad_p.write_bytes(bad_wire)
        for arm in ARMS:
            try:
                with CMPCT(bad_p) as reader:
                    read_arm(reader, arm, kind)
            except (OSError, ValueError):
                negatives.append({"kind":kind,"arm":arm,"rejected":True})
            else:
                raise AssertionError("referenced physical CRC was accepted")
    return positives, negatives


def run(args):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    workspace = Path(args.workspace).resolve()
    reader_blob = subprocess.check_output(
        ["git","rev-parse","HEAD:src/cmpct/reader.py"],cwd=workspace,text=True
    ).strip()
    if reader_blob != READER_BLOB:
        raise AssertionError("exact Reader blob drift")
    samples, archives = [], []
    with tempfile.TemporaryDirectory(prefix="o227-owner-scatter-") as td:
        root = Path(td)
        positives, negatives = controls(root)
        for family in FAMILIES:
            owners, codecs, _ = base.workload(family)
            refs = list(range(len(owners))) * (2 if family.endswith("twice") else 1)
            for kind in KINDS:
                wire, logical = base.archive(owners, codecs, refs, kind)
                path = root/(family+"-"+kind+".cmpct")
                path.write_bytes(wire)
                if preflight_archive(path, verify_blob_headers=True)["files"] != 1:
                    raise AssertionError("authentic strict preflight rejected fixture")
                with CMPCT(path) as reader:
                    if reader.read(base.NAME) != logical or reader.verify() != 1:
                        raise AssertionError("inherited Reader failed valid control")
                manifest = {
                    "family":family,"kind":kind,"archive_sha256":base.digest(wire),
                    "logical_sha256":base.digest(logical),"archive_bytes":len(wire),
                    "logical_bytes":len(logical),"refs":len(refs),
                    "distinct_owners":len(owners),
                    "physical_decoded_request_upper_bytes":len(refs)*3*1024*1024,
                    "physical_unique_decode_bytes":len(owners)*3*1024*1024,
                }
                archives.append(manifest)
                for rep in range(REPEATS):
                    order = list(ARMS)
                    random.Random(227001+rep*109+len(family)*5+len(kind)).shuffle(order)
                    for arm in order:
                        command = [
                            sys.executable, __file__, "--child", "--archive", str(path),
                            "--family",family, "--kind",kind, "--arm",arm,
                            "--logical-bytes",str(len(logical)),
                            "--logical-sha",base.digest(logical),
                            "--archive-sha",base.digest(wire),
                        ]
                        started = time.perf_counter()
                        result = subprocess.run(command,cwd=root,text=True,
                                                capture_output=True,timeout=120)
                        if result.returncode:
                            raise RuntimeError(f"child {family}/{kind}/{arm}/{rep}: "
                                               + result.stderr[-4000:])
                        record = json.loads(result.stdout)
                        record["rep"] = rep
                        record["process_wall_ms"] = (time.perf_counter()-started)*1000
                        samples.append(record)
                        print(f"o227 sample {len(samples)}/108 {family} {kind} {arm} "
                              f"{record['session_wall_ms']:.2f}ms",
                              file=sys.stderr,flush=True)
    summary=[]
    for family in FAMILIES:
        for kind in KINDS:
            group={"family":family,"kind":kind,"arms":{}}
            for arm in ARMS:
                rows=[x for x in samples if (x["family"],x["kind"],x["arm"])==(family,kind,arm)]
                group["arms"][arm]={key:statistics.median(x[key] for x in rows)
                    for key in ("session_wall_ms","session_cpu_ms","read_wall_ms",
                                "read_cpu_ms","open_wall_ms","VmHWM_kib")}
            b=group["arms"]
            best_wall=min(b["eager"]["session_wall_ms"],b["serial"]["session_wall_ms"])
            best_cpu=min(b["eager"]["session_cpu_ms"],b["serial"]["session_cpu_ms"])
            group["best_control_wall_speedup"]=best_wall/b["scatter"]["session_wall_ms"]
            group["best_control_cpu_speedup"]=best_cpu/b["scatter"]["session_cpu_ms"]
            group["rss_above_best_control_kib"]=b["scatter"]["VmHWM_kib"]-min(
                b["eager"]["VmHWM_kib"],b["serial"]["VmHWM_kib"])
            summary.append(group)
    reused=[x for x in summary if x["family"].endswith("twice")]
    once=[x for x in summary if x["family"].endswith("once")]
    material=[(x["family"],x["kind"]) for x in reused if
        x["best_control_wall_speedup"]>=1.20 and x["best_control_cpu_speedup"]>=1.20]
    once_penalty=any(x["best_control_wall_speedup"]<1/1.10 for x in once)
    rss_debt=any(x["rss_above_best_control_kib"]>8192 for x in summary)
    decision="SCATTER_SEED" if len(material)>=2 else "NO_MATERIAL_HEADROOM"
    if decision=="SCATTER_SEED" and (once_penalty or rss_debt):
        decision="SCATTER_SEED_WITH_EXPORTED_DEBT"
    outcome={
        "schema":"o227-owner-scatter-v1",
        "source_parent":PARENT,"reader_blob":READER_BLOB,"prereg_commit":PREREG_COMMIT,
        "families":list(FAMILIES),"kinds":list(KINDS),"arms":list(ARMS),
        "samples":samples,"archives":archives,"summary":summary,
        "heldout_controls":positives,"hostile_controls":negatives,
        "material_cells":material,
        "once_penalty":once_penalty,"rss_debt":rss_debt,"decision":decision,
    }
    dest=Path(args.output).resolve()
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":decision,"material_cells":material,
                      "once_penalty":once_penalty,"rss_debt":rss_debt,
                      "samples":len(samples)},sort_keys=True))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--output")
    ap.add_argument("--child",action="store_true")
    ap.add_argument("--archive")
    ap.add_argument("--family")
    ap.add_argument("--kind")
    ap.add_argument("--arm")
    ap.add_argument("--logical-bytes",type=int)
    ap.add_argument("--logical-sha")
    ap.add_argument("--archive-sha")
    a=ap.parse_args()
    child(a) if a.child else run(a)
