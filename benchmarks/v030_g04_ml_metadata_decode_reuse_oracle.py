from __future__ import annotations

"""Research-only exact A/B for duplicate authenticated G0-G4 metadata decoding.

A successful release-reader open currently authenticates the primary metadata and then reads,
decompresses, bounds-checks and validates the duplicate tail metadata again. For ordinary clean
archives those two compressed metadata payloads are byte-identical. Repeating the full decode is
therefore redundant inside one open if reuse is conditioned on exact compressed-byte equality plus
identical raw-size and SHA-256 declarations.

The candidate cache is scoped to one ``_stream_g04`` call. It never reuses across archives or calls,
and any difference in compressed bytes/declarations falls through to the existing semantic owner.
Tail framing, Merkle authentication, physical-record checks, logical hashes, cache budgets, locality
and extraction semantics are untouched. A valid weak result is durable negative evidence; timing
alone never grants production or release credit.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
ROUNDS = 7
MIN_VERIFY_IMPROVEMENT = 0.02
MIN_EXTRACT_IMPROVEMENT = 0.02


class _ExactMetadataReuse:
    def __init__(self, original):
        self.original = original
        self.cached_comp: bytes | None = None
        self.cached_raw_size: int | None = None
        self.cached_sha: bytes | None = None
        self.cached_meta: dict | None = None
        self.calls = 0
        self.reuses = 0

    def __call__(self, comp: bytes, raw_size: int, expected_sha: bytes, expected_count: int | None) -> dict:
        self.calls += 1
        if (
            self.cached_meta is not None
            and int(raw_size) == self.cached_raw_size
            and expected_sha == self.cached_sha
            and comp == self.cached_comp
        ):
            # The first decode was already fully bounded/validated. The tail invocation deliberately
            # carries expected_count=None; reusing the primary's stricter count validation is safe.
            if expected_count is not None and len(self.cached_meta["record_leaf_sha256"]) != int(expected_count):
                raise RuntimeError("cached G0-G4 metadata count mismatch")
            self.reuses += 1
            return self.cached_meta
        meta = self.original(comp, raw_size, expected_sha, expected_count)
        self.cached_comp = comp
        self.cached_raw_size = int(raw_size)
        self.cached_sha = bytes(expected_sha)
        self.cached_meta = meta
        return meta


@contextmanager
def _reuse_decode():
    original = RR._decode_g04_meta
    memo = _ExactMetadataReuse(original)
    RR._decode_g04_meta = memo
    try:
        yield memo
    finally:
        RR._decode_g04_meta = original


def _call(archive: Path, destination: Path | None, *, reuse: bool) -> tuple[dict, float, dict]:
    if destination is not None:
        shutil.rmtree(destination, ignore_errors=True)
    started = time.perf_counter()
    if reuse:
        with _reuse_decode() as memo:
            result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
        counters = {"decode_calls": memo.calls, "exact_reuses": memo.reuses}
    else:
        result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
        counters = {"decode_calls": None, "exact_reuses": 0}
    return result, time.perf_counter() - started, counters


def _equivalent(a: dict, b: dict) -> None:
    keys = (
        "ok", "engine", "reader", "files", "logical_bytes", "tree_sha256",
        "max_member_read_amplification", "max_physical_record_bytes", "max_logical_node_bytes",
        "record_cache_peak_bound_bytes", "node_cache_peak_bound_bytes", "physical_record_reads",
        "tail_metadata_authenticated",
    )
    for key in keys:
        if a.get(key) != b.get(key):
            raise RuntimeError(f"metadata-reuse reader result drift for {key}: {a.get(key)!r} != {b.get(key)!r}")


def _improvement(base: list[float], candidate: list[float]) -> tuple[float, float, float]:
    b = float(statistics.median(base)); c = float(statistics.median(candidate))
    return b, c, (b - c) / b if b else 0.0


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML metadata-reuse target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
        if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
            raise RuntimeError("canonical ML archive failed pre-A/B verification")

        archive_blob = archive.read_bytes()
        archive_sha = hashlib.sha256(archive_blob).hexdigest()
        archive_size = len(archive_blob)
        verify_base: list[float] = []
        verify_reuse: list[float] = []
        extract_base: list[float] = []
        extract_reuse: list[float] = []
        verify_counts: set[tuple[int, int]] = set()
        extract_counts: set[tuple[int, int]] = set()
        samples = []

        for rep in range(ROUNDS):
            order = (False, True) if rep % 2 == 0 else (True, False)
            pair = {}
            for reuse in order:
                label = "reuse" if reuse else "baseline"
                verified, verify_s, verify_counter = _call(archive, None, reuse=reuse)
                dest = work_root / f"extract-{rep}-{label}"
                extracted, extract_s, extract_counter = _call(archive, dest, reuse=reuse)
                if PRODUCT.treehash(dest) != source_tree:
                    raise RuntimeError("metadata-reuse extraction changed user tree")
                pair[label] = {
                    "verify": verified, "verify_s": verify_s, "verify_counter": verify_counter,
                    "extract": extracted, "extract_s": extract_s, "extract_counter": extract_counter,
                }
            _equivalent(pair["baseline"]["verify"], pair["reuse"]["verify"])
            _equivalent(pair["baseline"]["extract"], pair["reuse"]["extract"])
            verify_base.append(float(pair["baseline"]["verify_s"])); verify_reuse.append(float(pair["reuse"]["verify_s"]))
            extract_base.append(float(pair["baseline"]["extract_s"])); extract_reuse.append(float(pair["reuse"]["extract_s"]))
            vc = pair["reuse"]["verify_counter"]; ec = pair["reuse"]["extract_counter"]
            verify_counts.add((int(vc["decode_calls"]), int(vc["exact_reuses"])))
            extract_counts.add((int(ec["decode_calls"]), int(ec["exact_reuses"])))
            samples.append({
                "rep": rep,
                "order": ["reuse" if x else "baseline" for x in order],
                "baseline_verify_s": pair["baseline"]["verify_s"], "reuse_verify_s": pair["reuse"]["verify_s"],
                "baseline_extract_s": pair["baseline"]["extract_s"], "reuse_extract_s": pair["reuse"]["extract_s"],
                "verify_decode_calls": vc["decode_calls"], "verify_exact_reuses": vc["exact_reuses"],
                "extract_decode_calls": ec["decode_calls"], "extract_exact_reuses": ec["exact_reuses"],
                "physical_record_reads": pair["reuse"]["extract"]["physical_record_reads"],
            })

    if archive.stat().st_size != archive_size or hashlib.sha256(archive.read_bytes()).hexdigest() != archive_sha:
        raise RuntimeError("metadata-reuse A/B changed canonical archive bytes")
    vb, vr, vi = _improvement(verify_base, verify_reuse)
    eb, er, ei = _improvement(extract_base, extract_reuse)
    deterministic = len(verify_counts) == 1 and len(extract_counts) == 1
    verify_shape = next(iter(verify_counts)) if deterministic else (0, 0)
    extract_shape = next(iter(extract_counts)) if deterministic else (0, 0)
    valid = deterministic and verify_shape[0] == 2 and verify_shape[1] == 1 and extract_shape[0] == 2 and extract_shape[1] == 1
    promotion = valid and vi >= MIN_VERIFY_IMPROVEMENT and ei >= MIN_EXTRACT_IMPROVEMENT

    return {
        "schema": "cmpct-v030-g04-ml-metadata-decode-reuse-oracle-v1",
        "target": "/".join(TARGET),
        "contract": {
            "release_credit": False,
            "production_change": False,
            "archive_byte_change": False,
            "cache_budget_change": False,
            "physical_read_policy_change": False,
            "reuse_scope": "single G0-G4 reader call",
            "reuse_key": "exact compressed metadata bytes + raw-size declaration + SHA-256 declaration",
            "fallback_on_any_difference": True,
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
        },
        "archive": {"bytes": archive_size, "sha256": archive_sha, "tree_sha256": source_tree, "selected": built.get("selected")},
        "results": {
            "rounds": ROUNDS,
            "median_baseline_verify_s": vb, "median_reuse_verify_s": vr, "verify_improvement_fraction": vi,
            "median_baseline_extract_s": eb, "median_reuse_extract_s": er, "extract_improvement_fraction": ei,
            "verify_decode_shape": list(verify_shape), "extract_decode_shape": list(extract_shape),
            "samples": samples,
        },
        "gate": {
            "experiment_valid": bool(valid),
            "reader_results_identical": True,
            "archive_identity_preserved": True,
            "logical_identity_preserved": True,
            "exactly_one_duplicate_metadata_decode_reused": bool(valid),
            "promotion_signal": bool(promotion),
            "passed": bool(valid),
        },
        "claim_boundary": (
            "Research-only causal A/B. Exact duplicate metadata reuse is scoped to one authenticated open and any "
            "byte/declaration difference falls through to the existing decoder. A positive timing signal still "
            "requires direct semantic-owner implementation plus hostile/fuzz/native/Android/runtime authority."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-metadata-reuse-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-metadata-reuse.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"results": {k: v for k, v in result["results"].items() if k != "samples"}, "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("G0-G4 metadata-decode reuse experiment did not produce one exact duplicate reuse")


if __name__ == "__main__":
    main()
