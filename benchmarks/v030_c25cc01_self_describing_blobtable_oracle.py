from __future__ import annotations

"""Research-only C25CC01 control projection that elides the redundant r24 blob table.

Canonical r24 physical blob records are self-describing: every record carries codec, decoded
size, compressed size and metadata length in ``BHDR`` while its byte offset is implied by the
preceding record length.  The ordinary authenticated index repeats exactly those five values in
``index['blobs']``.  C25CC01 already preserves the complete physical data span byte-for-byte, so
this oracle asks whether the compact control can omit that duplicate table and reconstruct it by
one bounded structural scan of the authenticated payload span before expanding to the exact r24
semantic index.

This is a representation experiment only.  It changes no payload record, pack boundary, codec,
locality rule, selector, reader dispatch or release authority.  A candidate is valid only if the
scanned table equals the shipping r24 blob table exactly and the final expanded semantic index is
identical.  Two authenticated control copies remain charged in the projected archive size.
"""

import copy
import json

import msgpack

from benchmarks import v030_c25cc01_implicit_packmap_v4_oracle as V4
from benchmarks import v030_c25cc01_packmap_control_oracle as PACKMAP
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24


def _scan_blob_table(data: bytes) -> list[list[int]]:
    """Reconstruct the canonical five-column r24 blob table from physical records only."""
    rows: list[list[int]] = []
    pos = 0
    while pos < len(data):
        if pos + R24.BHDR.size > len(data):
            raise RuntimeError("truncated self-describing r24 blob header")
        magic, codec, _flags, _reserved, usize, csize, meta_len, _crc32, _digest = R24.BHDR.unpack_from(data, pos)
        if magic != R24.BMAGIC:
            raise RuntimeError(f"invalid r24 blob magic at data offset {pos}")
        usize = int(usize)
        csize = int(csize)
        meta_len = int(meta_len)
        codec = int(codec)
        if min(usize, csize, meta_len, codec) < 0:
            raise RuntimeError("negative self-describing r24 blob field")
        end = pos + R24.BHDR.size + meta_len + csize
        if end <= pos or end > len(data):
            raise RuntimeError("r24 blob record exceeds authenticated data span")
        rows.append([pos, usize, csize, codec, meta_len])
        pos = end
    if pos != len(data):
        raise RuntimeError("r24 blob scan did not consume the exact physical data span")
    return rows


def _compact_v5(index: dict, data: bytes) -> tuple[dict, dict]:
    compact, shape = V4._compact_v4(index)
    encoded_blob_table = copy.deepcopy(compact.pop("b"))
    scanned = _scan_blob_table(data)
    if scanned != index["blobs"]:
        raise RuntimeError("physical r24 record scan does not reconstruct the shipping blob table exactly")
    if encoded_blob_table != index["blobs"]:
        raise RuntimeError("compact-control blob table drifted from shipping r24 semantics")
    return compact, {
        **shape,
        "blob_rows_elided": len(scanned),
        "blob_table_msgpack_bytes_elided": len(msgpack.packb(encoded_blob_table, use_bin_type=True)),
        "blob_table_reconstructed_from_physical_records": True,
    }


def _restore_v5(candidate: dict, data: bytes) -> dict:
    restored = {k: copy.deepcopy(v) for k, v in candidate.items()}
    restored["b"] = _scan_blob_table(data)
    return V4._restore_v4(restored)


def _project_v5(index: dict, data: bytes) -> dict:
    candidate, shape = _compact_v5(index, data)
    restored = _restore_v5(candidate, data)
    expanded = CONTROL._expand_index(restored, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise RuntimeError("self-describing blob-table elision does not expand exactly to shipping r24 index")
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
        "physical_payload_records_unchanged": True,
    }


def run(work_root):
    old = V4._project_v4
    V4._project_v4 = _project_v5
    try:
        result = V4.run(work_root)
    finally:
        V4._project_v4 = old
    result["schema"] = "cmpct-v030-c25cc01-self-describing-blobtable-oracle-v1"
    result["contract"].update(
        {
            "blob_table_in_control": False,
            "blob_table_reconstruction": "bounded sequential scan of unchanged authenticated r24 physical records",
            "physical_blob_header_semantic_owner": True,
            "physical_payload_records_changed": False,
            "release_credit": False,
        }
    )
    result["claim_boundary"] = (
        "Research-only exact representation estimate. A strict signal authorizes only canonical grammar/reader "
        "productization prerequisites; hostile parsing, recovery, native, Android, all-15 selector and final "
        "release authority remain mandatory."
    )
    return result


def main() -> None:
    p = V4.V3.argparse.ArgumentParser()
    p.add_argument("--work-root", type=V4.V3.Path, default=V4.V3.Path("benchmark-artifacts/v030-c25cc01-self-describing-blobtable-work"))
    p.add_argument("--output", type=V4.V3.Path, default=V4.V3.Path("benchmark-artifacts/v030-c25cc01-self-describing-blobtable.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "competitors": result["competitors"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("self-describing blob-table experiment was not deterministic")


if __name__ == "__main__":
    main()
