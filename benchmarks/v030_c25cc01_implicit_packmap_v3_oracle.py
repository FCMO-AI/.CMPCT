from __future__ import annotations

"""Research-only v3 implicit S_PACK map over the locality-safe stable-order layout.

Stable-order locality packing makes S_PACK membership much more regular. The v2 control map
still spends bytes twice: every packed file keeps a one-element [S_PACK] marker even though
pack membership already identifies it, and every pack repeats a full member-length vector
even when all members have the same size. This experiment removes those redundancies and
delta-codes both pack ids and file-table membership from the previous pack.

Descriptor code = blob_delta*4 + mode, where modes are:
  0 contiguous membership + uniform member length: [code, [file_gap,count], length]
  1 contiguous membership + varied lengths:        [code, file_gap, lengths]
  2 sparse membership + uniform member length:     [code, file_deltas, length]
  3 sparse membership + varied lengths:            [code, file_deltas, lengths]

Packed file rows carry no storage marker in the research representation. The decoder derives
those rows only from the authenticated pack map and reconstructs the exact ordinary compact
control, which must then expand byte-semantically to the exact shipping r24 index. Physical
payload bytes, pack boundaries, locality, integrity, recovery, and the two authenticated
control copies are unchanged. No product or release credit is granted.
"""

import argparse
import copy
import json
from pathlib import Path
import shutil
import statistics
import time

import msgpack

from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_c25cc01_stable_order_packmap_oracle as STABLE
from benchmarks import v030_c25cc01_packmap_control_oracle as PACKMAP
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE
from experiments import entropygraph_v030_release_product as PRODUCT

LOCALITY = 8
ROUNDS = 5


def _compact_v3(index: dict) -> tuple[dict, dict]:
    compact = CONTROL._compact_index(index)
    rows = copy.deepcopy(compact["f"])
    groups: dict[int, list[tuple[int, int, int]]] = {}
    for fi, (src, enc) in enumerate(zip(index["files"], rows, strict=True)):
        storage = src[6]
        if src[1] != R24.K_FILE or not storage or int(storage[0]) != R24.S_PACK:
            continue
        blob, off, ln = int(storage[1]), int(storage[2]), int(storage[3])
        groups.setdefault(blob, []).append((off, fi, ln))
        # Membership in q3 is authoritative for identifying packed rows; the marker is redundant.
        enc[3] = None

    q3 = []
    previous_blob = 0
    previous_file_end = 0
    uniform_groups = 0
    contiguous_groups = 0
    packed_rows = 0
    for blob, members in sorted(groups.items()):
        members.sort()
        expected_off = 0
        file_indices = []
        lengths = []
        for off, fi, ln in members:
            if off != expected_off:
                raise RuntimeError("S_PACK slices are not contiguous in physical order")
            if ln < 0:
                raise RuntimeError("negative S_PACK member length")
            file_indices.append(fi)
            lengths.append(ln)
            expected_off += ln
        if not file_indices:
            raise RuntimeError("empty S_PACK group")
        blob_delta = blob - previous_blob
        if blob_delta < 0:
            raise RuntimeError("sorted S_PACK blob ids regressed")
        contiguous = file_indices == list(range(file_indices[0], file_indices[0] + len(file_indices)))
        uniform = len(set(lengths)) == 1
        if contiguous:
            gap = file_indices[0] - previous_file_end
            if gap < 0:
                raise RuntimeError("contiguous S_PACK groups overlap file-table membership")
            if uniform:
                mode = 0
                membership = [gap, len(file_indices)]
                length_spec = lengths[0]
                uniform_groups += 1
            else:
                mode = 1
                membership = gap
                length_spec = lengths
            contiguous_groups += 1
        else:
            deltas = []
            prev = previous_file_end
            for fi in file_indices:
                delta = fi - prev
                if delta < 0:
                    raise RuntimeError("sparse S_PACK membership is not monotonic")
                deltas.append(delta)
                prev = fi
            if uniform:
                mode = 2
                length_spec = lengths[0]
                uniform_groups += 1
            else:
                mode = 3
                length_spec = lengths
            membership = deltas
        q3.append([blob_delta * 4 + mode, membership, length_spec])
        previous_blob = blob
        previous_file_end = file_indices[-1] + 1
        packed_rows += len(file_indices)
    return {**compact, "f": rows, "q3": q3}, {
        "pack_groups": len(q3),
        "packed_rows": packed_rows,
        "uniform_length_groups": uniform_groups,
        "contiguous_groups": contiguous_groups,
    }


