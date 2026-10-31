#!/usr/bin/env python3
"""Detached standard-library referee for J24P15; never imports CMPCT or experiment."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import statistics

EXPECTED = ("small_config", "incompressible", "nested_deflate",
            "shared_blocks", "mixed_records")
RUN_ORDER = ("26.03", "26.05", "26.05", "26.03") * 2
ASSETS = {
    "26.03": "dc99eff5008f1ab79bd7084c68513701547a808a89502bf4133683535ab3c695",
    "26.05": "22cf82fcc6eb7474f1d5bb4f02c0f8ebd573a718089d6833dc30f8350a3b232e",
}


def digest(path: Path) -> str:
    obj = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            obj.update(chunk)
    return obj.hexdigest()


def source_manifest(root: Path) -> list[dict]:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AssertionError("symlink not covered by regular-file court")
        if path.is_file():
            entries.append({"path": path.relative_to(root).as_posix(),
                            "size": path.stat().st_size, "sha256": digest(path)})
    if not entries:
        raise AssertionError("empty source tree")
    return entries


def tree_hash(entries: list[dict]) -> str:
    return hashlib.sha256(json.dumps(entries, sort_keys=True,
                      separators=(",", ":")).encode()).hexdigest()


def validate(d: dict, root: Path, head: str) -> list[dict]:
    assert d["schema"] == "cmpct-j24p15-upstream-7zip-delta-v1"
    assert d["source_commit"] == head and re.fullmatch("[0-9a-f]{40}", head)
    assert d["research_credit"] is True and d["product_credit"] is False
    assert d["command_flags"] == ["a", "-t7z", "-m0=lzma2", "-mx=9", "-ms=on"]
    assert tuple(d["order"]) == RUN_ORDER
    assert d["asset_sha256"] == ASSETS
    assert set(d["tools"]) == set(ASSETS)
    for version in ASSETS:
        obj = d["tools"][version]
        assert obj["version"] == version
        assert version in obj["identity_line"] and "7-Zip" in obj["identity_line"]
        assert re.fullmatch("[a-f0-9]{64}", obj["binary_sha256"])
    assert tuple(x["family"] for x in d["families"]) == EXPECTED
    summaries = []
    for family in d["families"]:
        name = family["family"]
        physical = root / name
        src = source_manifest(physical / "input")
        source_sha = tree_hash(src)
        assert family["source_tree_sha256"] == source_sha
        assert family["source_members"] == len(src)
        assert family["source_logical_bytes"] == sum(i["size"] for i in src)
        assert len(family["runs"]) == len(RUN_ORDER)
        for ix, (version, run) in enumerate(zip(RUN_ORDER, family["runs"], strict=True)):
            assert run["version"] == version and run["order_index"] == ix
            for name_ns in ("create_wall_ns", "extract_wall_ns"):
                assert isinstance(run[name_ns], int) and 0 < run[name_ns] < 3_600_000_000_000
            archive = physical / f"{ix:02}-{version}" / "out.7z"
            assert archive.is_file()
            assert run["archive_bytes"] == archive.stat().st_size > 0
            assert run["archive_sha256"] == digest(archive)
            extracted = source_manifest(physical / f"{ix:02}-{version}" / "extract")
            assert extracted == src and run["extracted_tree_sha256"] == tree_hash(extracted)
        old = [r for r in family["runs"] if r["version"] == "26.03"]
        new = [r for r in family["runs"] if r["version"] == "26.05"]
        med = lambda entries, k: statistics.median(r[k] for r in entries)
        summaries.append({
            "family": name, "source_sha256": source_sha,
            "old_sizes": [r["archive_bytes"] for r in old],
            "new_sizes": [r["archive_bytes"] for r in new],
            "old_create_wall_ns_median": med(old, "create_wall_ns"),
            "new_create_wall_ns_median": med(new, "create_wall_ns"),
            "old_extract_wall_ns_median": med(old, "extract_wall_ns"),
            "new_extract_wall_ns_median": med(new, "extract_wall_ns"),
            "size_changed": set(r["archive_bytes"] for r in old) !=
                            set(r["archive_bytes"] for r in new),
            "ratio_new_old_median_create": med(new, "create_wall_ns") / med(old, "create_wall_ns")
        })
    return summaries


def hostile_tests(receipt: dict, root: Path, head: str) -> int:
    mutations = []
    a = copy.deepcopy(receipt)
    a["source_commit"] = "f" * 40
    mutations.append(a)
    a = copy.deepcopy(receipt)
    a["families"][0]["runs"][0]["archive_sha256"] = "0" * 64
    mutations.append(a)
    a = copy.deepcopy(receipt)
    a["families"][1]["runs"][3]["version"] = "26.05"
    mutations.append(a)
    a = copy.deepcopy(receipt)
    a["families"][2]["source_tree_sha256"] = "0" * 64
    mutations.append(a)
    a = copy.deepcopy(receipt)
    a["families"][3]["runs"][2]["create_wall_ns"] = -1
    mutations.append(a)
    a = copy.deepcopy(receipt)
    a["families"][4]["runs"][0]["archive_bytes"] += 1
    mutations.append(a)
    for ix, candidate in enumerate(mutations):
        try:
            validate(candidate, root, head)
        except (AssertionError, TypeError, KeyError, ValueError, OSError):
            continue
        raise AssertionError(f"hostile mutation {ix} incorrectly accepted")
    return len(mutations)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--work-root", required=True, type=Path)
    p.add_argument("--source-head", required=True)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    d = json.loads(a.receipt.read_text())
    summary = validate(d, a.work_root, a.source_head)
    attacks = hostile_tests(d, a.work_root, a.source_head)
    result = {"source_commit": a.source_head, "families": summary,
              "validated_archive_runs": len(EXPECTED) * len(RUN_ORDER),
              "hostile_receipt_mutations_rejected": attacks,
              "product_credit": False}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
