from __future__ import annotations

"""All-15 proof for removing an r24 dictionary blob only when no selected blob uses it.

This is intentionally narrower than the earlier dictionary-training experiment.  Training and codec
competition remain byte-for-byte unchanged.  After a normal shipping r24 archive exists, the transform
checks the authenticated blob table; if no physical record uses CODEC_ZSTDDICT, the dictionary is dead
payload and is removed while every surviving blob and logical recipe is remapped exactly.  If any blob
uses the dictionary, the archive is returned unchanged.

The oracle strong-verifies both sides over all 15 frozen workloads and fails promotion on any byte
regression, tree mismatch, or changed archive when the dictionary is live.  The target timing deliberately
charges shipping build + shipping verify + elision + candidate verify, so it cannot hide post-processing.
"""

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path

import msgpack

from benchmarks import v030_r24_binary_dictionary_isolation_oracle as PRIOR
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as P

ROUNDS = 5
TARGET = CONTROL.TARGET_NAME


def _remap_ref(value: int, removed: int) -> int:
    value = int(value)
    if value == removed:
        raise RuntimeError("dead dictionary was unexpectedly referenced by logical data")
    return value - 1 if value > removed else value


def _remap_index(index: dict, removed: int) -> None:
    C = R24
    for row in index.get("files", []):
        storage = row[6]
        if not storage:
            continue
        mode = int(storage[0])
        if mode == C.S_BLOB:
            storage[1] = _remap_ref(storage[1], removed)
        elif mode == C.S_CHUNKS:
            storage[1] = [_remap_ref(x, removed) for x in storage[1]]
        elif mode == C.S_CDC:
            storage[1] = [[ln, _remap_ref(ref, removed)] for ln, ref in storage[1]]
        elif mode == C.S_SPARSE:
            storage[1] = [[off, ln, [_remap_ref(ref, removed) for ref in refs]] for off, ln, refs in storage[1]]
        elif mode == C.S_PACK:
            storage[1] = _remap_ref(storage[1], removed)
    for recipe in index.get("recipes", []):
        recipe[0] = _remap_ref(recipe[0], removed)
        for payload in recipe[2]:
            payload[0] = _remap_ref(payload[0], removed)
            payload[3] = _remap_ref(payload[3], removed)
    index["dict_blob"] = None


def elide_dead_dictionary(src: Path, dst: Path) -> dict:
    C = R24
    raw = Path(src).read_bytes()
    magic, version, flags, ic_len, ib_len, data_len, ih = C.HDR.unpack_from(raw, 0)
    if magic != C.MAGIC or int(version) != 24:
        raise RuntimeError("not canonical r24")
    ic = raw[C.HDR.size:C.HDR.size + ic_len]
    ib = C.zd(ic, ib_len)
    if C.sha(ib) != ih:
        raise RuntimeError("primary index authentication failed")
    index = msgpack.unpackb(ib, raw=False)
    dict_blob = index.get("dict_blob")
    if dict_blob is None:
        Path(dst).write_bytes(raw)
        return {"changed": False, "reason": "no-dictionary", "saving_bytes": 0}
    dict_blob = int(dict_blob)
    blobs = index["blobs"]
    if not (0 <= dict_blob < len(blobs)):
        raise RuntimeError("dictionary blob index out of range")
    live_dict_users = [i for i, row in enumerate(blobs) if int(row[3]) == C.CODEC_ZSTDDICT]
    if live_dict_users:
        Path(dst).write_bytes(raw)
        return {"changed": False, "reason": "dictionary-live", "live_users": live_dict_users, "saving_bytes": 0}

    data_start = C.HDR.size + ic_len
    data = raw[data_start:data_start + data_len]
    records = []
    for i, row in enumerate(blobs):
        off, _usize, csize, _codec, meta_len = map(int, row)
        rec_len = C.BHDR.size + meta_len + csize
        rec = data[off:off + rec_len]
        if len(rec) != rec_len:
            raise RuntimeError("truncated physical record")
        if i != dict_blob:
            records.append((i, rec, row))

    _remap_index(index, dict_blob)
    new_blobs = []
    new_records = []
    offset = 0
    for _old_i, rec, row in records:
        _old_off, usize, csize, codec, meta_len = map(int, row)
        new_blobs.append([offset, usize, csize, codec, meta_len])
        new_records.append(rec)
        offset += len(rec)
    index["blobs"] = new_blobs

    new_ib = msgpack.packb(index, use_bin_type=True)
    new_ic = C.zc(new_ib, 12)
    new_ih = C.sha(new_ib)
    new_data = b"".join(new_records)
    header = C.HDR.pack(C.MAGIC, 24, flags, len(new_ic), len(new_ib), len(new_data), new_ih)
    footer = C.FTR.pack(C.FMAGIC, 0, 1, 0, 0, len(new_ic), len(new_ib), 0, new_ih)
    out = header + new_ic + new_data + new_ic + footer
    Path(dst).write_bytes(out)
    return {"changed": True, "reason": "dictionary-dead", "saving_bytes": len(raw) - len(out), "removed_blob_index": dict_blob}


def _verified(path: Path) -> dict:
    row = P.strong_verify(path)
    if not row.get("ok") or int(row.get("format_revision", -1)) != 24:
        raise RuntimeError(f"r24 verification failed: {row!r}")
    return row


