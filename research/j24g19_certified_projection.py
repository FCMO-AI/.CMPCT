#!/usr/bin/env python3
"""J24G19 research: C-certified conservative ignored-field projection.

Never uses the certificate to reject an input. On a proof miss it invokes the
unmodified canonical msgpack.unpackb(raw=False). Only delta 'blobs' and 'ops'
are materialized on the certified subset; no CMPCT product files are changed.
"""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import time
import msgpack

BASE = Path(__file__).resolve().parent
SO = BASE / "j24g19_certified_subset.so"
SCANNER = ctypes.CDLL(str(SO)).mp_certify_subset
SCANNER.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64)]
SCANNER.restype = ctypes.c_int
KEEP = frozenset(("ops", "blobs"))

def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def certify(b: bytes) -> tuple[bool, int]:
    nodes = ctypes.c_uint64()
    result = SCANNER(b, len(b), ctypes.byref(nodes))
    return (result == 1, nodes.value)

def direct(b: bytes):
    return msgpack.unpackb(b, raw=False)

def projected(b: bytes):
    # Preserve source acceptance for any unsupported size, type or nested wire.
    is_map = bool(b) and (0x80 <= b[0] <= 0x8f or b[0] in (0xde, 0xdf))
    if not is_map or not certify(b)[0]:
        return direct(b)
    try:
        unpacker = msgpack.Unpacker(io.BytesIO(b), raw=False)
        count = unpacker.read_map_header()
        reduced = {}
        for _ in range(count):
            key = unpacker.unpack()  # key's valid ASCII form was certified
            if key in KEEP:
                reduced[key] = unpacker.unpack()
            else:
                unpacker.skip()  # already certified: not a semantic oracle
        if unpacker.tell() != len(b):
            return direct(b)
        return reduced
    except Exception:
        # Conservative rollback: a streaming incompatibility must not change
        # accepted bytes, error class or metadata semantics.
        return direct(b)

def keep_known(value):
    return {key: value[key] for key in KEEP if key in value}

def selftest() -> dict:
    rng = random.Random(2026102817)
    cases = []
    scalar = [0, -1, 2**48, None, True, False, "a", "ascii", [], {}, [0], {"x": 0}]
    def val(depth=0):
        if depth == 3 or rng.randrange(3) == 0:
            return rng.choice(scalar)
        if rng.randrange(2):
            return [val(depth+1) for _ in range(rng.randrange(5))]
        return {"k"+str(i): val(depth+1) for i in range(rng.randrange(5))}
    for i in range(2600):
        cases.append(msgpack.packb({"ops":[], "blobs":[], "extension": val()}, use_bin_type=True))
    cases += [msgpack.packb({"ops":[], "extension": [{"x": 0}] * n},use_bin_type=True)
              for n in (0,1,1000,10000,200000)]
    # Strings, ext, binary and huge strings must be passed to canonical decode.
    cases += [msgpack.packb({"ops":[], "extension":x}, use_bin_type=True)
              for x in ("café", b"\0"*1000, msgpack.ExtType(1,b"a"), "x"*40)]
    # Duplicate top-level keys and an unknown key containing the word 'ops'.
    cases += [bytes.fromhex("83 a3 6f 70 73 90 a3 6f 70 73 91 90 a9 65 78 74 65 6e 73 69 6f 6e 90")]
    ncert = 0
    for b in cases:
        obj = direct(b)
        yes,_ = certify(b)
        ncert += yes
        projected_value = projected(b)
        if yes:
            assert projected_value == keep_known(obj), (b[:100], projected_value, keep_known(obj))
        else:
            assert projected_value == obj
    malformed = {
        "unhashable_nested_map_key": bytes.fromhex("81 a9 65 78 74 65 6e 73 69 6f 6e 81 91 01 c0"),
        "bad_utf8": bytes.fromhex("81 a9 65 78 74 65 6e 73 69 6f 6e a1 ff"),
        "trailing": msgpack.packb({"ops":[]}) + b"\xc0",
        "truncated": bytes.fromhex("81 a3 6f 70 73 91"),
        "invalid_map_key": bytes.fromhex("81 90 c0"),
        "reserved": bytes.fromhex("81 a3 6f 70 73 c1"),
        "truncated_ext": bytes.fromhex("81 a3 6f 70 73 d4 01"),
    }
    for name,b in malformed.items():
        try:
            direct(b)
        except Exception as expected:
            assert not certify(b)[0], (name, "certified malformed", repr(expected))
            try:
                projected(b)
            except Exception as actual:
                assert type(actual) is type(expected), (name, type(actual), type(expected))
            else:
                raise AssertionError((name, "projected accepted malformed"))
        else:
            raise AssertionError((name,"canonical accepted invalid control"))
    # Differential hostile byte mutations may be rejected, accepted, or unsupported.
    # A native certificate must never certify a value direct unpack rejects.
    mutants=0; certified_invalid=[]; wrong_semantics=[]
    for b in cases[:280]:
        for _ in range(8):
            c=bytearray(b)
            mode=rng.randrange(4)
            if mode==0: c[rng.randrange(len(c))]=rng.randrange(256)
            elif mode==1: del c[rng.randrange(len(c)):]
            elif mode==2: c.append(rng.randrange(256))
            else: c[rng.randrange(len(c))]=0xc1
            raw=bytes(c); yes,_=certify(raw)
            try: origin=direct(raw)
            except Exception:
                if yes: certified_invalid.append(raw.hex()[:80])
            else:
                res=projected(raw)
                expected=keep_known(origin) if yes and isinstance(origin,dict) else origin
                if res!=expected: wrong_semantics.append(raw.hex()[:80])
            mutants+=1
    assert not certified_invalid and not wrong_semantics, (certified_invalid[:3],wrong_semantics[:3])
    return {"valid_cases":len(cases), "certified_valid":int(ncert),"invalid_controls":len(malformed),
            "hostile_mutants":mutants,"certified_invalid":0,"wrong_known_field_values":0,
            "c_sha256":sha((BASE/"j24g19_certified_subset.c").read_bytes()),
            "msgpack_version":msgpack.__version__,"python":sys.version.split()[0]}

