#!/usr/bin/env python3
"""J24I56: O47 Win32 source ownership × J24G79 signed Reader composition.
Experimental-only Reader subclasses; no product, format, or release modification.
"""
from __future__ import annotations
import hashlib, json, os, platform, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path
import msgpack
from cmpct import _xattrs, transactions as tx
from cmpct.builder import Builder
from cmpct.codec import K_HARDLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g60_single_delta_chain_court import footer_chain, sha256_file
from j24g62_crossgen_rename_oracle import read_wire
from j24g64_mixed_fsmeta_oracle import reference, fingerprint
from j24g73_reader_open import FactoredCMPCT, xattr_projection, native_attr
from j24g74_owned_decoder_court import OwnedCMPCT

ROOT = Path(__file__).resolve().parents[1]
PARENT = "c15459f70001800f3781925efc7356409eb03ffe"
PREREG = "0fb19489013836e6be87fd95e0b1faf06576e810"
COMPOSITION_PARENT = "d75763393cf2f6b638447bf8dff02868a5207b6a"
COMPOSITION_PREREG = "8fea7f266e07b381bdc338d480054505bc84ca1e"
BLOBS = {
  "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
  "src/cmpct/builder.py": "5541cf5d818f36bcdab3b89834c97b6ed12d11f4",
  "tests/test_v031_win32_builder_hardlink_o47.py": "6c00ae49eea075957453d6d7238d988add6eedee",
  "research/j24g74_owned_decoder_court.py": "9af74e26e7585f6d88b1d59ead86514f41b0e373",
  "research/j24g64_mixed_fsmeta_oracle.py": "7657a41d11f2b3c8136c0b69cfe62401f9b19ccb",
}
KEY = "com.fcmo.cmpct.j24g79" if sys.platform == "darwin" else "user.cmpct_j24g79"
DEPTH = 63

def attest():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for sha in (PARENT, PREREG, COMPOSITION_PARENT, COMPOSITION_PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, head],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    for path, expected in BLOBS.items():
        actual = subprocess.check_output(["git", "rev-parse", "HEAD:" + path],
                                         cwd=ROOT, text=True).strip()
        assert actual == expected, (path, actual, expected)
    import cmpct.reader as installed
    assert Path(installed.__file__).read_bytes().replace(b"\r\n", b"\n") == (
        ROOT / "src/cmpct/reader.py").read_bytes().replace(b"\r\n", b"\n")
    return {"head": head, "prereg": PREREG, "blobs": BLOBS}

