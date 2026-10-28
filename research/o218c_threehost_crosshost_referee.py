#!/usr/bin/env python3
"""Validate independent O218c cross-host CI result receipts."""
import argparse
import hashlib
import json
from pathlib import Path
from o218c_threehost_independent_referee import check

def validate(directory):
    rows = {}
    for path in directory.glob("o218c-*/raw.json"):
        data = json.loads(path.read_text())
        result = check(data, path.parent)
        host = result["host"]
        if host in rows:
            raise ValueError("duplicate host")
        receipt = json.loads((path.parent / "referee.json").read_text())
        if receipt["receipt_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("receipt identity mismatch")
        if receipt["forgeries_rejected"] != 8:
            raise ValueError("host controls incomplete")
        rows[host] = (data, result, (path.parent / "source-head.txt").read_text().strip())
    if set(rows) != {"linux", "darwin", "win32"}:
        raise ValueError("all three operating systems required")
    if len({r[2] for r in rows.values()}) != 1:
        raise ValueError("source HEAD mismatch")
    for host, (data, _, _) in rows.items():
        profiles = {(m["count"], m["owners"]): (m["archive_sha256"], m["logical_sha256"])
                    for m in data["profiles"]}
        checks = {(c["case"], tuple(c["outcome"])) for c in data["semantics"]["named_cases"]}
        rows[host] = (profiles, checks, rows[host][1])
    first = rows["linux"]
    for host in ("darwin", "win32"):
        if rows[host][0] != first[0] or rows[host][1] != first[1]:
            raise ValueError("cross-platform archive or diagnostic mismatch")
    success = all(row[2]["decision"] == "HOST_C_EXTENSION_VIABLE" for row in rows.values())
    return {"decision": "PORTABLE_C_EXTENSION_RESEARCH_ROUTE" if success else "PORTABILITY_OR_ECONOMICS_NOT_PROVEN",
            "hosts": sorted(rows), "source_consistent": True, "wire_consistent": True,
            "timed_opens": sum(row[2]["timed_opens"] for row in rows.values()),
            "by_host": {host: row[2] for host, row in rows.items()},
            "scope": "CPython3.11 hosted full Reader research, not a release or packaging verdict"}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("directory", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    report = validate(a.directory)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("O218C_CROSS_HOST_REPLAY=PASS", report["decision"])
