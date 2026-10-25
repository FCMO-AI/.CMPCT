#!/usr/bin/env python3
"""O46 independent three-host referee; scientific H3 is a valid conclusion."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "cmpct-v031-crosshost-heldout-multitype-o46-v1"
HOSTS = ("ubuntu-24.04", "macos-14", "windows-2025")
ARMS = ("baseline", "o14_mode_only", "all_kind_mode")
SHA = re.compile(r"^[0-9a-f]{64}$")


def judge(root: Path, head: str) -> dict:
    receipts = {}
    for host in HOSTS:
        p = root / ("o46-" + host + "-" + head) / "o46-host.json"
        assert p.is_file(), ("missing actual host run", host, str(p))
        d = json.loads(p.read_text())
        assert d["schema"] == SCHEMA and d["source_sha"] == head
        assert d["builds_per_arm"] == 2 and d["research_only"] is True
        assert d["product_code_modified"] is False
        assert d["inherited_o14_oracle_blob"] == "c439829f358ef92a4ae71a7aaa4d9bbe8d83718a"
        assert len(d["fixture"]["entries"]) >= 12
        assert d["fixture"]["file_equivalence_groups"] == [
            ["README.md"], ["aliases/ref.bin", "shared/owner.bin"],
            ["bin/runner.sh"], ["empty.txt"], ["independent/copy.bin"],
            ["nested/sub/payload.bin"]
        ], ("source hardlink equivalence partition", host)
        assert set(d["outcomes"]) == set(ARMS)
        for arm in ARMS:
            v = d["outcomes"][arm]
            for key in ("archive_sha256", "physical_sha256", "index_digest_ignoring_modes"):
                assert SHA.fullmatch(v[key]), (host, arm, key)
            assert v["roundtrip"] == "PASS"
            assert v["hardlink_alias_identity"] is True
            assert v["equal_bytes_independent_identity"] is True
            assert v["verified_count"] >= 1
            assert len(v["index_rows"]) >= 12
        base = d["outcomes"]["baseline"]
        for arm in ARMS[1:]:
            cand = d["outcomes"][arm]
            assert cand["physical_sha256"] == base["physical_sha256"], (
                "physical payload changed in mode oracle", host, arm)
            assert cand["index_digest_ignoring_modes"] == base[
                "index_digest_ignoring_modes"], ("nonmode index changed", host, arm)
            assert cand["member_sha256"] == base["member_sha256"]
        receipts[host] = d

    # No cross-host credit if the logical fixture/tree is not the same.
    logical = [d["fixture"]["logical_digest"] for d in receipts.values()]
    assert len(set(logical)) == 1, "different logical source input"
    partitions = [d["fixture"]["file_equivalence_groups"] for d in receipts.values()]
    assert all(x == partitions[0] for x in partitions), "different hardlink topology"
    outcomes = {arm: {host: receipts[host]["outcomes"][arm]["archive_sha256"]
                      for host in HOSTS} for arm in ARMS}
    physical = {arm: {host: receipts[host]["outcomes"][arm]["physical_sha256"]
                     for host in HOSTS} for arm in ARMS}
    nonmode = {arm: {host: receipts[host]["outcomes"][arm][
        "index_digest_ignoring_modes"] for host in HOSTS} for arm in ARMS}
    equal = lambda mapping: len(set(mapping.values())) == 1
    baseline_diverges = not equal(outcomes["baseline"])
    o14_equal = equal(outcomes["o14_mode_only"])
    all_kind_equal = equal(outcomes["all_kind_mode"])
    all_phys_equal = all(equal(physical[arm]) for arm in ARMS)
    all_nonmode_equal = all(equal(nonmode[arm]) for arm in ARMS)
    if not baseline_diverges:
        result = "BASELINE_NOT_REPRODUCED_IN_HELDOUT"
    elif o14_equal and all_phys_equal and all_nonmode_equal:
        result = "H1_TRANSFER_IN_TESTED_SCOPE"
    elif not o14_equal and all_kind_equal and all_phys_equal and all_nonmode_equal:
        result = "H2_MISSING_HARDLINK_MODE_KIND_IN_TESTED_SCOPE"
    else:
        result = "H3_NONMODE_OR_NONDETERMINISTIC_HOST_DIFFERENCE"
    return {
        "schema": "cmpct-v031-o46-three-host-referee-v1", "source_sha": head,
        "hosts": list(HOSTS), "logical_input_equal": True,
        "hardlink_equivalence_equal": True,
        "complete_archive_sha256": outcomes, "physical_sha256": physical,
        "non_mode_index_sha256": nonmode,
        "baseline_diverges": baseline_diverges, "o14_mode_only_archive_equal": o14_equal,
        "all_kind_mode_archive_equal": all_kind_equal,
        "all_phys_equal": all_phys_equal, "all_nonmode_index_equal": all_nonmode_equal,
        "decision": result, "product_code_modified": False, "research_only": True,
        "limitation": "Held-out synthetic corpus only; changed metadata semantics; not a shipping mode, benchmark result or release claim."
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--sha", required=True)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    assert len(a.sha) == 40 and all(c in "0123456789abcdef" for c in a.sha)
    verdict = judge(a.root, a.sha)
    a.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, sort_keys=True))
