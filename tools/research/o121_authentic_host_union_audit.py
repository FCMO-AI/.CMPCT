#!/usr/bin/env python3
"""O121: audit *unchanged* O117 same-archive probe on original and Win32/APFS union Readers.

This is scientific outcome validation. A green test means the proposed unmerged
host guard rejected the known alias before any member write, not a release claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(manifest: Path, archive: Path, baseline: Path, candidate: Path) -> dict:
    m, b, c = (_read(p) for p in (manifest, baseline, candidate))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert m["archive_sha256"] == digest, "authentic archive changed across producer/consumers"
    assert set(m["members"]) == {"Report.txt", "report.txt", "other.txt"}, "unexpected corpus"
    assert m["members"]["Report.txt"]["sha256"] != m["members"]["report.txt"]["sha256"]
    assert b["archive_sha256"] == c["archive_sha256"] == digest
    assert b["reader_exact_all_members"] is True
    assert c["reader_exact_all_members"] is True

    # Both Readers ran on the same target filesystem. Host behavior is observed
    # with real temporary file names, not inferred from operating system names.
    assert b["host_case_alias_observed"] == c["host_case_alias_observed"], (
        "control and candidate disagree about target filesystem case behavior"
    )
    host_alias = b["host_case_alias_observed"]
    assert isinstance(host_alias, bool)
    if host_alias:
        assert b["verdict"] == "CONFIRMED_SILENT_HOST_CASE_ALIAS_LOSS", b
        assert b["extractall_error"] is None, b
        assert b["physical_count"] == 2, b
        assert b["Report_report_same_physical_file"] is True, b
        assert c["verdict"] == "EXTRACTION_REJECTED_ARCHIVE", c
        assert c["extractall_error"], c
        assert c["physical_count"] == 0, (
            "candidate refusal is too late: output members were already published", c
        )
        assert c["physical_file_inventory"] == [], c
        decision = "O121_EARLY_REFUSAL_REHABILITATES_O117_ON_ALIASING_HOST"
    else:
        assert b["verdict"] == c["verdict"] == "COMPLETE_SOURCE_TREE_FIDELITY", (b,c)
        for result in (b,c):
            assert result["physical_count"] == 3, result
            assert result["extractall_error"] is None, result
            assert all(result["member_bytes_equal_source"].values()), result
        decision = "O121_INHERITED_EXACT_FIDELITY_PRESERVED_ON_CASE_SENSITIVE_HOST"

    return {
        "decision": decision,
        "archive_sha256": digest,
        "host_case_alias_observed": host_alias,
        "baseline_verdict": b["verdict"],
        "candidate_verdict": c["verdict"],
        "baseline_file_count": b["physical_count"],
        "candidate_file_count": c["physical_count"],
        "scope": "unmerged #336 Reader candidate versus unchanged v0.31 at identical O117 physical archive",
        "limitations": (
            "static ordinary filesystem; no native Unicode/8.3 collation completeness, "
            "TOCTOU/reparse guarantees, ABBA, release or memory performance credit"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = audit(
        args.artifact / "manifest.json",
        args.artifact / "casefold-source.cmpct",
        args.baseline,
        args.candidate,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    print("O121_INDEPENDENT_SAME_ARCHIVE_AUDIT_PASS")


if __name__ == "__main__":
    main()
