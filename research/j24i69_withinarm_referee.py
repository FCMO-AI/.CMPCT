#!/usr/bin/env python3
"""J24I69 read-only, post-hoc source-identical ABBA temporal-placebo referee.

No CMPCT import. Four *sweep medians* are NOT the raw 7 repetitions.
Never use these diagnostics to waive or adjust official release gates.
"""
import argparse
import hashlib
import io
import json
import math
import statistics
import sys
import zipfile
from collections import Counter
from pathlib import Path

SCHEMA = "j24i69-intraarm-posthoc-v1"
PROVIDERS = {
    "cmpct_p835_firstfailure_12981944713.zip": "cf20ded12b7e5b6348a9fc272cadc7565dc4e76982e1760fce674b1b2e7e1598",
    "cmpct_source_identical_835_12986955317.zip": "aedd2d6150746f5c6bcef4b0e8a41af5ed5f5c9f9fbb0c3ba78b54da59bbd1ee",
    "cmpct_source_identical_837_12988780098.zip": "1d43e55fb359db5ec779607d9da25508efe61bbaa6d5ba5c5665d8819999490b",
}
HEADS = {
    "cmpct_p835_firstfailure_12981944713.zip": ("fe7669f7f1a07720187219200e24a972fa650f6b", "09e38915b79a83964cc816d5130251b3e748121e"),
    "cmpct_source_identical_835_12986955317.zip": ("fe7669f7f1a07720187219200e24a972fa650f6b", "09e38915b79a83964cc816d5130251b3e748121e"),
    "cmpct_source_identical_837_12988780098.zip": ("09e38915b79a83964cc816d5130251b3e748121e", "1ea579c5837d3b783614f423c423a121878dc0ca"),
}
CORPORA = ("tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined")
MODES = ("library", "cli")
ENGINES = ("cmpct", "zip")
OPERATIONS = ("create", "extract")
SWEEPS = ("base-a.json", "base-b.json", "candidate-a.json", "candidate-b.json")
CORPUS_HASH = "b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f"
MAX_PROVIDER_BYTES = 20 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024


def _names(z):
    names = z.namelist()
    if len(set(names)) != len(names):
        raise ValueError("duplicate ZIP member names")
    if any(m.file_size > MAX_MEMBER_BYTES for m in z.infolist()):
        raise ValueError("ZIP member exceeds research resource bound")
    if len(names) > 128:
        raise ValueError("excessive ZIP entries")
    return set(names)


def _json(z, name):
    val = json.loads(z.read(name))
    if not isinstance(val, dict):
        raise ValueError("malformed JSON object " + name)
    return val


def _positive_time(v, location):
    if type(v) is not float and type(v) is not int:
        raise ValueError("invalid timing type " + location)
    if not math.isfinite(v) or v <= 0:
        raise ValueError("non-finite or nonpositive timing " + location)
    return float(v)


def _extract_sweep_cells(data, label):
    if data.get("schema") != "cmpct-zip-parity-v1" or data.get("repetitions") != 7 or data.get("timing_statistic") != "median":
        raise ValueError("invalid original benchmark schema/repetitions/statistic " + label)
    corpora = data.get("corpora")
    if not isinstance(corpora, dict) or set(corpora) != set(CORPORA):
        raise ValueError("unexpected corpus set " + label)
    cells = {}
    for corpus in CORPORA:
        c = corpora[corpus]
        logical = c.get("logical_bytes")
        if not isinstance(logical, int) or logical < 0:
            raise ValueError("invalid logical bytes " + corpus)
        if set(c) != {"logical_bytes", *MODES}:
            raise ValueError("unexpected mode/field set " + corpus)
        for mode in MODES:
            d = c[mode]
            if set(d) != set(ENGINES):
                raise ValueError("unexpected engines " + corpus)
            for engine in ENGINES:
                metrics = d[engine]
                if set(metrics) != {"bytes", "create_s_median", "extract_s_median"}:
                    raise ValueError("unexpected metrics " + corpus)
                nbytes = metrics["bytes"]
                if not isinstance(nbytes, int) or nbytes < 0:
                    raise ValueError("invalid archive bytes")
                for op in OPERATIONS:
                    key = (corpus, mode, engine, op)
                    cells[key] = {"time_ms": 1000 * _positive_time(metrics[op + "_s_median"], str(key)), "bytes": nbytes, "logical_bytes": logical}
    return cells


def _effect(early, late):
    delta = late - early
    pct = delta / early * 100
    return {"early_ms": early, "late_ms": late, "delta_ms": delta, "delta_pct": pct, "magnitude_crossing": abs(delta) > 3 and abs(pct) > 5}


