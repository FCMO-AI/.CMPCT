#!/usr/bin/env python3
"""J24K13: source-locked *research-only* one-pass STORED VZIP physical witness.

Compare with the actual installed safe Reader (#653/#663). Never replace its
validator, mutate published files, or treat an oracle as product evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile

from j24k12_installed_bhdr_batch import (
    NAME, digest, make_authentic_archive, queries_for, rss_mib, source_digest
)

SIZES = (64, 512, 4096)
CASES = ("q1_early", "q1_tail", "q8_mixed", "q64_tail")
PAIRS = 3


def singlepass_read_range(reader, name, start, length):
    """Copy of the *logical* r24 range walk with the same physical STORED check inline.

    Proof is checked against this Reader's currently mapped archive, per call.
    This removes callback dispatch, NOT work, and keeps the Reader as the control.
    Deflate/unsupported cases delegate unchanged to the control.
    """
    from cmpct.codec import (
        S_VZIP, BHDR, BMAGIC, CODEC_DEFLATE
    )
    storage = reader.by[name][6]
    if storage[0] != S_VZIP:
        return reader.read_range(name, start, length)
    recipe = reader.recipes[storage[1]]
    skref, lens, payloads, want_sha, want_size, want_crc = recipe
    if type(start) is not int or type(length) is not int:
        return reader.read_range(name, start, length)
    end = start + length
    if start < 0 or length < 0 or end > want_size:
        return reader.read_range(name, start, length)
    if length == 0:
        return b""
    # Restrict the research claim to STORED without adding a second N-stream
    # prepass: unsupported members delegate as encountered to the safe Reader.
    sk = reader._blob(skref)
    out = []
    outpos = 0
    skpos = 0
    for i, pr in enumerate(payloads):
        if (type(pr) not in (tuple, list) or len(pr) != 6 or
                type(pr[1]) is not int or pr[1] != zipfile.ZIP_STORED):
            return reader.read_range(name, start, length)
        ln = lens[i]
        if outpos + ln > start and outpos < end:
            a = max(start, outpos) - outpos
            b = min(end, outpos + ln) - outpos
            out.append(sk[skpos + a:skpos + b])
        outpos += ln
        skpos += ln
        rawref, method, stream_mode, streamref, csize, level = pr
        if outpos + csize > start and outpos < end:
            seg = reader._blob(rawref)
            if len(seg) != csize:
                raise IOError("virtual ZIP selective reconstruction length mismatch")
            a = max(start, outpos) - outpos
            b = min(end, outpos + csize) - outpos
            out.append(seg[a:b])
        elif outpos < end:
            # Exact source-equivalent of #653 Reader._vzip_physical_stream_size
            # specialized to STORED. No cached index, snapshot, source reopen,
            # unsigned metadata or C shortcut is credited.
            idx = rawref
            if type(idx) is not int or idx < 0 or idx >= len(reader.blobs):
                raise IOError("virtual ZIP physical owner index outside blobs")
            off, us, cs, codec, ml = reader.blobs[idx]
            if not all(type(x) is int and x >= 0 for x in
                       (off, us, cs, codec, ml)):
                raise IOError("virtual ZIP invalid physical owner descriptor")
            pos = reader.record_base + off
            if pos < reader.record_base or pos + BHDR.size > len(reader.mm):
                raise IOError("virtual ZIP physical owner header outside archive")
            m, c, flags, res, rus, rcs, rml, rcrc, rh = BHDR.unpack_from(
                reader.mm, pos
            )
            if (m != BMAGIC or c != codec or flags or res or
                    rus != us or rcs != cs or rml != ml or
                    pos + BHDR.size + rml + rcs > len(reader.mm)):
                raise IOError("virtual ZIP physical owner/header mismatch")
            if rus != csize:
                raise IOError("virtual ZIP selective reconstruction length mismatch")
        outpos += csize
        if outpos >= end:
            result = b"".join(out)
            if len(result) != length:
                raise IOError("virtual ZIP selective reconstruction length mismatch")
            return result
    ln = lens[-1]
    if outpos + ln > start and outpos < end:
        a = max(start, outpos) - outpos
        b = min(end, outpos + ln) - outpos
        out.append(sk[skpos + a:skpos + b])
    result = b"".join(out)
    if len(result) != length:
        raise IOError("virtual ZIP selective reconstruction length mismatch")
    return result


def worker(argv):
    from cmpct.reader import CMPCT
    archive, original, strategy, scenario = map(str, argv)
    truth = Path(original).read_bytes()
    ranges = queries_for(len(truth), scenario)
    w0, c0 = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(Path(archive)) as reader:
        opened_w, opened_c = time.perf_counter_ns() - w0, time.process_time_ns() - c0
        w1, c1 = time.perf_counter_ns(), time.process_time_ns()
        outputs = []
        for start, length in ranges:
            got = (reader.read_range(NAME, start, length) if strategy == "control"
                   else singlepass_read_range(reader, NAME, start, length))
            if got != truth[start:start + length]:
                raise AssertionError(("range byte mismatch", strategy, start, length))
            outputs.append(got)
        read_w, read_c = time.perf_counter_ns() - w1, time.process_time_ns() - c1
    record = {
        "strategy": strategy, "scenario": scenario,
        "n_queries": len(ranges),
        "archive_sha256": digest(Path(archive).read_bytes()),
        "truth_sha256": digest(truth),
        "query_digest": digest(b"".join(outputs)),
        "opened_wall_ns": opened_w, "opened_cpu_ns": opened_c,
        "read_wall_ns": read_w, "read_cpu_ns": read_c,
        "total_wall_ns": time.perf_counter_ns() - w0,
        "total_cpu_ns": time.process_time_ns() - c0,
        "peak_rss_mib": rss_mib(),
    }
    print("J24K13_WORKER=" + json.dumps(record, sort_keys=True), flush=True)


def reauthenticated_attack(archive, original, folder):
    """Actual r24 signed-index csize lie; physical records and original truth unchanged."""
    import msgpack
    from cmpct.codec import FTR, FMAGIC, HDR, MAGIC, VERSION, sha, zc
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive

    wire = archive.read_bytes()
    with CMPCT(archive) as r:
        physical_len = HDR.unpack_from(wire)[5]
        physical = wire[r.record_base:r.record_base + physical_len]
        index = copy.deepcopy(r.index)
        rid = index["files"][0][6][1]
        recipe = index["recipes"][rid]
        pivot = len(recipe[2]) // 2
        assert recipe[2][pivot][1] == zipfile.ZIP_STORED
        recipe[2][pivot][4] += 1
        recipe[4] += 1
        index["files"][0][4] += 1
        flags = HDR.unpack_from(wire)[2]
    pidx = msgpack.packb(index, use_bin_type=True)
    cidx = zc(pidx, 12)
    signature = sha(pidx)
    hostile = (HDR.pack(MAGIC, VERSION, flags, len(cidx), len(pidx),
                        len(physical), signature) + cidx + physical + cidx +
               FTR.pack(FMAGIC, 0, 1, 0, 0, len(cidx), len(pidx), 0, signature))
    dst = folder / "j24k13-reauthenticated.cmpct"
    dst.write_bytes(hostile)
    try:
        preflight_archive(dst)
    except Exception as exc:
        preflight_reject = type(exc).__name__
    else:
        raise AssertionError("strict preflight accepted physical length lie")

    rejections = []
    with CMPCT(dst) as r:
        for strategy in ("control", "singlepass"):
            try:
                start = original.stat().st_size - 1
                if strategy == "control":
                    r.read_range(NAME, start, 1)
                else:
                    singlepass_read_range(r, NAME, start, 1)
            except Exception as exc:
                rejections.append([strategy, type(exc).__name__])
            else:
                raise AssertionError("strategy silently accepted signed length lie: " + strategy)
    return {
        "mutant_sha256": digest(hostile), "preflight_reject": preflight_reject,
        "rejections": rejections,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        return worker(sys.argv[2:])
    from cmpct import reader as reader_module
    from cmpct import codec as codec_module
    work = Path(os.environ.get("J24K13_WORKDIR",
                               tempfile.mkdtemp(prefix="j24k13-")))
    work.mkdir(parents=True, exist_ok=True)
    source = {
        "reader_sha256": source_digest(Path(reader_module.__file__).read_bytes()),
        "codec_sha256": source_digest(Path(codec_module.__file__).read_bytes()),
        "instrument_sha256": source_digest(Path(__file__).read_bytes()),
    }
    cases = []
    negative = None
    for n in SIZES:
        archive, original, truth, signed_sha = make_authentic_archive(work, n)
        if n == SIZES[0]:
            negative = reauthenticated_attack(archive, original, work)
        for case in CASES:
            queries = queries_for(len(truth), case)
            qdigest = digest(b"".join(truth[s:s+k] for s,k in queries))
            observations = {"control": [], "singlepass": []}
            for i in range(PAIRS):
                order = ("control", "singlepass") if i % 2 == 0 else ("singlepass", "control")
                for strategy in order:
                    t0 = time.perf_counter_ns()
                    command = [sys.executable, str(Path(__file__).resolve()), "--worker",
                               str(archive), str(original), strategy, case]
                    p = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
                    if p.returncode:
                        raise RuntimeError("child failed: " + p.stdout[-4500:])
                    raw = [json.loads(s.split("J24K13_WORKER=", 1)[1])
                           for s in p.stdout.splitlines() if s.startswith("J24K13_WORKER=")]
                    assert len(raw) == 1
                    rec = raw[0]
                    assert rec["archive_sha256"] == signed_sha
                    assert rec["query_digest"] == qdigest
                    rec["process_wall_ns"] = time.perf_counter_ns() - t0
                    observations[strategy].append(rec)
            medians = {
                strategy: {
                    k: statistics.median(row[k] for row in obs)
                    for k in ("opened_wall_ns","opened_cpu_ns","read_wall_ns",
                              "read_cpu_ns","total_wall_ns","total_cpu_ns",
                              "process_wall_ns")
                } for strategy,obs in observations.items()
            }
            ratio = {
                k: medians["control"][k] / max(1,medians["singlepass"][k])
                for k in ("total_wall_ns","total_cpu_ns","read_wall_ns","read_cpu_ns",
                          "process_wall_ns")
            }
            cell = {"n_streams":n,"scenario":case,"archive_sha256":signed_sha,
                    "truth_sha256":digest(truth),"queries":queries,
                    "query_digest":qdigest,"archive_bytes":archive.stat().st_size,
                    "observations":observations,"median":medians,"ratio":ratio}
            cases.append(cell)
            print("J24K13_CELL=" + json.dumps({
                k:v for k,v in cell.items() if k!="observations"
            },sort_keys=True),flush=True)
    critical = [c for c in cases if c["n_streams"]==4096 and c["scenario"]=="q64_tail"]
    assert len(critical)==1
    threshold = all(critical[0]["ratio"][metric]>=1.20 for metric in
                    ("total_wall_ns","total_cpu_ns"))
    result = {
        "schema":"j24k13-installed-singlepass-v1",
        "class":"science-only-unchanged-installed-reader",
        "platform":platform.platform(),"python":sys.version.split()[0],
        "source":source,"cases":cases,"case_count":len(cases),
        "raw_process_observations":len(cases)*PAIRS*2,
        "signed_attack":negative,
        "decision":"SINGLEPASS_HEADROOM_OBSERVED" if threshold
                   else "SINGLEPASS_MATERIALITY_FALSIFIED",
    }
    dest = Path(os.environ.get("J24K13_OUT","j24k13-results.json"))
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("J24K13_RESULT=" + json.dumps({
        k:v for k,v in result.items() if k not in ("cases","source")
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
