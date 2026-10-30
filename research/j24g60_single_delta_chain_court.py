#!/usr/bin/env python3
"""J24G60: physical public Writer one-op chain vs logically identical checkpoint.

Research-only charged oracle. Does not alter CMPCT production code or release gates.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

import msgpack
import zstandard as zstd

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct import transactions as tx
from cmpct.validation import preflight_archive

PINS = {
    "src/cmpct/builder.py": "a2160a2f6b1ca3ef8cd94897cb68bb2fcb74ebc2",
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "src/cmpct/transactions.py": "3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11",
    "src/cmpct/journal_replay.py": "03743ca2a06c022c2ec64243a90fe373cf91e899",
    "src/cmpct/validation.py": "5ea3b8f26058b0983c9686295c73f15472bc3ffe",
}
FMAGIC = b"CMPTF24\0"
import struct
FOOTER = struct.Struct("<8sBBBBQQQ32s")
SIZES = (512, 2048)
DEPTHS = (1, 16, 32, 63)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while part := f.read(1024 * 1024):
            h.update(part)
    return h.hexdigest()


def git_blob(data: bytes) -> str:
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_source() -> dict:
    root = Path(__file__).resolve().parents[1]
    imported = {
        "src/cmpct/builder.py": Path(sys.modules["cmpct.builder"].__file__),
        "src/cmpct/reader.py": Path(sys.modules["cmpct.reader"].__file__),
        "src/cmpct/transactions.py": Path(tx.__file__),
        "src/cmpct/journal_replay.py": Path(sys.modules["cmpct.journal_replay"].__file__),
        "src/cmpct/validation.py": Path(sys.modules["cmpct.validation"].__file__),
    }
    observed = {}
    for name, pin in PINS.items():
        fp = root / name
        digest = git_blob(fp.read_bytes())
        assert digest == pin, (name, digest, pin)
        assert fp.read_bytes().replace(b"\r\n", b"\n") == imported[name].read_bytes().replace(b"\r\n", b"\n"), name
        expected = subprocess.check_output(["git", "rev-parse", "HEAD:" + name], cwd=root, text=True).strip()
        assert expected == pin, (name, expected, pin)
        observed[name] = {"git_blob": pin, "imported_file": str(imported[name])}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert subprocess.run(["git", "merge-base", "--is-ancestor",
                           "1935c14c76f1bb39fd218d73cdbee93d3c2b76a1", head],
                          cwd=root).returncode == 0
    return {"head": head, "sources": observed}


def footer_chain(path: Path) -> list[dict]:
    """Read real r24 footer wire with independent struct/Zstd/MessagePack/SHA."""
    with CMPCT(path) as ar:
        pos = int(ar.latest_footer_pos)
        advertised_depth = int(ar.delta_depth)
    size = path.stat().st_size
    seen = set()
    out = []
    with path.open("rb") as f:
        while pos:
            assert pos not in seen and pos + FOOTER.size <= size, (pos, size)
            seen.add(pos)
            f.seek(pos)
            fields = f.read(FOOTER.size)
            assert len(fields) == FOOTER.size
            magic, kind, codec, flags, reserved, csize, usize, prev, digest = FOOTER.unpack(fields)
            assert magic == FMAGIC and kind in (0, 1) and codec in (0, 1)
            assert not flags and not reserved and 0 < csize <= pos
            assert prev == 0 or (0 < prev < pos and prev + FOOTER.size <= size)
            f.seek(pos - csize)
            encoded = f.read(csize)
            assert len(encoded) == csize
            payload = (encoded if codec == 0
                       else zstd.ZstdDecompressor().decompress(encoded, max_output_size=usize))
            assert len(payload) == usize and hashlib.sha256(payload).digest() == digest
            document = msgpack.unpackb(payload, raw=False)
            width = None
            if kind == 1:
                assert isinstance(document, dict) and isinstance(document.get("ops"), list)
                width = len(document["ops"])
            out.append({"kind": int(kind), "op_width": width, "payload_size": int(usize),
                        "stored_payload_size": int(csize), "offset": int(pos),
                        "prev": int(prev), "sha256": hashlib.sha256(payload).hexdigest()})
            if kind == 0:
                break
            pos = prev
    assert out and out[-1]["kind"] == 0
    assert sum(row["kind"] == 1 for row in out) == advertised_depth
    return out


def vmhwm_kib() -> int | None:
    p = Path("/proc/self/status")
    if not p.exists():
        return None
    for row in p.read_text().splitlines():
        if row.startswith("VmHWM:"):
            return int(row.split()[1])
    return None


def probe(path: Path) -> dict:
    # Imports happened before timer, process startup and packaging are out-of-scope.
    initial_hwm = vmhwm_kib()
    w0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    ar = CMPCT(path)
    w1 = time.perf_counter_ns()
    c1 = time.process_time_ns()
    try:
        output = {"open_wall_ns": w1 - w0, "open_cpu_ns": c1 - c0,
                  "rows": len(ar.files), "delta_depth": ar.delta_depth,
                  "hwm_before_kib": initial_hwm, "hwm_after_kib": vmhwm_kib()}
    finally:
        ar.close()
    return output


def check_exact_tree(chain: Path, checkpoint: Path, n: int, d: int) -> dict:
    with CMPCT(chain) as source, CMPCT(checkpoint) as snap:
        assert source.index == snap.index, "same-state checkpoint changed effective index"
        assert source.delta_depth == d and snap.delta_depth == 0
        assert len(source.files) == n and len(snap.files) == n
        # All source contents are identical, verified by both Reader implementations.
        assert source.verify() == n and snap.verify() == n
        assert sorted(source.by) == sorted(snap.by)
        witness_names = (f"r{0:04d}.dat", f"r{d-1:04d}.dat",
                         f"f{d:04d}.dat", f"f{n-1:04d}.dat")
        witness = {}
        for name in witness_names:
            assert name in source.by and name in snap.by
            a, b = source.read(name), snap.read(name)
            assert a == b
            witness[name] = hashlib.sha256(a).hexdigest()
        for name in (f"f{0:04d}.dat", f"f{d-1:04d}.dat"):
            assert name not in source.by and name not in snap.by
        index = msgpack.unpackb(msgpack.packb(source.index, use_bin_type=True), raw=False)
        prev = int(source.latest_footer_pos)
    pr_a = preflight_archive(chain)
    pr_b = preflight_archive(checkpoint)
    assert pr_a["files"] == pr_b["files"] == n
    assert pr_a["delta_depth"] == d and pr_b["delta_depth"] == 0
    return {"witness": witness, "chain_preflight": pr_a,
            "checkpoint_preflight": pr_b, "index_count": len(index["files"]),
            "last_chain_footer": prev}


def make_case(source: Path, stage: Path, n: int) -> dict:
    base = stage / f"n{n:04d}.cmpct"
    Builder(source, workers=1, reproducible=True).build(base)
    assert len(footer_chain(base)) == 1
    snapshots = {}
    for i in range(63):
        tx.append_rename(base, f"f{i:04d}.dat", f"r{i:04d}.dat")
        d = i + 1
        if d not in DEPTHS:
            continue
        chain = stage / f"n{n:04d}-d{d:02d}-chain.cmpct"
        checkpoint = stage / f"n{n:04d}-d{d:02d}-checkpoint.cmpct"
        shutil.copyfile(base, chain)
        shutil.copyfile(base, checkpoint)
        with CMPCT(chain) as ar:
            index = msgpack.unpackb(msgpack.packb(ar.index, use_bin_type=True), raw=False)
            previous = ar.latest_footer_pos
        tx._append_generation(checkpoint, {"blobs": [], "ops": []}, previous,
                              checkpoint_index=index)
        semantics = check_exact_tree(chain, checkpoint, n, d)
        wire = footer_chain(chain)
        own = footer_chain(checkpoint)
        assert len(wire) == d + 1 and len(own) == 1
        assert all(row["op_width"] == 1 for row in wire[:-1])
        assert own[0]["kind"] == 0
        snapshots[str(d)] = {
            "paths": {"chain": str(chain), "checkpoint": str(checkpoint)},
            "archive_bytes": {"chain": chain.stat().st_size, "checkpoint": checkpoint.stat().st_size},
            "archive_sha256": {"chain": sha256_file(chain), "checkpoint": sha256_file(checkpoint)},
            "checkpoint_premium_bytes": checkpoint.stat().st_size - chain.stat().st_size,
            "public_chain_wire": wire,
            "synthetic_checkpoint_wire": own,
            "semantics": semantics,
        }
    assert set(snapshots) == {str(d) for d in DEPTHS}
    return snapshots


def timed_fresh_process(script: Path, source: Path, env: dict) -> dict:
    result = subprocess.run([sys.executable, "-B", str(script), "--probe", str(source)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            env=env, check=False, timeout=90)
    assert result.returncode == 0, (source, result.returncode, result.stderr[-1200:])
    return json.loads(result.stdout.strip())


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--probe":
        print(json.dumps(probe(Path(sys.argv[2])), sort_keys=True))
        return
    identity = verify_source()
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPYCACHEPREFIX"] = tempfile.mkdtemp(prefix="cmpct-j24g60-pycache-")
    report = {
        "claim_scope": "research-only fresh-process Reader open, OS page cache uncontrolled",
        "decision": "INCONCLUSIVE",
        "source": identity, "platform": platform.platform(),
        "python": platform.python_version(), "corpus": {}, "samples": [],
        "limits": ["checkpoint is a private same-state oracle, not a public Writer action",
                   "process startup/import outside timing",
                   "fresh-process is not cold physical disk",
                   "VmHWM is Linux-only and may be dominated by imports",
                   "no product create/extract/recovery/ZIP/Zstd performance credit"],
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g60-") as temp:
        stage = Path(temp)
        script = Path(__file__).resolve()
        for n in SIZES:
            corpus = stage / f"source-{n}"
            corpus.mkdir()
            for i in range(n):
                (corpus / f"f{i:04d}.dat").write_bytes(
                    hashlib.sha256(f"generic-record-{i}".encode()).digest() * 2)
            report["corpus"][str(n)] = {
                "logical_bytes": n * 64, "members": n,
                "snapshots": make_case(corpus, stage, n),
            }
        # Alternate order for every pair, retain every individual observation.
        for n in SIZES:
            for depth in DEPTHS:
                entry = report["corpus"][str(n)]["snapshots"][str(depth)]
                for block in range(4):
                    seq = ("chain", "checkpoint", "checkpoint", "chain") if block % 2 == 0 else (
                        "checkpoint", "chain", "chain", "checkpoint")
                    for position, variant in enumerate(seq):
                        measure = timed_fresh_process(script, Path(entry["paths"][variant]), env)
                        assert measure["rows"] == n
                        assert measure["delta_depth"] == (depth if variant == "chain" else 0)
                        report["samples"].append({
                            "n": n, "depth": depth, "block": block,
                            "phase": position, "variant": variant, **measure,
                        })
        for n in SIZES:
            for depth in DEPTHS:
                pair = [r for r in report["samples"] if r["n"] == n and r["depth"] == depth]
                chain = [r["open_wall_ns"] for r in pair if r["variant"] == "chain"]
                checkpoint = [r["open_wall_ns"] for r in pair if r["variant"] == "checkpoint"]
                assert len(chain) == len(checkpoint) == 8
                a = statistics.median(chain)
                b = statistics.median(checkpoint)
                summary = {"chain_wall_ns_median": a, "checkpoint_wall_ns_median": b,
                           "chain_to_checkpoint_wall_ratio": a / b if b else None,
                           "delta_wall_ns": a - b,
                           "chain_cpu_ns_median": statistics.median(
                               r["open_cpu_ns"] for r in pair if r["variant"] == "chain"),
                           "checkpoint_cpu_ns_median": statistics.median(
                               r["open_cpu_ns"] for r in pair if r["variant"] == "checkpoint")}
                report["corpus"][str(n)]["snapshots"][str(depth)]["measurements"] = summary
        decisive = report["corpus"]["2048"]["snapshots"]["63"]["measurements"]
        delta_ns = decisive["delta_wall_ns"]
        advantage = 1.0 - 1.0 / decisive["chain_to_checkpoint_wall_ratio"]
        report["primary_threshold"] = {
            "n": 2048, "depth": 63, "required_absolute_ms": 3.0,
            "required_fraction_of_chain": 0.10,
            "observed_absolute_ms": delta_ns / 1e6, "observed_fraction_of_chain": advantage,
        }
        report["decision"] = (
            "MATERIAL_SINGLE_DELTA_CHAIN_COST" if delta_ns >= 3e6 and advantage >= 0.10
            else "NO_MATERIAL_SINGLE_DELTA_CHAIN_COST_ON_MEASURED_HOST"
        )
    shutil.rmtree(env["PYTHONPYCACHEPREFIX"], ignore_errors=True)
    output = Path(os.environ.get("J24G60_RESULT", "evidence/j24g60-result.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print("J24G60_DECISION", report["decision"])
    print("J24G60_HEAD", identity["head"])
    print("J24G60_N2048_D63", json.dumps(decisive, sort_keys=True))
    print("J24G60_RESULT_SHA256", sha256_file(output))
    print("J24G60_RESULT_PATH", output)


if __name__ == "__main__":
    main()
