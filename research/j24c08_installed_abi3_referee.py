#!/usr/bin/env python3
"""Independent J24C08 judge: recompute raw-worker medians; negative economics is not a CI crash."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics


def evaluate(data):
    assert data["schema"] == "cmpct-j24c08-installed-economics-v1"
    assert data["prospective"]["strict_over_native_wall_at_least"] == 2.0
    assert data["prospective"]["rss_growth_max_bytes"] == 8 * 1024 * 1024
    source = data["source"]
    profiles = [(65536, 1), (262144, 1), (65536, 256)]
    raw = data["raw_workers"]
    assert len(raw) == 48, f"expected 48 workers, received {len(raw)}"
    manifest = {(f["count"], f["owners"]): f for f in data["fixtures"]}
    assert set(manifest) == set(profiles)
    for f in manifest.values():
        assert f["archive_bytes"] > 0 and len(bytes.fromhex(f["archive_sha256"])) == 32
        assert len(bytes.fromhex(f["logical_sha256"])) == 32
    combos = Counter((r["count"], r["owners"], r["mode"]) for r in raw)
    assert combos == Counter({(n, o, mode): 8 for n, o in profiles for mode in ("strict", "native")})
    ids = set()
    for row in raw:
        assert row["source"] == source
        assert row["mode"] in ("native", "strict")
        assert row["native_available"] is (row["mode"] == "native")
        assert len(row["samples"]) == 5 and [v["sample"] for v in row["samples"]] == list(range(5))
        assert all(v["wall_ns"] > 0 and v["cpu_ns"] >= 0 for v in row["samples"])
        assert row["total_process_wall_ns"] > 0
        ids.add((row["count"], row["owners"], row["cycle"], row["slot"]))
    assert len(ids) == len(raw)
    summary = []
    qualified = True
    for n, o in profiles:
        groups = {}
        for mode in ("strict", "native"):
            matches = [r for r in raw if (r["count"], r["owners"], r["mode"]) == (n, o, mode)]
            groups[mode] = {"wall_ms": statistics.median(statistics.median(
                s["wall_ns"] for s in r["samples"]) for r in matches) / 1e6,
                "cpu_ms": statistics.median(statistics.median(
                s["cpu_ns"] for s in r["samples"]) for r in matches) / 1e6,
                "rss_max_bytes": max((r["rss_bytes"] for r in matches
                                      if r["rss_bytes"] is not None), default=None)}
        ratio = groups["strict"]["wall_ms"] / groups["native"]["wall_ms"]
        rs = [groups["strict"]["rss_max_bytes"], groups["native"]["rss_max_bytes"]]
        rss_growth = (rs[1] - rs[0]) if None not in rs else None
        row = {"count": n, "owners": o, "strict": groups["strict"],
               "native": groups["native"], "wall_ratio": ratio,
               "rss_growth_bytes": rss_growth}
        summary.append(row)
        if o == 1:
            if ratio < 2.0 or (rss_growth is not None and rss_growth > 8 * 1024 * 1024):
                qualified = False
    decision = ("NATIVE_OPTIONAL_READER_ECONOMICS_WORTH_BROADER_D5" if qualified
                else "NATIVE_OPTIONAL_READER_ECONOMICS_INSUFFICIENT")
    return {"decision": decision, "source": source, "evidence_head": data["evidence_head"],
            "platform": data["platform"], "python": data["python"], "profiles": summary,
            "raw_workers": len(raw), "rss_note": "on unsupported hosts RSS is unmeasured, not zero",
            "tier": "installed constructor research, not whole-product or release credit"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    decision = evaluate(data)
    # The referee must reject counterfeit/omitted workers rather than rubber-stamp a badge.
    forgery = json.loads(json.dumps(data))
    forgery["raw_workers"].pop()
    try:
        evaluate(forgery)
    except AssertionError:
        pass
    else:
        raise AssertionError("judge accepted an omitted raw worker")
    args.output.write_text(json.dumps(decision, sort_keys=True, indent=2) + "\n")
    print("J24C08_DECISION=" + decision["decision"])
    print("J24C08_SUMMARY=" + json.dumps(decision["profiles"], sort_keys=True))


if __name__ == "__main__":
    main()
