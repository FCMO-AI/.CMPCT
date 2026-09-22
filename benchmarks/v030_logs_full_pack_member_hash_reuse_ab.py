from __future__ import annotations

"""Frozen R1 A/B for exact whole-pack logical SHA-256 proof reuse in Logs full extraction."""

import argparse
import gc
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as RUNTIME
from experiments import entropygraph_v030_logs_fused_extract as FUSED

ROUNDS = 21
SUPPORT_REDUCTION = 0.04
RETIRE_REDUCTION = 0.01
PREREG = "docs/v030-rnd/R25_LOGS_FULL_PACK_MEMBER_HASH_REUSE_AB_PREREG.md"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _clean(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _extract_control(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()
    started = time.perf_counter()
    RUNTIME.extract(archive, dst)
    elapsed = time.perf_counter() - started
    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs whole-pack proof-reuse control tree drift")
    return {"wall_s": elapsed}


def _candidate_patch():
    archive_cls = FUSED.LOGS.Archive
    inherited_restore = archive_cls._restore_session
    inherited_read_pack = archive_cls._read_pack
    counters = {
        "proof_reuses": 0,
        "ordinary_logical_sha_checks": 0,
        "pack_calls": 0,
    }

    def counted_read_pack(self, index: int) -> bytes:
        raw = inherited_read_pack(self, index)
        counters["pack_calls"] += 1
        return raw

    def proof_reuse_restore(
        self,
        item: int,
        *,
        member_cache: dict[int, tuple[bytes, int]],
        pack_cache: dict[int, bytes],
        active: set[int],
    ) -> tuple[bytes, int]:
        if item in member_cache:
            return member_cache[item]
        if item in active or item < 0 or item >= len(self.files):
            raise RuntimeError("logs profile dependency error")
        active.add(item)
        try:
            _prefix, _suffix, size, expected_sha, storage, _rel = self.files[item]
            size = int(size)
            kind = storage[0]
            whole_pack_identity_proven = False
            if kind in ("pack", "raw"):
                pack_index, offset, length = map(int, storage[1:])
                pack = pack_cache.get(pack_index)
                if pack is None:
                    pack = self._read_pack(pack_index)
                    pack_cache[pack_index] = pack
                if offset < 0 or length != size or offset + length > len(pack):
                    raise RuntimeError("logs profile slice bounds")
                value = pack[offset : offset + length]
                decoded_context = len(pack) if kind == "pack" else length
                pack_expected_sha = self.pack_offsets[pack_index][5]
                whole_pack_identity_proven = (
                    offset == 0
                    and length == len(pack)
                    and expected_sha == pack_expected_sha
                )
            elif kind == "derive":
                source_index = int(storage[1])
                if source_index == item:
                    raise RuntimeError("logs profile self dependency")
                source, source_context = proof_reuse_restore(
                    self,
                    source_index,
                    member_cache=member_cache,
                    pack_cache=pack_cache,
                    active=active,
                )
                value = FUSED.LOGS.V2.BASE._decode(storage[2], source)
                decoded_context = source_context + len(value)
            else:
                raise RuntimeError("unknown logs profile storage")

            if len(value) != size:
                raise RuntimeError("logs profile logical identity")
            if whole_pack_identity_proven:
                # _read_pack already established SHA256(pack)==pack_expected_sha. Geometry proves value==pack,
                # and the equality above proves member_expected_sha==pack_expected_sha, so hashing value again
                # would establish no new identity fact.
                counters["proof_reuses"] += 1
            else:
                counters["ordinary_logical_sha_checks"] += 1
                if hashlib.sha256(value).digest() != expected_sha:
                    raise RuntimeError("logs profile logical identity")
            member_cache[item] = (value, decoded_context)
            return member_cache[item]
        finally:
            active.discard(item)

    archive_cls._read_pack = counted_read_pack
    archive_cls._restore_session = proof_reuse_restore
    return archive_cls, inherited_restore, inherited_read_pack, counters, proof_reuse_restore


def _restore_patch(archive_cls, inherited_restore, inherited_read_pack) -> None:
    archive_cls._restore_session = inherited_restore
    archive_cls._read_pack = inherited_read_pack


def _hostile_expected_sha_separation(archive: Path) -> bool:
    archive_cls, inherited_restore, inherited_read_pack, counters, candidate_restore = _candidate_patch()
    try:
        with archive_cls(archive) as opened:
            eligible = None
            for index, row in enumerate(opened.files):
                storage = row[4]
                if storage[0] not in ("pack", "raw"):
                    continue
                pack_index, offset, length = map(int, storage[1:])
                _pack_offset, _codec, usize, _csize, _crc, pack_sha = opened.pack_offsets[pack_index]
                if offset == 0 and length == int(row[2]) == usize and row[3] == pack_sha:
                    eligible = index
                    break
            if eligible is None:
                raise RuntimeError("frozen Logs target has no whole-pack proof-reuse member")
            original_sha = opened.files[eligible][3]
            opened.files[eligible][3] = b"\x00" * 32
            rejected = False
            try:
                candidate_restore(
                    opened,
                    eligible,
                    member_cache={},
                    pack_cache={},
                    active=set(),
                )
            except RuntimeError as exc:
                rejected = "logical identity" in str(exc)
            finally:
                opened.files[eligible][3] = original_sha
            return bool(rejected and counters["proof_reuses"] == 0 and counters["ordinary_logical_sha_checks"] == 1)
    finally:
        _restore_patch(archive_cls, inherited_restore, inherited_read_pack)


def _extract_candidate(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()
    archive_cls, inherited_restore, inherited_read_pack, counters, _candidate_restore = _candidate_patch()
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        elapsed = time.perf_counter() - started
    finally:
        _restore_patch(archive_cls, inherited_restore, inherited_read_pack)
    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs whole-pack proof-reuse candidate tree drift")
    return {
        "wall_s": elapsed,
        **counters,
        "methods_restored": (
            archive_cls._restore_session is inherited_restore
            and archive_cls._read_pack is inherited_read_pack
        ),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.corpus_logs(corpus)
    source = corpus / "05_logs_and_telemetry"
    tree = PRODUCT.treehash(source)
    archive = work_root / "logs.cmpct"
    stats = dict(PRODUCT.build(source, archive))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok") or verified.get("tree_sha256") != tree or stats.get("selected") != "logs-inverse":
        raise RuntimeError("frozen Logs whole-pack proof-reuse archive/selection verification failed")

    hostile_separation_ok = _hostile_expected_sha_separation(archive)
    if not hostile_separation_ok:
        raise RuntimeError("whole-pack proof-reuse hostile expected-SHA separation failed")

    _extract_control(archive, work_root / "warm-control", tree)
    warm_candidate = _extract_candidate(archive, work_root / "warm-candidate", tree)
    if warm_candidate["proof_reuses"] < 1 or warm_candidate["pack_calls"] != 7:
        raise RuntimeError("warm candidate did not exercise frozen proof-reuse/pack lifecycle")

    control_rows: list[dict] = []
    candidate_rows: list[dict] = []
    order: list[str] = []
    for i in range(ROUNDS):
        pair = ("control", "candidate") if i % 2 == 0 else ("candidate", "control")
        for label in pair:
            order.append(label)
            dst = work_root / f"round-{i:02d}-{label}"
            if label == "control":
                control_rows.append(_extract_control(archive, dst, tree))
            else:
                candidate_rows.append(_extract_candidate(archive, dst, tree))

    control_median = float(statistics.median(float(row["wall_s"]) for row in control_rows))
    candidate_median = float(statistics.median(float(row["wall_s"]) for row in candidate_rows))
    wall_ratio = candidate_median / control_median
    reduction = 1.0 - wall_ratio
    proof_counts = {int(row["proof_reuses"]) for row in candidate_rows}
    ordinary_counts = {int(row["ordinary_logical_sha_checks"]) for row in candidate_rows}
    pack_counts = {int(row["pack_calls"]) for row in candidate_rows}
    lifecycle_ok = (
        len(proof_counts) == 1
        and next(iter(proof_counts)) >= 1
        and len(ordinary_counts) == 1
        and len(pack_counts) == 1
        and next(iter(pack_counts)) == 7
        and all(row["methods_restored"] is True for row in candidate_rows)
    )
    valid = (
        len(control_rows) == ROUNDS
        and len(candidate_rows) == ROUNDS
        and lifecycle_ok
        and hostile_separation_ok
    )
    if not valid:
        decision = "INVALID_LOGS_FULL_PACK_MEMBER_HASH_REUSE_AB"
    elif reduction >= SUPPORT_REDUCTION and wall_ratio <= 0.96:
        decision = "LOGS_FULL_PACK_MEMBER_HASH_REUSE_SUPPORTED"
    elif reduction < RETIRE_REDUCTION:
        decision = "LOGS_FULL_PACK_MEMBER_HASH_REUSE_RETIRED"
    else:
        decision = "LOGS_FULL_PACK_MEMBER_HASH_REUSE_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-logs-full-pack-member-hash-reuse-ab-v1",
        "preregistration": PREREG,
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "selected": stats.get("selected"),
        "tree_sha256": tree,
        "strong_verify": verified,
        "rounds": ROUNDS,
        "order": order,
        "control_rows": control_rows,
        "candidate_rows": candidate_rows,
        "control_median_s": control_median,
        "candidate_median_s": candidate_median,
        "candidate_wall_ratio": wall_ratio,
        "candidate_total_reduction_fraction": reduction,
        "candidate_proof_reuse_counts": sorted(proof_counts),
        "candidate_ordinary_logical_sha_counts": sorted(ordinary_counts),
        "candidate_pack_call_counts": sorted(pack_counts),
        "candidate_lifecycle_ok": lifecycle_ok,
        "hostile_expected_sha_separation_ok": hostile_separation_ok,
        "support_reduction_floor": SUPPORT_REDUCTION,
        "retire_reduction_ceiling": RETIRE_REDUCTION,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "pack_crc32_preserved": True,
        "pack_sha256_preserved": True,
        "derived_member_sha256_preserved": True,
        "partial_pack_member_sha256_preserved": True,
        "cold_selective_semantics_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-full-pack-member-hash-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-full-pack-member-hash-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "control_median_s", "candidate_median_s", "candidate_wall_ratio",
        "candidate_total_reduction_fraction", "candidate_proof_reuse_counts",
        "candidate_ordinary_logical_sha_counts", "candidate_pack_call_counts",
        "hostile_expected_sha_separation_ok", "candidate_lifecycle_ok", "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs whole-pack logical SHA proof-reuse evidence invalid")


if __name__ == "__main__":
    main()
