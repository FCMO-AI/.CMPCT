"""J24I12b source-exact phase witness for sparse compaction; no product patch.

Measurement-only wrapper delegates once to the original CMPCT.read. Memory samples
are current worker /proc/self/status VmHWM and VmRSS, not inherited-child rusage.
"""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from j24i12_sparse_compaction_cost import make_fixture, digest


def memory_status() -> dict:
    names = {"VmRSS", "VmHWM"}
    out = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        key, _, rest = line.partition(":")
        if key in names:
            out[key + "_kib"] = int(rest.strip().split()[0])
    assert names == {x.removesuffix("_kib") for x in out}
    return out


def run_child(src: Path, dst: Path, receipt: Path) -> None:
    from cmpct.reader import CMPCT
    from cmpct.transactions import compact_archive
    from cmpct.codec import S_SPARSE

    original = CMPCT.read
    events = []
    source_sha = digest(src)

    def observe(self: CMPCT, name: str):
        row = self.by.get(name)
        sparse = row is not None and bool(row[6]) and row[6][0] == S_SPARSE
        if not sparse:
            return original(self, name)
        before = memory_status()
        actual = original(self, name)  # EXACTLY ONCE: no behavioral replacement
        after = memory_status()
        events.append({
            "reader_source": str(self.path),
            "name": name,
            "logical_size": row[4],
            "read_return_bytes": len(actual),
            "read_return_sha256": hashlib.sha256(actual).hexdigest(),
            "before": before,
            "after": after,
            "peak_increment_kib": after["VmHWM_kib"] - before["VmHWM_kib"],
        })
        return actual

    before = memory_status()
    try:
        CMPCT.read = observe
        result = compact_archive(src, dst)
    finally:
        CMPCT.read = original
    after = memory_status()
    assert digest(src) == source_sha
    assert len(events) == 2, events
    assert events[0]["logical_size"] == events[1]["logical_size"] == 128 << 20
    assert events[0]["read_return_sha256"] == events[1]["read_return_sha256"]
    assert events[0]["read_return_bytes"] == events[1]["read_return_bytes"] == 128 << 20
    assert events[0]["reader_source"] != events[1]["reader_source"], "source/result verification must be distinct"

    with CMPCT(dst) as ar:
        assert ar.by["sparse.bin"][6][0] == S_SPARSE
        assert ar.file_sha256("sparse.bin").hex() == events[0]["read_return_sha256"]

    evidence = {
        "schema": "j24i12b-phase-v1",
        "source_sha256_unchanged": source_sha,
        "output_sha256": digest(dst),
        "before_compaction": before,
        "after_compaction": after,
        "sparse_read_events": events,
        "compaction_result": result,
        "first_read_peak_delta_kib": events[0]["peak_increment_kib"],
        "other_uncaptured_peak_kib": after["VmHWM_kib"] - max(before["VmHWM_kib"], events[0]["after"]["VmHWM_kib"]),
        "origin": "installed original #723 reader; wrapper invokes original method once",
    }
    if evidence["first_read_peak_delta_kib"] >= 128 << 10:
        evidence["decision"] = "FIRST_SPARSE_READ_MATERIALIZATION_CONFIRMED"
    elif evidence["first_read_peak_delta_kib"] < 32 << 10:
        evidence["decision"] = "FIRST_SPARSE_READ_MATERIALIZATION_FALSIFIED"
    else:
        evidence["decision"] = "FIRST_SPARSE_READ_MATERIALIZATION_AMBIGUOUS"
    receipt.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": evidence["decision"],
        "first_read_peak_delta_kib": evidence["first_read_peak_delta_kib"],
        "sparse_read_calls": len(events)
    }, sort_keys=True))


def main():
    artifact_dir = Path(os.environ["CMPCT_J24I12_ARTIFACT_DIR"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="j24i12b-") as temporary:
        root = Path(temporary)
        fixture = make_fixture(root, 128 << 20)
        before_sha = fixture["input_archive_sha256"]
        out = root / "compacted.cmpct"
        receipt = artifact_dir / "j24i12b-phase-court.json"
        cmd = [sys.executable, str(Path(__file__).resolve()), "--child",
               str(fixture["source"]), str(out), str(receipt)]
        process = subprocess.run(cmd, cwd=root, capture_output=True,
                                 text=True, check=False, timeout=360,
                                 env={**os.environ, "CMPCT_ENCODE_WORKERS": "1"})
        (artifact_dir / "j24i12b-phase-stdout.txt").write_text(process.stdout)
        (artifact_dir / "j24i12b-phase-stderr.txt").write_text(process.stderr)
        assert process.returncode == 0, process.stderr
        assert digest(fixture["source"]) == before_sha
        assert receipt.exists()
        record = json.loads(receipt.read_text())
        assert record["origin"].startswith("installed original #723")
        assert record["first_read_peak_delta_kib"] >= 0
        assert record["decision"] in (
            "FIRST_SPARSE_READ_MATERIALIZATION_CONFIRMED",
            "FIRST_SPARSE_READ_MATERIALIZATION_FALSIFIED",
            "FIRST_SPARSE_READ_MATERIALIZATION_AMBIGUOUS")
        print(json.dumps({"decision":record["decision"],
                          "first_peak_delta_kib":record["first_read_peak_delta_kib"]},
                         sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--child":
        run_child(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("usage: no args or --child src dst receipt")
