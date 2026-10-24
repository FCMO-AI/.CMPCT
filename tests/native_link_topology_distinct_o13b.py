#!/usr/bin/env python3
"""O13b held-out distinct-content hardlink target oracle; preregistered separately."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.reader import CMPCT
from native_link_topology_abi_o13 import (
    MTIME_NS, load_library, observe_native, setup_api,
)

A = b"alpha-source content-distinct from bravo|" * 25
B = b"bravo-source content-distinct from alpha|" * 25
assert len(A) == len(B) and hashlib.sha256(A).digest() != hashlib.sha256(B).digest()


def make(root: Path, owner: str, outfile: Path) -> tuple[str, dict]:
    root.mkdir()
    for name, data in (("a.bin", A), ("b.bin", B)):
        (root / name).write_bytes(data)
        (root / name).chmod(0o644)
    os.link(root / owner, root / "z_alias.bin")
    for name in ("a.bin", "b.bin"):
        os.utime(root / name, ns=(MTIME_NS, MTIME_NS))
    os.utime(root, ns=(MTIME_NS, MTIME_NS))
    a, b, alias = [os.stat(root / x) for x in ("a.bin", "b.bin", "z_alias.bin")]
    assert (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino)
    assert (alias.st_dev, alias.st_ino) == (
        (a.st_dev, a.st_ino) if owner == "a.bin"
        else (b.st_dev, b.st_ino)
    )
    Builder(root, workers=1, reproducible=True).build(outfile)
    with CMPCT(outfile) as rdr:
        rows = {r[0]: r for r in rdr.files}
        assert set(rows) == {"a.bin", "b.bin", "z_alias.bin"}
        assert rows["a.bin"][1] == rows["b.bin"][1] == K_FILE
        assert rows["z_alias.bin"][1] == K_HARDLINK
        assert rows["z_alias.bin"][6][0] == owner
        assert rdr.read("a.bin") == A and rdr.read("b.bin") == B
        assert rdr.read("z_alias.bin") == (A if owner == "a.bin" else B)
    return hashlib.sha256(outfile.read_bytes()).hexdigest(), {
        "alias_owner": owner, "alias_output_sha256": hashlib.sha256(
            A if owner == "a.bin" else B
        ).hexdigest()
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: native_link_topology_distinct_o13b.py RESULT.json")
    lib = load_library()
    setup_api(lib)
    with tempfile.TemporaryDirectory(prefix="cmpct-link-abi-o13b-") as tmp:
        p = Path(tmp)
        left = p / "left.cmpct"
        right = p / "right.cmpct"
        left_sha, left_py = make(p / "src-left", "a.bin", left)
        right_sha, right_py = make(p / "src-right", "b.bin", right)
        assert left_sha != right_sha
        assert left_py["alias_output_sha256"] != right_py["alias_output_sha256"]
        obs_left = observe_native(lib, left)
        obs_right = observe_native(lib, right)
        assert obs_left == obs_right, (
            "DISPROOF: native ABI distinguishes different-owner aliases",
            obs_left, obs_right
        )
        alias = next(x for x in obs_left["entries"] if x["path"] == "z_alias.bin")
        assert alias["kind"] == K_HARDLINK and alias["range_rc"] == -7
        for name, data in (("a.bin", A), ("b.bin", B)):
            entry = next(x for x in obs_left["entries"] if x["path"] == name)
            assert entry["range_rc"] == 0
            assert entry["range_sha256"] == hashlib.sha256(data).hexdigest()
        result = {
            "schema": "cmpct-native-hardlink-topology-o13b-v1",
            "decision": "DISTINCT_SOURCE_CONTENT_STILL_NATIVE_UNOBSERVABLE",
            "real_archive_sha256": {"owner_a": left_sha, "owner_b": right_sha},
            "authenticated_index_oracle": {"owner_a": left_py, "owner_b": right_py},
            "public_native_observation_sha256": hashlib.sha256(
                json.dumps(obs_left, sort_keys=True).encode()
            ).hexdigest(),
            "controls": {
                "same_regular_files_distinct_logical_bytes": True,
                "source_inode_hardlink_partitions_differ": True,
                "same_entry_names_modes_times_sizes": True,
                "different_signed_index_owner_paths": True,
                "different_python_alias_contents": True,
                "equal_documented_native_observations": True,
                "native_alias_range_unsupported": True,
            },
            "boundaries": [
                "POSIX hosted source-exact research only",
                "No new product code, format, security or speed guarantee",
                "No conclusion for future native C ABI additions",
            ],
        }
    path = Path(sys.argv[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
