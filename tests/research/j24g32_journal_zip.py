#!/usr/bin/env python3
"""J24G32: authentic r24 committed journal -> ZIP interoperability falsifier.

Modes are separate processes, so the historic Writer/Reader and candidate Reader
cannot silently share import state. The final stdlib-only audit does not import CMPCT.
This is a narrow conformance test, NOT a release benchmark or ZIP64 claim.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import sys
import time
import zipfile
import zlib

RELEASE_READER = "e716233403dabd0966863c45635e18fa5ac6afb8"
CANDIDATE_READER = "cd6a2971396d6fe02a1d7f460d850107b3dcc397"
STABLE_NS = 1580601600000000000  # 2020-02-02 UTC
ALPHA = (b"J24G32 alpha deterministic record\x00" * 91) + bytes(range(64))
DROP = b"this member must never survive deletion\x00" * 107
OLD_EDIT = b"superseded bytes must not leak" * 181
NEW_EDIT = (bytes(range(256)) * 37) + b"journal committed new payload"

def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

def git_blob(raw: bytes) -> str:
    raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def identity(expected: str) -> str:
    import inspect
    from cmpct.reader import CMPCT
    raw = Path(inspect.getfile(CMPCT)).read_bytes()
    found = git_blob(raw)
    if found != expected:
        raise AssertionError(f"installed Reader source mismatch: {found} != {expected}")
    return found

def snapshot(path: Path) -> dict:
    return {"bytes":path.stat().st_size, "sha256":digest(path.read_bytes())}

def desired_members() -> dict[str,bytes]:
    return {"edit.txt":NEW_EDIT, "moved-α.txt":ALPHA}

def prepare(root: Path) -> None:
    identity(RELEASE_READER)
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.transactions import append_delete, append_rename, append_update

    root.mkdir(parents=True, exist_ok=True)
    source = root / "source-tree"
    source.mkdir()
    for name, raw in [("alpha.txt",ALPHA),("drop.bin",DROP),("edit.txt",OLD_EDIT)]:
        p = source / name
        p.write_bytes(raw)
        os.utime(p, ns=(STABLE_NS,STABLE_NS))
    archive = root / "committed.cmpct"
    Builder(source,workers=1).build(archive)
    with CMPCT(archive) as reader:
        if sorted(row[0] for row in reader.files if row[1] != 1) != ["alpha.txt","drop.bin","edit.txt"]:
            raise AssertionError("initial real Builder index does not match expected three files")
    append_rename(archive, "alpha.txt", "moved-α.txt")
    append_delete(archive, "drop.bin")
    replacement = root / "replacement-input.txt"
    replacement.write_bytes(NEW_EDIT)
    os.utime(replacement, ns=(STABLE_NS,STABLE_NS))
    append_update(archive, "edit.txt", replacement)
    with CMPCT(archive) as reader:
        if sorted(reader.by) != sorted(desired_members()):
            raise AssertionError("committed Reader live set disagrees with manifest")
        for name,payload in desired_members().items():
            if reader.read(name) != payload or reader.file_sha256(name) != bytes.fromhex(digest(payload)):
                raise AssertionError("post-journal read / SHA mismatch " + name)
        if reader.verify() != 2:
            raise AssertionError("expected exactly two verified regular files")
        generation_depth = reader.delta_depth
        generation_footer = reader.latest_footer_pos
    orphan = root / "uncommitted-tail.cmpct"
    shutil.copyfile(archive,orphan)
    with orphan.open("ab") as f:
        # Deliberately not a footer and not a committed generation.
        f.write(b"J24G32-uncommitted-tail-\x00\x01\x02")
    manifest = {
        "source_reader_blob":RELEASE_READER,
        "writer_lineage":"main@80c358f8824ec1b20d349c92ed94c898090969b0",
        "committed":snapshot(archive),
        "uncommitted_tail":snapshot(orphan),
        "delta_depth":generation_depth,
        "latest_footer_pos":generation_footer,
        "expected":{name:{"bytes":len(raw),"sha256":digest(raw),
                          "crc32":zlib.crc32(raw)&0xffffffff}
                    for name,raw in desired_members().items()},
        "forbidden":["alpha.txt","drop.bin"],
    }
    (root/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("J24G32_PREPARED", json.dumps(manifest,sort_keys=True))

def export(root: Path, label: str) -> None:
    if label not in ("released","candidate"):
        raise ValueError("export requires released or candidate")
    expected_blob = RELEASE_READER if label == "released" else CANDIDATE_READER
    found_blob = identity(expected_blob)
    from cmpct.reader import CMPCT
    manifest = json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    receipts = []
    for kind,filename in [("committed","committed.cmpct"),
                          ("uncommitted_tail","uncommitted-tail.cmpct")]:
        source = root/filename
        if snapshot(source) != manifest[kind]:
            raise AssertionError(f"input bytes changed before export: {kind}")
        dest = root/f"{label}-{kind}.zip"
        with CMPCT(source) as reader:
            names = sorted(reader.by)
            if names != sorted(manifest["expected"]):
                raise AssertionError(f"effective journal names differ: {names}")
            for name,meta in manifest["expected"].items():
                data = reader.read(name)
                if digest(data) != meta["sha256"] or len(data) != meta["bytes"]:
                    raise AssertionError("Reader lossless mismatch: " + name)
            if reader.verify() != 2:
                raise AssertionError("Reader verify count differs")
            reader.export_zip(dest)
        if snapshot(source) != manifest[kind]:
            raise AssertionError("source archive mutated by ZIP export")
        receipts.append({"kind":kind,"archive_sha256":manifest[kind]["sha256"],
                         "zip_file":dest.name,**snapshot(dest)})
    report = {"reader_blob":found_blob, "label":label,
              "platform":platform.platform(), "python":sys.version,
              "archives":receipts}
    (root/f"{label}-receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("J24G32_EXPORTED", json.dumps(report,sort_keys=True))

def audit(root: Path) -> None:
    # This mode imports no CMPCT modules, and reads only physical source/ZIP bytes
    # and the result-bearing manifest, never the Reader's reported parsed contents.
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    expected=manifest["expected"]
    audits=[]
    for kind,filename in [("committed","committed.cmpct"),
                          ("uncommitted_tail","uncommitted-tail.cmpct")]:
        if snapshot(root/filename) != manifest[kind]:
            raise AssertionError("physical archive identity changed at audit")
        zips={}
        for label in ("released","candidate"):
            report=json.loads((root/f"{label}-receipt.json").read_text(encoding="utf-8"))
            record=next(x for x in report["archives"] if x["kind"]==kind)
            path=root/record["zip_file"]
            if snapshot(path) != {"bytes":record["bytes"],"sha256":record["sha256"]}:
                raise AssertionError("ZIP physical identity differs from receipt")
            with zipfile.ZipFile(path,"r") as z:
                names=z.namelist()
                if len(names)!=len(set(names)) or sorted(names)!=sorted(expected):
                    raise AssertionError(f"{label}/{kind}: name collision/stale/deleted member {names}")
                if any(x in names for x in manifest["forbidden"]):
                    raise AssertionError("deleted/renamed source name survived")
                for name,meta in expected.items():
                    info=z.getinfo(name)
                    raw=z.read(name)
                    if (len(raw),digest(raw),zlib.crc32(raw)&0xffffffff) != (
                            meta["bytes"],meta["sha256"],meta["crc32"]):
                        raise AssertionError(f"independent ZIP payload mismatch {label}/{kind}/{name}")
                    if info.flag_bits & 0x800 == 0 and not name.isascii():
                        raise AssertionError("non-ASCII legacy ZIP name lacks UTF-8 flag")
                    if info.date_time[0]<1980 or info.date_time[0]>2107:
                        raise AssertionError("invalid ZIP DOS calendar")
                if z.testzip() is not None:
                    raise AssertionError("ZIP CRC test returned bad member")
            zips[label]=path.read_bytes()
        if zips["released"]!=zips["candidate"]:
            raise AssertionError(f"historical/composed same-input ZIP physical divergence: {kind}")
        audits.append({"kind":kind,"bytes":len(zips["released"]),
                       "zip_sha256":digest(zips["released"]),
                       "identical_historical_candidate":True,
                       "logical_members":len(expected)})
    if (root/"released-committed.zip").read_bytes() != (root/"released-uncommitted_tail.zip").read_bytes():
        raise AssertionError("orphan-tail output differs from latest committed generation")
    if (root/"candidate-committed.zip").read_bytes() != (root/"candidate-uncommitted_tail.zip").read_bytes():
        raise AssertionError("candidate orphan-tail output differs from latest committed generation")
    result={"decision":"PASS_CROSS_LAYER_JOURNAL_ZIP" ,"audits":audits,
            "scope":"three generic regular members, three r24 journal operations, one orphan tail",
            "platform":platform.platform(),"unix_time":int(time.time())}
    (root/"independent-audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("J24G32_INDEPENDENT_AUDIT",json.dumps(result,sort_keys=True))

def main() -> None:
    if len(sys.argv) not in (3,4):
        raise SystemExit("usage: j24g32_journal_zip.py prepare|export|audit ROOT [released|candidate]")
    mode,root=sys.argv[1],Path(sys.argv[2])
    if mode=="prepare" and len(sys.argv)==3:prepare(root)
    elif mode=="export" and len(sys.argv)==4:export(root,sys.argv[3])
    elif mode=="audit" and len(sys.argv)==3:audit(root)
    else:raise SystemExit("invalid mode/arguments")

if __name__=="__main__":main()
