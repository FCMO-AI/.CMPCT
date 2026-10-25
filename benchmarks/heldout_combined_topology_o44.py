"""O44: non-frozen held-out combined corpus and physical-topology oracle.

Run from repository root: python -m benchmarks.heldout_combined_topology_o44 --generate --output ...
This research instrument does not alter the frozen universal corpus or release gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from .heldout_physical_tree import copytree_with_hardlinks


SUBTREES = ("tiny", "source", "media", "dedup_links", "nested")
BINARY_FILES = ("pattern32m.bin", "random16m.bin")


def build_nonfrozen_combined(corpora: Path, destination: Path) -> Path:
    """Materialize an **additional** combined tree from unchanged source categories."""
    corpora, destination = Path(corpora), Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    for name in SUBTREES:
        copytree_with_hardlinks(corpora / name, destination / name)
    for name in BINARY_FILES:
        shutil.copy2(corpora / "binary" / name, destination / name)
    return destination


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def physical_tree(root: Path) -> dict:
    """Root-independent physical graph plus exact typed member snapshot."""
    entries = {}
    inode_groups = {}
    total_logical = 0
    charged_once = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        common = {"mode": stat.S_IMODE(st.st_mode), "mtime_ns": st.st_mtime_ns}
        if stat.S_ISLNK(st.st_mode):
            entries[rel] = {"kind": "symlink", "target": os.readlink(path), **common}
        elif stat.S_ISDIR(st.st_mode):
            entries[rel] = {"kind": "dir", **common}
        elif stat.S_ISREG(st.st_mode):
            entries[rel] = {"kind": "file", "size": st.st_size, "sha256": _hash_file(path), **common}
            key = (st.st_dev, st.st_ino)
            if key not in inode_groups:
                charged_once += st.st_size
            inode_groups.setdefault(key, []).append(rel)
            total_logical += st.st_size
        else:
            raise ValueError(f"unsupported corpus type: {rel}")
    # Singleton groups are retained to reveal accidental equality via hardlinking.
    groups = sorted([sorted(g) for g in inode_groups.values()])
    return {
        "entries": entries,
        "hardlink_partition": groups,
        "entries_total": len(entries),
        "file_count": sum(x["kind"] == "file" for x in entries.values()),
        "logical_bytes": total_logical,
        "unique_inode_charged_bytes": charged_once,
    }


def assess(corpora: Path, destination: Path) -> dict:
    original = physical_tree(corpora / "combined")
    candidate = physical_tree(destination)
    source = physical_tree(corpora / "dedup_links")
    alias = sorted(("hardlink.dat", "real.dat"))
    source_links = alias in source["hardlink_partition"]
    historical_copy_links = [f"dedup_links/{x}" for x in alias] in original["hardlink_partition"]
    heldout_links = [f"dedup_links/{x}" for x in alias] in candidate["hardlink_partition"]
    content_same = original["entries"] == candidate["entries"]
    expected_groups = sorted(
        sorted([f"{group}/{rel}" for rel in members])
        for group in SUBTREES
        for members in physical_tree(corpora / group)["hardlink_partition"]
    )
    expected_groups.extend([[name] for name in BINARY_FILES])
    expected_groups.sort()
    expected_partition = candidate["hardlink_partition"] == expected_groups
    result = {
        "source_hardlink_pair": source_links,
        "historical_combined_hardlink_pair": historical_copy_links,
        "heldout_combined_hardlink_pair": heldout_links,
        "typed_member_snapshots_equal": content_same,
        "heldout_partition_matches_sources": expected_partition,
        "legacy_file_count": original["file_count"],
        "heldout_file_count": candidate["file_count"],
        "legacy_logical_bytes": original["logical_bytes"],
        "heldout_logical_bytes": candidate["logical_bytes"],
        "legacy_unique_inode_charged_bytes": original["unique_inode_charged_bytes"],
        "heldout_unique_inode_charged_bytes": candidate["unique_inode_charged_bytes"],
        "distinct_physical_hardlink_groups_legacy": sum(len(g) > 1 for g in original["hardlink_partition"]),
        "distinct_physical_hardlink_groups_heldout": sum(len(g) > 1 for g in candidate["hardlink_partition"]),
        "verdict": "PASS" if (source_links and not historical_copy_links and heldout_links and content_same and expected_partition) else "FAIL",
    }
    return result


def _git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true", help="generate real source corpora in a temporary directory")
    ap.add_argument("--corpora", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--expected-generator-blob", default="2668948a64a03fc7f2b7c97fd97c8e0696aa9bee")
    args = ap.parse_args()
    if args.generate == bool(args.corpora):
        ap.error("select exactly one of --generate or --corpora")
    blob = _git("hash-object", "benchmarks/universal_bench.py")
    if blob != args.expected_generator_blob:
        raise RuntimeError(f"generator source changed: {blob}")
    with tempfile.TemporaryDirectory(prefix="cmpct-o44-") as work:
        if args.generate:
            from . import universal_bench as universal
            root = Path(work) / "corpora"
            root.mkdir()
            universal.CORP = root
            universal.make_corpora()
        else:
            root = args.corpora
        destination = Path(work) / "heldout-combined"
        build_nonfrozen_combined(root, destination)
        result = assess(root, destination)
    result["source_head"] = _git("rev-parse", "HEAD")
    result["generator_git_blob"] = blob
    result["evidence_class"] = "research-only; no archive performance or release credit"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["verdict"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
