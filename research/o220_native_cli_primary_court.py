#!/usr/bin/env python3
"""O220 source-pinned existing native CLI vs Python Reader r24 primary-only court.

Both commands receive exactly the same authentic archive bytes. No Reader/Rust patches.
Native lacks transactional tail recovery: this is a semantic negative, not parity credit.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
NATIVE = ROOT / "native/cmpct-core/target/release/cmpct-native"
COUNTS = (4096, 65536, 262144)
PAIRS = 9
SEED = 220


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def source_identity():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    head = git("rev-parse", "HEAD")
    reader = git("rev-parse", "HEAD:src/cmpct/reader.py")
    native = git("rev-parse", "HEAD:native/cmpct-core/src/lib.rs")
    assert reader == "dbd4ac576a05a47eae97e1e40de89cf1de440516", ("Reader drift", reader)
    assert git("merge-base", "eee2d03265c2a240c80b7dcedd8cdf3494f31c5e", head) == "eee2d03265c2a240c80b7dcedd8cdf3494f31c5e"
    assert NATIVE.is_file(), ("missing unmodified native binary", NATIVE)
    return {"head": head, "reader_blob": reader, "native_core_blob": native,
            "native_executable_sha256": sha(NATIVE.read_bytes()), "python": sys.version}


def commands(path):
    return {
        "rust_cli": [str(NATIVE), "info", str(path)],
        "python_cli": [PYTHON, str(Path(__file__).resolve()), "--pyinfo", str(path)],
    }


def spawn(command):
    """Isolated process; Linux wait4 directly attributes CPU and peak RSS to this child."""
    before = time.perf_counter_ns()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid, status, usage = os.wait4(proc.pid, 0)
    after = time.perf_counter_ns()
    assert pid == proc.pid
    stdout = proc.stdout.read()
    stderr = proc.stderr.read()
    proc.stdout.close()
    proc.stderr.close()
    exit_code = os.waitstatus_to_exitcode(status)
    proc.returncode = exit_code
    return {"exit": exit_code, "stdout": stdout.decode("utf-8", "replace"),
            "stderr": stderr.decode("utf-8", "replace")[:1000],
            "wall_ns": after - before, "cpu_ns": int(round((usage.ru_utime + usage.ru_stime) * 1e9)),
            "maxrss_kib": usage.ru_maxrss}


def pyinfo(path):
    from cmpct.reader import CMPCT
    with CMPCT(Path(path)) as archive:
        print(json.dumps({"revision": archive.index["v"], "entries": len(archive.files)},
                         sort_keys=True))


def compare_semantics(path, expect_good, label):
    reports = {key: spawn(command) for key, command in commands(path).items()}
    valid = {key: row["exit"] == 0 for key, row in reports.items()}
    if expect_good:
        assert all(valid.values()), (label, reports)
        assert json.loads(reports["rust_cli"]["stdout"]) == json.loads(reports["python_cli"]["stdout"])
        assert json.loads(reports["python_cli"]["stdout"]) == {"entries": 1, "revision": 24}
    else:
        assert not any(valid.values()), (label, reports)
    return {"case": label, "archive_sha256": sha(path.read_bytes()),
            "archive_bytes": path.stat().st_size,
            "acceptance": valid,
            "return_codes": {k: v["exit"] for k, v in reports.items()}}


def ranges_match(path, count):
    from cmpct.reader import CMPCT
    with CMPCT(path) as reader:
        for offset in (0, 4 * (count // 2), 4 * (count - 1)):
            expect = reader.read_range("fixed.bin", offset, 4)
            assert expect == b"ABCD", (count, offset, expect)
            actual = subprocess.run([str(NATIVE), "range", str(path), "fixed.bin",
                                     str(offset), "4"], check=True, capture_output=True).stdout
            assert actual == expect, (count, offset, actual)
    return 3


def med(rows, name):
    return statistics.median(row[name] for row in rows)


def main():
    assert sys.platform == "linux" and hasattr(os, "wait4")
    sys.path.insert(0, str(ROOT / "tests"))
    from test_o215_fixed_chunk_admission import _make_archive
    rng = random.Random(SEED)
    output = {"question": "O220 existing Rust vs Python CLI primary-only execution",
              "source": source_identity(), "profiles": [], "semantic_controls": [],
              "scope": "science only; CLI-to-CLI startup included; no native journal equivalence",
              "build": "native Rust binary built once outside timed samples"}
    with tempfile.TemporaryDirectory(prefix="o220-authentic-r24-") as tmp:
        directory = Path(tmp)
        for count in COUNTS:
            data = _make_archive([0] * count, b"ABCD" * count)
            archive = directory / ("valid-" + str(count) + ".cmpct")
            archive.write_bytes(data)
            output["semantic_controls"].append(compare_semantics(archive, True, "valid-" + str(count)))
            output["semantic_controls"][-1]["successful_cross_language_ranges"] = ranges_match(archive, count)
            samples = []
            for pair in range(PAIRS):
                arms = list(commands(archive))
                rng.shuffle(arms)
                for arm in arms:
                    row = spawn(commands(archive)[arm])
                    assert row["exit"] == 0, (arm, count, row)
                    assert json.loads(row["stdout"]) == {"revision": 24, "entries": 1}
                    samples.append({"pair": pair, "mode": arm,
                                    "wall_ns": row["wall_ns"], "cpu_ns": row["cpu_ns"],
                                    "maxrss_kib": row["maxrss_kib"]})
            arms = {a: [x for x in samples if x["mode"] == a] for a in commands(archive)}
            native_wall, python_wall = med(arms["rust_cli"], "wall_ns"), med(arms["python_cli"], "wall_ns")
            profile = {"reference_count": count, "archive_bytes": len(data),
                       "archive_sha256": sha(data), "samples": samples,
                       "summary": {a: {key: med(rows, key) for key in ("wall_ns","cpu_ns","maxrss_kib")}
                                   for a, rows in arms.items()},
                       "python_to_native_wall_ratio": python_wall / native_wall,
                       "python_minus_native_ms": (python_wall - native_wall) / 1e6}
            output["profiles"].append(profile)
            print("O220_COUNTS=%d CLI_RATIO=%.3fx SAVING_MS=%.3f" %
                  (count, profile["python_to_native_wall_ratio"], profile["python_minus_native_ms"]), flush=True)

        corrupt = directory / "overdeclared.cmpct"
        corrupt.write_bytes(_make_archive([0], b"ABCD", declared_size=5))
        output["semantic_controls"].append(compare_semantics(corrupt, False, "primary-overdeclared"))
        corrupt.write_bytes(_make_archive([7], b"ABCD", declared_size=4))
        output["semantic_controls"].append(compare_semantics(corrupt, False, "missing-physical-ref"))
        # Explicitly distinct owner: the native core documents primary-only semantics, while
        # Python follows the newest authenticated footer checkpoint.
        journal = directory / "later-valid.cmpct"
        journal.write_bytes(_make_archive([0], b"ABCD", declared_size=5,
                                          latest_refs=[0], latest_size=4))
        outcome = {key: spawn(command) for key, command in commands(journal).items()}
        native_accepts = outcome["rust_cli"]["exit"] == 0
        python_accepts = outcome["python_cli"]["exit"] == 0
        assert python_accepts and not native_accepts, outcome
        output["journal_counterexample"] = {
            "sha256": sha(journal.read_bytes()), "archive_bytes": journal.stat().st_size,
            "python_accepts_later_valid_checkpoint": python_accepts,
            "native_rejects_invalid_primary": not native_accepts,
            "semantic_equivalence": False}
    last = next(p for p in output["profiles"] if p["reference_count"] == 262144)
    material = (last["python_to_native_wall_ratio"] >= 2.0 and
                last["python_minus_native_ms"] >= 5.0)
    output["decision"] = ("PRIMARY_ONLY_NATIVE_ECONOMIC_HEADROOM_WITH_RECOVERY_DEBT"
                          if material else "NATIVE_CLI_NO_MATERIAL_FULL_PROCESS_GAIN_WITH_RECOVERY_DEBT")
    output["preregistered_materiality_met"] = material
    target = Path(os.environ.get("O220_OUTPUT", "o220-evidence/o220-results.json"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print("O220_DECISION=" + output["decision"], flush=True)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--pyinfo":
        pyinfo(sys.argv[2])
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("usage: python research/o220_native_cli_primary_court.py [--pyinfo PATH]")
