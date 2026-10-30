#!/usr/bin/env python3
"""J24P06: inert Python-source PEP427 spread collision, native-SHA-only falsifier.

Science-only, never import a modified Python module nor load Mach-O. Source-exact
J24P04 validator and J24P05d synthetic wheel fixture are reused unchanged.
"""
from __future__ import annotations
import base64, csv, hashlib, io, json, platform, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import j24p05d_wheel_spread_court as prior

NAME = prior.NAME
LIB = prior.NATIVE
MODULE = "cmpct/native_codec.py"
RECORD = prior.RECORD
ORIGINAL = b"# J24P06 trusted inert Python; never imported\nTOKEN = 'original'\n"
REPLACEMENT = b"# J24P06 alternate inert Python; never imported\nTOKEN = 'replacement'\n"
DISJOINT = b"J24P06 unrelated content\n"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def create(root: Path, label: str) -> Path:
    wheel = prior.make(root, label, None, False)
    with zipfile.ZipFile(wheel) as z:
        entries = {i.filename: z.read(i) for i in z.infolist() if i.filename != RECORD}
    entries[MODULE] = ORIGINAL
    if label in ("disjoint_purelib", "disjoint_platlib"):
        scheme = label.split("_")[1]
        entries[f"cmpct-0.30.0.data/{scheme}/cmpct/unrelated.txt"] = DISJOINT
    elif label not in ("original",):
        scheme, order = label.split("_")
        colliding = f"cmpct-0.30.0.data/{scheme}/{MODULE}"
        entries = ({colliding: REPLACEMENT, **entries} if order == "before"
                   else {**entries, colliding: REPLACEMENT})
    rows = []
    for name, data in entries.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        rows.append([name, "sha256=" + digest, str(len(data))])
    rows.append([RECORD, "", ""])
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)
    entries[RECORD] = out.getvalue().encode()
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return wheel

def install(wheel: Path, target: Path) -> dict:
    cmd = [sys.executable, "-m", "pip", "install", "--no-index", "--no-deps",
           "--no-compile", "--ignore-installed", "--only-binary=:all:",
           "--platform", "macosx_10_12_universal2", "--python-version", "3.11",
           "--implementation", "cp", "--abi", "cp311", "--target", str(target),
           str(wheel)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    def physical(name: str) -> dict:
        path = target / name
        return {"exists": path.is_file(), "sha256": sha(path.read_bytes()) if path.is_file() else None,
                "bytes": path.stat().st_size if path.is_file() else None}
    record = target / RECORD
    rows = []
    if record.is_file():
        with record.open(newline="", encoding="utf-8") as f:
            rows = [line for line in csv.reader(f) if line and line[0] == MODULE]
    return {"pip_exit": proc.returncode, "stdout_tail": proc.stdout[-400:],
            "stderr_tail": proc.stderr[-700:], "native": physical(LIB),
            "python_module": physical(MODULE), "record_module_rows": rows}

def run(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    cases = {}
    labels = ("original", "disjoint_purelib", "disjoint_platlib",
              "purelib_before", "purelib_after", "platlib_before", "platlib_after")
    for label in labels:
        wheel = create(root / "wheels", label)
        guard = prior.gate.inspect(wheel)
        with zipfile.ZipFile(wheel) as z:
            original_native = z.read(LIB)
            original_module = z.read(MODULE)
        observed = install(wheel, root / "installed" / label)
        assert guard["pass"] and observed["pip_exit"] == 0, label
        assert observed["native"]["sha256"] == sha(original_native), label + ": native shifted"
        assert observed["python_module"]["sha256"] == sha(REPLACEMENT if "_" in label and
                 not label.startswith("disjoint") else ORIGINAL), label + ": unexpected module"
        cases[label] = {"wheel_sha256": sha(wheel.read_bytes()), "wheel_bytes": wheel.stat().st_size,
                        "zip_native_sha256": sha(original_native),
                        "zip_python_sha256": sha(original_module),
                        "physical_validator_pass": guard["pass"],
                        "installed": observed,
                        "native_only_identity_pass": observed["native"]["sha256"] == sha(original_native),
                        "whole_package_identity_pass": observed["python_module"]["sha256"] == sha(original_module)
                                                       and observed["native"]["sha256"] == sha(original_native)}
    result = {"schema": "cmpct-j24p06-python-module-spread-v1",
              "host": {"system": platform.system(), "machine": platform.machine(),
                       "python": sys.version.split()[0]},
              "source": {"prior_fixture_sha256": sha((ROOT/"tools"/"j24p05d_wheel_spread_court.py").read_bytes()),
                         "unchanged_validator_sha256": sha((ROOT/"tools"/"validate_macos_wheel_abi.py").read_bytes()),
                         "court_sha256": sha(Path(__file__).read_bytes())},
              "baseline": {"trusted_python_sha256": sha(ORIGINAL),
                           "replacement_sha256": sha(REPLACEMENT),
                           "native_sha256": sha(prior.good_fat())},
              "cases": cases,
              "decision": "NATIVE_ONLY_SHA_CANNOT_ATTEST_WHOLE_PACKAGE",
              "scope": "Synthetic inert wheels, real pip --target, physical file hashes. No native/Python execution."}
    (root / "court.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"host":result["host"],"decision":result["decision"],
                      "cases":{k: {"pip":v["installed"]["pip_exit"],
                                    "native":v["native_only_identity_pass"],
                                    "whole":v["whole_package_identity_pass"]}
                               for k,v in cases.items()}}, indent=2))
    return result

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    run(p.parse_args().output_dir)
