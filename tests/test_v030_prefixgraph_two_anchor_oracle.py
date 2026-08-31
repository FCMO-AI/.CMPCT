from __future__ import annotations

from pathlib import Path

from benchmarks import v030_prefixgraph_two_anchor_representation_oracle as ORACLE
from experiments import entropygraph_v030_prefixgraph as PG


def _fixture():
    rels = ["v1/a.bin", "v2/a.bin", "v3/a.bin", "notes.txt"]
    common = (b"prefix-graph-shared-structure-" * 96)
    raws = [
        common + b"A" * 512,
        common + b"B" * 512,
        common[:1800] + b"C" * 700,
        b"unrelated" * 80,
    ]
    tree = PG._treehash_parts(rels, raws)
    direct = [PG._compress(raw) for raw in raws]
    trials = {}
    for anchor in range(len(raws)):
        compressor, _dictionary = PG._prefix_codec(raws[anchor])
        row = []
        for index, raw in enumerate(raws):
            if index == anchor:
                row.append(None)
            else:
                payload = compressor.compress(raw)
                row.append((len(payload), PG.H(payload)))
        trials[anchor] = row
    return rels, raws, tree, direct, trials


def test_single_anchor_projection_matches_historical_serializer_exactly() -> None:
    rels, raws, tree, direct, trials = _fixture()
    all_direct, _stats = PG._serialize_candidate(rels, raws, direct, tree, None)
    priced_direct, _records, _meta = ORACLE._price(rels, raws, direct, tree, (), trials)
    assert priced_direct == len(all_direct)

    for anchor in range(len(raws)):
        historical, _stats = PG._serialize_candidate(rels, raws, direct, tree, anchor)
        projected, _records, _meta = ORACLE._price(rels, raws, direct, tree, (anchor,), trials)
        assert projected == len(historical)


def test_two_anchor_materialization_matches_exact_price_and_existing_reader(tmp_path: Path) -> None:
    rels, raws, tree, direct, trials = _fixture()
    anchors = (0, 2)
    priced, records, _meta = ORACLE._price(rels, raws, direct, tree, anchors, trials)
    archive = tmp_path / "two-anchor.cmpct"
    ORACLE._materialize(archive, rels, raws, direct, tree, anchors, records)
    assert archive.stat().st_size == priced
    verified = PG.strong_verify(archive)
    assert verified["ok"] is True
    assert verified["tree_sha256"] == tree


def test_two_anchor_records_never_reference_a_non_direct_base() -> None:
    rels, raws, tree, direct, trials = _fixture()
    anchors = (0, 2)
    _priced, records, _meta = ORACLE._price(rels, raws, direct, tree, anchors, trials)
    for row in records:
        if row[0] == "prefix":
            assert row[1] in anchors
            assert records[int(row[1])][0] == "direct"
