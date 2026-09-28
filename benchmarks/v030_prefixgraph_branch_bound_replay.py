from __future__ import annotations

"""Exact retrospective PrefixGraph branch-and-bound headroom oracle.

Research-only D3/S5 evidence. This does not change shipping bytes or scheduling.
It asks a cheaper question before implementing an early-termination builder:

    Given the exact current level-15 canonical candidate bytes, how many raw-prefix
    compression trials could a mathematically safe monotone lower bound have skipped
    while preserving the historical complete-artifact winner exactly?

The oracle uses the private canonical PrefixGraph owner, current r25 filesystem staging,
and the two frozen workloads used by the historical parallel-anchor promotion. Every
candidate is built by the existing canonical `_serialize_candidate`; this file never
reimplements the archive grammar. Candidate metadata is then read back with the existing
canonical `_read` parser to replay a prospective lower-bound stop point.

The lower bound after member i is:

    HEADER.size + FOOTER.size + sum(final_payload_size[0:i+1])

Both metadata copies and all future payloads are gifted as zero bytes. Since all omitted
physical components are non-negative, the final candidate cannot be smaller than this
bound. Anchors are visited in ascending historical order, so equality with the current
incumbent also cannot win the `(archive_bytes, anchor)` tie law.

A green result is only headroom evidence. Product/runtime/release credit remains zero until
an implementation preserves exact bytes and survives unchanged product gates.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import v030_prefixgraph_parallel_anchor_oracle_v2 as TARGETS
from benchmarks import v030_prefixgraph_parallel_anchor_oracle as PRIOR
from experiments import entropygraph_v030_canonical_final as CANONICAL
from experiments.entropygraph_v030_prefixgraph_process_executor import SUPPORTED_PREFIX_LEVEL

SCHEMA = "cmpct-v030-prefixgraph-branch-bound-replay-v1"
EXPECTED_OWNER = "experiments._v030_canonical_prefixgraph"
MIN_TRIAL_REDUCTION = 0.20


def _level15_codec(pg):
    def codec(prefix: bytes):
        dictionary = pg.zstd.ZstdCompressionDict(prefix, dict_type=pg.zstd.DICT_TYPE_RAWCONTENT)
        return (
            pg.zstd.ZstdCompressor(level=SUPPORTED_PREFIX_LEVEL, dict_data=dictionary),
            dictionary,
        )
    return codec


def _key(blob: bytes, stats: dict) -> tuple[int, int]:
    anchor = stats["anchor"]
    return len(blob), -1 if anchor is None else int(anchor)


def _read_candidate(pg, blob: bytes, path: Path) -> tuple[dict, list[bytes]]:
    path.write_bytes(blob)
    return pg._read(path)


def _trial_mask(raws: list[bytes], anchor: int) -> list[bool]:
    anchor_raw = raws[anchor]
    return [index != anchor and bool(raw) and bool(anchor_raw) for index, raw in enumerate(raws)]


def _replay_anchor(
    pg,
    *,
    blob: bytes,
    raws: list[bytes],
    anchor: int,
    incumbent_bytes: int,
    incumbent_anchor: int | None,
    scratch: Path,
) -> dict:
    if incumbent_anchor is not None and not incumbent_anchor < anchor:
        raise RuntimeError("branch-bound replay requires ascending incumbent anchor order")

    meta, payloads = _read_candidate(pg, blob, scratch)
    if int(meta.get("anchor", -2)) != anchor:
        raise RuntimeError("candidate metadata anchor drift")
    if len(payloads) != len(raws):
        raise RuntimeError("candidate payload count drift")

    trials = _trial_mask(raws, anchor)
    total_trials = sum(trials)
    lower_bound = pg.HEADER.size + pg.FOOTER.size
    spent_trials = 0
    prune_after: int | None = None

    for index, payload in enumerate(payloads):
        if trials[index]:
            spent_trials += 1
        lower_bound += len(payload)
        if lower_bound >= incumbent_bytes and index + 1 < len(payloads):
            prune_after = index
            break

    avoided_trials = total_trials - spent_trials if prune_after is not None else 0
    return {
        "anchor": anchor,
        "complete_archive_bytes": len(blob),
        "incumbent_before_bytes": incumbent_bytes,
        "incumbent_before_anchor": incumbent_anchor,
        "prunable": prune_after is not None,
        "prune_after_member_index": prune_after,
        "partial_lower_bound_bytes": lower_bound,
        "prefix_trials_total": total_trials,
        "prefix_trials_spent_before_prune": spent_trials,
        "prefix_trials_avoided": avoided_trials,
    }


def _measure_target(suite: str, source: Path, work: Path) -> dict:
    pg = CANONICAL.RC.PG
    if pg.__name__ != EXPECTED_OWNER or pg.build.__module__ != EXPECTED_OWNER:
        raise RuntimeError("private canonical PrefixGraph owner drift")

    staged = work / "profile-tree"
    prepared = CANONICAL._prepare_profile_tree(source, staged)
    expected_tree = pg.treehash(staged)
    files = sorted(path for path in staged.rglob("*") if path.is_file())
    rels = [path.relative_to(staged).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    direct_payloads = [pg._compress(raw) for raw in raws]

    original_codec = pg._prefix_codec
    pg._prefix_codec = _level15_codec(pg)
    try:
        direct_blob, direct_stats = pg._serialize_candidate(
            rels, raws, direct_payloads, expected_tree, None
        )
        anchors = pg._anchor_indices(len(raws))
        if anchors != sorted(anchors):
            raise RuntimeError("historical anchor nomination is no longer ascending")

        best = (direct_blob, direct_stats)
        incumbent_anchor: int | None = None
        total_trials = 0
        avoided_trials = 0
        anchor_rows = []
        scratch = work / "candidate-replay.cmpct"

        for anchor in anchors:
            blob, stats = pg._serialize_candidate(
                rels, raws, direct_payloads, expected_tree, anchor
            )
            row = _replay_anchor(
                pg,
                blob=blob,
                raws=raws,
                anchor=anchor,
                incumbent_bytes=len(best[0]),
                incumbent_anchor=incumbent_anchor,
                scratch=scratch,
            )
            total_trials += int(row["prefix_trials_total"])
            avoided_trials += int(row["prefix_trials_avoided"])
            anchor_rows.append(row)

            if _key(blob, stats) < _key(*best):
                best = (blob, stats)
                incumbent_anchor = anchor

        replay_blob, replay_stats = best
        serial_path = work / "serial.cmpct"
        serial_stats = dict(pg.build(staged, serial_path))
    finally:
        pg._prefix_codec = original_codec

    if serial_path.read_bytes() != replay_blob:
        raise RuntimeError(f"replay tournament changed exact winner bytes: {suite}/{source.name}")
    if serial_stats["anchor"] != replay_stats["anchor"]:
        raise RuntimeError(f"replay tournament changed winner anchor: {suite}/{source.name}")

    verified = dict(CANONICAL.RC.READER.strong_verify(serial_path))
    locality = dict(CANONICAL.RC._prefixgraph_locality(serial_path))
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"PrefixGraph strong verification failed: {suite}/{source.name}")
    if not locality.get("passed"):
        raise RuntimeError(f"PrefixGraph locality failed: {suite}/{source.name}")

    reduction = avoided_trials / max(1, total_trials)
    return {
        "label": f"{suite}/{source.name}",
        "files": len(files),
        "anchor_auditions": len(anchors),
        "winner_anchor": serial_stats["anchor"],
        "archive_bytes": serial_path.stat().st_size,
        "tree_sha256": expected_tree,
        "filesystem_manifest_sha256": prepared["manifest_sha256"],
        "prefix_trials_total": total_trials,
        "prefix_trials_avoided": avoided_trials,
        "prefix_trial_reduction": reduction,
        "prunable_anchor_count": sum(1 for row in anchor_rows if row["prunable"]),
        "anchor_rows": anchor_rows,
        "max_member_read_amplification": locality["max_member_read_amplification"],
        "exact_winner_identity": True,
        "material_trial_reduction": reduction >= MIN_TRIAL_REDUCTION,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    targets = TARGETS._find_targets(work_root / "corpus")
    rows = []
    for suite, source in targets:
        with tempfile.TemporaryDirectory(prefix="cmpct-pg-bnb-", dir=work_root) as td:
            row = _measure_target(suite, source, Path(td))
        rows.append(row)
        print(json.dumps(row, separators=(",", ":")), flush=True)

    gate = {
        "exact_target_count": len(rows) == len(PRIOR.TARGETS),
        "exact_winner_identity_all": all(row["exact_winner_identity"] for row in rows),
        "material_trial_reduction_all": all(row["material_trial_reduction"] for row in rows),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": SCHEMA,
        "semantic_owner": EXPECTED_OWNER,
        "prefix_level": SUPPORTED_PREFIX_LEVEL,
        "targets": sorted(PRIOR.TARGETS),
        "minimum_trial_reduction": MIN_TRIAL_REDUCTION,
        "rows": rows,
        "gate": gate,
        "claim_boundary": (
            "Retrospective exact-futility headroom only. It proves only how many current canonical "
            "prefix-compression trials a safe monotone lower bound could have skipped while preserving "
            "the exact winner. It changes no shipping code and grants no product/runtime/release credit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-prefixgraph-branch-bound-replay-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-prefixgraph-branch-bound-replay.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("PrefixGraph branch-and-bound headroom was below the frozen research hurdle")


if __name__ == "__main__":
    main()
