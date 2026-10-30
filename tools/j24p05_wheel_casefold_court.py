#!/usr/bin/env python3
"""J24P05: independent, inert wheel-name casefold/installed-path identity court.

No CMPCT native library is executed; Mach-O bytes come from J24P04's offline
synthetic fixture. The source-exact current gate runs before a real pip --target
installation on each host, recording both policy admission and physical path
identity. This is science, not a shipping archive or release gate.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_macos_wheel_physical_contract import good_fat, wheel as make_fixture_wheel
from j24p05_wheel_installed_path_oracle import inspect_wheel as path_oracle

SPEC = importlib.util.spec_from_file_location("j24p05_gate", ROOT / "tools" / "validate_macos_wheel_abi.py")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
NATIVE = "cmpct/cmpct_core.cpython-311-darwin.so"
RECORD = "cmpct-0.30.0.dist-info/RECORD"
NAME = "cmpct-0.30.0-cp311-cp311-macosx_10_12_universal2.whl"
INERT = b"J24P05_INERT_CASEFOLD_BYTES_NO_NATIVE_CODE\n"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build(root: Path, label: str, extra: str | None, before: bool) -> Path:
    folder = root / label
    folder.mkdir(parents=True, exist_ok=True)
    original = folder / NAME
    make_fixture_wheel(original, good_fat())
    if extra is None:
        return original
    with zipfile.ZipFile(original) as z:
        src = {info.filename: z.read(info) for info in z.infolist() if info.filename != RECORD}
    entries = {}
    if before:
        entries[extra] = INERT
    entries.update(src)
    if not before:
        entries[extra] = INERT
    rows = []
    for name, data in entries.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        rows.append([name, "sha256=" + digest, str(len(data))])
    rows.append([RECORD, "", ""])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    entries[RECORD] = buf.getvalue().encode("utf-8")
    with zipfile.ZipFile(original, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return original

def host_casefold(root: Path) -> bool:
    case = root / "caseprobe"
    case.mkdir()
    (case / "A").write_bytes(b"casefold")
    return (case / "a").exists()

def install(path: Path, root: Path, label: str) -> dict:
    target = root / ("installed-" + label)
    cmd = [sys.executable, "-m", "pip", "install", "--no-index", "--no-deps",
           "--no-compile", "--ignore-installed", "--target", str(target), str(path)]
    if platform.system() == "Linux":
        # A real macOS wheel is incompatible with this Linux host by default.
        # pip's explicit cross-platform target validates its actual install path
        # mapping while leaving the inert foreign Mach-O unexecuted.
        cmd[4:4] = ["--platform", "macosx_10_12_universal2", "--python-version", "3.11",
                    "--implementation", "cp", "--abi", "cp311", "--only-binary=:all:"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    actual = target / NATIVE
    raw = actual.read_bytes() if actual.is_file() else None
    record_path = target / "cmpct-0.30.0.dist-info" / "RECORD"
    record_native = None
    if record_path.is_file():
        rows = list(csv.reader(io.StringIO(record_path.read_text("utf-8"))))
        exact_rows = [{"path": row[0], "sha256_record": row[1], "size_record": row[2]}
                      for row in rows if len(row) == 3 and row[0] == NATIVE]
        portable_rows = [{"path": row[0], "sha256_record": row[1], "size_record": row[2]}
                         for row in rows if len(row) == 3 and row[0].casefold() == NATIVE.casefold()]
        physical_hash = ("sha256=" + base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
                         .decode().rstrip("=")) if raw is not None else None
        record_native = {
            "exact_rows": exact_rows,
            "portable_casefold_rows": portable_rows,
            "physical_sha256_record_form": physical_hash,
            "physical_size": str(len(raw)) if raw is not None else None,
            "exact_record_path_ambiguous": len(exact_rows) != 1,
            "portable_record_path_ambiguous": len(portable_rows) != 1,
            "any_exact_row_matches_physical": (any(
                row["sha256_record"] == physical_hash and
                row["size_record"] == str(len(raw))
                for row in exact_rows) if raw is not None else None),
        }
        custody = root / "installed-native"
        custody.mkdir(exist_ok=True)
        (custody / (label + ".RECORD.csv")).write_bytes(record_path.read_bytes())
    if raw is not None:
        # Preserve the *physical installed file* for detached comparison with
        # independently parsed wheel members, not only the self-reported SHA.
        custody = root / "installed-native"
        custody.mkdir(exist_ok=True)
        (custody / (label + ".bin")).write_bytes(raw)
    return {
        "returncode": p.returncode,
        "stdout_tail": p.stdout[-1000:],
        "stderr_tail": p.stderr[-1400:],
        "installed_native_exists": raw is not None,
        "installed_native_sha256": sha(raw) if raw is not None else None,
        "installed_native_nbytes": len(raw) if raw is not None else None,
        "primary_native_retained": raw == good_fat() if raw is not None else None,
        "inert_collision_won": raw == INERT if raw is not None else None,
        "installed_record_native": record_native,
    }

def run(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    equivalent_name = "cmpct/CMPCT_CORE.cpython-311-darwin.so"
    assert NATIVE.casefold() == equivalent_name.casefold()
    samples = {
        "original": build(root, "original", None, False),
        "unrelated": build(root, "unrelated", "cmpct/UNRELATED.txt", False),
        "collision_before": build(root, "collision_before", equivalent_name, True),
        "collision_after": build(root, "collision_after", equivalent_name, False),
        # Post-hoc local discovery, prospectively replicated by J24P05b host court.
        "alias_parent": build(root, "alias_parent", "cmpct/../" + NATIVE, False),
        "alias_dot": build(root, "alias_dot", "./" + NATIVE, False),
        "alias_repeated_separator": build(root, "alias_repeated_separator",
                                          "cmpct//" + NATIVE.split("/", 1)[1], False),
        "alias_internal_dot": build(root, "alias_internal_dot",
                                    "cmpct/./" + NATIVE.split("/", 1)[1], False),
    }
    result = {
        "schema": "cmpct-j24p05-path-equivalence-court-v1",
        "host": {"system": platform.system(), "release": platform.release(),
                 "machine": platform.machine(), "python": sys.version.split()[0],
                 "pip": subprocess.run([sys.executable, "-m", "pip", "--version"],
                                     capture_output=True, text=True).stdout.strip(),
                 "casefold_equivalent": host_casefold(root)},
        "source": {"gate_sha256": sha((ROOT / "tools" / "validate_macos_wheel_abi.py").read_bytes()),
                   "fixture_sha256": sha((ROOT / "tests" / "test_macos_wheel_physical_contract.py").read_bytes()),
                   "primary_native_sha256": sha(good_fat()),
                   "inert_sha256": sha(INERT)},
        "cases": {},
    }
    for label, path in samples.items():
        try:
            guard = GATE.inspect(path)
            verdict = {"pass": True, "native_sha256": guard["native_sha256"]}
        except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
            verdict = {"pass": False, "reason": str(exc)}
        result["cases"][label] = {
            "wheel": path.name, "wheel_sha256": sha(path.read_bytes()),
            "size": path.stat().st_size, "gate": verdict,
            "installed_path_oracle": path_oracle(path),
            "pip": install(path, root, label) if platform.system() in ("Darwin", "Linux") else
                   {"not_executed": "unsupported host for the bounded court"}
        }
    # Positive-control failures mean that this court did not establish its baseline.
    assert result["cases"]["original"]["gate"]["pass"], "positive gate control failed"
    assert result["cases"]["unrelated"]["gate"]["pass"], "distinct-name control failed"
    assert not result["cases"]["original"]["installed_path_oracle"], "original wheel identity ambiguous"
    assert not result["cases"]["unrelated"]["installed_path_oracle"], "distinct control falsely rejected"
    for alias in ("collision_before", "collision_after", "alias_parent", "alias_dot",
                  "alias_repeated_separator", "alias_internal_dot"):
        assert result["cases"][alias]["installed_path_oracle"], alias + " escaped independent oracle"
    if platform.system() in ("Darwin", "Linux"):
        assert result["cases"]["original"]["pip"]["returncode"] == 0, "positive pip control failed"
        assert result["cases"]["original"]["pip"]["primary_native_retained"], "positive pip native changed"
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("j24p05-results"))
    args = parser.parse_args()
    result = run(args.output_dir)
    dest = args.output_dir / "court.json"
    dest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
    print("J24P05 RESEARCH COURT COMPLETE; gate acceptance is NOT installation authority")

if __name__ == "__main__":
    main()
