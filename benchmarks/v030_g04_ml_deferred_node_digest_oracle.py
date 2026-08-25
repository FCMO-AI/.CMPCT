from __future__ import annotations

"""A/B redundant logical-node SHA work in the canonical G0-G4 ML streaming reader.

The complete streaming verifier/extractor already authenticates every physical record and then
verifies the declared SHA-256 of every complete logical file.  The current G0-G4 session also
SHA-256 hashes every reconstructed logical node before those same bytes are immediately fed into
the enclosing file SHA.  On ML graphs this can hash the logical payload twice while also paying
physical-record authentication.

This research oracle changes no archive bytes, cache budget, graph reconstruction, file/tree
identity, recovery rule or resource limit.  The candidate defers *derived node* SHA checks only
inside complete-file streaming; node size checks remain, physical records remain authenticated,
and every complete file must still match its independently declared SHA-256 before verification or
transactional extraction can succeed.  Hostile physical corruption must still fail closed.

A green result is promotion-incomplete.  It only justifies implementing an explicit complete-stream
reader mode and then rerunning reader/fuzz/native/runtime authority.  Random/selective member reads
continue to require ordinary node integrity unless separately proven.
"""

import argparse
import binascii
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

G04 = RR.G04
A5 = RR.A5
P = RR.P
ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.08
MIN_EXTRACT_IMPROVEMENT = 0.08


def _node_deferred(self, node_id: int) -> bytes:
    """Exact shipping node reconstruction minus the redundant per-node SHA in full-file mode."""
    node_id = RR._int(node_id, "G0-G4 node id", maximum=len(self.nodes) - 1)
    cached = self.node_cache.pop(node_id, None)
    if cached is not None:
        self.node_cache[node_id] = cached
        return cached
    desc = self.nodes[node_id]
    kind = desc[0]
    if kind == "direct":
        _, record_id, offset, length, _expected = desc
        pack = self.record(record_id)
        if offset > len(pack) or length > len(pack) - offset:
            raise RuntimeError("G0-G4 direct slice bounds")
        raw = pack[offset : offset + length]
    elif kind == "delta":
        _, base_id, record_id, length, _expected = desc
        raw = P.delta_decode(self.node(base_id), self.record(record_id), expected_size=length, max_output=A5.MAX_CHUNK)
    elif kind == "delta_pack":
        _, base_id, record_id, recipe_offset, recipe_len, length, _expected = desc
        pack = self.record(record_id)
        if len(pack) > A5.MAX_RESIDUAL_PACK or recipe_offset > len(pack) or recipe_len > len(pack) - recipe_offset:
            raise RuntimeError("G0-G4 packed-delta recipe bounds")
        if len(pack) / max(1, int(length)) > A5.MAX_ADDITIONAL_RECIPE_AMP:
            raise RuntimeError("G0-G4 packed-delta read amplification")
        recipe = pack[recipe_offset : recipe_offset + recipe_len]
        raw = P.delta_decode(self.node(base_id), recipe, expected_size=length, max_output=A5.MAX_CHUNK)
    elif kind == "mosaic":
        _, base_ids, record_id, length, _expected = desc
        raw = P.mosaic_delta_decode(
            [self.node(base_id) for base_id in base_ids],
            self.record(record_id),
            expected_size=length,
            max_bases=A5.MAX_MOSAIC_BASES,
            max_source_bytes=A5.MAX_MOSAIC_SOURCE_INDEX,
            max_output=A5.MAX_CHUNK,
        )
    elif kind == "pack_mosaic":
        _, record_id, offset, recipe_len, base_ids, length, _expected = desc
        pack = self.record(record_id)
        if offset > len(pack) or recipe_len > len(pack) - offset:
            raise RuntimeError("G0-G4 pack-mosaic recipe bounds")
        raw = P.mosaic_delta_decode(
            [self.node(base_id) for base_id in base_ids],
            pack[offset : offset + recipe_len],
            expected_size=length,
            max_bases=A5.MAX_MOSAIC_BASES,
            max_source_bytes=A5.MAX_MOSAIC_SOURCE_INDEX,
            max_output=A5.MAX_CHUNK,
        )
    else:
        raise RuntimeError("unknown G0-G4 node kind")
    if len(raw) > A5.MAX_CHUNK:
        raise RuntimeError("G0-G4 logical node size bound")
    self.max_logical_node_bytes = max(self.max_logical_node_bytes, len(raw))
    RR._cache_put(self.node_cache, self.node_cache_bytes, node_id, raw, RR.MAX_NODE_CACHE_BYTES)
    return raw


def _measure(archive: Path, destination: Path | None, *, deferred: bool) -> tuple[float, dict]:
    original = RR._G04Session.node
    if deferred:
        RR._G04Session.node = _node_deferred
    try:
        started = time.perf_counter()
        result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
        return time.perf_counter() - started, result
    finally:
        RR._G04Session.node = original


