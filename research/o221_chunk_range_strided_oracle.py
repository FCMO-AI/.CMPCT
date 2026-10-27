#!/usr/bin/env python3
"""O221 genuine signed r24 S_CHUNKS/S_CDC random-range amortization court.

Science only. Does not monkeypatch/modify cmpct.reader. Compare installed original
Reader.read_range() against a separately implemented stride-256 range adapter,
charging adapter creation inside a fresh Reader session. Prereg 9114674.
"""
from __future__ import annotations
import argparse
import bisect
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time

STRIDE = 256
SPEC_N = (65536, 262144)
KINDS = ("fixed", "cdc")
QS = (1, 64)
TRIALS = 3
NAME = {"fixed": "fixed.bin", "cdc": "cdc.bin"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_py(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def archive_bytes(workspace: Path, kind: str, n: int) -> bytes:
    logical = b"Q" * n
    if kind == "fixed":
        mod = load_py(workspace / "tests/test_o215_fixed_chunk_admission.py")
        return mod._make_archive([0] * n, logical, blobs=(b"Q",))
    mod = load_py(workspace / "tests/test_o214_cdc_admission.py")
    return mod._r24([[1, 0] for _ in range(n)], logical, blobs=(b"Q",))


def queries(kind: str, n: int, q: int):
    rng = random.Random(221000 + 7 * n + q + len(kind))
    # Unordered random-tail queries disallow a monotone streaming-cursor shortcut.
    starts = [rng.randrange(n // 4, n - 17) for _ in range(q)]
    rng.shuffle(starts)
    return [(s, 17) for s in starts]


def build_anchors(reader, name: str):
    row = reader.by[name]
    kind = row[6][0]
    from cmpct.codec import S_CHUNKS, S_CDC
    assert kind in (S_CHUNKS, S_CDC)
    descriptors = row[6][1]
    anchor_offsets = []
    anchor_indices = []
    offset = 0
    for i, item in enumerate(descriptors):
        if i % STRIDE == 0:
            anchor_offsets.append(offset)
            anchor_indices.append(i)
        offset += reader.blobs[item][1] if kind == S_CHUNKS else item[0]
    if offset != row[4]:
        raise AssertionError("candidate index not built from structurally admitted logical length")
    return (anchor_offsets, anchor_indices, descriptors, kind)


def indexed_range(reader, name: str, start: int, length: int, anchors):
    from cmpct.codec import S_CHUNKS, S_CDC
    row = reader.by[name]
    end = start + length
    if start < 0 or length < 0 or end > row[4]:
        raise ValueError("range outside member")
    if length == 0:
        return b""
    offsets, indices, entries, kind = anchors
    k = bisect.bisect_right(offsets, start) - 1
    if k < 0:
        k = 0
    i, p = indices[k], offsets[k]
    out = []
    while i < len(entries) and p < end:
        item = entries[i]
        idx = item if kind == S_CHUNKS else item[1]
        bsize = reader.blobs[idx][1] if kind == S_CHUNKS else item[0]
        if p + bsize > start and p < end:
            b = reader._blob(idx)
            a = max(start, p) - p
            z = min(end, p + bsize) - p
            out.append(b[a:z])
        p += bsize
        i += 1
    return b"".join(out)


def child(args):
    # Excludes process startup/imports, includes real Reader open, admission,
    # candidate index creation (if any) and every selective read.
    from cmpct.reader import CMPCT
    ranges = queries(args.kind, args.n, args.q)
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    with CMPCT(Path(args.archive)) as reader:
        assert reader.by[NAME[args.kind]][4] == args.n
        anchors = build_anchors(reader, NAME[args.kind]) if args.arm == "stride" else None
        streamed = hashlib.sha256()
        for start, size in ranges:
            v = (reader.read_range(NAME[args.kind], start, size)
                 if anchors is None else
                 indexed_range(reader, NAME[args.kind], start, size, anchors))
            if v != b"Q" * size:
                raise AssertionError((args.arm, args.kind, start, size, v[:32]))
            streamed.update(v)
        # Boundary, empty and random-access backward probes: identical r24
        # read semantics, but not included in the timed session claim.
        timed_end_wall = time.perf_counter_ns()
        timed_end_cpu = time.process_time_ns()
        for pos, length in ((0, 1), (args.n-1, 1), (args.n-17, 17),
                            (args.n//2 - 1, 2), (args.n, 0)):
            read = (reader.read_range(NAME[args.kind], pos, length)
                    if anchors is None else
                    indexed_range(reader, NAME[args.kind], pos, length, anchors))
            assert read == b"Q" * length
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({
        "kind": args.kind, "n": args.n, "q": args.q, "arm": args.arm,
        "wall_ms": (timed_end_wall-start_wall)/1e6,
        "cpu_ms": (timed_end_cpu-start_cpu)/1e6,
        "peak_rss_kib": rss,
        "logical_digest": digest(b"Q"*args.n),
        "ranges_digest": streamed.hexdigest(),
        "range_starts_sha256": digest(json.dumps(ranges).encode()),
        "count": len(ranges),
        "anchor_count": len(anchors[0]) if anchors else 0,
    }, sort_keys=True))



def held_out_variable_payloads(workspace: Path):
    """Differently rooted byte-sensitive range oracle; repeated b'Q' alone masks offsets."""
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    payloads=(b"A", b"BC", b"DEF", b"GHIJ", b"KLMNO")
    refs=[(i*i+3*i+1)%len(payloads) for i in range(173)]
    logical=b"".join(payloads[i] for i in refs)
    results=[]
    with tempfile.TemporaryDirectory(prefix="o221-variable-") as td:
        for kind in KINDS:
            mod=load_py(workspace / ("tests/test_o215_fixed_chunk_admission.py"
                                  if kind=="fixed" else "tests/test_o214_cdc_admission.py"))
            if kind=="fixed":
                wire=mod._make_archive(refs,logical,blobs=payloads)
            else:
                entries=[[len(payloads[idx]),idx] for idx in refs]
                wire=mod._r24(entries,logical,blobs=payloads)
            path=Path(td)/(kind+".cmpct")
            path.write_bytes(wire)
            assert preflight_archive(path,verify_blob_headers=True)["files"]==1
            with CMPCT(path) as reader:
                assert reader.verify()==1
                assert reader.read(NAME[kind])==logical
                anchors=build_anchors(reader,NAME[kind])
                cases=0
                for start in range(len(logical)+1):
                    for length in (0,1,2,3,7,17,33):
                        if start+length>len(logical):continue
                        expected=logical[start:start+length]
                        original=reader.read_range(NAME[kind],start,length)
                        indexed=indexed_range(reader,NAME[kind],start,length,anchors)
                        assert original==expected and indexed==expected, (kind,start,length)
                        cases+=1
                assert cases>1000
            results.append({"kind":kind,"case_count":cases,"archive_sha256":digest(wire),
                            "logical_sha256":digest(logical),"blob_lengths":list(map(len,payloads)),
                            "repeated_reference_count":len(refs)})
    return results

def run(args):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    from cmpct.codec import S_CHUNKS, S_CDC
    root = Path(args.workspace).resolve()
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    variable_cases=held_out_variable_payloads(root)
    samples = []
    archives = []
    with tempfile.TemporaryDirectory(prefix="o221-r24-") as td:
        for kind in KINDS:
            for n in SPEC_N:
                wire = archive_bytes(root, kind, n)
                path = Path(td) / ("%s-%d.cmpct" % (kind, n))
                path.write_bytes(wire)
                info = preflight_archive(path, verify_blob_headers=True)
                assert info["files"] == 1
                with CMPCT(path) as reader:
                    assert reader.by[NAME[kind]][6][0] == (S_CHUNKS if kind == "fixed" else S_CDC)
                    assert len(reader.by[NAME[kind]][6][1]) == n
                    assert reader.verify() == 1
                    assert reader.read(NAME[kind]) == b"Q" * n
                    # First-independent, last and crossing ranges on actual signed archive.
                    for pos,ln in ((0,1),(n-1,1),(n//2-1,3)):
                        assert reader.read_range(NAME[kind],pos,ln)==b"Q"*ln
                archives.append({"kind":kind,"n":n,"archive_bytes":len(wire),
                                 "archive_sha256":digest(wire),
                                 "logical_sha256":digest(b"Q"*n)})
                for q in QS:
                    for rep in range(args.repeats):
                        order=["baseline", "stride"]
                        random.Random(221 + n + rep*17 + q + len(kind)).shuffle(order)
                        matched={}
                        for arm in order:
                            cmd=[sys.executable,__file__,"--child","--archive",str(path),
                                 "--kind",kind,"--n",str(n),"--q",str(q),
                                 "--arm",arm]
                            start=time.perf_counter_ns()
                            p=subprocess.run(cmd,cwd=td,capture_output=True,text=True,check=False)
                            process_wall_ms=(time.perf_counter_ns()-start)/1e6
                            if p.returncode:
                                raise RuntimeError("CHILD_FAILED "+str(cmd)+"\n"+p.stdout+"\n"+p.stderr)
                            obj=json.loads(p.stdout.strip().splitlines()[-1])
                            assert obj["kind"]==kind and obj["n"]==n
                            assert obj["q"]==q and obj["arm"]==arm
                            assert obj["count"]==q
                            assert obj["logical_digest"]==digest(b"Q"*n)
                            obj.update({"rep":rep,"process_wall_ms":process_wall_ms,
                                        "archive_sha256":digest(wire)})
                            matched[arm]=obj
                            samples.append(obj)
                        assert matched["baseline"]["ranges_digest"]==matched["stride"]["ranges_digest"]
                        assert matched["baseline"]["range_starts_sha256"]==matched["stride"]["range_starts_sha256"]
                        print("PAIR",kind,n,q,rep,
                              round(matched["baseline"]["wall_ms"],3),
                              round(matched["stride"]["wall_ms"],3),flush=True)
    summary=[]
    for kind in KINDS:
        for n in SPEC_N:
            for q in QS:
                pair={a:[s for s in samples if s["kind"]==kind and s["n"]==n and
                          s["q"]==q and s["arm"]==a] for a in ("baseline","stride")}
                b,c=pair["baseline"],pair["stride"]
                mw={a:statistics.median(s["wall_ms"] for s in pair[a]) for a in pair}
                mc={a:statistics.median(s["cpu_ms"] for s in pair[a]) for a in pair}
                rss={a:statistics.median(s["peak_rss_kib"] for s in pair[a]) for a in pair}
                summary.append({"kind":kind,"n":n,"q":q,
                                "baseline_wall_ms":mw["baseline"],
                                "stride_wall_ms":mw["stride"],
                                "baseline_cpu_ms":mc["baseline"],
                                "stride_cpu_ms":mc["stride"],
                                "wall_speedup":mw["baseline"]/mw["stride"],
                                "cpu_speedup":mc["baseline"]/mc["stride"],
                                "peak_rss_delta_mib":(rss["stride"]-rss["baseline"])/1024})
    decisive=[s for s in summary if s["q"]==64 and s["n"]==262144]
    passed=(len(decisive)==2 and all(
        s["wall_speedup"]>=1.5 and s["cpu_speedup"]>=1.5 and
        s["peak_rss_delta_mib"]<=8.0 for s in decisive))
    result={"question":"O221","tier":"installed_reader_out_of_tree_scientific_AB_not_product",
            "exact_source_parent":"c5e13bb3fbb4cdade8b64246658ce7c7818de41f",
            "prereg_commit":"9114674cf217dd8b8b463f4f602fa8b91b825fee",
            "runner_python":sys.version,"samples":samples,"archives":archives,
            "held_out_variable_payloads":variable_cases,
            "summary":summary,
            "decision":"CHARGED_RANDOM_RANGE_HEADROOM" if passed else "CHARGED_RANDOM_RANGE_NOT_PROVEN",
            "limitations":"Only repeated one-byte physical RAW refs; indexed adapter not production; parallelism, diverse codecs, update/recovery and release parity unmeasured."}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RESULT",json.dumps({"decision":result["decision"],"summary":summary},sort_keys=True))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--child",action="store_true")
    p.add_argument("--archive")
    p.add_argument("--kind",choices=KINDS)
    p.add_argument("--n",type=int)
    p.add_argument("--q",type=int)
    p.add_argument("--arm",choices=("baseline","stride"))
    p.add_argument("--workspace",default=os.getenv("GITHUB_WORKSPACE",str(Path(__file__).resolve().parents[1])))
    p.add_argument("--output")
    p.add_argument("--repeats",type=int,default=TRIALS)
    a=p.parse_args()
    if a.child:
        child(a)
    else:
        if a.output is None:
            p.error("--output required")
        run(a)
