from __future__ import annotations

"""Research-only census for cross-member decode reuse in canonical ML G0-G4.

This instrument does not time a candidate and grants no release credit. It asks a
narrow causal question before another native-reader mutation: how much logical node
reconstruction and physical-record decoding is repeated when each member owns an
independent decode context, versus an operation-scoped cache like the Python reader.
"""

import json
from pathlib import Path
import shutil

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")


def _node_length(desc: list) -> int:
    kind = desc[0]
    if kind == "direct":
        return int(desc[3])
    if kind in ("delta", "mosaic"):
        return int(desc[3])
    if kind in ("delta_pack", "pack_mosaic"):
        return int(desc[5])
    raise RuntimeError(f"unknown node kind {kind!r}")


def _node_dependencies(nodes: list, node_id: int, out: set[int]) -> None:
    if node_id in out:
        return
    out.add(node_id)
    desc = nodes[node_id]
    kind = desc[0]
    if kind in ("delta", "delta_pack"):
        _node_dependencies(nodes, int(desc[1]), out)
    elif kind == "mosaic":
        for base in desc[1]:
            _node_dependencies(nodes, int(base), out)
    elif kind == "pack_mosaic":
        for base in desc[4]:
            _node_dependencies(nodes, int(base), out)


def _node_records(nodes: list, node_id: int, out: set[int]) -> None:
    desc = nodes[node_id]
    kind = desc[0]
    if kind == "direct":
        out.add(int(desc[1]))
    elif kind in ("delta", "delta_pack"):
        _node_records(nodes, int(desc[1]), out)
        out.add(int(desc[2]))
    elif kind == "mosaic":
        for base in desc[1]:
            _node_records(nodes, int(base), out)
        out.add(int(desc[2]))
    elif kind == "pack_mosaic":
        for base in desc[4]:
            _node_records(nodes, int(base), out)
        out.add(int(desc[1]))
    else:
        raise RuntimeError(f"unknown node kind {kind!r}")


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    archive = work_root / "ml.cmpct"
    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
    if archive.read_bytes()[:8] != RR.G04.MAG:
        raise RuntimeError("ML target did not select canonical G0-G4")

    stream, meta, record_start, offsets, _merkle, _tail = RR._g04_open(archive)
    try:
        record_usize: list[int] = []
        record_codec: list[int] = []
        for rel in offsets:
            stream.seek(int(record_start) + int(rel))
            header = stream.read(RR.PH.size)
            if len(header) != RR.PH.size:
                raise RuntimeError("short G0-G4 physical header")
            codec, usize, _csize, _crc, _sha = RR.PH.unpack(header)
            record_codec.append(int(codec))
            record_usize.append(int(usize))
    finally:
        stream.close()

    nodes = meta["nodes"]
    files = meta["files"]
    per_member_node_closure_bytes = 0
    per_member_record_decode_bytes = 0
    per_member_node_refs = 0
    per_member_record_refs = 0
    all_nodes: set[int] = set()
    all_records: set[int] = set()
    preflate_members = 0

    for desc in files.values():
        member_nodes: set[int] = set()
        member_records: set[int] = set()
        if desc[0] == "preflate":
            preflate_members += 1
            member_records.add(int(desc[1]))
        elif desc[0] == "nodes":
            for node_id in desc[1]:
                _node_dependencies(nodes, int(node_id), member_nodes)
                _node_records(nodes, int(node_id), member_records)
        else:
            raise RuntimeError(f"unknown file kind {desc[0]!r}")
        per_member_node_refs += len(member_nodes)
        per_member_record_refs += len(member_records)
        per_member_node_closure_bytes += sum(_node_length(nodes[node_id]) for node_id in member_nodes)
        per_member_record_decode_bytes += sum(record_usize[record_id] for record_id in member_records)
        all_nodes.update(member_nodes)
        all_records.update(member_records)

    unique_node_bytes = sum(_node_length(nodes[node_id]) for node_id in all_nodes)
    unique_record_bytes = sum(record_usize[record_id] for record_id in all_records)
    repeated_node_bytes = per_member_node_closure_bytes - unique_node_bytes
    repeated_record_bytes = per_member_record_decode_bytes - unique_record_bytes
    preflate_records = sum(1 for codec in record_codec if codec == RR.G04.O.CODEC_PREFLATE)

    return {
        "schema": "cmpct-v030-g04-ml-cross-member-reuse-census-v1",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "files": len(files),
        "nodes": len(nodes),
        "records": len(offsets),
        "preflate_members": preflate_members,
        "preflate_records": preflate_records,
        "per_member_node_closure_refs": per_member_node_refs,
        "operation_unique_node_refs": len(all_nodes),
        "per_member_node_closure_bytes": per_member_node_closure_bytes,
        "operation_unique_node_bytes": unique_node_bytes,
        "cross_member_repeated_node_bytes": repeated_node_bytes,
        "node_reconstruction_reuse_fraction": repeated_node_bytes / max(per_member_node_closure_bytes, 1),
        "per_member_record_refs": per_member_record_refs,
        "operation_unique_record_refs": len(all_records),
        "per_member_record_decode_bytes": per_member_record_decode_bytes,
        "operation_unique_record_decode_bytes": unique_record_bytes,
        "cross_member_repeated_record_decode_bytes": repeated_record_bytes,
        "record_decode_reuse_fraction": repeated_record_bytes / max(per_member_record_decode_bytes, 1),
        "release_credit": False,
        "claim_boundary": "Static exact-metadata work-volume census only. It identifies duplicate decode/reconstruction work addressable by operation-scoped caches; it does not predict wall-time improvement or authorize product promotion.",
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-reuse-census-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-reuse-census.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