def _restore_v3(candidate: dict) -> dict:
    standard = {k: copy.deepcopy(v) for k, v in candidate.items() if k != "q3"}
    previous_blob = 0
    previous_file_end = 0
    seen = set()
    for desc in candidate["q3"]:
        if not isinstance(desc, list) or len(desc) != 3:
            raise RuntimeError("malformed implicit S_PACK descriptor")
        code = int(desc[0])
        if code < 0:
            raise RuntimeError("negative implicit S_PACK descriptor code")
        mode = code & 3
        blob = previous_blob + (code >> 2)
        membership, length_spec = desc[1], desc[2]
        if mode in (0, 1):
            if mode == 0:
                if not isinstance(membership, list) or len(membership) != 2:
                    raise RuntimeError("uniform contiguous membership descriptor")
                gap, count = int(membership[0]), int(membership[1])
                if gap < 0 or count <= 0:
                    raise RuntimeError("invalid contiguous membership range")
                file_indices = list(range(previous_file_end + gap, previous_file_end + gap + count))
                lengths = [int(length_spec)] * count
            else:
                gap = int(membership)
                lengths = [int(v) for v in length_spec]
                if gap < 0 or not lengths:
                    raise RuntimeError("invalid varied contiguous membership range")
                first = previous_file_end + gap
                file_indices = list(range(first, first + len(lengths)))
        elif mode in (2, 3):
            deltas = [int(v) for v in membership]
            if not deltas:
                raise RuntimeError("empty sparse membership descriptor")
            file_indices = []
            prev = previous_file_end
            for delta in deltas:
                if delta < 0:
                    raise RuntimeError("negative sparse membership delta")
                prev += delta
                file_indices.append(prev)
            if mode == 2:
                lengths = [int(length_spec)] * len(file_indices)
            else:
                lengths = [int(v) for v in length_spec]
                if len(lengths) != len(file_indices):
                    raise RuntimeError("sparse membership/length count mismatch")
        else:  # pragma: no cover
            raise RuntimeError("unknown implicit S_PACK mode")
        if any(ln < 0 for ln in lengths):
            raise RuntimeError("negative implicit S_PACK member length")
        offset = 0
        for fi, ln in zip(file_indices, lengths, strict=True):
            if fi < 0 or fi >= len(standard["f"]) or fi in seen:
                raise RuntimeError("implicit S_PACK file membership out of range or duplicated")
            standard["f"][fi][3] = [R24.S_PACK, blob, offset, ln]
            offset += ln
            seen.add(fi)
        previous_blob = blob
        previous_file_end = file_indices[-1] + 1
    return standard


def _project(index: dict, data: bytes) -> dict:
    candidate, shape = _compact_v3(index)
    restored = _restore_v3(candidate)
    expanded = CONTROL._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("implicit S_PACK v3 does not expand exactly to shipping r24 index")
    envelope = {"x": list(index["features"]), "c": candidate}
    raw = msgpack.packb(envelope, use_bin_type=True)
    level, comp = PACKMAP._compress(raw)
    framing = R24.HDR.size + R24.FTR.size
    return {
        **shape,
        "raw_control_bytes": len(raw),
        "compressed_control_bytes_per_copy": len(comp),
        "control_level": int(level),
        "projected_archive_bytes": int(framing + 2 * len(comp) + len(data)),
        "semantic_index_roundtrip_exact": True,
    }


