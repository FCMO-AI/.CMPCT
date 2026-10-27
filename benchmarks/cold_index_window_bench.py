#!/usr/bin/env python3
"""Reproduce the index-only research ablation on a public seeded repeated tree."""
import argparse
import importlib.util
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "benchmarks")]
from cold_tree_corpus import generate
from cmpct import native_codec
from cmpct.builder import Builder
from cmpct.codec import HDR, zd
from cmpct.reader import CMPCT

spec = importlib.util.spec_from_file_location("window", ROOT / "experiments/cold_index_window.py")
window = importlib.util.module_from_spec(spec)
spec.loader.exec_module(window)


def measure(work):
    work.mkdir(parents=True, exist_ok=False)
    source = generate(work / "tree")
    base, candidate = work / "base.cmpct", work / "candidate.cmpct"
    start = time.monotonic()
    Builder(source, workers=4, reproducible=True).build(base)
    create = time.monotonic() - start
    start = time.monotonic()
    rewrite = window.recompress(base, candidate)
    rewrite_s = time.monotonic() - start
    with base.open("rb") as f:
        header = HDR.unpack(f.read(HDR.size))
        raw = zd(f.read(header[3]), header[4])
    ablation = {}
    for name, flags in [("12", ["-12"]), ("19", ["-19"]), ("19-long", ["-19", "--long=31"])]:
        start = time.monotonic()
        encoded = subprocess.run(["zstd", "-q", *flags, "-c"], input=raw,
                                 stdout=subprocess.PIPE, check=True).stdout
        ablation[name] = {"bytes": len(encoded), "wall_s": time.monotonic() - start}
    reads = {}
    for name, archive in [("base", base), ("candidate", candidate)]:
        start = time.monotonic()
        with CMPCT(archive) as reader:
            opened = time.monotonic() - start
            start = time.monotonic()
            count = 0
            for row in reader.files:
                if row[1] == 0:
                    if reader.read(row[0]) != (source / row[0]).read_bytes():
                        raise RuntimeError("logical bytes differ from public source")
                    count += 1
            reads[name] = {"open_s": opened, "read_all_s": time.monotonic() - start,
                           "regular_files": count}
    result = {
        "schema": "cmpct-cold-index-diagnostic-v1",
        "source_base": "80c358f8824ec1b20d349c92ed94c898090969b0", "audio_fix_commit": "ebcdbca4",
        "runtime": {**getattr(native_codec, "diagnostic_runtime", {"status": "package-owned"}),
                    "python": platform.python_version(), "os": platform.system(),
                    "machine": platform.machine()},
        "corpus": {"generator": "benchmarks/cold_tree_corpus.py", "seed": 20261027,
                   "stages": 4, "files_per_stage": 256},
        "semantics": {"layer": "in-process Builder and open+read; uncontrolled cache and background load",
                      "repetitions": 1, "workers": 4, "reproducible": True,
                      "metadata": "logical source-byte check, not full filesystem restoration",
                      "integrity": "every logical file byte-compared against generated source",
                      "durability": "no fsync", "native_reader": "not tested", "rss": "not measured"},
        "create_s": create, "rewrite_s": rewrite_s, "complete_checkpoint": rewrite,
        "index_codec_ablation": ablation, "logical_reads": reads, "every_file_exact": True,
    }
    (work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work", type=Path, help="new work directory")
    args = ap.parse_args()
    print(json.dumps(measure(args.work), indent=2))