def make_archive(root, strict):
    source = root / "source"
    source.mkdir()
    expected, tags = {}, {}
    owner, alias = source / "a-owner.dat", source / "z-alias.dat"
    raw = hashlib.sha256(b"j24g79-hardlink-owner").digest() * 3
    owner.write_bytes(raw)
    try:
        os.link(owner, alias)
        source_hardlink = os.stat(owner).st_ino == os.stat(alias).st_ino
    except (OSError, NotImplementedError):
        alias.write_bytes(raw)
        source_hardlink = False
    # Unlike inherited J24G79, native physical source ownership is mandatory on every host.
    # O47 already established that os.link works on hosted Windows NTFS; no copy fallback earns success.
    assert source_hardlink and os.path.samefile(owner, alias), "physical source hardlink unavailable"
    expected[owner.name] = expected[alias.name] = raw
    if strict:
        assert source_hardlink, "POSIX hardlink source not creatable"
        assert _xattrs.can_set() and _xattrs.can_list(), "POSIX native xattr unsupported"
        _xattrs.setxattr(owner, KEY, b"hardlink-inode-j24g79", follow_symlinks=False)
        assert native_attr(alias, KEY) == b"hardlink-inode-j24g79"
        tags[owner.name] = tags[alias.name] = b"hardlink-inode-j24g79"
    for i in range(128):
        name = f"f{i:03d}.dat"
        raw = hashlib.sha256(f"j24g79-filler-{i}".encode()).digest() * 2
        path = source / name
        path.write_bytes(raw)
        expected[name] = raw
        if strict and i in (0, 32):
            value = f"identity-{i}".encode()
            _xattrs.setxattr(path, KEY, value, follow_symlinks=False)
            tags[name] = value
    archive = root / "hardlink-journal.cmpct"
    Builder(source, workers=1, reproducible=False).build(archive)
    with CMPCT(archive) as reader:
        actual_links = [row[0] for row in reader.files if row[1] == K_HARDLINK]
        assert "z-alias.dat" in actual_links, ("Builder physical link missing", actual_links)
        assert next(r for r in reader.files if r[0] == "z-alias.dat")[6][0] == "a-owner.dat"
        if strict:
            initial_tags = xattr_projection(reader.index)
            for name, value in tags.items():
                assert initial_tags.get(name, {}).get(KEY) == value, ("Builder baseline xattr", name)
    for i in range(21):
        old, new = f"f{i:03d}.dat", f"r{i:03d}.dat"
        tx.append_rename(archive, old, new)
        expected[new] = expected.pop(old)
        if old in tags:
            tags[new] = tags.pop(old)
        deleted = f"f{32+i:03d}.dat"
        tx.append_delete(archive, deleted)
        del expected[deleted]
        tags.pop(deleted, None)
        newraw = hashlib.sha256(f"j24g79-put-{i}".encode()).digest() * 2
        update_source = root / f"update-{i}.bin"
        update_source.write_bytes(newraw)
        target = f"f{64+i:03d}.dat" if i % 2 == 0 else f"new{i:03d}.dat"
        tx.append_update(archive, target, update_source)
        expected[target] = newraw
    return archive, expected, tags, {"source_hardlink": source_hardlink, "encoded_hardlinks": actual_links}

def check(path, expected, tags, strict):
    physical_sha = sha256_file(path)
    chain = footer_chain(path)
    assert len(chain) == DEPTH + 1
    assert chain[-1]["kind"] == 0
    assert all(x["kind"] == 1 and x["op_width"] == 1 for x in chain[:-1])
    base, deltas = read_wire(path)
    assert len(deltas) == DEPTH
    oracle = reference(base, deltas)
    wire = msgpack.packb(oracle, use_bin_type=True)
    routes = {}
    for cls in (CMPCT, FactoredCMPCT, OwnedCMPCT):
        with cls(path) as reader:
            assert reader.delta_depth == DEPTH
            assert reader.index == oracle
            assert msgpack.packb(reader.index, use_bin_type=True) == wire
            assert set(reader.by) == set(expected)
            assert reader.verify() == len(expected)
            for name, content in expected.items():
                assert reader.read(name) == content, (cls.__name__, name)
            if cls is not CMPCT:
                routes[cls.__name__] = reader._research_route
            if strict:
                actual = xattr_projection(reader.index)
                for name, value in tags.items():
                    assert actual.get(name, {}).get(KEY) == value, ("wrong metadata identity", cls.__name__, name)
                for name in expected:
                    if name not in tags:
                        assert KEY not in actual.get(name, {}), ("phantom metadata", cls.__name__, name)
    with OwnedCMPCT(path) as reader:
        with tempfile.TemporaryDirectory(prefix="j24g79-extract-") as td:
            dest = Path(td)
            reader.extractall(dest, require_xattrs=strict)
            for name, content in expected.items():
                assert (dest / name).read_bytes() == content
            a,b = dest / "a-owner.dat", dest / "z-alias.dat"
            assert os.path.samefile(a, b), "owned Reader lost physical hardlink after signed journal"
            assert os.stat(a).st_ino == os.stat(b).st_ino
            assert os.stat(a).st_dev == os.stat(b).st_dev
            if strict:
                for name,value in tags.items():
                    assert native_attr(dest / name, KEY) == value, ("lost extracted xattr",name)
                for name in expected:
                    if name not in tags:
                        assert native_attr(dest / name, KEY) is None, ("unexpected extracted xattr",name)
    pf = preflight_archive(path)
    assert pf["files"] == len(expected) and pf["delta_depth"] == DEPTH
    recovery = {}
    data = path.read_bytes()
    for label, damaged in (
        ("crc", data[:-1] + bytes([data[-1] ^ 0x77])),
        ("trunc", data[:-17]),
    ):
        with tempfile.TemporaryDirectory(prefix="j24g79-corrupt-") as td:
            bad = Path(td) / (label+".cmpct")
            bad.write_bytes(damaged)
            with CMPCT(bad) as a, FactoredCMPCT(bad) as b, OwnedCMPCT(bad) as c:
                assert a.index == b.index == c.index
                assert a.delta_depth == b.delta_depth == c.delta_depth == DEPTH-1
                recovery[label] = fingerprint(c.index)
    with OwnedCMPCT(path) as reader:
        first = reader.index["files"][0]
        original = first[0]
        first[0] = "j24g79-public-postopen-descriptor-mutated"
        assert first[0] != original
    with OwnedCMPCT(path) as fresh:
        assert fresh.index == oracle, "post-open public alias polluted fresh decoder"
    assert sha256_file(path) == physical_sha
    return {
      "archive_sha256": physical_sha, "archive_bytes": path.stat().st_size,
      "index_sha256": fingerprint(oracle), "initial_index_sha256": fingerprint(base),
      "members":len(expected),"footer_count":len(chain), "recovery":recovery,
      "routes":routes, "owned_route_reached":routes.get("OwnedCMPCT")=="owned-fresh-decoder",
      "xattr_members":len(tags), "postopen_descriptor_mutable":True,
      "extracted_physical_hardlink":True,
    }

