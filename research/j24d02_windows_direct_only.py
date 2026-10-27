"""J24D02 Windows direct-only transport court. Not a replacement for frozen 5-vector POSIX court.

Released chunked extraction hits known missing os.fchmod on Windows (#535/#536).
This independent six-case subset retains all three direct codecs and both modes; it
never claims Windows inherited chunked parity or platform-wide green status.
"""
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

from j24d02_direct_stage_court import run_case

def sha(b):
    return hashlib.sha256(b).hexdigest()

def check(receipt, repo, head):
    assert receipt["schema"] == "cmpct-j24d02-windows-direct-only-r1"
    assert receipt["head_sha"] == head
    assert receipt["reader_blob"] == "8b74c3994b59af63528acff960cd7f59f535bf8f"
    assert receipt["scope"] == "WINDOWS_DIRECT_ONLY_INHERITED_CHUNK_OS_FCHMOD_UNTESTED"
    fixture=json.loads((repo/"tests/conformance/v24-direct-codecs.json").read_text())
    assert fixture["format_revision"] == 24
    assert len(receipt["cases"]) == len(fixture["vectors"])*2 == 6
    n=4
    for ordinal,v in enumerate(fixture["vectors"]):
        for idx,mode in enumerate(("clean","fault")):
            row=receipt["cases"][ordinal*2+idx]
            assert (row["family"],row["member"],row["mode"]) == ("direct",v["name"],mode)
            assert row["archive_sha256"] == v["archive_sha256"]
            assert row["expected_member_sha256"] == v["logical_sha256"]
            sentinel=b"preexisting-destination-J24D02-"*7+bytes([ordinal*2+idx])
            assert row["before_sha256"] == sha(sentinel)
            assert row["stage_remainders"] == []
            assert row["external_alias_created"] in (True,False)
            if row["external_alias_created"]:
                assert row["external_alias_preserved"] is True
                assert row["external_alias_sha256"] == row["before_sha256"]
            if mode=="clean":
                assert row["decision"] == "CLEAN_EXACT_RECONSTRUCTION"
                assert row["after_sha256"] == v["logical_sha256"]
                assert row["after_size"] == v["logical_size"]
                assert row["error"] is None and row["fault_calls"] == 0
            else:
                assert row["decision"] == "STAGED_DIRECT_DESTINATION_PRESERVED"
                assert row["after_sha256"] == row["before_sha256"]
                assert row["before_inode"] == row["after_inode"]
                assert row["error_errno"] == errno.ENOSPC
                assert row["fault_calls"] == 2
                assert 1 <= len(bytes.fromhex(row["real_short_write_hex"])) <= 7
            n+=12
    assert receipt["clean_exact"] == 3 and receipt["direct_preserved"] == 3
    return n+2

def hostile(receipt,repo,head):
    edits=[
        lambda r:r.update(reader_blob="0"*40),
        lambda r:r["cases"][1].update(after_sha256="f"*64),
        lambda r:r["cases"][1].update(error_errno=errno.EIO),
        lambda r:r["cases"][1].update(fault_calls=1),
        lambda r:r["cases"][1].update(stage_remainders=["leftover"]),
        lambda r:r["cases"][2].update(expected_member_sha256="0"*64),
        lambda r:r["cases"].pop(),
    ]
    rejected=0
    for f in edits:
        r=copy.deepcopy(receipt);f(r)
        try:check(r,repo,head)
        except (AssertionError,KeyError,ValueError):rejected+=1
    assert rejected==len(edits)
    return rejected

def main():
    if len(sys.argv)!=3:
        raise SystemExit("usage: j24d02_windows_direct_only.py REPO_ROOT OUTPUT_JSON")
    repo,output=map(Path,sys.argv[1:])
    from cmpct import reader as mod
    assert repo.resolve() not in Path(mod.__file__).resolve().parents
    fixture=json.loads((repo/"tests/conformance/v24-direct-codecs.json").read_text())
    rows=[]
    with tempfile.TemporaryDirectory(prefix="cmpct-j24d02-windows-direct-") as d:
        root=Path(d)
        for v in fixture["vectors"]:
            for fault in (False,True):
                rows.append(run_case(root,v,"direct",fault,len(rows)))
    receipt=dict(schema="cmpct-j24d02-windows-direct-only-r1",
                 scope="WINDOWS_DIRECT_ONLY_INHERITED_CHUNK_OS_FCHMOD_UNTESTED",
                 head_sha=os.environ["J24D02_HEAD_SHA"],
                 reader_blob=os.environ["J24D02_READER_BLOB"],
                 platform=platform.platform(),cases=rows,
                 clean_exact=sum(v["decision"]=="CLEAN_EXACT_RECONSTRUCTION" for v in rows),
                 direct_preserved=sum(v["decision"]=="STAGED_DIRECT_DESTINATION_PRESERVED" for v in rows))
    checks=check(receipt,repo,os.environ["J24D02_HEAD_SHA"])
    rejected=hostile(receipt,repo,os.environ["J24D02_HEAD_SHA"])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"result":"DIRECT_ONLY_PASS","cases":len(rows),
                      "independent_checks":checks,"hostile_rejected":rejected,
                      "inherited_chunk_platform_gate":"UNTESTED_KNOWN_FCHMOD_BLOCKER"},sort_keys=True))
if __name__=="__main__":main()
