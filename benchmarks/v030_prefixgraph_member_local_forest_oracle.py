from __future__ import annotations

"""R4 structural oracle: member-local PrefixGraph forest capacity on Shifted.

Small global anchor sets are saturated: exhaustive two- and three-anchor depth-1
extensions miss the strict Zstd-19 size boundary, and the three-anchor candidate is
materially worse than shipping. This oracle changes the representation boundary.
Every member may be stored directly or prefix-compressed from another member's raw
bytes. A directed minimum spanning arborescence rooted at a synthetic direct root
selects the payload-minimum acyclic forest. We then materialize the exact chosen
payloads, charge real MessagePack/Zstd metadata plus duplicated recovery metadata and
framing, and independently reconstruct every member through the experimental forest.

The search is research-only. It is intentionally exhaustive and does not claim product
creation-time competitiveness. A size win only authorizes the next prerequisite:
bound dependency depth/locality and derive a content-agnostic fast construction law.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import msgpack
import networkx as nx
import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_prefixgraph_two_anchor_representation_oracle as BASE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

TARGET = BASE.TARGET
ROOT = "__direct_root__"
MAGIC = b"CMPNXPF\0"
TAIL = b"CMPNXPFT"


def _depths(parents: dict[int, int | None]) -> dict[int, int]:
    memo: dict[int, int] = {}
    visiting: set[int] = set()

    def one(i: int) -> int:
        if i in memo:
            return memo[i]
        if i in visiting:
            raise RuntimeError("forest solver returned a dependency cycle")
        visiting.add(i)
        parent = parents[i]
        depth = 0 if parent is None else one(parent) + 1
        visiting.remove(i)
        memo[i] = depth
        return depth

    for i in parents:
        one(i)
    return memo


def _verify_records(raws: list[bytes], payloads: list[bytes], records: list[list]) -> list[bytes]:
    cache: dict[int, bytes] = {}
    visiting: set[int] = set()

    def decode(i: int) -> bytes:
        if i in cache:
            return cache[i]
        if i in visiting:
            raise RuntimeError("experimental forest decode cycle")
        visiting.add(i)
        kind, base, usize, _csize, payload_sha, logical_sha = records[i]
        payload = payloads[i]
        if PG.H(payload) != bytes(payload_sha):
            raise RuntimeError("experimental forest payload authentication")
        if kind == "direct":
            raw = zstd.ZstdDecompressor().decompress(payload, max_output_size=int(usize))
        elif kind == "prefix":
            parent = decode(int(base))
            dictionary = zstd.ZstdCompressionDict(parent, dict_type=zstd.DICT_TYPE_RAWCONTENT)
            raw = zstd.ZstdDecompressor(dict_data=dictionary).decompress(payload, max_output_size=int(usize))
        else:
            raise RuntimeError("experimental forest record kind")
        if len(raw) != int(usize) or PG.H(raw) != bytes(logical_sha):
            raise RuntimeError("experimental forest logical authentication")
        visiting.remove(i)
        cache[i] = raw
        return raw

    return [decode(i) for i in range(len(records))]


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

    graph = nx.DiGraph()
    graph.add_node(ROOT)
    trials: dict[tuple[int, int], tuple[int, bytes]] = {}
    for target, payload in enumerate(direct):
        graph.add_edge(ROOT, target, weight=len(payload), kind="direct")
    exact_prefix_trials = 0
    for base, base_raw in enumerate(raws):
        if not base_raw:
            continue
        compressor, _dictionary = PG._prefix_codec(base_raw)
        for target, raw in enumerate(raws):
            if target == base or not raw:
                continue
            payload = compressor.compress(raw)
            trials[(base, target)] = (len(payload), PG.H(payload))
            graph.add_edge(base, target, weight=len(payload), kind="prefix")
            exact_prefix_trials += 1

    arb = nx.minimum_spanning_arborescence(graph, attr="weight", preserve_attrs=True)
    if ROOT not in arb or arb.in_degree(ROOT) != 0:
        raise RuntimeError("minimum arborescence is not rooted at the synthetic direct root")

    parents: dict[int, int | None] = {}
    for target in range(len(raws)):
        incoming = list(arb.in_edges(target, data=True))
        if len(incoming) != 1:
            raise RuntimeError("minimum arborescence did not assign exactly one storage parent")
        parent, _target, _data = incoming[0]
        parents[target] = None if parent == ROOT else int(parent)
    depths = _depths(parents)

    payloads: list[bytes] = []
    records: list[list] = []
    direct_records = 0
    prefix_records = 0
    for target, raw in enumerate(raws):
        parent = parents[target]
        if parent is None:
            payload = direct[target]
            kind = "direct"
            base = -1
            direct_records += 1
        else:
            compressor, _dictionary = PG._prefix_codec(raws[parent])
            payload = compressor.compress(raw)
            priced = trials[(parent, target)]
            if len(payload) != priced[0] or PG.H(payload) != priced[1]:
                raise RuntimeError("forest recompression differs from priced pairwise trial")
            kind = "prefix"
            base = parent
            prefix_records += 1
        payloads.append(payload)
        records.append([kind, base, len(raw), len(payload), PG.H(payload), PG.H(raw)])

    meta = {
        "v": 1,
        "engine": "PrefixGraph-forest-v1",
        "tree_sha256": expected_tree,
        "files": rels,
        "records": records,
        "max_dependency_depth": max(depths.values(), default=0),
        "max_file_bytes": PG.MAX_FILE_BYTES,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > PG.MAX_META_BYTES:
        raise RuntimeError("forest metadata exceeds decode-unit ceiling")
    meta_comp = zstd.ZstdCompressor(level=PG.META_LEVEL).compress(meta_raw)
    header = PG.HEADER.pack(MAGIC, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    footer = PG.FOOTER.pack(TAIL, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    blob = header + meta_comp + b"".join(payloads) + meta_comp + footer
    candidate = work_root / "member-local-forest.cmpct"
    candidate.write_bytes(blob)

    verified_raws = _verify_records(raws, payloads, records)
    verified_tree = PG._treehash_parts(rels, verified_raws)
    if verified_tree != expected_tree:
        raise RuntimeError("experimental member-local forest changed logical tree")

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)

    ext_parent = work_root / "external"
    ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-extracted")
    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(normalized, work_root / "shifted.tar.zst", work_root / "zstd-extracted", zstd_work)
    source_tree = EXT._tree(normalized)
    EXT._verify_extracted(work_root / "zip-extracted", source_tree, "ZIP")
    if zstd_row.get("available"):
        EXT._verify_extracted(work_root / "zstd-extracted", source_tree, "Zstd-19")
    zstd_bytes = int(zstd_row["archive_bytes"]) if zstd_row.get("available") else None

    optimistic_payload_floor = sum(
        min([len(direct[target]), *[trials[(base, target)][0] for base in range(len(raws)) if (base, target) in trials]])
        for target in range(len(raws))
    )
    optimistic_complete_floor = PG.HEADER.size + PG.FOOTER.size + optimistic_payload_floor
    strict_size_win = bool(zstd_bytes is not None and len(blob) < zstd_bytes and len(blob) < int(zip_row["archive_bytes"]))
    if strict_size_win:
        decision = "PROMOTE_NEXT_PREREQUISITE"
        next_test = "solve a depth/locality-bounded member-local forest and derive a content-agnostic fast admission/construction law"
    elif zstd_bytes is not None and optimistic_complete_floor >= zstd_bytes:
        decision = "RETIRE_FAMILY"
        next_test = "invent a non-prefix physical representation; even the zero-metadata per-member prefix floor loses"
    else:
        decision = "ITERATE_SAME_FAMILY"
        next_test = "separate arborescence-vs-metadata debt and test depth-bounded cluster-owned bases before further global-anchor work"

    return {
        "schema": "cmpct-v030-prefixgraph-member-local-forest-oracle-v1",
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "files": len(raws),
        "exact_prefix_trials": exact_prefix_trials,
        "direct_records": direct_records,
        "prefix_records": prefix_records,
        "max_dependency_depth": max(depths.values(), default=0),
        "shipping_prefixgraph_bytes": shipping.stat().st_size,
        "shipping_prefixgraph_sha256": hashlib.sha256(shipping.read_bytes()).hexdigest(),
        "forest_bytes": len(blob),
        "forest_sha256": hashlib.sha256(blob).hexdigest(),
        "payload_bytes": sum(len(p) for p in payloads),
        "meta_raw_bytes": len(meta_raw),
        "meta_comp_bytes": len(meta_comp),
        "optimistic_zero_metadata_unconstrained_floor_bytes": optimistic_complete_floor,
        "saving_vs_shipping_prefixgraph_bytes": shipping.stat().st_size - len(blob),
        "zip_bytes": int(zip_row["archive_bytes"]),
        "zstd19_bytes": zstd_bytes,
        "margin_vs_zstd19_bytes": None if zstd_bytes is None else zstd_bytes - len(blob),
        "strict_size_win_vs_zip_and_zstd19": strict_size_win,
        "tree_sha256": expected_tree,
        "verified_tree_sha256": verified_tree,
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "product_create_time_claim": False,
        "payload_optimal_complete_archive_claim": False,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "active_saturation": ["S2", "S3", "S4"],
            "research_priority_score": 94,
            "rps_rationale": "15 necessity + 20 upside + 15 root-cause fit + 6 generality + 15 information gain + 8 decisive efficiency + 10 survival path + 5 portability = 94",
            "measured_gap_change_bytes": shipping.stat().st_size - len(blob),
            "strongest_self_critique": "The unconstrained forest can export debt into dependency depth, locality, recovery and construction search; a size win is capacity evidence only, not a shippable mechanism.",
            "terminal_decision": decision,
            "next_decisive_test": next_test,
        },
        "decision": decision,
        "claim_boundary": "R4 structural-capacity oracle only; exhaustive all-pairs construction is not a product selector and grants zero release credit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-member-local-forest-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-member-local-forest.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