def _corrupt_first_physical_payload(source: Path, target: Path) -> None:
    shutil.copy2(source, target)
    stream, _meta, record_start, offsets, _merkle, _tail = RR._g04_open(target)
    try:
        first = int(record_start) + int(offsets[0])
    finally:
        stream.close()
    with target.open("r+b") as fh:
        fh.seek(first)
        header = fh.read(RR.PH.size)
        if len(header) != RR.PH.size:
            raise RuntimeError("short physical header while preparing corruption case")
        _codec, _usize, csize, _crc, _sha = RR.PH.unpack(header)
        if csize <= 0:
            raise RuntimeError("cannot corrupt empty physical payload")
        pos = first + RR.PH.size + min(7, int(csize) - 1)
        fh.seek(pos)
        old = fh.read(1)
        if len(old) != 1:
            raise RuntimeError("short physical payload while preparing corruption case")
        fh.seek(pos)
        fh.write(bytes((old[0] ^ 0x01,)))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML runtime target did not select canonical G0-G4")
        shipping = PRODUCT.strong_verify(archive)
        if not shipping.get("ok") or shipping.get("tree_sha256") != source_tree:
            raise RuntimeError("source archive failed shipping strong verification")

        samples = {
            "baseline_verify": [],
            "deferred_verify": [],
            "baseline_extract": [],
            "deferred_extract": [],
        }
        reads = {key: [] for key in samples}
        for round_index in range(ROUNDS):
            # Rotate order so filesystem/cache state does not systematically favor one side.
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for deferred in order:
                label = "deferred" if deferred else "baseline"
                verify_s, verified = _measure(archive, None, deferred=deferred)
                if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
                    raise RuntimeError("deferred-node-digest verification identity drift")
                samples[f"{label}_verify"].append(float(verify_s))
                reads[f"{label}_verify"].append(int(verified["physical_record_reads"]))

                destination = work_root / f"{label}-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                extract_s, extracted = _measure(archive, destination, deferred=deferred)
                if not extracted.get("ok") or extracted.get("tree_sha256") != source_tree:
                    raise RuntimeError("deferred-node-digest extraction identity drift")
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("deferred-node-digest extracted filesystem identity drift")
                samples[f"{label}_extract"].append(float(extract_s))
                reads[f"{label}_extract"].append(int(extracted["physical_record_reads"]))
                shutil.rmtree(destination, ignore_errors=True)

        corrupt = work_root / "ml-corrupt.cmpct"
        _corrupt_first_physical_payload(archive, corrupt)
        hostile_rejected = False
        try:
            _measure(corrupt, None, deferred=True)
        except Exception:
            hostile_rejected = True

    medians = {key: float(statistics.median(values)) for key, values in samples.items()}
    verify_improvement = 1.0 - medians["deferred_verify"] / max(medians["baseline_verify"], 1e-9)
    extract_improvement = 1.0 - medians["deferred_extract"] / max(medians["baseline_extract"], 1e-9)
    baseline_reads = statistics.median(reads["baseline_extract"])
    deferred_reads = statistics.median(reads["deferred_extract"])
    gate = {
        "archive_bytes_unchanged": True,
        "memory_budget_change_bytes": 0,
        "physical_record_authentication_preserved": hostile_rejected,
        "complete_file_sha_preserved": True,
        "complete_tree_identity_preserved": True,
        "physical_reads_not_increased": deferred_reads <= baseline_reads,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-ml-deferred-node-digest-v1",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "canonical_profile": {
            "format_revision": 25,
            "magic": PRODUCT.G04_MAGIC.hex(),
            "tail_magic": PRODUCT.G04_TAIL.hex(),
        },
        "change": {
            "scope": "complete-file streaming only",
            "archive_bytes_changed": False,
            "cache_budget_changed": False,
            "physical_record_sha_changed": False,
            "complete_file_sha_changed": False,
            "selective_member_reader_changed": False,
            "deferred_check": "per-logical-node SHA-256",
        },
        "samples": samples,
        "physical_reads": reads,
        "medians_s": medians,
        "verify_improvement_fraction": float(verify_improvement),
        "extract_improvement_fraction": float(extract_improvement),
        "hostile_physical_corruption_rejected": hostile_rejected,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "node_cache_limit_bytes": RR.MAX_NODE_CACHE_BYTES,
            "record_cache_limit_bytes": RR.MAX_RECORD_CACHE_BYTES,
        },
        "gate": gate,
        "claim_boundary": (
            "Research-only A/B for complete G0-G4 streaming. A green result can only justify an explicit reader "
            "mode that retains physical authentication and declared complete-file SHA verification. Selective/random "
            "reads are outside this optimization. Reader/fuzz/native/runtime authority remain mandatory."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-deferred-node-digest-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-deferred-node-digest.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "medians_s": result["medians_s"],
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "hostile_physical_corruption_rejected": result["hostile_physical_corruption_rejected"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("deferred G0-G4 node digest did not earn promotion")


if __name__ == "__main__":
    main()
