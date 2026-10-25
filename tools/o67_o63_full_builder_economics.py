"""O67: source-exact, full-Builder O60 vs O63 experiment (research only).

A single physical tree is generated once. Both actual independently installed engines
run ABBA fresh Python processes. All successful archives must reconstruct their
manifest exactly; comparison preserves unrounded wall/CPU/RSS and complete bytes.
This is not CMPCT's frozen official release/performance comparator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import sys
import time
import zipfile
import zlib
from pathlib import Path

O60_BLOB = "bda9d7f8005e276ba891aac75ae50eabe67bd431"
O63_BLOB = "382e60983bf1e8e7595ea7112f3a5553dc33dcc0"
CODEC_BLOB = "dc3446b0eed82edfba9380e3885a20aa45577899"
CASES = ("late", "early", "accepted", "ordinary", "multiple_late")
EXPECTED = 5 * 4 * 4


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def fixed_zip(path: Path, *, kind: str) -> None:
    source = zipfile._get_compressor

    def fixed_compressor(compress_type, compresslevel=None):
        if compress_type == zipfile.ZIP_DEFLATED:
            return zlib.compressobj(
                6, zlib.DEFLATED, -15, zlib.DEF_MEM_LEVEL, zlib.Z_FIXED
            )
        return source(compress_type, compresslevel)

    def write_fixed(z):
        old = zipfile._get_compressor
        try:
            zipfile._get_compressor = fixed_compressor
            z.writestr("fixed-last.bin", b"late fixed Huffman is different\\n" * 1100,
                       compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        finally:
            zipfile._get_compressor = old

    with zipfile.ZipFile(path, "w") as z:
        if kind == "early":
            write_fixed(z)
        for i in range(14):
            body = (
                f"member={i} exact physical bytes not an oracle\\n".encode() * (45 + i * 3)
                + hashlib.sha256(str(i).encode()).digest() * (10 + i)
            )
            z.writestr(f"members/{i:03d}.dat", body,
                       compress_type=zipfile.ZIP_STORED if i % 3 else zipfile.ZIP_DEFLATED)
        if kind == "late":
            write_fixed(z)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == (15 if kind in ("late", "early") else 14)


def make_corpora(dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=False)
    for kind in CASES:
        root = dest / kind
        root.mkdir()
        if kind in ("late", "early", "accepted"):
            fixed_zip(root / "archive.zip", kind=kind)
        elif kind == "ordinary":
            (root / "nested").mkdir()
            for i in range(150):
                b = (hashlib.sha256(str(i).encode()).digest() * (2 + i % 8)
                     + f"index {i}.".encode() * 25)
                (root / "nested" / f"{i:03d}.bin").write_bytes(b)
        else:
            for i in range(5):
                fixed_zip(root / f"archive-{i:02d}.zip", kind="late")
        assert list(root.rglob("*"))
    hashes = {k: manifest(dest / k) for k in CASES}
    return {"cases": list(CASES), "manifest": hashes}


def manifest(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): {"sha256": sha(p.read_bytes()), "size": p.stat().st_size}
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def sample(root: Path, output: Path, *, case: str, role: str, repetition: int, slot: int) -> dict:
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    import cmpct.builder
    import cmpct.codec

    expected = {"base": O60_BLOB, "candidate": O63_BLOB}[role]
    installed = Path(cmpct.builder.__file__).resolve()
    installed_codec = Path(cmpct.codec.__file__).resolve()
    checkout = Path(os.environ["O67_CHECKOUT"]).resolve()
    assert not installed.is_relative_to(checkout), installed
    assert not installed_codec.is_relative_to(checkout), installed_codec
    observed = git_blob(installed.read_bytes())
    observed_codec = git_blob(installed_codec.read_bytes())
    assert observed == expected, (role, observed, expected)
    assert observed_codec == CODEC_BLOB, (observed_codec, CODEC_BLOB)

    m_before = manifest(root)
    out = output
    out.parent.mkdir(parents=True, exist_ok=True)
    p0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0).build(out)
    c1 = time.process_time_ns()
    t1 = time.perf_counter_ns()
    p1 = resource.getrusage(resource.RUSAGE_SELF)
    encoded = out.read_bytes()

    verification_start = time.perf_counter_ns()
    with CMPCT(out) as reader:
        n_verified = reader.verify()
        assert n_verified >= 1
        for path, meta in m_before.items():
            decoded = reader.read(path)
            assert sha(decoded) == meta["sha256"], (role, case, path)
            assert len(decoded) == meta["size"]
    verification_end = time.perf_counter_ns()
    assert manifest(root) == m_before, ("source changed during experiment", case)
    return {
        "role": role, "case": case, "repetition": repetition, "slot": slot,
        "builder_blob": observed, "codec_blob": observed_codec,
        "python": sys.version.split()[0], "platform": platform.platform(),
        "create_wall_ns": t1 - t0, "create_cpu_ns": c1 - c0,
        "verify_read_wall_ns": verification_end - verification_start,
        "peak_rss_kib": p1.ru_maxrss,
        "io_input_blocks_delta": p1.ru_inblock - p0.ru_inblock,
        "io_output_blocks_delta": p1.ru_oublock - p0.ru_oublock,
        "archive_bytes": len(encoded), "archive_sha256": sha(encoded),
        "member_manifest_sha256": sha(json.dumps(m_before, sort_keys=True).encode()),
        "member_count": len(m_before),
        "source_mtime_ns": max(p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()),
        "recorded_at_ns": time.time_ns(),
    }


def report(directory: Path, destination: Path) -> None:
    rows = [json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))]
    assert len(rows) == EXPECTED, (len(rows), EXPECTED)
    summaries = {}
    for kind in CASES:
        pairs = {}
        for rep in range(4):
            rs = [x for x in rows if x["case"] == kind and x["repetition"] == rep]
            assert len(rs) == 4, (kind, rep, len(rs))
            assert [x["role"] for x in sorted(rs, key=lambda z:z["slot"])] == [
                "base", "candidate", "candidate", "base"
            ]
            assert len({x["member_manifest_sha256"] for x in rs}) == 1
            assert len({x["archive_bytes"] for x in rs if x["role"] == "base"}) == 1
            assert len({x["archive_bytes"] for x in rs if x["role"] == "candidate"}) == 1
            pairs[rep] = {
                role: [x for x in rs if x["role"] == role] for role in ("base", "candidate")
            }
        by = {role: [x for x in rows if x["case"] == kind and x["role"] == role]
              for role in ("base", "candidate")}
        for role in by:
            assert len(by[role]) == 8
            assert len({x["archive_sha256"] for x in by[role]}) == 1
        a, b = (by["base"][0]["archive_bytes"], by["candidate"][0]["archive_bytes"])
        def med(role, key):
            return statistics.median(x[key] for x in by[role])
        stats = {
            "base_complete_archive_bytes": a, "candidate_complete_archive_bytes": b,
            "candidate_minus_base_bytes": b-a,
            "physical_archive_sha_equal": (
                by["base"][0]["archive_sha256"] == by["candidate"][0]["archive_sha256"]
            ),
            "create_wall_base_ns": med("base","create_wall_ns"),
            "create_wall_candidate_ns": med("candidate","create_wall_ns"),
            "create_cpu_base_ns": med("base","create_cpu_ns"),
            "create_cpu_candidate_ns": med("candidate","create_cpu_ns"),
            "peak_rss_base_kib": med("base","peak_rss_kib"),
            "peak_rss_candidate_kib": med("candidate","peak_rss_kib"),
            "verify_read_base_ns": med("base","verify_read_wall_ns"),
            "verify_read_candidate_ns": med("candidate","verify_read_wall_ns"),
            "output_blocks_base": med("base","io_output_blocks_delta"),
            "output_blocks_candidate": med("candidate","io_output_blocks_delta"),
        }
        stats["candidate_minus_base_create_wall_ns"] = (
            stats["create_wall_candidate_ns"]-stats["create_wall_base_ns"]
        )
        stats["candidate_minus_base_create_cpu_ns"] = (
            stats["create_cpu_candidate_ns"]-stats["create_cpu_base_ns"]
        )
        if kind in ("accepted","ordinary") and a != b:
            stats["exact_byte_parity_prediction"] = "FALSIFIED"
        elif kind in ("accepted","ordinary"):
            stats["exact_byte_parity_prediction"] = (
                "PASS" if stats["physical_archive_sha_equal"] else "FALSIFIED"
            )
        else:
            stats["byte_savings_prediction"] = "PASS" if b <= a else "FALSIFIED"
        summaries[kind] = stats
    obj = {
        "experiment": "O67", "kind": "observational source-exact complete-Builder research",
        "official_release_gate": False, "repetitions": 4,
        "method": "fresh-process ABBA, same physical source, one Linux runner",
        "raw": rows, "summary": summaries,
    }
    destination.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\\n")
    print("O67_SOURCE_BOUND_COMPLETE_BUILDER_ECONOMICS",json.dumps(summaries, sort_keys=True))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--create", action="store_true")
    g.add_argument("--sample", action="store_true")
    g.add_argument("--report", action="store_true")
    ap.add_argument("--root", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--role", choices=["base","candidate"])
    ap.add_argument("--repetition", type=int, default=0)
    ap.add_argument("--slot", type=int, default=0)
    ns = ap.parse_args()
    if ns.create:
        result = make_corpora(ns.root)
        ns.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\\n")
    elif ns.sample:
        result = sample(ns.root, ns.out.with_suffix(".cmpct"), case=ns.case,
                        role=ns.role, repetition=ns.repetition, slot=ns.slot)
        ns.out.write_text(json.dumps(result, sort_keys=True) + "\\n")
        print("O67_SAMPLE",json.dumps(result, sort_keys=True))
    else:
        report(ns.root, ns.out)
