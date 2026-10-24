#!/usr/bin/env python3
"""O14 cross-host referee. Scientific falsification is a valid green job result."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re


HOSTS = ("ubuntu-24.04", "macos-14", "windows-2025")
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")


def check_sha(value: object) -> None:
    assert isinstance(value, str) and HEX_SHA.fullmatch(value), value


def all_equal(values) -> bool:
    return len(set(values)) == 1


def decide(root: Path, source_sha: str) -> dict:
    observed = {}
    for host in HOSTS:
        path = root / ("o14-" + host + "-" + source_sha) / "o14-result.json"
        assert path.is_file(), ("missing platform artifact", host, path)
        item = json.loads(path.read_text())
        assert item["schema"] == "cmpct-v031-crosshost-mode-o14-v1"
        assert item["source_sha"] == source_sha
        assert item["repeat_count_per_variant"] == 2
        assert item["only_index_modes_changed"] is True
        assert item["product_code_modified"] is False
        assert item["research_only"] is True
        for v in ("baseline", "mode_only"):
            sub = item[v]
            for key in ("archive_sha256", "physical_sha256", "index_digest_ignoring_modes"):
                check_sha(sub[key])
        assert item["baseline"]["physical_sha256"] == item["mode_only"]["physical_sha256"]
        assert (
            item["baseline"]["index_digest_ignoring_modes"]
            == item["mode_only"]["index_digest_ignoring_modes"]
        )
        observed[host] = item

    fixtures = [
        tuple((f["path"], f["type"], f["size"], f["sha256"]) for f in observed[h]["fixture"])
        for h in HOSTS
    ]
    assert all_equal(list(map(repr, fixtures))), "source logical members differ across hosts"
    member_sha = [observed[h]["baseline"]["member_sha256"] for h in HOSTS]
    assert all_equal(list(map(repr, member_sha))), "roundtrip member bytes diverge"
    mode_rows = {
        h: {r["path"]: r["mode"] for r in observed[h]["baseline"]["rows"]}
        for h in HOSTS
    }
    baseline = {h: observed[h]["baseline"]["archive_sha256"] for h in HOSTS}
    portable = {h: observed[h]["mode_only"]["archive_sha256"] for h in HOSTS}
    physical = {h: observed[h]["mode_only"]["physical_sha256"] for h in HOSTS}
    nonmode = {
        h: observed[h]["mode_only"]["index_digest_ignoring_modes"] for h in HOSTS
    }
    index_only_modes = all_equal(list(nonmode.values()))
    physical_equal = all_equal(list(physical.values()))
    portable_equal = all_equal(list(portable.values()))
    modes_differ = not all_equal(list(map(repr, mode_rows.values())))
    baseline_diverges = not all_equal(list(baseline.values()))
    if baseline_diverges and modes_differ and portable_equal and index_only_modes and physical_equal:
        decision = "H1_SUPPORTED_IN_TESTED_THREE_HOST_CORPUS"
    elif baseline_diverges and not portable_equal:
        decision = "H1_FALSIFIED_OR_INSUFFICIENT_MODE_EXPLANATION"
    elif not baseline_diverges:
        decision = "BASELINE_NOT_REPRODUCED_IN_THIS_COURT"
    else:
        decision = "INDETERMINATE"
    result = {
        "schema": "cmpct-v031-crosshost-mode-o14-referee-v1",
        "source_sha": source_sha,
        "hosts": list(HOSTS),
        "source_logical_members_equal": True,
        "baseline_sha256": baseline,
        "mode_only_sha256": portable,
        "baseline_modes": mode_rows,
        "baseline_diverges": baseline_diverges,
        "modes_differ": modes_differ,
        "mode_only_archive_equal": portable_equal,
        "mode_only_physical_equal": physical_equal,
        "non_mode_index_equal": index_only_modes,
        "decision": decision,
        "limitation": (
            "Two regular files and one directory only; normalized mode changes "
            "archive semantics; no full-product portable-mode promise, installed-wheel "
            "platform determinism or release claim."
        ),
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--sha", default=os.environ.get("EVIDENCE_HEAD"), required=False)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    assert args.sha and len(args.sha) == 40
    result = decide(args.root, args.sha)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
