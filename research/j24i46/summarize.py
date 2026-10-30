#!/usr/bin/env python3
"""Independent outcome recomputation for the J24I46 research oracle.

No CMPCT import. Preserve raw samples; do not transform a research win into
a product acceptance signal. A 'green' court means custody and exact bytes only.
"""
import argparse
import hashlib
import json
import statistics as st
from pathlib import Path


def median(xs):
    return st.median(xs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cycles", type=int, default=12)
    args = ap.parse_args()
    source = Path(__file__).with_name("j24i46_seek.py")
    raw = json.loads((args.out / "raw.json").read_text())
    expected_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert raw["source_script_sha256"] == expected_sha, "Measured source differs"
    events = raw["observations"]
    assert len(events) == 2 * 3 * args.cycles * 4
    cases = {}
    for case in ("stereo", "mono"):
        for pos in ("25", "75", "tail"):
            selected = [e for e in events if e["case"] == case and e["position"] == pos]
            assert len(selected) == 4 * args.cycles
            pair = {}
            for mode in ("seek", "full"):
                sample = [e for e in selected if e["mode"] == mode]
                assert len(sample) == 2 * args.cycles
                assert set(e["logical_bytes"] for e in sample) == {4096}
                assert len(set(e["logical_sha256"] for e in sample)) == 1
                pair[mode] = {
                    "n": len(sample),
                    "wall_ms_median": median(e["wall_ns"] for e in sample) / 1e6,
                    "cpu_ms_median": median(e["cpu_ns"] for e in sample) / 1e6,
                    "read_bytes_median": median(e["flac_read_bytes"] for e in sample),
                    "rss_kib_median": median(e["maxrss_kib_process"] for e in sample),
                    "decoded_bytes_returned": sample[0]["decoded_bytes_returned_to_python"],
                    "requested_sha256": sample[0]["logical_sha256"],
                    "wall_ms_min": min(e["wall_ns"] for e in sample) / 1e6,
                    "wall_ms_max": max(e["wall_ns"] for e in sample) / 1e6,
                }
            assert pair["seek"]["requested_sha256"] == pair["full"]["requested_sha256"]
            pair["speedup_full_over_seek"] = pair["full"]["wall_ms_median"] / pair["seek"]["wall_ms_median"]
            pair["read_ratio_full_over_seek"] = pair["full"]["read_bytes_median"] / pair["seek"]["read_bytes_median"]
            cases[case + "/" + pos] = pair
    report = {
        "schema": "cmpct-j24i46-seek-vs-full-audited-v1",
        "scope": "libsndfile selected-PCM oracle only, not native Archive::read_range, not authenticated CMA4",
        "raw_sha256": hashlib.sha256((args.out / "raw.json").read_bytes()).hexdigest(),
        "source_sha256": expected_sha,
        "n": len(events),
        "software": {"numpy": raw["numpy"], "soundfile": raw["soundfile"],
                     "libsndfile": raw["libsndfile"], "python": raw["python"]},
        "platform": raw["platform"],
        "input": raw["cases"],
        "cases": cases
    }
    (args.out / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