def main():
    evidence = Path(os.getenv("J24I56_EVIDENCE_DIR","evidence"))
    evidence.mkdir(parents=True,exist_ok=True)
    receipt = {"schema":"cmpct-j24i56-win32-owned-compose-v1",
               "source":attest(),"os":sys.platform,"host":platform.platform(),
               "product_credit":0,"status":"RUNNING"}
    try:
        with tempfile.TemporaryDirectory(prefix="j24g79-") as td:
            archive,expected,tags,builder = make_archive(Path(td),sys.platform in ("linux","darwin"))
            receipt["builder"] = builder
            retained = evidence / "hardlink-journal-physical.cmpct"
            shutil.copyfile(archive,retained)
            receipt["physical_sha256"] = sha256_file(retained)
            receipt["result"] = check(archive,expected,tags,sys.platform in ("linux","darwin"))
        # The source/physical extracted inode tests are now mandatory on all three hosts.
        # Windows still has NO POSIX xattr claim; only POSIX results include signed xattrs.
        if not receipt["result"]["owned_route_reached"]:
            receipt["decision"] = "FALLBACK_NOT_ELIGIBLE"
        elif sys.platform in ("linux", "darwin"):
            receipt["decision"] = "H1_PHYSICAL_POSIX_PASS"
        else:
            receipt["decision"] = "H1_PHYSICAL_WIN32_HARDLINK_PASS"
        receipt["status"] = "PASS"
    except BaseException as err:
        receipt["status"]="FAIL"
        receipt["decision"]="H1_FALSIFIED_OR_BASELINE_BLOCKED"
        receipt["failure"]={"type":type(err).__name__,"message":str(err),
                            "traceback":traceback.format_exc()}
        raise
    finally:
        report=evidence/"j24i56-result.json"
        report.write_text(json.dumps(receipt,indent=2,sort_keys=True,default=str)+"\n")
        print("J24I56_HEAD",receipt["source"]["head"])
        print("J24I56_DECISION",receipt.get("decision"))
        print("J24I56_RECEIPT",report)

if __name__=="__main__":
    main()
