from __future__ import annotations

"""Resource-tight v2 of the capped token dependency certificate.

The v1 prototype capped the visited set but materialized an 8 KiB pending stack and therefore did not
literally prove its stated live-query-state bound. Preserve v1 as a non-authoritative attempt. This v2
walks each requested byte's single DEFLATE parent chain directly, so the only position-bearing query
state is the visited set itself, capped at LIMIT+1. All scientific thresholds, corpora and exact-oracle
comparisons are otherwise unchanged.
"""

import argparse
from bisect import bisect_right
import json
import os
from pathlib import Path

from benchmarks import v030_r4_capped_token_dependency_certificate as BASE

SCHEMA = "cmpct-v030-r4-capped-token-dependency-certificate-v2"


def capped_closure(tokens: dict, start: int, end: int) -> tuple[int, bool, int]:
    """Single-parent chain walk with no request-sized stack; visited state is hard-capped."""
    starts = tokens["starts"]
    ends = tokens["ends"]
    distances = tokens["distances"]
    seen: set[int] = set()
    peak = 0
    for node in range(start, end):
        p = node
        while p not in seen:
            seen.add(p)
            peak = max(peak, len(seen))
            if len(seen) >= BASE.CAP:
                return len(seen), True, peak
            i = bisect_right(starts, p) - 1
            if i < 0 or p >= ends[i]:
                raise RuntimeError(f"token lookup failed at output byte {p}")
            distance = distances[i]
            if not distance:
                break
            p -= distance
            if p < 0:
                raise RuntimeError("negative DEFLATE parent")
    return len(seen), False, peak


def run(work: Path) -> dict:
    # compare_stream resolves capped_closure through BASE module globals, so replace only the candidate
    # traversal mechanism; the frozen corpus, token parser, exact oracle and classification remain v1.
    BASE.capped_closure = capped_closure
    d = BASE.run(work)
    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["contract"]["v1_stack_accounting_rejected_before_adjudication"] = True
    d["contract"]["candidate_query_position_state_is_only_capped_seen_set"] = True
    d["next_if_supported"] = (
        "serialize a compact authenticated token/range index and implement a physical selective reader; "
        "charge stored bytes, pread bytes/ranges, auth/recovery, CPU/wall/RSS and reconstruction work "
        "before selector integration"
    )
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-capped-token-v2-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-capped-token-v2.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"summary": d["summary"], "hypothesis": d["hypothesis"], "controls": d["controls"]}, indent=2))


if __name__ == "__main__":
    main()
