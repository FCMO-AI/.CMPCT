from __future__ import annotations

"""Focused causality proof for the v0.30 r24 nested-container locality repair.

The frozen deflate-family workload contains 14 nested ZIP bundles. Mature r24 deliberately stores 8+ nested
containers as slices of one solid ``S_PACK`` blob. That is excellent for size but causes one selected ZIP read to
decode the entire 14-ZIP cohort. v0.30 cannot publish such a representation because member-read amplification is
frozen at <=8x.

This oracle builds the exact same source twice:
- generic/historical Builder policy, which must remain unchanged and reproduce the oversized cohort;
- promoted shipping-r24 policy, which must use the same r24 grammar while splitting that cohort into bounded packs.

It also performs an exhaustive research-only search over every unique 7+7 split of the 14 exact ZIP byte streams.
Seven is the maximum possible group cardinality here: with eight unequal positive-size members, group bytes are
strictly greater than ``8 * smallest_member``. Every searched split therefore obeys the same immutable <=8x / <=8
MiB decoded-context law. Each group is scored with the exact Zstd levels used by r24 container packs, and the best
partition is then rebuilt as a *real revision-24 archive* by temporarily substituting only the grouping function.
That exact archive is strongly verified and measured through public ``CMPCT.read`` calls. The search cannot alter
shipping bytes; it exists to determine whether the locality byte tax is caused by lexical partitioning or by the
unavoidable loss of one shared compression context.

Both shipping/historical artifacts are strongly verified. Locality is measured through actual public ``CMPCT.read``
calls while tracking every decoded physical blob. The result preserves the byte cost of the repair rather than
hiding it.
"""

import argparse
import itertools
import json
from pathlib import Path
import shutil

import cmpct.v030_release_locality as LOCALITY
from cmpct import codec as CODEC
from cmpct.builder import Builder
from cmpct.codec import K_FILE, S_PACK
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_release_product as PRODUCT
from benchmarks import resemblance_hostile_corpus_v1 as CORPUS


def _pack_count(archive: Path) -> int:
    with CMPCT(archive) as reader:
        return len({
            bytes(row[6][1])
            for row in reader.files
            if row[1] == K_FILE and row[6] and row[6][0] == S_PACK
        })


def _all_member_locality(archive: Path) -> dict:
    class Tracking(CMPCT):
        def __init__(self, path):
            super().__init__(path)
            self.observed: set[int] = set()
        def _blob(self, idx):
            self.observed.add(int(idx))
            return super()._blob(idx)

    rows = []
    with Tracking(archive) as reader:
        verified_files = reader.verify()
        for row in reader.files:
            if row[1] != K_FILE:
                continue
            rel, _kind, _mode, _mtime, size, _digest, _storage = row
            reader.observed.clear()
            raw = bytes(reader.read(rel))
            if len(raw) != int(size):
                raise RuntimeError(f"r24 read length drift for {rel!r}")
            decoded = sum(int(reader.blobs[idx][1]) for idx in reader.observed)
            amp = max(len(raw), decoded) / max(1, len(raw))
            rows.append({
                "path": rel,
                "logical_bytes": len(raw),
                "decoded_context_bytes": decoded,
                "amplification": amp,
            })
    return {
        "verified_files": verified_files,
        "rows": rows,
        "max_amplification": max((row["amplification"] for row in rows), default=0.0),
    }


def _container_members(source: Path) -> list[tuple[str, bytes]]:
    members = [(path.name, path.read_bytes()) for path in sorted(source.glob("*.zip"))]
    if len(members) != 14:
        raise RuntimeError(f"partition oracle expects exact frozen 14-ZIP cohort, got {len(members)}")
    return members


def _group_payload_bytes(raw: bytes) -> int:
    # Builder._encode_candidate uses exactly these levels for .cmpct-container-pack candidates and charges the
    # tiny MessagePack level metadata. All searched groups are strongly compressible, but retain the RAW fallback
    # arithmetic so the score remains faithful if the corpus changes unexpectedly.
    best = len(raw)
    for level in (15, 12, 9):
        comp = CODEC.zc(raw, level)
        meta = __import__("msgpack").packb([level], use_bin_type=True)
        if len(comp) + len(meta) + 16 < len(raw):
            best = min(best, len(comp) + len(meta))
    return best


