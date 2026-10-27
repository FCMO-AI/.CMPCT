#!/usr/bin/env python3
"""J24F09: installed, independent-r24, crash-isolated RAW descriptor lifetime court.

J24F05 mmap parent versus descriptor-bounded candidate. A *separate* writable
actor truncates the opened archive inode after the first genuine SHA/stage write.
Negative SIGBUS control is deliberately executed only in a subprocess.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile

from j24f04_raw_chunk_immutable_transfer import independent_revision24, blob_sha

ROOT = Path(__file__).resolve().parents[1]
PARENT_BLOB = "41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e"
CANDIDATE_BLOB = "a6a74068b34d726fc38bc151e5f191ce2dd45993"
WINDOW = 65536


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def fixture():
    chunks = [
        hashlib.shake_256(b"J24F09 authentic RAW 8MiB").digest(8 * 1024 * 1024),
        hashlib.shake_256(b"J24F09 authentic RAW small").digest(131072),
        hashlib.shake_256(b"J24F09 authentic RAW tail").digest(98309),
    ]
    return chunks, b"".join(chunks)


def get_reader(which: str, parent: Path):
    if which == "candidate":
        import cmpct.reader as module
    else:
        assert blob_sha(parent.read_bytes()) == PARENT_BLOB
        spec = importlib.util.spec_from_file_location(
            "cmpct._j24f09_historical_reader", parent)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.CMPCT


def actor(path: Path, how: str):
    before = os.stat(path)
    if how == "truncate":
        with open(path, "r+b", buffering=0) as handle:
            assert os.fstat(handle.fileno()).st_ino == before.st_ino
            os.ftruncate(handle.fileno(), 0)
            os.fsync(handle.fileno())
        after = os.stat(path)
        assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        assert after.st_size == 0
    elif how == "replace":
        replacement = path.with_name(path.name + ".other-inode")
        replacement.write_bytes(b"Z" * before.st_size)
        assert os.stat(replacement).st_ino != before.st_ino
        os.replace(replacement, path)
        after = os.stat(path)
        assert (after.st_dev,after.st_ino)!=(before.st_dev,before.st_ino)
        assert after.st_size == before.st_size
    else:
        raise ValueError(how)
    return {
        "mode": how, "pid": os.getpid(), "before_ino": before.st_ino,
        "after_ino": after.st_ino, "before_size": before.st_size,
        "after_size": after.st_size,
    }


def child_case(tmp: Path, storage_kind: int, which: str, mode: str, parent: Path):
    chunks, original = fixture()
    name, archive_bytes, payload_start = independent_revision24(chunks, storage_kind)
    source = tmp / "source.cmpct"
    source.write_bytes(archive_bytes)
    dest = tmp / "destination"
    dest.mkdir()
    sentinel = b"J24F09 existing authenticated destination"
    (dest / name).write_bytes(sentinel)
    Original = get_reader(which, parent)

    with Original(source) as reader:
        assert reader.by[name][4] == len(original)
        assert bytes(reader.by[name][5]) == hashlib.sha256(original).digest()
        assert reader.read(name) == original
        assert reader.verify() == 1
        real_write = os.write
        real_pread = os.pread
        writes, preads, reports = [], [], []

        def spy_pread(fd, n, offset):
            if fd == reader.f.fileno():
                preads.append((n,offset))
                if n > WINDOW:
                    raise AssertionError(f"unbounded source pread {n} B")
            return real_pread(fd, n, offset)

        def spy_write(fd, data):
            writes.append(len(data))
            if len(data) > WINDOW:
                raise AssertionError(f"unbounded stage write {len(data)} B")
            if not reports and mode != "none":
                # First genuine stage write follows SHA of the same detached window.
                assert len(data) == WINDOW and bytes(data) == chunks[0][:WINDOW]
                stage = os.fstat(fd)
                assert stat.S_ISREG(stage.st_mode) and stage.st_size == 0
                proc = subprocess.run([
                    sys.executable, str(Path(__file__).resolve()), "--actor",
                    str(source), mode,
                ], text=True, capture_output=True, check=True, timeout=30)
                report = json.loads(proc.stdout.strip())
                assert report["pid"] != os.getpid()
                reports.append(report)
                print("ACTOR_TRUTH=" + json.dumps(report, sort_keys=True), flush=True)
            return real_write(fd, data)

        error = None
        os.write = spy_write
        os.pread = spy_pread
        try:
            try:
                reader.extractall(dest, metadata=False)
            except Exception as exc:
                error = type(exc).__name__ + ": " + str(exc)
        finally:
            os.write = real_write
            os.pread = real_pread

    published = (dest / name).read_bytes()
    if mode == "truncate":
        safe = bool(error) and published == sentinel and len(reports) == 1
        if which == "candidate":
            assert any(n == WINDOW for n,_ in preads), "candidate never reached RAW window pread"
            assert safe, "candidate failed to reject truncation and preserve destination"
    else:
        safe = error is None and published == original
        assert safe, f"stable/inode-replacement control failed {which}/{storage_kind}/{mode}: {error}"

    result = {
        "which": which, "mode": mode, "storage_kind": storage_kind,
        "physical_archive_length": len(archive_bytes),
        "logical_length": len(original),
        "logical_sha256": sha(original),
        "published_sha256": sha(published),
        "published_is_original": published == original,
        "prior_destination_preserved": published == sentinel,
        "actor": reports[0] if reports else None,
        "max_source_pread": max((n for n,_ in preads), default=0),
        "source_pread_calls": len(preads),
        "max_stage_write": max(writes, default=0),
        "stage_writes": len(writes),
        "exception": error,
        "outcome": "PASS" if safe else "FAIL",
    }
    print("RESULT_JSON=" + json.dumps(result,sort_keys=True),flush=True)


def controller(parent: Path, out: Path):
    import cmpct.reader as candidate
    location = Path(candidate.__file__).resolve()
    assert not location.is_relative_to(ROOT), "reader must be installed outside source tree"
    assert blob_sha(location.read_bytes()) == CANDIDATE_BLOB
    assert blob_sha(parent.read_bytes()) == PARENT_BLOB
    assert hasattr(os, "pread") and os.name == "posix"
    cases = []
    with tempfile.TemporaryDirectory(prefix="j24f09-controller-") as td:
        root = Path(td)
        for storage in (1,5):
            for which in ("historical", "candidate"):
                for mode in ("none", "replace", "truncate"):
                    target = root / f"{storage}-{which}-{mode}"
                    target.mkdir()
                    cmd = [
                        sys.executable, str(Path(__file__).resolve()),
                        "--child", str(target), str(storage), which, mode,
                        str(parent)
                    ]
                    proc = subprocess.run(cmd,text=True,capture_output=True,timeout=50)
                    payloads = [
                        json.loads(x.split("=",1)[1])
                        for x in proc.stdout.splitlines() if x.startswith("RESULT_JSON=")
                    ]
                    actors = [
                        json.loads(x.split("=",1)[1])
                        for x in proc.stdout.splitlines() if x.startswith("ACTOR_TRUTH=")
                    ]
                    case = {
                        "which": which, "kind": storage, "mode": mode,
                        "returncode": proc.returncode,
                        "signal": -proc.returncode if proc.returncode < 0 else None,
                        "result": payloads[0] if payloads else None,
                        "actors": actors,
                        "stderr_tail": proc.stderr[-1300:],
                    }
                    if mode == "truncate" and which == "historical":
                        # Baseline must truly die from the *same* source lifetime fault.
                        expected_signal = signal.SIGBUS
                        assert proc.returncode == -expected_signal, case
                        assert len(actors) == 1 and actors[0]["after_size"] == 0, case
                        assert not payloads, "signal control surprisingly returned success"
                    else:
                        assert proc.returncode == 0 and len(payloads) == 1, case
                        assert payloads[0]["outcome"] == "PASS", case
                        if mode != "none":
                            assert len(actors)==1, case
                        if mode == "truncate":
                            assert payloads[0]["prior_destination_preserved"] and payloads[0]["exception"], case
                        else:
                            assert payloads[0]["published_is_original"], case
                    cases.append(case)
    result={
        "schema":"j24f09-r24-source-lifetime-v1",
        "candidate_reader_blob":CANDIDATE_BLOB,
        "parent_reader_blob":PARENT_BLOB,
        "platform":sys.platform,
        "cases":cases,
        "decision":"RAW_PREAD_TRUNCATION_FAIL_CLOSED_WITH_SIGBUS_NEGATIVE_CONTROL_PASS",
        "nonclaims":["general Reader mmap reads", "mixed/decoded content", "source-open races",
                     "Windows mmap fallback", "stage pathname substitution #528",
                     "full-product timing or RSS", "canonical release"],
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True))
    print("J24F09_DECISION="+result["decision"],flush=True)
    for case in cases:
        print("J24F09_CASE="+json.dumps({k:case[k] for k in ("which","kind","mode","returncode","signal")},sort_keys=True))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--actor",nargs=2)
    ap.add_argument("--child",nargs=5)
    ap.add_argument("--parent",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.actor:
        print(json.dumps(actor(Path(args.actor[0]),args.actor[1]),sort_keys=True))
    elif args.child:
        d,kind,which,mode,p=args.child
        child_case(Path(d),int(kind),which,mode,Path(p))
    else:
        if not args.parent or not args.output:
            ap.error("--parent and --output are required")
        controller(args.parent,args.output)


if __name__=="__main__":
    main()
