"""J24W02 independent installed-Reader court. No tests/conftest.py / historical experiment imports."""
from __future__ import annotations
import hashlib, json, os, random, stat, tempfile
from contextlib import contextmanager
from pathlib import Path

from cmpct.reader import CMPCT
from cmpct.core import Builder


@contextmanager
def fd_chmod_case(kind: str):
    existing = getattr(os, "fchmod", None)
    try:
        if kind == "absent":
            if hasattr(os, "fchmod"): delattr(os, "fchmod")
        elif kind in ("oserror", "valueerror"):
            error = OSError if kind == "oserror" else ValueError
            def injected(_fd, _mode): raise error("synthetic fd-mode failure")
            setattr(os, "fchmod", injected)
        elif kind != "native":
            raise ValueError(kind)
        yield
    finally:
        if existing is None:
            if hasattr(os, "fchmod"): delattr(os, "fchmod")
        else: setattr(os, "fchmod", existing)


def assert_exact(path: Path, expected: bytes):
    actual = path.read_bytes()
    assert len(actual) == len(expected) and hashlib.sha256(actual).digest() == hashlib.sha256(expected).digest()


def frozen_court(root: Path):
    import base64
    data = json.loads((Path(__file__).resolve().parents[1]/"tests/conformance/v24-chunk-maps.json").read_text())
    assert data["schema"] == "cmpct-v24-golden-chunk-maps-v1"
    assert {r["storage_kind"] for r in data["vectors"]} == {1, 5}
    checked=[]
    for row in data["vectors"]:
        archive = root / ("golden-" + str(row["storage_kind"]) + ".cmpct")
        raw = base64.b64decode(row["archive_base64"], validate=True)
        assert hashlib.sha256(raw).hexdigest() == row["archive_sha256"]
        archive.write_bytes(raw)
        with CMPCT(archive) as ar:
            assert ar.verify() == 1
            expected = ar.read(row["name"])
            assert hashlib.sha256(expected).hexdigest() == row["logical_sha256"]
            assert ar.read_range(row["name"],row["range"]["offset"],row["range"]["length"]) == bytes.fromhex(row["range"]["hex"])
            for mode in ("native","absent"):
                dest = root / f"out-{row['storage_kind']}-{mode}"
                with fd_chmod_case(mode):
                    ar.extractall(dest, metadata=False)
                assert_exact(dest/row["name"], expected)
                assert not list(dest.glob(".*.cmpct-part-*"))
                if mode == "native" and os.name == "posix":
                    assert stat.S_IMODE((dest/row["name"]).stat().st_mode) == stat.S_IMODE(int(ar.by[row["name"]][2]) or 0o666)
                checked.append(f"{row['storage_kind']}:{mode}:sha")
            storage=ar.by[row["name"]][6]
            ids=storage[1] if storage[0]==1 else [x[1] for x in storage[1]]
            original=ar._blob
            victim=ids[0]
            def damaged(idx):
                b=original(idx)
                return bytes([b[0]^1])+b[1:] if idx==victim and b else b
            ar._blob=damaged
            dest=root/f"out-corrupt-{row['storage_kind']}"
            dest.mkdir()
            target=dest/row["name"]
            target.write_bytes(b"EXISTING-UNCHANGED")
            failed=False
            with fd_chmod_case("absent"):
                try:ar.extractall(dest,metadata=False)
                except IOError as e:
                    assert "file integrity failure" in str(e)
                    failed=True
            assert failed
            assert target.read_bytes()==b"EXISTING-UNCHANGED"
            assert not list(dest.glob(".*.cmpct-part-*"))
            checked.append(f"{row['storage_kind']}:corrupt-preservation")
            ar._blob=original
            for behavior in ("oserror","valueerror"):
                dest=root/f"out-mode-{row['storage_kind']}-{behavior}"
                dest.mkdir()
                target=dest/row["name"]
                target.write_bytes(b"EXISTING-UNCHANGED")
                failed=False
                with fd_chmod_case(behavior):
                    try:ar.extractall(dest,metadata=False)
                    except ValueError as e:
                        assert behavior=="valueerror" and "synthetic fd-mode" in str(e)
                        failed=True
                assert failed == (behavior=="valueerror")
                if failed:assert target.read_bytes()==b"EXISTING-UNCHANGED"
                else:assert_exact(target,expected)
                assert not list(dest.glob(".*.cmpct-part-*"))
                checked.append(f"{row['storage_kind']}:{behavior}:exception-boundary")
    return checked


def builder_court(root: Path):
    source=root/"builder-src"
    source.mkdir()
    block=b"CMPCT streaming extraction parity regression\n"*8192
    payload=(block*8)[:3*1024*1024]
    (source/"large.bin").write_bytes(payload)
    archive=root/"builder.cmpct"
    Builder(source).build(archive)
    with CMPCT(archive) as ar:
        assert ar.by["large.bin"][6][0] in (1,5)
        ar.extractall(root/"builder-out",metadata=False)
    assert_exact(root/"builder-out"/"large.bin",payload)
    return ["builder:chunked:sha"]


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="j24w02-") as temp:
        root=Path(temp)
        tests=frozen_court(root)+builder_court(root)
    outcome={"decision":"PORTABLE_FCHMOD_CHUNKED_CANDIDATE_PASS","checks":tests,"count":len(tests),
             "host":os.name,"fchmod_available":hasattr(os,"fchmod")}
    Path(args.out).write_text(json.dumps(outcome,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(outcome,sort_keys=True))