def _candidate_once(source: Path, root: Path, tag: str) -> dict:
    archive = root / f"{tag}.cmpct"
    started = time.perf_counter()
    with STABLE._patched():
        PRODUCT._locality_bounded_r24_build(source, archive)
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError("stable-order locality-safe source failed verification")
    index, data, _physical = PROFILE._source_r24_parts(archive)
    locality = PROFILE._audit_s_pack_locality(index)
    if float(locality["max_member_read_amplification"]) > LOCALITY:
        raise RuntimeError("implicit S_PACK v3 source violated locality")
    projected = _project(index, data)
    return {
        **projected,
        "tree_sha256": verified.get("tree_sha256"),
        "locality": locality,
        "complete_create_s": time.perf_counter() - started,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)
    samples = []
    cmpct_sizes, zip_sizes, zstd_sizes, trees, shapes = set(), set(), set(), set(), set()
    for rep in range(ROUNDS):
        rep_root = work_root / f"rep-{rep}"
        rep_root.mkdir(parents=True, exist_ok=True)
        order = ["cmpct", "zip", "zstd"]
        order = order[rep % 3:] + order[:rep % 3]
        current = {}
        for kind in order:
            if kind == "cmpct":
                current[kind] = _candidate_once(source, rep_root, "candidate")
            elif kind == "zip":
                current[kind] = EXT._zip(source, rep_root / "target.zip", rep_root / "zip-out")
            else:
                zwork = rep_root / "zstd-work"
                zwork.mkdir(parents=True, exist_ok=True)
                current[kind] = EXT._tar_zstd(source, rep_root / "target.tar.zst", rep_root / "zstd-out", zwork)
        c = current["cmpct"]
        cmpct_sizes.add(int(c["projected_archive_bytes"]))
        zip_sizes.add(int(current["zip"]["archive_bytes"]))
        zstd_sizes.add(int(current["zstd"]["archive_bytes"]))
        trees.add(str(c["tree_sha256"]))
        shapes.add((int(c["pack_groups"]), int(c["packed_rows"]), int(c["uniform_length_groups"]), int(c["contiguous_groups"])))
        samples.append({
            "cmpct_create_s": float(c["complete_create_s"]),
            "zip_create_s": float(current["zip"]["create_s"]),
            "zstd19_create_s": float(current["zstd"]["create_s"]),
        })
    deterministic = len(cmpct_sizes) == len(zip_sizes) == len(zstd_sizes) == len(trees) == len(shapes) == 1
    cmpct_bytes, zip_bytes, zstd_bytes = next(iter(cmpct_sizes)), next(iter(zip_sizes)), next(iter(zstd_sizes))
    cmpct_s = statistics.median(x["cmpct_create_s"] for x in samples)
    zip_s = statistics.median(x["zip_create_s"] for x in samples)
    zstd_s = statistics.median(x["zstd19_create_s"] for x in samples)
    structural = _candidate_once(source, work_root / "structural", "candidate")
    strict = bool(deterministic and cmpct_bytes < zip_bytes and cmpct_bytes < zstd_bytes and cmpct_s < zip_s and cmpct_s < zstd_s)
    return {
        "schema": "cmpct-v030-c25cc01-implicit-packmap-v3-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "format_revision_change": False,
            "physical_pack_boundaries_changed": False,
            "locality_ceiling": LOCALITY,
            "two_authenticated_control_copies_retained": True,
            "semantic_index_roundtrip_exact": True,
            "policy_inputs": ["authenticated_pack_blob_order", "canonical_file_table_order", "authenticated_member_lengths"],
            "forbidden_policy_inputs": ["benchmark_name", "workload_label", "file_path_literal", "content_hash_as_identity_dispatch", "frozen_pack_hash"],
        },
        "target": name,
        "rounds": ROUNDS,
        "candidate": structural,
        "competitors": {
            "cmpct_projected_bytes": cmpct_bytes,
            "zip_bytes": zip_bytes,
            "zstd19_bytes": zstd_bytes,
            "median_cmpct_complete_create_s": cmpct_s,
            "median_zip_create_s": zip_s,
            "median_zstd19_create_s": zstd_s,
            "remaining_zstd_deficit_bytes": cmpct_bytes - zstd_bytes,
        },
        "samples": samples,
        "gate": {
            "experiment_valid": deterministic,
            "strict_four_way_signal": strict,
            "passed": deterministic,
        },
        "claim_boundary": "Research-only exact representation estimate. A strict signal authorizes only canonical productization prerequisites; reader/native/Android/all-15/recovery/final authority remain mandatory.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-implicit-packmap-v3-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-implicit-packmap-v3.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "competitors": result["competitors"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("implicit S_PACK v3 experiment was not deterministic")


if __name__ == "__main__":
    main()
