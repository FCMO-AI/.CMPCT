#!/usr/bin/env python3
"""Independent J24I04 raw-receipt referee; stdlib-only and no CMPCT imports.

Distinct implementation of A/A timing comparisons; DOES NOT authorize release
or claim that emitted hashes alone prove archive bytes not physically retained.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics

SOURCE = "293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef"
NAMES = ("tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined")
ORDER = (("base-a", "A"), ("candidate-a", "B"), ("candidate-b", "B"), ("base-b", "A"))
TIMES = ("create_s_median", "extract_s_median")


class ReceiptError(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ReceiptError(reason)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(buf)
    return digest.hexdigest()


def evaluate(folder: Path, record: dict | None = None,
             raw: dict[str, dict] | None = None) -> dict:
    record = record if record is not None else read(folder / "j24i04-record.json")
    raw = raw if raw is not None else {k: read(folder / f"{k}.json")
                                     for k, _ in ORDER}
    require(record.get("schema") == "cmpct-v031-j24i04-full-matrix-aa-v1", "schema")
    require(record.get("expected_engine_sha") == SOURCE, "source SHA")
    require(record.get("repetitions_per_sweep") == 7, "original seven-rep law")
    require([list(v) for v in record.get("order", [])] ==
            [list(v) for v in ORDER], "chronology")
    require([s.get("label") for s in record.get("sweeps", [])] ==
            [k for k, _ in ORDER], "sweep labels")
    require(record.get("decision") in ("AA_FULL_NEUTRAL", "AA_FALSE_RED_REPRODUCED"),
            "no completed scientific decision")
    require(record.get("corpus_before") == record.get("corpus_after"), "corpus drift")
    require(record["corpus_before"]["files"] > 0 and
            len(record["corpus_before"]["tree_sha256"]) == 64, "corpus shape")
    a, b = record["engine_a"], record["engine_b"]
    require(a.get("source_commit") == b.get("source_commit") == SOURCE, "engine commits")
    for k in ("native_sha256", "native_bytes", "native_name", "python_source_sha256"):
        require(a.get(k) == b.get(k), f"engine field mismatch: {k}")
    require(len(a.get("python_source_sha256", {})) > 4, "unbound Python source")
    require(a["native_bytes"] > 0 and len(a["native_sha256"]) == 64, "native payload")
    require(a["engine_root"] != b["engine_root"], "same physical source location")
    for e in (a, b):
        for k in ("package", "native"):
            require(Path(e["imported_paths"][k]).resolve().is_relative_to(
                Path(e["engine_root"]).resolve() / "src" / "cmpct"), "import ownership")
    require(set(raw) == {k for k, _ in ORDER}, "missing original sweep")
    for name, side in ORDER:
        s = next(row for row in record["sweeps"] if row["label"] == name)
        e = a if side == "A" else b
        require(s["side"] == side and s["engine_sha"] == SOURCE and
                s["engine_root"] == e["engine_root"] and s["return_code"] == 0,
                f"source execution mismatch: {name}")
        v = raw[name]
        require(v.get("schema") == "cmpct-zip-parity-v1", "parity raw schema")
        require(v.get("repetitions") == 7, "per-sweep repetition mismatch")
        require(set(v.get("corpora", {})) == set(NAMES), "eight-corpus mismatch")
        require(set(s.get("archive_sha256", {})) ==
                {f"{n}/{layer}" for n in NAMES for layer in ("library", "cli")},
                "missing archive identity")
        for n in NAMES:
            for layer in ("library", "cli"):
                blob = v["corpora"][n][layer]["cmpct"]
                stored = s["archive_sha256"][f"{n}/{layer}"]
                require(len(stored) == 2 and int(blob["bytes"]) == stored[0] and
                        isinstance(stored[1], str) and len(stored[1]) == 64,
                        f"archive metadata mismatch {name}/{n}/{layer}")
                for fmt in ("cmpct", "zip"):
                    for field in TIMES:
                        val = v["corpora"][n][layer][fmt][field]
                        require(type(val) in (float, int) and
                                math.isfinite(val) and val >= 0, "invalid timing")

    base_archive_ids = record["sweeps"][0]["archive_sha256"]
    for s in record["sweeps"][1:]:
        require(s["archive_sha256"] == base_archive_ids,
                "same-source archive identity contradiction")

    # Exact independently retained physical archive snapshots, not just self-declared SHA.
    for label in ("base-a", "candidate-a"):
        blob = folder / f"{label}-binary-library.cmpct"
        stored = next(s for s in record["sweeps"] if s["label"] == label)
        require(blob.exists(), f"missing retained archive {label}")
        identity = stored["archive_sha256"]["binary/library"]
        require(blob.stat().st_size == identity[0] and sha_file(blob) == identity[1],
                f"physical archive mismatch {label}")

    observations, discrepancies = [], []
    for name in NAMES:
        for layer in ("library", "cli"):
            for fmt in ("cmpct", "zip"):
                cells = [raw[label]["corpora"][name][layer][fmt] for label, _ in ORDER]
                sizes = [int(x["bytes"]) for x in cells]
                require(len(set(sizes)) == 1, f"same-source variable archive bytes: {name}/{layer}/{fmt}")
                for field in TIMES:
                    ab = statistics.median(float(cells[i][field]) for i in (0, 3))
                    ba = statistics.median(float(cells[i][field]) for i in (1, 2))
                    # Match aggregated files independently, without importing official checker.
                    for label, value in (("base", ab), ("candidate", ba)):
                        archived = read(folder / f"{label}.json")["corpora"][name][layer][fmt][field]
                        require(math.isclose(value, float(archived), rel_tol=1e-12, abs_tol=1e-12),
                                f"aggregated median mismatch: {label}/{name}/{layer}/{fmt}/{field}")
                    confirmed = fmt == "cmpct" and (ba > ab * 1.05 and
                                 (ba - ab) * 1000 > 3)
                    o = {"name": name, "layer": layer, "format": fmt, "metric": field,
                         "base_ms": round(ab * 1000, 6),
                         "candidate_ms": round(ba * 1000, 6),
                         "delta_ms": round((ba - ab) * 1000, 6),
                         "delta_pct": round((ba / ab - 1) * 100, 6) if ab > 0 else None,
                         "release_cell_red": confirmed}
                    observations.append(o)
                    if confirmed:
                        discrepancies.append(o)
    decision = "AA_FALSE_RED_REPRODUCED" if discrepancies else "AA_FULL_NEUTRAL"
    require(record["decision"] == decision, "decision contradicts independent computation")
    require(record["diagnostic_gate_return_code"] == (1 if discrepancies else 0),
            "original checker status contradicts independent computation")

    return {"schema": "cmpct-v031-j24i04-independent-audit-v1",
            "engine_sha": SOURCE,
            "scientific_decision": decision,
            "candidate_release_credit": False,
            "comparison_cells_checked": len(observations),
            "false_red_cells": discrepancies,
            "physical_archives_rehashed": ["base-a-binary-library", "candidate-a-binary-library"],
            "limitation": "Only two retained physical archives independently rehashed; others are exact SHA reports from the producing run, not independently retained bytes",
            "timing_observations": observations}


def mutation_court(folder: Path) -> dict:
    record = read(folder / "j24i04-record.json")
    raw = {label: read(folder / f"{label}.json") for label, _ in ORDER}
    probes = [
        ("wrong source", lambda r, v: r.update(expected_engine_sha="0" * 40)),
        ("native changed", lambda r, v: r["engine_b"].update(native_sha256="0" * 64)),
        ("false decision", lambda r, v: r.update(
            decision=("AA_FULL_NEUTRAL" if r["decision"] != "AA_FULL_NEUTRAL" else "AA_FALSE_RED_REPRODUCED"))),
        ("corpus drift", lambda r, v: r["corpus_after"].update(tree_sha256="1" * 64)),
        ("wrong archive hash", lambda r, v: r["sweeps"][0]["archive_sha256"]["binary/library"].__setitem__(1, "2" * 64)),
        ("wrong aggregation", lambda r, v: v["base-a"]["corpora"]["binary"]["library"]["cmpct"].__setitem__("create_s_median", 100.)),
        ("wrong repetition", lambda r, v: v["candidate-b"].__setitem__("repetitions", 6)),
    ]
    results = {}
    for name, mutate in probes:
        r, v = copy.deepcopy(record), copy.deepcopy(raw)
        mutate(r, v)
        try:
            evaluate(folder, r, v)
        except (ReceiptError, KeyError, IndexError, StopIteration, ValueError) as e:
            results[name] = str(e)
        else:
            raise ReceiptError("independent referee accepted forged receipt: " + name)
    return results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=Path, required=True)
    a = p.parse_args()
    folder = a.folder.resolve()
    report = evaluate(folder)
    report["rejected_mutations"] = mutation_court(folder)
    (folder / "independent-referee.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("INDEPENDENT_REFEREE",
          report["scientific_decision"],
          "cells", report["comparison_cells_checked"],
          "mutations", len(report["rejected_mutations"]),
          "NO PRODUCT/RELEASE CREDIT")


if __name__ == "__main__":
    main()
