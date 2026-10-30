#!/usr/bin/env python3
"""Independent J24P05 artifact referee — wheel and installed bytes, no CMPCT import.

Accepts the *original hosted GitHub Actions artifact ZIP* from either host.
Recomputes raw wheel/RECORD checksums and the actual installed native payload
identity independently of the claimed court.json booleans or CMPCT validator.
Never imports, loads or executes an altered native component.
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

NATIVE = "cmpct/cmpct_core.cpython-311-darwin.so"
RECORD = "cmpct-0.30.0.dist-info/RECORD"
INERT = b"J24P05_INERT_CASEFOLD_BYTES_NO_NATIVE_CODE\n"
CASES = {"original", "unrelated", "collision_before", "collision_after",
         "alias_parent", "alias_dot", "alias_repeated_separator", "alias_internal_dot"}
ALIASES = {"alias_parent", "alias_dot", "alias_repeated_separator", "alias_internal_dot"}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hard_check(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError(message)

def check_wheel(data: bytes, label: str) -> tuple[dict[str, bytes], list[str]]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        paths = [i.filename for i in infos]
        hard_check(len(paths) == len(set(paths)), label + ": duplicated raw member")
        hard_check(len(paths) >= 4, label + ": insufficient members")
        members = {name: z.read(name) for name in paths}
    hard_check(RECORD in members and NATIVE in members, label + ": missing RECORD/native")
    records = list(csv.reader(io.StringIO(members[RECORD].decode("utf-8"))))
    hard_check(all(len(row) == 3 for row in records), label + ": bad RECORD columns")
    names = [row[0] for row in records]
    hard_check(len(names) == len(set(names)) and set(names) == set(paths), label + ": RECORD path mismatch")
    for name, stored, length in records:
        if name == RECORD:
            hard_check((stored,length) == ("",""), label + ": self-hashed RECORD")
            continue
        hard_check(stored == "sha256=" +
                   base64.urlsafe_b64encode(hashlib.sha256(members[name]).digest()).decode("ascii").rstrip("="),
                   label + ": RECORD sha256 mismatch for " + name)
        hard_check(length.isdecimal() and int(length) == len(members[name]), label + ": RECORD length mismatch")
    return members, paths

def verify(artifact: Path) -> dict:
    raw = artifact.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [i.filename for i in z.infolist()]
        hard_check(len(names) == len(set(names)), "duplicate artifact ZIP entries")
        hard_check("court.json" in names, "missing court")
        court = json.loads(z.read("court.json"))
        hard_check(court.get("schema") == "cmpct-j24p05-path-equivalence-court-v1", "bad court schema")
        cases = court["cases"]
        hard_check(set(cases) == CASES, "missing/unexpected case")
        host = court["host"]
        system = host["system"]
        hard_check(system in ("Darwin","Linux"), "unsupported host for this court")
        hard_check(host["casefold_equivalent"] == (system == "Darwin"),
                   "host expected case sensitivity not observed (narrow claim)")
        source = court["source"]
        hard_check(source["inert_sha256"] == digest(INERT), "inert source SHA mismatch")
        verified = {}
        observed_installed = {}
        original_path = next((n for n in names if n.startswith("original/") and n.endswith(".whl")), None)
        hard_check(original_path is not None, "missing positive control")
        original_entries, _ = check_wheel(z.read(original_path), "original")
        baseline = original_entries[NATIVE]
        hard_check(digest(baseline) == source["primary_native_sha256"], "baseline primary SHA mismatch")
        for label in sorted(CASES):
            wheel_matches = [n for n in names if n.startswith(label + "/") and n.endswith(".whl")]
            hard_check(len(wheel_matches) == 1, label + ": missing physical wheel")
            wheel_data = z.read(wheel_matches[0])
            row = cases[label]
            hard_check(digest(wheel_data) == row["wheel_sha256"] and len(wheel_data) == row["size"],
                       label + ": physical wheel receipt mismatch")
            entries, paths = check_wheel(wheel_data,label)
            hard_check(row["gate"]["pass"] is True, label + ": unchanged gate did not admit")
            hard_check(digest(entries[NATIVE]) == row["gate"]["native_sha256"], label + ": gate native SHA claim invalid")
            if label == "original":
                baseline = entries[NATIVE]
                hard_check(digest(baseline) == source["primary_native_sha256"], "baseline primary SHA mismatch")
            else:
                hard_check(entries[NATIVE] == baseline, label + ": inherited native bytes changed before installation")
            if label in ALIASES | {"collision_before","collision_after"}:
                hard_check(INERT in entries.values(), label + ": missing controlled inert collision")
                hard_check(row["installed_path_oracle"], label + ": path identity oracle missed collision")
            else:
                hard_check(not row["installed_path_oracle"], label + ": positive oracle false red")
            installed_path = "installed-native/" + label + ".bin"
            hard_check(installed_path in names, label + ": missing physical installed artifact")
            installed_bytes = z.read(installed_path)
            info = row["pip"]
            hard_check(info["returncode"] == 0, label + ": pip installation red")
            hard_check(info["installed_native_exists"] is True and
                       info["installed_native_sha256"] == digest(installed_bytes) and
                       info["installed_native_nbytes"] == len(installed_bytes),
                       label + ": installed byte receipt mismatch")
            eq_original, eq_inert = installed_bytes == baseline, installed_bytes == INERT
            hard_check(eq_original != eq_inert, label + ": installed data neither original nor inert")
            hard_check(info["primary_native_retained"] is eq_original and
                       info["inert_collision_won"] is eq_inert, label + ": self-report contradicted actual installed data")
            expected_overwrite = label in ALIASES or (system == "Darwin" and label == "collision_after")
            hard_check(eq_inert == expected_overwrite, label + ": host identity outcome changed")
            observed_installed[label] = {"actual_bytes":len(installed_bytes),
                                         "actual_sha256":digest(installed_bytes),
                                         "equivalent_to":("inert" if eq_inert else "original"),
                                         "aliases_baseline_path": bool(expected_overwrite)}
            verified[label] = {"wheel_bytes":len(wheel_data),
                               "wheel_sha256":digest(wheel_data),
                               "raw_wheel_members":len(paths),
                               "record_integrity":"verified",
                               "installed":observed_installed[label]}
    return {"schema":"cmpct-j24p05-detached-referee-v1",
            "artifact_zip_sha256":digest(raw), "artifact_zip_bytes":len(raw),
            "system":system, "casefold_equivalent":host["casefold_equivalent"],
            "native_original_sha256":digest(baseline), "inert_sha256":digest(INERT),
            "cases_verified":len(verified), "overwrite_count":sum(x["aliases_baseline_path"] for x in observed_installed.values()),
            "all_zip_and_record_checks_pass":True,
            "all_installed_byte_checks_pass":True, "details":verified,
            "claim_scope":"detached original artifact + wheel RECORD + physical installed byte identity; not real production wheel or executable exploit"}

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("original_hosted_artifact_zip", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        result = verify(args.original_hosted_artifact_zip)
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile, KeyError, TypeError, AssertionError) as exc:
        print(json.dumps({"pass":False,"reason":str(exc)},sort_keys=True))
        return 2
    body = json.dumps(result, sort_keys=True, indent=2)+"\n"
    if args.output:
        args.output.write_text(body)
    print(body)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
