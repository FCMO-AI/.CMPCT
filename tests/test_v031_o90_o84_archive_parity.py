"""O90 same-input O84 Builder source-exact archive-byte parity control.

This tests historical Builder *source* with the candidate's otherwise identical
installed codec/runtime; it is not a full historical wheel or release benchmark.
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

from cmpct.core import Builder, CMPCT

O84_HEAD = "7efcc51154b64fd6394ddffaab599760659f6c91"
O84_BLOB = "64b0cd21ad54ce7c8e8c6f5847b3c613fff6511c"


def _historical_builder():
    src=subprocess.check_output(["git","show",f"{O84_HEAD}:src/cmpct/builder.py"])
    blob=subprocess.run(["git","hash-object","--stdin"],input=src,stdout=subprocess.PIPE,check=True).stdout.decode().strip()
    assert blob==O84_BLOB,blob
    spec=importlib.util.spec_from_loader("cmpct._o84_exact_source",loader=None)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    exec(compile(src.decode("utf-8"),f"{O84_HEAD}/src/cmpct/builder.py","exec"),mod.__dict__)
    return mod.Builder


def test_o90_exact_o84_regular_output_complete_archive_parity(tmp_path):
    source=tmp_path/"payload"
    source.mkdir()
    (source/"nested").mkdir()
    payloads={
        "plain.txt":b"Exact CMPCT source/output admission parity\n"*40,
        "nested/binary.dat":hashlib.shake_256(b"O90 O84 parity").digest(4096),
        "nested/empty":b"",
    }
    for rel,data in payloads.items():
        (source/rel).write_bytes(data)
    baseline=tmp_path/"parent.cmpct"
    candidate=tmp_path/"candidate.cmpct"
    old_builder=_historical_builder()
    old_builder(source,workers=1,reproducible=True).build(baseline)
    Builder(source,workers=1,reproducible=True).build(candidate)
    a,b=baseline.read_bytes(),candidate.read_bytes()
    assert a==b,(len(a),len(b),hashlib.sha256(a).hexdigest(),hashlib.sha256(b).hexdigest())
    for path in (baseline,candidate):
        with CMPCT(path) as ar:
            ar.verify()
            for rel,data in payloads.items():
                assert ar.read(rel)==data
    print("O90_O84_COMPLETE_ARCHIVE_PARITY="+hashlib.sha256(a).hexdigest(),flush=True)
