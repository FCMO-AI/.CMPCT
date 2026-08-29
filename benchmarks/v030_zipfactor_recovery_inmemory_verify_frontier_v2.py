from __future__ import annotations

"""Semantic-owner in-memory verification frontier for recovered ZIP-factor V3.

The v1 in-memory oracle proved the right optimization target but copied the V3 parser into
the benchmark.  That is not an acceptable productization boundary: a second parser can
drift from the format owner.  This v2 experiment removes the duplicated parser entirely.

For each reconstructed exact V3 byte stream, a scoped ``Path.read_bytes`` boundary serves
those bytes to the unchanged ``V3.verify_and_identities`` entry point.  The existing V3
parser therefore remains the single semantic owner for bounds, decompression, SHA-256,
manifest decoding, ZIP reconstruction, identity, locality and decode-unit checks.  The
legacy recovery verifier is still cross-checked every round by the inherited v1 harness.

This is a research timing oracle only.  It changes no archive bytes, recovery rules,
comparators, selector, native/Android implementation or release authority.
"""

import argparse
from contextlib import contextmanager
import json
from pathlib import Path

from benchmarks import v030_zipfactor_recovery_inmemory_verify_frontier as V1
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3


_SENTINEL = Path("/__cmpct_v030_v3_inmemory_verify_sentinel__")


@contextmanager
def _serve_candidate(candidate: bytes):
    original = Path.read_bytes

    def read_bytes(path: Path) -> bytes:
        if Path(path) == _SENTINEL:
            return candidate
        return original(path)

    Path.read_bytes = read_bytes
    try:
        yield
    finally:
        Path.read_bytes = original


def _verify_v3_bytes_semantic_owner(candidate: bytes) -> dict:
    # V3.verify_and_identities -> V3._open -> Path(...).read_bytes.  Only that final
    # byte acquisition is substituted; all parsing and verification remains unchanged.
    with _serve_candidate(candidate):
        return V3.verify_and_identities(_SENTINEL)


@contextmanager
def _semantic_owner_boundary():
    original = V1._verify_v3_bytes
    V1._verify_v3_bytes = _verify_v3_bytes_semantic_owner
    try:
        yield
    finally:
        V1._verify_v3_bytes = original


def run(work_root: Path) -> dict:
    with _semantic_owner_boundary():
        result = dict(V1.run(work_root))
    result["schema"] = "cmpct-v030-zipfactor-recovery-inmemory-verify-frontier-v2"
    contract = dict(result["contract"])
    contract.update(
        {
            "verification_semantics": "unchanged-v3-semantic-owner-served-reconstructed-bytes-in-memory",
            "duplicated_v3_parser_in_benchmark": False,
            "v3_verify_and_identities_is_single_semantic_owner": True,
            "filesystem_roundtrip_removed": True,
            "path_read_boundary_scoped_and_restored": True,
        }
    )
    result["contract"] = contract
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Research-only verifier-cost evidence. Reconstructed recovery bytes are supplied in memory to the unchanged "
        "V3 verify_and_identities semantic owner; the benchmark owns no V3 parser. Legacy recovery verification is "
        "cross-checked each round. Archive bytes, recovery semantics and comparator boundaries are unchanged."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor semantic-owner in-memory verification frontier invalid")


if __name__ == "__main__":
    main()
