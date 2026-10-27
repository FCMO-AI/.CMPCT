"""Second-root exact-source receipt check for J24R03; no Reader imports."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

BASE = "c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
CANDIDATE = "70336307312b5b277f0885c0057d2cddab0aefc1"
COUNTS = (1, 4, 4096, 65536)
REGIMES = ("front", "middle", "tail", "balanced", "span")
METRICS = ("open_wall_ms", "open_cpu_ms", "range_wall_ms", "range_cpu_ms")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def original_source_hash(repo: Path, commit: str):
    raw = subprocess.check_output(("git", "show", commit + ":src/cmpct/reader.py"), cwd=repo)
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def expected_query_hash(count: int, regime: str):
    # Independently encode the preregistered distribution, not the producer's output.
    eof = 16 * (count - 1) + 4
    anchor = {"front": 0, "middle": count//2, "tail": count-1}
    selections = ("front", "middle", "tail")
    requests = []
    for k in range(128):
        position_kind = selections[k % 3] if regime == "balanced" else ("middle" if regime == "span" else regime)
        pos = 16 * anchor[position_kind] + (0, 1, 3, 4, 8, 11)[k % 6]
        pos = min(eof - 1, pos)
        limit = (16, 64, 256, 512)[k % 4] if regime == "span" else (1, 4, 12)[k % 3]
        requests.append((pos, min(eof-pos, limit)))
    return hashlib.sha256(json.dumps(requests, separators=(",", ":")).encode()).hexdigest()


def audit(raw_path: Path, repo: Path, base_site: Path, candidate_site: Path):
    evidence = json.loads(raw_path.read_text(encoding="utf-8"))
    require(evidence["schema"] == "j24r03-locality-v1", "schema mismatch")
    observations = evidence["observations"]
    require(len(observations) == 240, "missing/new observations")
    sites = {"baseline": base_site.resolve(), "candidate": candidate_site.resolve()}
    source_hash = {"baseline": original_source_hash(repo, BASE),
                   "candidate": original_source_hash(repo, CANDIDATE)}
    for count in COUNTS:
        entry = evidence["manifest"][str(count)]
        wire, truth = Path(entry["archive"]), Path(entry["truth"])
        require(wire.exists() and truth.exists(), "physical fixture missing")
        require(wire.stat().st_size == entry["archive_bytes"] and
                truth.stat().st_size == entry["logical_bytes"], "fixture size mismatch")
        require(hashlib.sha256(wire.read_bytes()).hexdigest() == entry["archive_sha256"],
                "physical fixture hash mismatch")
        require(hashlib.sha256(truth.read_bytes()).hexdigest() == entry["logical_sha256"],
                "logical oracle hash mismatch")
        require(entry["logical_bytes"] == 16*(count-1)+4, "logical fixture geometry mismatch")
    index = 0
    for round_ in range(3):
        for count in COUNTS:
            entry = evidence["manifest"][str(count)]
            for regime in REGIMES:
                expected = ("baseline", "candidate", "candidate", "baseline") if round_%2 == 0 else ("candidate", "baseline", "baseline", "candidate")
                for source in expected:
                    row = observations[index]
                    index += 1
                    require((row["source"], row["extent_count"], row["regime"], row["round"]) ==
                            (source, count, regime, round_), "ABBA/source/axis order mismatch")
                    require(row["reader_source_sha256"] == source_hash[source], "source hash mismatch")
                    p = Path(row["reader_module"]).resolve()
                    require(p.is_relative_to(sites[source]), "checkout import contamination")
                    require(row["archive_bytes"] == entry["archive_bytes"] and
                            row["logical_bytes"] == entry["logical_bytes"], "input geometry changed")
                    require(row["query_digest"] == expected_query_hash(count, regime),
                            "position/length distribution changed")
                    require(type(row["query_checks"]) is int and row["query_checks"] == 258,
                            "missing exact-byte/OOB controls")
                    for name in METRICS:
                        v = row[name]
                        require(type(v) in (int, float) and math.isfinite(v) and v >= 0,
                                "invalid or nonfinite raw timing: " + name)
                    require(row["open_wall_ms"] > 0 and row["range_wall_ms"] > 0,
                            "missing timed phase")
    medians = {}
    outcomes = {}
    for count in COUNTS:
        medians[str(count)] = {}
        outcomes[str(count)] = {}
        for regime in REGIMES:
            medians[str(count)][regime] = {}
            for source in sites:
                subset = [x for x in observations if x["extent_count"] == count and
                          x["regime"] == regime and x["source"] == source]
                require(len(subset) == 6, "paired distribution incomplete")
                metrics = {m: statistics.median(x[m] for x in subset) for m in METRICS}
                for m in METRICS:
                    claim = evidence["medians"][str(count)][regime][source][m]
                    require(type(claim) in (int, float) and math.isclose(metrics[m], claim,
                            abs_tol=1e-10, rel_tol=1e-10), "incorrect median")
                medians[str(count)][regime][source] = metrics
            pair = medians[str(count)][regime]
            outcomes[str(count)][regime] = {
                "range_wall_speedup": pair["baseline"]["range_wall_ms"] / pair["candidate"]["range_wall_ms"],
                "range_cpu_speedup": pair["baseline"]["range_cpu_ms"] / pair["candidate"]["range_cpu_ms"],
                "candidate_open_wall_delta_ms": pair["candidate"]["open_wall_ms"] - pair["baseline"]["open_wall_ms"],
            }
    transfer = all(outcomes[str(e)][r]["range_wall_speedup"] > minimum
                   for e in (4096, 65536)
                   for r, minimum in (("middle", 10), ("tail", 10), ("balanced", 5)))
    negative = [dict(extents=e, regime=r, slowdown=o["range_wall_speedup"])
                for e, d in outcomes.items() for r, o in d.items()
                if o["range_wall_speedup"] < 1]
    return {"schema": "j24r03-independent-v1",
            "decision": "HIGH_E_TRANSFER_SCOPED" if transfer else "TRANSFER_HYPOTHESIS_NARROWED",
            "raw_observations_verified": len(observations), "baseline_sha256": source_hash["baseline"],
            "candidate_sha256": source_hash["candidate"], "medians": medians,
            "outcomes": outcomes, "negative_controls": negative,
            "limitations": "Selected reads on one public synthetic sparse structural family only; no product promotion"}


def main():
    if len(sys.argv) != 7:
        raise SystemExit("usage: referee raw.json repo base-site candidate-site audit.json mutate-check")
    path, repo, base, candidate, output = [Path(x) for x in sys.argv[1:6]]
    report = audit(path, repo, base, candidate)
    output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    if sys.argv[6] == "mutate-check":
        evidence = json.loads(path.read_text())
        originals = (evidence["observations"][0]["reader_source_sha256"],
                     evidence["observations"][0]["range_wall_ms"])
        for field, fake in (("reader_source_sha256", "0"*64), ("range_wall_ms", float("nan"))):
            evidence["observations"][0][field] = fake
            temp = output.parent / "mutated-evidence.json"
            temp.write_text(json.dumps(evidence), encoding="utf-8")
            try:
                audit(temp, repo, base, candidate)
            except (ValueError, AssertionError):
                pass
            else:
                raise AssertionError("referee accepted mutated evidence: " + field)
            evidence["observations"][0][field] = originals[0] if field.endswith("sha256") else originals[1]
        temp.unlink(missing_ok=True)
    print("J24R03_INDEPENDENT_AUDIT=PASS")
    print("J24R03_TRANSFER="+report["decision"])
    print("J24R03_NEGATIVE_REGIMES="+str(len(report["negative_controls"])))


if __name__ == "__main__":
    main()