def _build_pair(root: Path, td: Path) -> dict:
    shipping_path = td / "shipping.cmpct"
    candidate_path = td / "candidate.cmpct"
    t0 = time.perf_counter()
    shipping = PRIOR._shipping_build(root, shipping_path)
    transform = elide_dead_dictionary(shipping_path, candidate_path)
    candidate_verify = _verified(candidate_path)
    overcharged_create_s = time.perf_counter() - t0
    candidate_bytes = candidate_path.stat().st_size
    return {
        "shipping_bytes": int(shipping["archive_bytes"]),
        "candidate_bytes": int(candidate_bytes),
        "delta_bytes": int(candidate_bytes) - int(shipping["archive_bytes"]),
        "shipping_tree_sha256": shipping["tree_sha256"],
        "candidate_tree_sha256": candidate_verify["tree_sha256"],
        "same_verified_tree": shipping["tree_sha256"] == candidate_verify["tree_sha256"],
        "transform": transform,
        "overcharged_complete_create_s": overcharged_create_s,
    }


def _target(work_root: Path) -> dict:
    sources = CONTROL._build_sources(work_root / "sources")
    root = sources[TARGET]
    samples = []
    bytes_seen = set()
    deltas = set()
    trees = set()
    changed = set()
    for _i in range(ROUNDS):
        with tempfile.TemporaryDirectory(prefix="cmpct-dead-dict-target-", dir=work_root) as td_name:
            row = _build_pair(root, Path(td_name))
        samples.append(float(row["overcharged_complete_create_s"]))
        bytes_seen.add(int(row["candidate_bytes"]))
        deltas.add(int(row["delta_bytes"]))
        trees.add(bool(row["same_verified_tree"]))
        changed.add(bool(row["transform"]["changed"]))
    return {
        "label": f"neutral_hostile_v1/{TARGET}",
        "rounds": ROUNDS,
        "candidate_bytes": next(iter(bytes_seen)) if len(bytes_seen) == 1 else None,
        "delta_bytes": next(iter(deltas)) if len(deltas) == 1 else None,
        "median_overcharged_complete_create_s": statistics.median(samples),
        "deterministic": len(bytes_seen) == len(deltas) == 1,
        "same_verified_tree": trees == {True},
        "dead_dictionary_elided": changed == {True},
    }


def _all15(work_root: Path) -> dict:
    accepted = PRIOR.PACKGEN.GENERAL._accepted_v029_rows()
    neutral = PRIOR.PACKGEN.GENERAL.V029._load(PRIOR.PACKGEN.GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_dead_dict_neutral")
    hostile = PRIOR.PACKGEN.GENERAL.V029._load(PRIOR.PACKGEN.GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_v030_dead_dict_hostile")
    repair = PRIOR.PACKGEN.GENERAL.V029._load(PRIOR.PACKGEN.GENERAL.V029.REPAIR_PATH, "cmpct_v030_dead_dict_repair")
    repair.install_generation_hooks(neutral)
    rows = []
    for suite, module, root in (("neutral_hostile_v1", neutral, work_root / "neutral"), ("resemblance_hostile_v1", hostile, work_root / "resemblance")):
        module.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for workload in sorted(p for p in root.iterdir() if p.is_dir()):
            expected = accepted[(suite, workload.name)]["tree_sha256"]
            with tempfile.TemporaryDirectory(prefix="cmpct-dead-dict-", dir=work_root) as td_name:
                row = _build_pair(workload, Path(td_name))
            row.update({"label": f"{suite}/{workload.name}", "frozen_source_tree_sha256": expected})
            row["same_verified_tree"] = row["same_verified_tree"] and row["candidate_tree_sha256"] == expected
            rows.append(row)
            print(json.dumps({"label": row["label"], "delta_bytes": row["delta_bytes"], "reason": row["transform"]["reason"]}), flush=True)
    gate = {
        "exact_workload_count": len(rows) == 15,
        "all_source_and_candidate_trees_match": all(r["same_verified_tree"] for r in rows),
        "zero_byte_regressions": all(r["delta_bytes"] <= 0 for r in rows),
        "at_least_one_strict_improvement": any(r["delta_bytes"] < 0 for r in rows),
        "live_dictionaries_unchanged": all(r["delta_bytes"] == 0 for r in rows if r["transform"]["reason"] == "dictionary-live"),
    }
    gate["promotion_candidate"] = all(gate.values())
    return {"rows": rows, "gate": gate, "shipping_total_bytes": sum(r["shipping_bytes"] for r in rows), "candidate_total_bytes": sum(r["candidate_bytes"] for r in rows)}


def run(work_root: Path) -> dict:
    import shutil
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    target_root = work_root / "target"
    target_root.mkdir()
    all_root = work_root / "all15"
    all_root.mkdir()
    return {
        "schema": "cmpct-v030-r24-dead-dictionary-elision-v1",
        "hypothesis": "a trained dictionary is pure dead payload when no selected physical blob uses CODEC_ZSTDDICT",
        "target": _target(target_root),
        "all15": _all15(all_root),
        "contract": {
            "format_revision": 24,
            "training_changed": False,
            "codec_competition_changed": False,
            "logical_semantics_changed": False,
            "live_dictionary_archives_must_remain_byte_identical": True,
            "strong_verification_required": True,
            "release_effect": "evidence only until builder materialization change is promoted and exact-head authorities regenerate",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-dead-dict-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-dead-dict.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target": result["target"], "gate": result["all15"]["gate"], "delta_total": result["all15"]["candidate_total_bytes"] - result["all15"]["shipping_total_bytes"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
