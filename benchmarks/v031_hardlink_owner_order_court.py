#!/usr/bin/env python3
"""Real revision-24 Builder/Reader hardlink ordering court; see companion prereg."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def case(root: Path, alias_name: str, *, predicted_late_owner: bool) -> dict:
    case_dir = root / ("case-" + alias_name.replace(".", "dot").replace("!", "bang").replace("-", "dash"))
    source = case_dir / "source"
    source.mkdir(parents=True)
    owner = source / "a" / "owner.bin"
    owner.parent.mkdir()
    original = (b"hardlink-order-exact-source\\x00" + bytes(range(256))) * 9
    # Deliberately keep source owner below a/ while the alias is at the root.
    owner.write_bytes(original)
    alias = source / alias_name
    os.link(owner, alias)
    assert os.stat(owner).st_ino == os.stat(alias).st_ino
    archive = case_dir / "source.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    observed = {
        "alias": alias_name,
        "predicted_late_owner": predicted_late_owner,
        "archive_sha256": sha(archive.read_bytes()),
        "logical_sha256": sha(original),
        "archive_bytes": archive.stat().st_size,
        "preflight": None,
        "verify": None,
        "read_alias_sha256": None,
        "rows": [],
        "baseline": None,
        "dependency_first": None,
    }
    observed["preflight"] = preflight_archive(archive)
    with CMPCT(archive) as reader:
        observed["rows"] = [
            [row[0], row[1], row[6][0] if row[1] == K_HARDLINK else ""]
            for row in reader.files
        ]
        assert reader.by[alias_name][1] == K_HARDLINK
        assert reader.by[alias_name][6][0] == "a/owner.bin"
        assert reader.by["a/owner.bin"][1] == K_FILE
        observed["verify"] = reader.verify()
        assert reader.read(alias_name) == original
        observed["read_alias_sha256"] = sha(reader.read(alias_name))
        target = case_dir / "extract-baseline"
        try:
            reader.extractall(target)
        except Exception as exc:
            observed["baseline"] = {"outcome": "REJECT", "error_type": type(exc).__name__, "error": str(exc)}
        else:
            a, b = target / alias_name, target / "a" / "owner.bin"
            exact = a.read_bytes() == original and b.read_bytes() == original
            same_inode = os.stat(a).st_ino == os.stat(b).st_ino
            observed["baseline"] = {"outcome": "ACCEPT", "exact": exact, "same_inode": same_inode}
        # Scientific counterfactual; never changes archive bytes or the canonical writer.
        reader.files = sorted(reader.files, key=lambda row: (row[1] == K_HARDLINK, row[0]))
        target = case_dir / "extract-dependency-first"
        reader.extractall(target)
        a, b = target / alias_name, target / "a" / "owner.bin"
        observed["dependency_first"] = {
            "exact": a.read_bytes() == original and b.read_bytes() == original,
            "same_inode": os.stat(a).st_ino == os.stat(b).st_ino,
        }
        assert observed["dependency_first"] == {"exact": True, "same_inode": True}
    return observed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-order-bug", action="store_true")
    parser.add_argument("--expect-fixed", action="store_true")
    args = parser.parse_args()
    if args.expect_order_bug == args.expect_fixed:
        parser.error("select exactly one baseline or candidate expectation")
    if os.name != "posix":
        raise SystemExit("POSIX filesystem required; cannot claim cross-platform")
    cases = [("a!.bin", True), ("a-.bin", True), ("a..bin", True),
             ("a0.bin", False), ("z.bin", False)]
    with tempfile.TemporaryDirectory(prefix="cmpct-v031-hardlink-owner-") as td:
        results = [case(Path(td), alias, predicted_late_owner=late) for alias, late in cases]
    outcomes = [x["baseline"]["outcome"] for x in results]
    expected = ["ACCEPT"] * 5 if args.expect_fixed else ["REJECT"] * 3 + ["ACCEPT"] * 2
    identity_ok = all(x["read_alias_sha256"] == x["logical_sha256"] for x in results)
    controls_ok = all(x["baseline"].get("exact") is True and x["baseline"].get("same_inode") is True
                      for x in results if x["baseline"]["outcome"] == "ACCEPT")
    negative_reason_ok = all("hardlink target not yet extracted" in x["baseline"].get("error", "")
                             for x in results if x["baseline"]["outcome"] == "REJECT")
    verdict = "PASS" if outcomes == expected and identity_ok and controls_ok and negative_reason_ok else "FAIL"
    print(json.dumps({"schema": "cmpct-hardlink-order-court-v1",
                      "source": "agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b",
                      "expect": "fixed" if args.expect_fixed else "baseline",
                      "outcomes": outcomes, "expected": expected, "cases": results,
                      "verdict": verdict}, indent=2, default=str))
    if verdict != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
