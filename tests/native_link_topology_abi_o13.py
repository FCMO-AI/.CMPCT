#!/usr/bin/env python3
"""O13: independently distinguish real r24 hardlink graphs via public native C ABI.

Research-only information-boundary court; no product code or format changes.
The prediction is frozen in docs/v031-research/NATIVE_HARDLINK_ABI_TOPOLOGY_O13_PREREG.md.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_HARDLINK, K_SYMLINK
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_batch_abi import load_library, map_paths, open_native

MTIME_NS = 1_700_000_000_000_000_000
PAYLOAD = (b"cmpct-native-hardlink-abi-o13; shared exact bytes;\n" * 20) + b"END"


class EntryInfo(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("mode", ctypes.c_uint32),
        ("size", ctypes.c_uint64),
        ("mtime_ns", ctypes.c_int64),
    ]


def setup_api(lib):
    lib.cmpct_revision.argtypes = [ctypes.c_void_p]
    lib.cmpct_revision.restype = ctypes.c_uint16
    lib.cmpct_entry_info.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(EntryInfo),
    ]
    lib.cmpct_entry_info.restype = ctypes.c_int
    lib.cmpct_entry_pack_owner.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    lib.cmpct_entry_pack_owner.restype = ctypes.c_int


def make_tree(root: Path, link_owner: str, symbolic: bool = False):
    root.mkdir()
    for name in ("a.bin", "b.bin"):
        path = root / name
        path.write_bytes(PAYLOAD)
        path.chmod(0o644)
    assert os.stat(root / "a.bin").st_ino != os.stat(root / "b.bin").st_ino
    if symbolic:
        os.symlink(link_owner, root / "z_symbolic.bin")
        try:
            os.utime(root / "z_symbolic.bin", ns=(MTIME_NS, MTIME_NS), follow_symlinks=False)
        except (NotImplementedError, OSError):
            pass
    else:
        os.link(root / link_owner, root / "z_alias.bin")
    for name in ("a.bin", "b.bin"):
        os.utime(root / name, ns=(MTIME_NS, MTIME_NS))
    os.utime(root, ns=(MTIME_NS, MTIME_NS))
    if not symbolic:
        alias = os.stat(root / "z_alias.bin")
        a = os.stat(root / "a.bin")
        b = os.stat(root / "b.bin")
        assert (alias.st_dev, alias.st_ino) == (
            (a.st_dev, a.st_ino) if link_owner == "a.bin"
            else (b.st_dev, b.st_ino)
        )
        assert (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino)
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ("a.bin", "b.bin")}


def build_archive(root: Path, output: Path):
    Builder(root, workers=1, reproducible=True).build(output)
    assert output.is_file()
    with CMPCT(output) as source:
        rows = {row[0]: row for row in source.files}
        assert set(rows) == set(p.name for p in root.iterdir())
        assert rows["a.bin"][1] == rows["b.bin"][1] == K_FILE
        assert source.read("a.bin") == source.read("b.bin") == PAYLOAD
        if "z_alias.bin" in rows:
            assert rows["z_alias.bin"][1] == K_HARDLINK
            assert source.read("z_alias.bin") == PAYLOAD
            target = rows["z_alias.bin"][6][0]
            assert target in ("a.bin", "b.bin")
        else:
            assert rows["z_symbolic.bin"][1] == K_SYMLINK
            target = source.read("z_symbolic.bin").decode("utf-8")
            assert target in ("a.bin", "b.bin")
        # Capture only decision-relevant ground truth; never use private
        # Python rows to fabricate the native ABI observations.
        assert bytes(rows["a.bin"][5]) == bytes(rows["b.bin"][5]) or (
            rows["a.bin"][5] is None and rows["b.bin"][5] is None
        )
    return target


def observe_native(lib, archive_path: Path):
    handle = open_native(lib, archive_path)
    try:
        paths = map_paths(lib, handle)
        obs = []
        for name, index in sorted(paths.items()):
            info = EntryInfo()
            status = lib.cmpct_entry_info(handle, index, ctypes.byref(info))
            assert status == 0, (name, status)
            size = int(info.size)
            assert 0 < size < 8192, (name, size)
            # Every file is small enough to request completely through the
            # documented public range API (no internal Rust/index access).
            out = ctypes.create_string_buffer(size)
            written = ctypes.c_size_t(65535)
            rc = lib.cmpct_entry_read_range(
                handle, index, 0, out, size, ctypes.byref(written)
            )
            if rc == 0:
                assert written.value == size
                digest = hashlib.sha256(out.raw[:size]).hexdigest()
                sample = out.raw[:size].hex()
            else:
                assert written.value == 0, (name, rc, written.value)
                digest, sample = None, None
            owner = ctypes.c_size_t(999999)
            owner_status = lib.cmpct_entry_pack_owner(
                handle, index, ctypes.byref(owner)
            )
            if owner_status != 0:
                assert owner.value == 0, (name, owner_status, owner.value)
            obs.append({
                "path": name, "kind": int(info.kind), "mode": int(info.mode),
                "size": size, "mtime_ns": int(info.mtime_ns),
                "range_rc": int(rc), "range_written": int(written.value),
                "range_sha256": digest, "range_bytes": sample,
                "pack_owner_rc": int(owner_status),
                "pack_owner_key": int(owner.value) if owner_status == 0 else None,
            })
        return {"revision": lib.cmpct_revision(handle), "entries": obs}
    finally:
        lib.cmpct_close(handle)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_link_topology_abi_o13.py RESULT.json")
    lib = load_library()
    setup_api(lib)
    with tempfile.TemporaryDirectory(prefix="cmpct-native-link-abi-o13-") as td:
        base = Path(td)
        root_a = base / "hardlink-a"
        root_b = base / "hardlink-b"
        digest_a = make_tree(root_a, "a.bin")
        digest_b = make_tree(root_b, "b.bin")
        assert digest_a == digest_b
        archive_a, archive_b = base / "hardlink-a.cmpct", base / "hardlink-b.cmpct"
        actual_a = build_archive(root_a, archive_a)
        actual_b = build_archive(root_b, archive_b)
        assert (actual_a, actual_b) == ("a.bin", "b.bin")
        a_bytes, b_bytes = archive_a.read_bytes(), archive_b.read_bytes()
        assert a_bytes != b_bytes, "authenticated hardlink target must affect r24 archive"
        a_obs = observe_native(lib, archive_a)
        b_obs = observe_native(lib, archive_b)
        assert a_obs == b_obs, (
            "DISPROOF: documented native C API distinguishes the two hardlink graphs",
            a_obs, b_obs
        )
        row = next(x for x in a_obs["entries"] if x["path"] == "z_alias.bin")
        assert row["kind"] == K_HARDLINK and row["range_rc"] == -7, row
        for name in ("a.bin", "b.bin"):
            entry = next(x for x in a_obs["entries"] if x["path"] == name)
            assert entry["range_rc"] == 0 and entry["range_sha256"] == digest_a[name], entry

        # Positive capability control: the SAME native C API can observe a
        # symlink's direct stored target bytes in this particular source.
        root_sa = base / "symbolic-a"
        root_sb = base / "symbolic-b"
        assert make_tree(root_sa, "a.bin", symbolic=True) == digest_a
        assert make_tree(root_sb, "b.bin", symbolic=True) == digest_a
        archive_sa, archive_sb = base / "symbolic-a.cmpct", base / "symbolic-b.cmpct"
        assert build_archive(root_sa, archive_sa) == "a.bin"
        assert build_archive(root_sb, archive_sb) == "b.bin"
        syma = observe_native(lib, archive_sa)
        symb = observe_native(lib, archive_sb)
        a_link = next(x for x in syma["entries"] if x["path"] == "z_symbolic.bin")
        b_link = next(x for x in symb["entries"] if x["path"] == "z_symbolic.bin")
        assert a_link["kind"] == b_link["kind"] == K_SYMLINK
        assert a_link["range_rc"] == b_link["range_rc"] == 0
        assert bytes.fromhex(a_link["range_bytes"]) == b"a.bin"
        assert bytes.fromhex(b_link["range_bytes"]) == b"b.bin"

        result = {
            "schema": "cmpct-native-hardlink-abi-topology-o13-v1",
            "question": "Can public native C API distinguish distinct hardlink inode graphs?",
            "decision": "HARDLINK_GRAPH_UNOBSERVABLE_OVER_DOCUMENTED_NATIVE_ABI",
            "base_sha": "43ba79f9b9395af22a0f408de565704c268a4758",
            "source_sha256": digest_a,
            "archive_sha256": {
                "hardlink_a": hashlib.sha256(a_bytes).hexdigest(),
                "hardlink_b": hashlib.sha256(b_bytes).hexdigest(),
            },
            "native_observation_sha256": hashlib.sha256(
                json.dumps(a_obs, sort_keys=True).encode()
            ).hexdigest(),
            "native_observations": a_obs,
            "controls": {
                "actual_hardlink_inode_partitions_differ": True,
                "same_exact_regular_bytes_and_visible_metadata": True,
                "signed_python_hardlink_owner_differs": True,
                "complete_documented_native_observation_equal": True,
                "hardlink_read_unsupported_in_both": True,
                "symlink_target_native_range_observable": True,
                "r24_format_and_product_source_unchanged": True,
            },
            "limitations": [
                "Not a proof for other native APIs added after this source SHA",
                "Does not imply r24 format/Python Reader loses hardlink owner",
                "Does not prove a secure generic extractor",
                "Only a POSIX hosted real-Builder counterexample",
            ],
        }
    target = Path(sys.argv[1])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "native_observations"}, sort_keys=True))


if __name__ == "__main__":
    main()
