#!/usr/bin/env python3
"""J24P06 independent ZIP/installed-file referee. No CMPCT code imported.

Read actual wheels and installed files, recompute full PEP427 RECORD identities,
and independently verify the source-preserving native / source-replacing Python
split. This referee has its own code and is not an alias for the instrument.
"""
from __future__ import annotations
import argparse, base64, csv, hashlib, io, json, sys, zipfile
from pathlib import Path

NAME = "cmpct-0.30.0-cp311-cp311-macosx_10_12_universal2.whl"
LIB = "cmpct/cmpct_core.cpython-311-darwin.so"
MODULE = "cmpct/native_codec.py"
RECORD = "cmpct-0.30.0.dist-info/RECORD"
CONTROL = {"original", "disjoint_purelib", "disjoint_platlib"}
COLLISION = {"purelib_before", "purelib_after", "platlib_before", "platlib_after"}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)

def referee(root: Path, receipt: dict) -> dict:
    require(set(receipt["cases"]) == CONTROL | COLLISION, "wrong case family")
    results = {}
    for label, reported in receipt["cases"].items():
        path = root / "wheels" / label / NAME
        require(path.is_file(), f"{label}: missing original wheel")
        require(digest(path.read_bytes()) == reported["wheel_sha256"],
                f"{label}: wheel receipt SHA mismatch")
        with zipfile.ZipFile(path) as z:
            members = z.infolist()
            require(len(members) == len({m.filename for m in members}), "duplicate raw member")
            rows = list(csv.reader(io.StringIO(z.read(RECORD).decode("utf8"))))
            rmap = {r[0]: r for r in rows}
            require(len(rows) == len(rmap) == len(members), "bad member/RECORD cardinality")
            for member in members:
                require(member.filename in rmap, "unrecorded ZIP member")
                if member.filename == RECORD:
                    require(rmap[RECORD][1:] == ["", ""], "RECORD self-hash invalid")
                    continue
                data = z.read(member)
                expected = "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
                require(rmap[member.filename][1:] == [expected, str(len(data))],
                        f"{label}: RECORD mismatch for {member.filename}")
            raw_native, raw_source = z.read(LIB), z.read(MODULE)
        require(digest(raw_native) == reported["zip_native_sha256"], f"{label}: native source mismatch")
        require(digest(raw_source) == reported["zip_python_sha256"], f"{label}: source code mismatch")
        npath = root / "installed" / label / LIB
        mpath = root / "installed" / label / MODULE
        require(npath.is_file() and mpath.is_file(), f"{label}: missing installed physical files")
        actual_native, actual_source = npath.read_bytes(), mpath.read_bytes()
        require(digest(actual_native) == reported["installed"]["native"]["sha256"],
                f"{label}: installed native receipt mismatch")
        require(digest(actual_source) == reported["installed"]["python_module"]["sha256"],
                f"{label}: installed source receipt mismatch")
        require(actual_native == raw_native, f"{label}: unexpected native mutation")
        expected_match = label in CONTROL
        require((actual_source == raw_source) == expected_match,
                f"{label}: wrong installed Python identity")
        require(reported["whole_package_identity_pass"] == expected_match,
                f"{label}: incorrect whole-package assertion")
        require(reported["native_only_identity_pass"] is True,
                f"{label}: native-only assertion changed")
        inst_record = root / "installed" / label / RECORD
        require(inst_record.is_file(), f"{label}: installed RECORD missing")
        rows_installed = list(csv.reader(inst_record.read_text(encoding="utf8").splitlines()))
        source_rows = [r for r in rows_installed if r and r[0] == MODULE]
        require(len(source_rows) == (1 if expected_match else 2),
                f"{label}: expected same-path RECORD multiplicity differs")
        result = {"native_matches_original": True,
                  "python_matches_original": expected_match,
                  "installed_record_same_path_count": len(source_rows),
                  "wheel_member_count": len(members)}
        results[label] = result
    return {"schema": "cmpct-j24p06-detached-referee-v1",
            "checks": len(results), "all_source_record_members_verified": True,
            "native_only_proves_complete_package": False,
            "cases": results}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    data = json.loads((args.root / "court.json").read_text(encoding="utf8"))
    report = referee(args.root, data)
    # An independent receipt tamper must not be accepted.
    tampered = json.loads(json.dumps(data))
    tampered["cases"]["original"]["wheel_sha256"] = "0" * 64
    try:
        referee(args.root, tampered)
    except AssertionError:
        report["tamper_rejected"] = True
    else:
        raise AssertionError("tampered wheel digest was accepted")
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(text)
    if args.output:
        args.output.write_text(text, encoding="utf8")

if __name__ == "__main__":
    main()