def _read_raw_provider(content, filename, expected_sha):
    if len(content) > MAX_PROVIDER_BYTES:
        raise ValueError("provider size limit")
    if hashlib.sha256(content).hexdigest() != expected_sha:
        raise ValueError("provider SHA256 mismatch: " + filename)
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        members = _names(z)
        required = set(SWEEPS) | {"corpus.json", "environment.txt"}
        if not required <= members:
            raise ValueError("missing original benchmark sweeps/receipts")
        corpus = _json(z, "corpus.json")
        if corpus.get("tree_sha256") != CORPUS_HASH or corpus.get("files") != 7713 or corpus.get("logical_bytes") != 303738466:
            raise ValueError("corpus fingerprint mismatch")
        env = z.read("environment.txt").decode("utf-8")
        receipts = dict(line.strip().split("=", 1) for line in env.splitlines() if "=" in line)
        if (receipts.get("base_commit"), receipts.get("candidate_commit")) != HEADS[filename]:
            raise ValueError("unexpected historical source commits")
        if receipts.get("format_revision") != "24":
            raise ValueError("non-r24 source")
        data = {n: _extract_sweep_cells(_json(z, n), n) for n in SWEEPS}
    expected_keys = set(data[SWEEPS[0]])
    if len(expected_keys) != 64:
        raise ValueError("missing expected 64 cell keys")
    for k in expected_keys:
        arr = [data[n][k] for n in SWEEPS]
        if any(a["logical_bytes"] != arr[0]["logical_bytes"] or a["bytes"] != arr[0]["bytes"] for a in arr[1:]):
            raise ValueError("archived bytes/logical bytes differ across original sweeps")
    effects = []
    for arm in ("base", "candidate"):
        for k in sorted(expected_keys):
            a, b = data[arm + "-a.json"][k]["time_ms"], data[arm + "-b.json"][k]["time_ms"]
            e = _effect(a, b)
            effects.append({"arm": arm, "corpus": k[0], "mode": k[1], "engine": k[2], "operation": k[3], **e})
    official = []
    for k in sorted(expected_keys):
        if k[2] != "cmpct":
            continue
        ba = statistics.median([data["base-a.json"][k]["time_ms"], data["base-b.json"][k]["time_ms"]])
        ca = statistics.median([data["candidate-a.json"][k]["time_ms"], data["candidate-b.json"][k]["time_ms"]])
        e = _effect(ba, ca)
        # Historical release gate: positive slowdown only. Negative is a speedup, not a release red.
        official.append({"corpus": k[0], "mode": k[1], "operation": k[3], **e, "historical_release_red": e["delta_ms"] > 3 and e["delta_pct"] > 5})
    lookup = {(e["arm"], e["corpus"], e["mode"], e["operation"]): e for e in effects if e["engine"] == "cmpct"}
    for e in official:
        e["both_within_arm_neutral"] = all(not lookup[(a, e["corpus"], e["mode"], e["operation"])]["magnitude_crossing"] for a in ("base", "candidate"))
    return {"provider_filename": filename, "provider_sha256": expected_sha, "source_heads": list(HEADS[filename]), "cpu_model": receipts.get("cpu_model"), "corpus_sha256": CORPUS_HASH, "effects": effects, "official_cmpct": official}


def analyze_provider_bundle(bundle_content):
    if len(bundle_content) > MAX_PROVIDER_BYTES:
        raise ValueError("outer bundle exceeds research bound")
    with zipfile.ZipFile(io.BytesIO(bundle_content)) as z:
        names = _names(z)
        if not set(PROVIDERS) <= names:
            raise ValueError("missing required original provider evidence")
        results = [_read_raw_provider(z.read(name), name, digest) for name, digest in PROVIDERS.items()]
    totals = {}
    for d in results:
        effects = d["effects"]
        official = d["official_cmpct"]
        c = {engine: sum(e["magnitude_crossing"] for e in effects if e["engine"] == engine) for engine in ENGINES}
        byarm = {arm: {eng: sum(e["magnitude_crossing"] for e in effects if e["arm"] == arm and e["engine"] == eng) for eng in ENGINES} for arm in ("base", "candidate")}
        totals[d["provider_filename"]] = {"within_arm_magnitude_crossings": c, "by_arm": byarm, "official_cmpct_positive_reds": sum(e["historical_release_red"] for e in official), "official_reds_on_neutral_withinarms": sum(e["historical_release_red"] and e["both_within_arm_neutral"] for e in official), "official_reds_on_non_neutral_withinarms": sum(e["historical_release_red"] and not e["both_within_arm_neutral"] for e in official), "cmpct_magnitude_cases": [e for e in effects if e["engine"] == "cmpct" and e["magnitude_crossing"]], "cmpct_official_red_cases": [e for e in official if e["historical_release_red"]]}
    return {"schema": SCHEMA, "classification": "POSTHOC_RESEARCH_ONLY; NO_PRODUCT_OR_GATE_CREDIT", "source": "three original source-identical J24I65 GitHub Actions ABBA ZIP archives", "sample_boundary": "sweep medians of seven repetitions, NOT the individual seven raw measurements", "trials": results, "summaries": totals}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path, help="J24I65 provider evidence bundle containing original three provider ZIPs")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = analyze_provider_bundle(args.bundle.read_bytes())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    for fn, s in result["summaries"].items():
        print(fn, "CMPCT within-arm placebo", s["within_arm_magnitude_crossings"]["cmpct"], "ZIP placebo", s["within_arm_magnitude_crossings"]["zip"], "official reds", s["official_cmpct_positive_reds"], "official reds despite neutral within-arm", s["official_reds_on_neutral_withinarms"])


if __name__ == "__main__":
    main()
