from __future__ import annotations

"""Bounded fresh-process oracle for Logs full-extraction pack-hash ownership.

Research only.  The fast arm changes no archive bytes and keeps every logical-member
SHA-256 check.  It may defer only the decoded-pack SHA when authenticated direct-member
storage rows form an exact non-overlapping partition of the decoded pack.  CRC, decoded
size, decompression and all member hashes remain mandatory.  Selective/strong verification
are not modified because the monkeypatch is installed only inside the extraction worker.
"""

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import zstandard as zstd

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
ORDERS = (("control", "ownership"), ("ownership", "control")) * 2


def _install_ownership() -> dict[str, object]:
    from experiments import entropygraph_v030_logs_fused_extract as F

    base = F.LOGS.Archive
    counters: dict[str, object] = {"pack_sha_deferred": 0, "covered_pack_ids": [], "coverage_bytes": 0, "total_pack_bytes": 0}

    class OwnershipArchive(base):
        def __init__(self, path: Path):
            super().__init__(path)
            intervals: dict[int, list[tuple[int, int]]] = {i: [] for i in range(len(self.pack_offsets))}
            for row in self.files:
                size = int(row[2])
                storage = row[4]
                if storage[0] not in ("pack", "raw"):
                    continue
                pack_id, offset, length = map(int, storage[1:])
                if pack_id < 0 or pack_id >= len(self.pack_offsets) or offset < 0 or length != size:
                    continue
                intervals[pack_id].append((offset, offset + length))
            covered: set[int] = set()
            coverage_bytes = 0
            total = 0
            for pack_id, pack_row in enumerate(self.pack_offsets):
                usize = int(pack_row[2])
                total += usize
                spans = sorted(intervals[pack_id])
                cursor = 0
                valid = bool(spans)
                for start, end in spans:
                    if start != cursor or end < start or end > usize:
                        valid = False
                        break
                    cursor = end
                if valid and cursor == usize:
                    covered.add(pack_id)
                    coverage_bytes += usize
            self._ownership_covered_packs = covered
            counters["covered_pack_ids"] = sorted(covered)
            counters["coverage_bytes"] = coverage_bytes
            counters["total_pack_bytes"] = total

        def _read_pack(self, index: int) -> bytes:
            if index not in self._ownership_covered_packs:
                return super()._read_pack(index)
            if index < 0 or index >= len(self.pack_offsets):
                raise RuntimeError("logs profile pack index")
            offset, codec, usize, csize, crc, _sha = self.pack_offsets[index]
            self.handle.seek(offset)
            payload = self.handle.read(csize)
            if len(payload) != csize:
                raise RuntimeError("short logs profile pack")
            if codec == F.LOGS.V2.P.CODEC_RAW:
                raw = payload
            else:
                raw = zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
            # Pack SHA is the only deferred proof.  Every byte must subsequently belong
            # to a direct member whose authenticated logical SHA is checked by _restore_session.
            if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                raise RuntimeError("logs profile pack identity")
            counters["pack_sha_deferred"] = int(counters["pack_sha_deferred"]) + 1
            return raw

    F.LOGS.Archive = OwnershipArchive
    return counters


def _worker(arm: str, archive: Path, dst: Path) -> dict:
    counters: dict[str, object] = {"pack_sha_deferred": 0, "covered_pack_ids": [], "coverage_bytes": 0, "total_pack_bytes": 0}
    if arm == "ownership":
        counters = _install_ownership()
    started_cpu = time.process_time()
    started = time.perf_counter()
    PRODUCT.extract(archive, dst)
    wall = time.perf_counter() - started
    cpu = time.process_time() - started_cpu
    return {"arm": arm, "wall_s": wall, "cpu_s": cpu, "tree_sha256": PRODUCT.treehash(dst), **counters}


def _fresh(arm: str, archive: Path, dst: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cp = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker", arm, "--archive", str(archive), "--dst", str(dst)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    return json.loads([line for line in cp.stdout.splitlines() if line.strip()][-1])


def run(root: Path) -> dict:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    src = PERF._build_corpora(root / "corpora")[("neutral_hostile_v1", "05_logs_and_telemetry")]
    archive = root / "logs.cmpct"
    stats = PRODUCT.build(src, archive)
    if not stats.get("logs_terminal"):
        raise RuntimeError("frozen Logs workload did not select logs terminal")
    expected = PRODUCT.treehash(src)
    pairs = []
    for rep, order in enumerate(ORDERS):
        rows = {arm: _fresh(arm, archive, root / f"r{rep}-{arm}") for arm in order}
        if any(row["tree_sha256"] != expected for row in rows.values()):
            raise RuntimeError("semantic drift")
        fast = rows["ownership"]
        if int(fast["pack_sha_deferred"]) < 1:
            raise RuntimeError("ownership arm deferred no pack SHA")
        c, f = rows["control"], fast
        pairs.append({
            "rep": rep, "order": list(order), "rows": rows,
            "wall_improvement_pct": (c["wall_s"] - f["wall_s"]) / c["wall_s"] * 100.0,
            "cpu_improvement_pct": (c["cpu_s"] - f["cpu_s"]) / c["cpu_s"] * 100.0,
        })
    improvements = sorted(float(p["wall_improvement_pct"]) for p in pairs)
    median = (improvements[1] + improvements[2]) / 2.0
    return {
        "schema": "cmpct-v030-logs-pack-hash-ownership-oracle-v1",
        "release_credit": False,
        "source_sha": os.environ.get("EVIDENCE_HEAD"),
        "pairs": pairs,
        "median_wall_improvement_pct": median,
        "required_logs_gap_pct": 5.515,
        "decision": "advance-hostile-proof" if median > 5.515 else "kill-low-headroom",
        "proof_boundary": "pack SHA deferred only for exact direct-member partition; CRC/size/member SHA retained; extraction worker only",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", choices=("control", "ownership"))
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--dst", type=Path)
    ap.add_argument("--root", type=Path, default=Path("benchmark-artifacts/v030-logs-pack-hash-ownership"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-pack-hash-ownership.json"))
    args = ap.parse_args()
    if args.worker:
        print(json.dumps(_worker(args.worker, args.archive, args.dst), separators=(",", ":")))
        return
    result = run(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
