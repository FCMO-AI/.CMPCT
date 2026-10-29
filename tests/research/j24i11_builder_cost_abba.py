"""J24I11 A/A-safe diagnostic: exact old/new Builder on identical ordinary-file tree.

The source has no hardlinks, so source/output semantics are identical. This is a
single-process micro A/B, not an official complete-product release benchmark.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

from cmpct.builder import Builder as CandidateBuilder

OLD_BLOB = "387192edd783e02bf7a44a38945214bf9d6c183e"


def load_old_builder(path: Path):
    name = "cmpct._j24i11_exact_old_builder"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load source-exact baseline Builder")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod.Builder


def make_tree(root: Path):
    root.mkdir()
    for i in range(256):
        # Two SHA digests, deterministic, unique, independent physical files.
        raw = hashlib.sha256(("J24I11/unique/"+str(i)).encode()).digest()
        raw += hashlib.sha256(("J24I11/second/"+str(i)).encode()).digest()
        (root / ("independent-%04d.bin" % i)).write_bytes(raw)
    if len(list(root.iterdir())) != 256:
        raise AssertionError("wrong control corpus count")


def run():
    original_path = Path(os.environ["CMPCT_J24I11_ORIGINAL_BUILDER"])
    # Workflow verifies the source by git hash-object; pin exact source here too.
    if not original_path.is_file():
        raise AssertionError("historical source missing")
    old = load_old_builder(original_path)
    record = {"schema": "j24i11-identical-regular-corpus-abba-v1",
              "host": platform.platform(), "source_sha": os.environ["CMPCT_J24I11_HEAD"],
              "baseline_blob": OLD_BLOB, "input_files": 256,
              "same_semantics_required": True, "raw": [],
              "status": "RUNNING"}
    try:
        with tempfile.TemporaryDirectory(prefix="j24i11-cost-") as td:
            base = Path(td)
            tree = base / "input"
            make_tree(tree)
            output_sha = None
            # Warm both implementations before timing; ABBA pairs cancel linear
            # time drift but not nonlinear scheduling/cache effects.
            for name, impl in (("A", old), ("B", CandidateBuilder)):
                out = base / ("warm-"+name+".cmpct")
                impl(tree, reproducible=True, workers=1).build(out)
                candidate_sha = hashlib.sha256(out.read_bytes()).hexdigest()
                if output_sha is not None and candidate_sha != output_sha:
                    raise AssertionError("candidate and baseline ordinary files differ in bytes")
                output_sha = candidate_sha
            for round_id in range(4):
                for order, name in enumerate(("A", "B", "B", "A")):
                    impl = old if name == "A" else CandidateBuilder
                    output = base / ("measure-%d-%d.cmpct" % (round_id, order))
                    start_wall = time.perf_counter_ns()
                    start_cpu = time.process_time_ns()
                    impl(tree, reproducible=True, workers=1).build(output)
                    cpu_ns = time.process_time_ns() - start_cpu
                    wall_ns = time.perf_counter_ns() - start_wall
                    physical = output.read_bytes()
                    physical_sha = hashlib.sha256(physical).hexdigest()
                    if physical_sha != output_sha:
                        raise AssertionError("failed exact physical size/content parity on ordinary files")
                    record["raw"].append({"round": round_id, "order": order,
                                          "side": name, "wall_ns": wall_ns,
                                          "cpu_ns": cpu_ns, "archive_bytes": len(physical),
                                          "archive_sha": physical_sha})
            for metric in ("wall_ns", "cpu_ns"):
                med = {name: statistics.median(x[metric] for x in record["raw"]
                                                if x["side"] == name)
                       for name in ("A", "B")}
                record[metric+"_medians"] = med
                record[metric+"_ratio"] = med["B"] / med["A"]
            record["physical_sha"] = output_sha
            record["status"] = "DIAGNOSTIC_PARITY_MEASURED_NOT_RELEASE"
            try:
                import resource
                record["ambient_peak_rss_ru_maxrss"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                record["rss_unit"] = "platform-dependent resource ru_maxrss"
            except ImportError:
                record["ambient_peak_rss_ru_maxrss"] = None
                record["rss_unit"] = "UNMEASURED (Windows)"
            return record
    except BaseException as exc:
        record["status"] = "NONPASS"
        record["error"] = repr(exc)
        raise
    finally:
        Path(os.environ["CMPCT_J24I11_COST_RECEIPT"]).write_text(
            json.dumps(record, sort_keys=True, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
