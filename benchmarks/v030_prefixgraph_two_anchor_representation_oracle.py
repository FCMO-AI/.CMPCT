from __future__ import annotations

"""Exact structural-red oracle: can two depth-1 PrefixGraph anchors close Shifted's Zstd size gap?

The shipping family tournaments one global raw-content anchor. Its reader grammar already stores a base index per
prefix record and enforces only that every referenced base is a direct record, so a depth-1 forest is a
representation-level extension rather than deeper dependency recursion. This oracle asks the decisive question
before any product or search optimization: does allowing exactly two direct anchors buy enough complete-artifact
size to beat solid Zstd-19 at all?

Every nominated single-anchor trial is compressed once and reduced to exact csize/hash metadata. All anchor pairs
are then priced with the real MessagePack + Zstd-12 metadata framing, so pair search does not approximate the
complete archive. Only the winning pair is recompressed for byte materialization and independently verified by
the existing PrefixGraph reader. Creation time of this exhaustive oracle is diagnostic only; a size win merely
justifies inventing a bounded fast selector. No shipping grammar, selector, benchmark identity policy or release
threshold changes here.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

TARGET = ("resemblance_hostile_v1", "01_shifted_versions")


def _meta_blob(rels: list[str], raws: list[bytes], records: list[list], expected_tree: str, anchors: tuple[int, ...]) -> bytes:
    meta = {
        "v": 1,
        "engine": "PrefixGraph-depth1-v1",
        "tree_sha256": expected_tree,
        "files": rels,
        "records": records,
        "anchor": anchors[0] if len(anchors) == 1 else -1,
        "max_dependency_depth": 1 if any(row[0] == "prefix" for row in records) else 0,
        "max_file_bytes": PG.MAX_FILE_BYTES,
    }
    # Preserve exact historical metadata for the all-direct/single-anchor parity check. The extra field is added
    # only for the genuinely new two-anchor representation; the existing bounded reader ignores unknown map keys.
    if len(anchors) > 1:
        meta["anchor_set"] = list(anchors)
    raw = PG.msgpack.packb(meta, use_bin_type=True)
    if len(raw) > PG.MAX_META_BYTES:
        raise RuntimeError("two-anchor metadata exceeds PrefixGraph decode-unit ceiling")
    return PG.zstd.ZstdCompressor(level=PG.META_LEVEL).compress(raw)


def _records_for(
    anchors: tuple[int, ...],
    raws: list[bytes],
    direct: list[bytes],
    trials: dict[int, list[tuple[int, bytes] | None]],
) -> list[list]:
    anchor_set = set(anchors)
    records: list[list] = []
    for index, (raw, payload) in enumerate(zip(raws, direct, strict=True)):
        kind = "direct"
        base = -1
        csize = len(payload)
        payload_sha = PG.H(payload)
        if index not in anchor_set and raw:
            choices = []
            for anchor in anchors:
                trial = trials[anchor][index]
                if trial is not None and len(payload) - int(trial[0]) >= PG.MIN_PREFIX_PAYLOAD_SAVING:
                    choices.append((int(trial[0]), int(anchor), bytes(trial[1])))
            if choices:
                chosen_size, chosen_anchor, chosen_sha = min(choices, key=lambda row: (row[0], row[1]))
                kind = "prefix"
                base = chosen_anchor
                csize = chosen_size
                payload_sha = chosen_sha
        records.append([kind, base, len(raw), csize, payload_sha, PG.H(raw)])
    return records


def _price(rels: list[str], raws: list[bytes], direct: list[bytes], expected_tree: str, anchors: tuple[int, ...], trials) -> tuple[int, list[list], bytes]:
    records = _records_for(anchors, raws, direct, trials)
    meta_comp = _meta_blob(rels, raws, records, expected_tree, anchors)
    payload_bytes = sum(int(row[3]) for row in records)
    total = PG.HEADER.size + len(meta_comp) + payload_bytes + len(meta_comp) + PG.FOOTER.size
    return total, records, meta_comp


def _materialize(path: Path, rels: list[str], raws: list[bytes], direct: list[bytes], expected_tree: str, anchors: tuple[int, ...], records: list[list]) -> None:
    compressors = {anchor: PG._prefix_codec(raws[anchor])[0] for anchor in anchors}
    payloads: list[bytes] = []
    materialized_records: list[list] = []
    for index, record in enumerate(records):
        kind, base, usize, expected_csize, expected_payload_sha, logical_sha = record
        payload = direct[index] if kind == "direct" else compressors[int(base)].compress(raws[index])
        if len(payload) != int(expected_csize) or PG.H(payload) != bytes(expected_payload_sha):
            raise RuntimeError("two-anchor recompression differed from priced trial bytes")
        payloads.append(payload)
        materialized_records.append([kind, base, usize, len(payload), PG.H(payload), logical_sha])
    meta_comp = _meta_blob(rels, raws, materialized_records, expected_tree, anchors)
    meta_raw = PG.zstd.ZstdDecompressor().decompress(meta_comp, max_output_size=PG.MAX_META_BYTES)
    header = PG.HEADER.pack(PG.MAGIC, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    footer = PG.FOOTER.pack(PG.TAIL, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    path.write_bytes(header + meta_comp + b"".join(payloads) + meta_comp + footer)


def run(work_root: Path) -> dict:
    started = time.perf_counter()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]

    staged = work_root / "r25-stage"
    CANON._prepare_profile_tree(source, staged)
    files = sorted(path for path in staged.rglob("*") if path.is_file())
    rels = [path.relative_to(staged).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    if not raws or len(raws) > PG.MAX_FILES or any(len(raw) > PG.MAX_FILE_BYTES for raw in raws):
        raise RuntimeError("Shifted r25 stage left PrefixGraph representation envelope")
    expected_tree = PG._treehash_parts(rels, raws)
    direct = [PG._compress(raw) for raw in raws]
    anchors = PG._anchor_indices(len(raws))

    trials: dict[int, list[tuple[int, bytes] | None]] = {}
    for anchor in anchors:
        compressor, _dictionary = PG._prefix_codec(raws[anchor])
        row: list[tuple[int, bytes] | None] = []
        for index, raw in enumerate(raws):
            if index == anchor or not raw or not raws[anchor]:
                row.append(None)
                continue
            payload = compressor.compress(raw)
            row.append((len(payload), PG.H(payload)))
        trials[anchor] = row

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)
    all_direct_price = _price(rels, raws, direct, expected_tree, (), trials)[0]
    single_prices = {anchor: _price(rels, raws, direct, expected_tree, (anchor,), trials)[0] for anchor in anchors}
    projected_shipping = min([all_direct_price, *single_prices.values()])
    if projected_shipping != shipping.stat().st_size:
        raise RuntimeError(
            f"pair oracle single-anchor pricing drift: projected={projected_shipping} shipping={shipping.stat().st_size}"
        )

    pair_rows = []
    best = None
    for left_index, left in enumerate(anchors):
        for right in anchors[left_index + 1:]:
            pair = (left, right)
            priced, records, _meta = _price(rels, raws, direct, expected_tree, pair, trials)
            pair_rows.append({"anchors": list(pair), "archive_bytes": priced})
            key = (priced, pair)
            if best is None or key < best[0]:
                best = (key, pair, records)
    if best is None:
        raise RuntimeError("Shifted stage did not expose two nominated PrefixGraph anchors")

    best_bytes = int(best[0][0])
    best_pair = best[1]
    best_records = best[2]
    candidate = work_root / "two-anchor-prefixgraph.cmpct"
    _materialize(candidate, rels, raws, direct, expected_tree, best_pair, best_records)
    if candidate.stat().st_size != best_bytes:
        raise RuntimeError("materialized two-anchor archive differs from exact projected price")
    verified = PG.strong_verify(candidate)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError("existing PrefixGraph reader rejected two-anchor depth-1 forest")

    ext_parent = work_root / "external"
    ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-extracted")
    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(
        normalized,
        work_root / "shifted.tar.zst",
        work_root / "zstd-extracted",
        zstd_work,
    )
    source_tree = EXT._tree(normalized)
    EXT._verify_extracted(work_root / "zip-extracted", source_tree, "ZIP")
    if zstd_row.get("available"):
        EXT._verify_extracted(work_root / "zstd-extracted", source_tree, "Zstd-19")

    zstd_bytes = int(zstd_row["archive_bytes"]) if zstd_row.get("available") else None
    strict_size_win = bool(
        best_bytes < int(zip_row["archive_bytes"])
        and zstd_bytes is not None
        and best_bytes < zstd_bytes
    )
    return {
        "schema": "cmpct-v030-prefixgraph-two-anchor-representation-oracle-v2",
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "r25_manifest_encoding": "filesystem-v1",
        "files": len(raws),
        "nominated_anchors": len(anchors),
        "evaluated_pairs": len(pair_rows),
        "single_anchor_pricing_exact": True,
        "shipping_prefixgraph_bytes": shipping.stat().st_size,
        "shipping_prefixgraph_sha256": hashlib.sha256(shipping.read_bytes()).hexdigest(),
        "two_anchor_bytes": best_bytes,
        "two_anchor_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "best_pair": list(best_pair),
        "saving_vs_shipping_prefixgraph_bytes": shipping.stat().st_size - best_bytes,
        "zip_bytes": int(zip_row["archive_bytes"]),
        "zstd19_bytes": zstd_bytes,
        "margin_vs_zstd19_bytes": None if zstd_bytes is None else zstd_bytes - best_bytes,
        "strict_size_win_vs_zip_and_zstd19": strict_size_win,
        "reader_reused_without_depth_change": True,
        "max_dependency_depth": 1,
        "tree_sha256": expected_tree,
        "verified_tree_sha256": verified.get("tree_sha256"),
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "product_create_time_claim": False,
        "decision": "PROMOTE_FAST_SELECTOR_RESEARCH" if strict_size_win else "ESCALATE_REPRESENTATION_BEYOND_TWO_ANCHORS",
        "claim_boundary": "Structural representation-potential oracle only. Exhaustive trial construction is not a shippable creation-time policy and grants zero release credit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-two-anchor-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-two-anchor.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