def worker(path: Path, method: str, repeats: int) -> dict:
    b=path.read_bytes()
    f=direct if method=="direct" else projected
    # Measure only decode/projection, not Python import, file read or process startup.
    for _ in range(3):
        obj=f(b)
        assert isinstance(obj, dict) and "ops" in obj
        del obj
    raw=[]
    for _ in range(repeats):
        t0=time.perf_counter_ns();c0=time.process_time_ns()
        obj=f(b)
        cpu=time.process_time_ns()-c0; wall=time.perf_counter_ns()-t0
        assert obj.get("ops")==[] and obj.get("blobs")==[]
        raw.append({"cpu_ns":cpu,"wall_ns":wall})
        del obj
    return {"method":method,"input":path.name,"input_sha256":sha(b),"input_bytes":len(b),
            "certified":certify(b)[0],"samples":raw,
            "rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}

def generate(dest:Path):
    dest.mkdir(parents=True,exist_ok=True)
    values={
        "linked_200k": {"ops":[],"blobs":[],"extension":[{"x":0} for _ in range(200000)]},
        "ordinary_10k": {"ops":[],"blobs":[],"extension":[{"x":0} for _ in range(10000)]},
        "ordinary_1k": {"ops":[],"blobs":[],"extension":[{"x":0} for _ in range(1000)]},
        "unrecognized_unicode": {"ops":[],"blobs":[],"extension":[{"clé":0} for _ in range(10000)]},
    }
    manifest={}
    for name,value in values.items():
        b=msgpack.packb(value,use_bin_type=True)
        p=dest/(name+".mpk");p.write_bytes(b)
        manifest[name]={"bytes":len(b),"sha256":sha(b),"native_certified":certify(b)[0]}
    (dest/"inputs.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def court(dest:Path):
    selft=selftest()
    inputs=generate(dest)
    runs=[]
    for name in inputs:
        p=dest/(name+".mpk")
        for method in ("direct","projected"):
            for k in range(3):
                s=subprocess.run([sys.executable,__file__,"worker",str(p),method,"5"],capture_output=True,text=True)
                assert s.returncode==0,(s.stdout,s.stderr)
                row=json.loads(s.stdout);row["worker"]=k;runs.append(row)
    grouped={}
    for name in inputs:
        grouped[name]={}
        for method in ("direct","projected"):
            entries=[x for x in runs if x["input"]==name+".mpk" and x["method"]==method]
            grouped[name][method]={"cpu_ns_median":statistics.median(y["cpu_ns"] for x in entries for y in x["samples"]),
                                   "rss_kib_median":statistics.median(x["rss_kib"] for x in entries)}
    output={"schema":"cmpct-j24g19-projection-component-v1","source_c_sha256":selft["c_sha256"],
            "source_py_sha256":sha(Path(__file__).read_bytes()),"selftest":selft,"inputs":inputs,
            "grouped":grouped,"runs":runs,"product_claim":False}
    (dest/"result.json").write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps({"selftest":selft,"grouped":grouped},indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=["selftest","worker","court"])
    parser.add_argument("args",nargs="*");ns=parser.parse_args()
    if ns.command=="selftest":print(json.dumps(selftest(),indent=2))
    if ns.command=="worker":print(json.dumps(worker(Path(ns.args[0]),ns.args[1],int(ns.args[2]))))
    if ns.command=="court":court(Path(ns.args[0]))