def _partition_search(source: Path, work_root: Path) -> dict:
    members = _container_members(source)
    raws = [raw for _name, raw in members]
    names = [name for name, _raw in members]
    n = len(members)
    if n != 14:
        raise AssertionError(n)

    # Fix member 0 in group A so complements are not scored twice: C(13,6)=1716 unique 7+7 partitions.
    cache: dict[tuple[int, ...], tuple[int, int, float]] = {}

    def score(indices: tuple[int, ...]) -> tuple[int, int, float]:
        key = tuple(sorted(indices))
        cached = cache.get(key)
        if cached is not None:
            return cached
        group_raw = b"".join(raws[i] for i in key)
        smallest = min(len(raws[i]) for i in key)
        limit = min(LOCALITY.MAX_DECODE_UNIT_BYTES, LOCALITY.MAX_MEMBER_READ_AMPLIFICATION * smallest)
        if len(group_raw) > limit:
            raise RuntimeError("searched partition escaped immutable locality envelope")
        result = (_group_payload_bytes(group_raw), len(group_raw), len(group_raw) / max(1, smallest))
        cache[key] = result
        return result

    all_indices = set(range(n))
    lexical_a = tuple(range(7))
    lexical_b = tuple(range(7, 14))
    lexical_score = score(lexical_a)[0] + score(lexical_b)[0]
    best = (lexical_score, lexical_a, lexical_b)
    evaluated = 0
    for rest in itertools.combinations(range(1, n), 6):
        a = (0, *rest)
        b = tuple(sorted(all_indices - set(a)))
        total = score(a)[0] + score(b)[0]
        evaluated += 1
        if total < best[0] or (total == best[0] and (a, b) < (best[1], best[2])):
            best = (total, a, b)

    best_score, best_a, best_b = best
    candidate = work_root / "partition-best-r24.cmpct"
    original_groups = LOCALITY._groups

    def forced_groups(items):
        # LOCALITY supplies rows in lexical order. Pin by row name rather than object identity so this remains an
        # exact representation experiment, not a benchmark mutation.
        by_name = {str(row[0]): (row, raw) for row, raw in items}
        ordered = [by_name[name] for name in names]
        return [
            [ordered[i] for i in best_a],
            [ordered[i] for i in best_b],
        ]

    try:
        LOCALITY._groups = forced_groups
        stats = PRODUCT._locality_bounded_r24_build(source, candidate)
    finally:
        LOCALITY._groups = original_groups

    locality = _all_member_locality(candidate)
    verified = PRODUCT.strong_verify(candidate)
    return {
        "partitions_evaluated": evaluated,
        "unique_group_payloads_scored": len(cache),
        "lexical_group_a": [names[i] for i in lexical_a],
        "lexical_group_b": [names[i] for i in lexical_b],
        "lexical_payload_bytes": lexical_score,
        "best_group_a": [names[i] for i in best_a],
        "best_group_b": [names[i] for i in best_b],
        "best_payload_bytes": best_score,
        "payload_saving_vs_lexical_bytes": lexical_score - best_score,
        "archive_bytes": candidate.stat().st_size,
        "release_byte_knobs": stats.get("release_byte_knobs"),
        "pack_count": _pack_count(candidate),
        **locality,
        "strong_verify": verified,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"
    historical_tree = CORPUS.tree_hash(source)

    historical = work_root / "historical-r24.cmpct"
    shipping = work_root / "shipping-r24.cmpct"

    Builder(source).build(historical)
    shipping_stats = PRODUCT._locality_bounded_r24_build(source, shipping)

    historical_locality = _all_member_locality(historical)
    shipping_locality = _all_member_locality(shipping)
    shipping_verify = PRODUCT.strong_verify(shipping)
    expected_product_tree = PRODUCT.treehash(source)
    partition_search = _partition_search(source, work_root)

    result = {
        "schema": "cmpct-v030-r24-nested-container-locality-v2",
        "claim_boundary": "shipping r24 encoder grouping only; exhaustive partition search is research-only and changes no shipping bytes",
        "workload": "resemblance_hostile_v1/04_deflate_family",
        "historical_tree_sha256": historical_tree,
        "product_tree_sha256": expected_product_tree,
        "historical": {
            "archive_bytes": historical.stat().st_size,
            "pack_count": _pack_count(historical),
            **historical_locality,
        },
        "shipping": {
            "archive_bytes": shipping.stat().st_size,
            "pack_count": _pack_count(shipping),
            "release_byte_knobs": shipping_stats.get("release_byte_knobs"),
            **shipping_locality,
            "strong_verify": shipping_verify,
        },
        "partition_search": partition_search,
    }
    result["byte_delta_shipping_vs_historical"] = result["shipping"]["archive_bytes"] - result["historical"]["archive_bytes"]
    result["byte_delta_best_partition_vs_shipping"] = partition_search["archive_bytes"] - result["shipping"]["archive_bytes"]
    result["gate"] = {
        "historical_reproduces_single_pack": result["historical"]["pack_count"] == 1,
        "historical_reproduces_over_8x": result["historical"]["max_amplification"] > 8.0,
        "shipping_splits_pack": result["shipping"]["pack_count"] >= 2,
        "shipping_all_members_le_8x": result["shipping"]["max_amplification"] <= 8.0,
        "shipping_strong_verify": bool(shipping_verify.get("ok")) and shipping_verify.get("tree_sha256") == expected_product_tree,
        "same_verified_file_count": result["shipping"]["verified_files"] == result["historical"]["verified_files"],
        "partition_search_exhaustive": partition_search["partitions_evaluated"] == 1716,
        "best_partition_all_members_le_8x": partition_search["max_amplification"] <= 8.0,
        "best_partition_strong_verify": bool(partition_search["strong_verify"].get("ok")) and partition_search["strong_verify"].get("tree_sha256") == expected_product_tree,
    }
    result["gate"]["passed"] = all(result["gate"].values())
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-container-locality-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-container-locality.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "historical": result["historical"],
        "shipping": result["shipping"],
        "partition_search": result["partition_search"],
        "byte_delta": result["byte_delta_shipping_vs_historical"],
        "best_partition_delta": result["byte_delta_best_partition_vs_shipping"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("r24 nested-container locality causality gate failed")


if __name__ == "__main__":
    main()
