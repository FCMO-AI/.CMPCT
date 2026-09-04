from __future__ import annotations

"""Research-only v4 implicit S_PACK map with no blob-id ordering assumption.

The first marker-free v3 draft tried to delta-code physical blob ids while also delta-coding
file-table pack runs. That silently assumes those two orders are correlated. They are not:
canonical r24 assigns physical blob ids from sorted content hashes, independently of the order
in which locality-safe packs were constructed. v4 orders pack descriptors by their first
logical file-table member and stores the authenticated blob id explicitly. This keeps file-run
gaps non-negative without imposing a false representation invariant.

For the stable-order locality layout the expected hot form remains compact:
  [blob, 0, [file_gap,count], uniform_length]
or
  [blob, 1, file_gap, member_lengths].
Sparse fallback rows store exact absolute file-table indices, avoiding another accidental
monotonicity assumption. Per-file S_PACK markers remain elided because authenticated pack-map
membership reconstructs them exactly. Physical payload bytes, pack boundaries, locality,
integrity, recovery and both authenticated control copies are unchanged.
"""

import copy
import json

import msgpack

from benchmarks import v030_c25cc01_implicit_packmap_v3_oracle as V3
from benchmarks import v030_c25cc01_packmap_control_oracle as PACKMAP
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24


def _compact_v4(index: dict) -> tuple[dict, dict]:
    compact = CONTROL._compact_index(index)
    rows = copy.deepcopy(compact["f"])
    groups: dict[int, list[tuple[int, int, int]]] = {}
    for fi, (src, enc) in enumerate(zip(index["files"], rows, strict=True)):
        storage = src[6]
        if src[1] != R24.K_FILE or not storage or int(storage[0]) != R24.S_PACK:
            continue
        blob, off, ln = int(storage[1]), int(storage[2]), int(storage[3])
        groups.setdefault(blob, []).append((off, fi, ln))
        enc[3] = None

    ordered_groups = []
    for blob, members in groups.items():
        members.sort()
        if not members:
            raise RuntimeError("empty S_PACK group")
        ordered_groups.append((min(fi for _off, fi, _ln in members), blob, members))
    ordered_groups.sort()

    q4 = []
    previous_file_end = 0
    uniform_groups = 0
    contiguous_groups = 0
    packed_rows = 0
    for _first_member, blob, members in ordered_groups:
        expected_off = 0
        file_indices: list[int] = []
        lengths: list[int] = []
        for off, fi, ln in members:
            if off != expected_off:
                raise RuntimeError("S_PACK slices are not contiguous in physical order")
            if ln < 0:
                raise RuntimeError("negative S_PACK member length")
            file_indices.append(fi)
            lengths.append(ln)
            expected_off += ln

        contiguous = file_indices == list(range(file_indices[0], file_indices[0] + len(file_indices)))
        uniform = len(set(lengths)) == 1
        if contiguous:
            gap = file_indices[0] - previous_file_end
            if gap < 0:
                raise RuntimeError("file-ordered S_PACK groups overlap file-table membership")
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
            # Sparse fallback is exact and deliberately pays absolute indices. The optimized stable
            # representation is expected to use contiguous runs; correctness does not depend on it.
            membership = file_indices
            if uniform:
                mode = 2
                length_spec = lengths[0]
                uniform_groups += 1
            else:
                mode = 3
                length_spec = lengths
        q4.append([blob, mode, membership, length_spec])
        previous_file_end = max(previous_file_end, max(file_indices) + 1)
        packed_rows += len(file_indices)

    return {**compact, "f": rows, "q4": q4}, {
        "pack_groups": len(q4),
        "packed_rows": packed_rows,
        "uniform_length_groups": uniform_groups,
        "contiguous_groups": contiguous_groups,
        "descriptor_order": "first_file_table_member",
        "blob_id_encoding": "absolute_authenticated_id",
    }


def _restore_v4(candidate: dict) -> dict:
    standard = {k: copy.deepcopy(v) for k, v in candidate.items() if k != "q4"}
    previous_file_end = 0
    seen: set[int] = set()
    for desc in candidate["q4"]:
        if not isinstance(desc, list) or len(desc) != 4:
            raise RuntimeError("malformed implicit S_PACK v4 descriptor")
        blob, mode, membership, length_spec = int(desc[0]), int(desc[1]), desc[2], desc[3]
        if blob < 0 or mode not in (0, 1, 2, 3):
            raise RuntimeError("invalid implicit S_PACK v4 header")
        if mode == 0:
            if not isinstance(membership, list) or len(membership) != 2:
                raise RuntimeError("uniform contiguous membership descriptor")
            gap, count = int(membership[0]), int(membership[1])
            if gap < 0 or count <= 0:
                raise RuntimeError("invalid contiguous membership range")
            first = previous_file_end + gap
            file_indices = list(range(first, first + count))
            lengths = [int(length_spec)] * count
        elif mode == 1:
            gap = int(membership)
            lengths = [int(v) for v in length_spec]
            if gap < 0 or not lengths:
                raise RuntimeError("invalid varied contiguous membership range")
            first = previous_file_end + gap
            file_indices = list(range(first, first + len(lengths)))
        elif mode == 2:
            file_indices = [int(v) for v in membership]
            if not file_indices:
                raise RuntimeError("empty sparse membership descriptor")
            lengths = [int(length_spec)] * len(file_indices)
        else:
            file_indices = [int(v) for v in membership]
            lengths = [int(v) for v in length_spec]
            if not file_indices or len(lengths) != len(file_indices):
                raise RuntimeError("sparse membership/length count mismatch")
        if any(ln < 0 for ln in lengths):
            raise RuntimeError("negative implicit S_PACK member length")

        offset = 0
        for fi, ln in zip(file_indices, lengths, strict=True):
            if fi < 0 or fi >= len(standard["f"]) or fi in seen:
                raise RuntimeError("implicit S_PACK membership out of range or duplicated")
            standard["f"][fi][3] = [R24.S_PACK, blob, offset, ln]
            offset += ln
            seen.add(fi)
        previous_file_end = max(previous_file_end, max(file_indices) + 1)
    return standard


def _project_v4(index: dict, data: bytes) -> dict:
    candidate, shape = _compact_v4(index)
    restored = _restore_v4(candidate)
    expanded = CONTROL._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("implicit S_PACK v4 does not expand exactly to shipping r24 index")
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


def run(work_root):
    old = V3._project
    V3._project = _project_v4
    try:
        result = V3.run(work_root)
    finally:
        V3._project = old
    result["schema"] = "cmpct-v030-c25cc01-implicit-packmap-v4-oracle-v1"
    result["contract"]["blob_id_order_assumption"] = False
    result["contract"]["descriptor_order"] = "first_file_table_member"
    result["contract"]["sparse_membership_encoding"] = "absolute_file_indices"
    result["claim_boundary"] = (
        "Research-only exact representation estimate with no physical-blob/file-order coupling. "
        "A strict signal authorizes only canonical grammar/reader productization prerequisites; "
        "native/Android/all-15/recovery/final authority remain mandatory."
    )
    return result


def main() -> None:
    p = V3.argparse.ArgumentParser()
    p.add_argument("--work-root", type=V3.Path, default=V3.Path("benchmark-artifacts/v030-c25cc01-implicit-packmap-v4-work"))
    p.add_argument("--output", type=V3.Path, default=V3.Path("benchmark-artifacts/v030-c25cc01-implicit-packmap-v4.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "competitors": result["competitors"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("implicit S_PACK v4 experiment was not deterministic")


if __name__ == "__main__":
    main()
