"""J24F07 source-preserved J24W02 native-host wire/Builder court plus bounded RAW probe.

Source: PR #536 Reader acceptance court; original frozen_court and builder_court
assertions are preserved unchanged. Separate J24F05 archive constructor only creates
new large RAW actual-r24 inputs. This module does not alter the Reader or its format.
"""
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



def bound_raw_window_court(root: Path):
    """New independent composition positive on genuine large RAW r24 S_CHUNKS/S_CDC."""
    from j24f04_raw_chunk_immutable_transfer import independent_revision24
    from j24f05_raw_window_court import large_chunks
    from cmpct.reader import CMPCT
    from cmpct.codec import CODEC_RAW

    chunks = large_chunks()
    expected = b"".join(chunks)
    assert len(chunks[0]) == 8 * 1024 * 1024
    outcome=[]
    for kind in (1, 5):
        name, physical, _ = independent_revision24(chunks, kind)
        path=root / f"bounded-{kind}.cmpct"
        path.write_bytes(physical)
        with CMPCT(path) as reader:
            assert reader.verify() == 1
            row=reader.by[name]
            storage=row[6]
            ids=list(storage[1]) if kind==1 else [part[1] for part in storage[1]]
            assert storage[0]==kind and len(ids)==3
            assert all(reader.blobs[idx][3]==CODEC_RAW for idx in ids)
            assert hashlib.sha256(expected).digest()==bytes(row[5])
            dest=root / f"bounded-output-{kind}"
            observed=[]
            original_write=os.write
            def measured_write(fd, payload):
                observed.append(len(payload))
                assert len(payload) <= 65536, ("RAW immutable window contract", len(payload))
                return original_write(fd, payload)
            try:
                os.write=measured_write
                with fd_chmod_case("absent"):
                    reader.extractall(dest,metadata=False)
            finally:
                os.write=original_write
            assert_exact(dest/name,expected)
            assert observed and len(observed)>=120 and max(observed)==65536
            assert not list(dest.glob(".*.cmpct-part-*"))
            outcome.append(dict(storage_kind=kind,logical_bytes=len(expected),
                                archive_sha256=hashlib.sha256(physical).hexdigest(),
                                output_sha256=hashlib.sha256((dest/name).read_bytes()).hexdigest(),
                                stage_calls=len(observed),max_stage_write_bytes=max(observed)))
    return outcome


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="j24f07-") as temp:
        root=Path(temp)
        tests=frozen_court(root)+builder_court(root)
        large=bound_raw_window_court(root)
    assert len(tests)==11, ("inherited J24W02 coverage must not shrink", tests)
    assert len(large)==2 and all(x["max_stage_write_bytes"]==65536 for x in large)
    outcome={"schema":"cmpct-j24f07-installed-three-host-v1",
             "decision":"PORTABLE_BOUNDED_RAW_COMPOSITION_PASS",
             "inherited_j24w02_checks":tests,"inherited_count":len(tests),
             "large_raw":large,"large_count":len(large),
             "host":os.name,"fchmod_available":hasattr(os,"fchmod"),
             "nonclaims":["stage-path substitution #528","source-mmap SIGBUS #460",
                          "full product parity","whole-process RSS"]}
    Path(args.out).write_text(json.dumps(outcome,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(outcome,sort_keys=True))
