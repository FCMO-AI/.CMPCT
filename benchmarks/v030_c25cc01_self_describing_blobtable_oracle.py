from __future__ import annotations

"""Research-only C25CC01 control projection that elides the redundant r24 blob table.

Canonical r24 physical blob records are self-describing: every record carries codec, decoded
size, compressed size and metadata length in ``BHDR`` while its byte offset is implied by the
preceding record length. The ordinary authenticated index repeats exactly those five values in
``index['blobs']``. C25CC01 already preserves the complete physical data span byte-for-byte, so
this oracle asks whether the compact control can omit that duplicate table and reconstruct it by
one bounded structural scan of the authenticated payload span before expanding to the exact r24
semantic index.

This is a representation experiment only. It changes no payload record, pack boundary, codec,
locality rule, selector, reader dispatch or release authority. A candidate is valid only if the
scanned table equals the shipping r24 blob table exactly and the final expanded semantic index is
identical. Two authenticated control copies remain charged in the projected archive size. The
same projection is also run across all 15 deterministic sources and may not regress the preceding
order-safe v4 control representation on any source.
"""

import copy
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_c25cc01_implicit_packmap_v4_oracle as V4
from benchmarks import v030_c25cc01_packmap_control_oracle as PACKMAP
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24


_UNSUPPORTED_V4_LAYOUT = "S_PACK slices are not contiguous in physical order"


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


def _project_pair(index: dict, data: bytes) -> tuple[dict | None, dict | None, str | None]:
    """Project v4/v5 or fail closed for the known non-canonical v4 layout assumption.

    v4 is a research predecessor, not the canonical grammar. Some valid r24 S_PACK layouts are
    physically sparse, and v4 deliberately cannot represent them. That is a falsified research
    candidate, not an invalid source archive. Preserve the negative result instead of crashing
    the all-15 custody lane. Any other exception remains a hard error.
    """
    try:
        baseline = V4._project_v4(index, data)
        candidate = _project_v5(index, data)
    except RuntimeError as exc:
        if str(exc) != _UNSUPPORTED_V4_LAYOUT:
            raise
        return None, None, str(exc)
    return baseline, candidate, None


def _all15_projection(work_root: Path) -> dict:
    """Prove exact reconstruction and non-regression against v4 on every deterministic source."""
    matrix_root = Path(work_root) / "all15-projection"
    shutil.rmtree(matrix_root, ignore_errors=True)
    matrix_root.mkdir(parents=True)
    roots = V4.V3.SAFE._build_all(matrix_root / "corpus")
    rows = []
    for key, source in sorted(roots.items(), key=lambda item: str(item[0])):
        label = "/".join(key) if isinstance(key, tuple) else str(key)
        tag = label.replace("/", "__")
        case_root = matrix_root / "cases" / tag
        case_root.mkdir(parents=True, exist_ok=True)
        archive = case_root / "source-r24.cmpct"
        with V4.V3.STABLE._patched():
            V4.V3.PRODUCT._locality_bounded_r24_build(source, archive)
        verified = V4.V3.PRODUCT.strong_verify(archive)
        if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
            raise RuntimeError(f"all-15 self-describing source failed strong verification: {label}")
        index, data, _physical = V4.V3.PROFILE._source_r24_parts(archive)
        locality = V4.V3.PROFILE._audit_s_pack_locality(index)
        if float(locality["max_member_read_amplification"]) > V4.V3.LOCALITY:
            raise RuntimeError(f"all-15 self-describing source violated locality: {label}")
        baseline, candidate, rejection = _project_pair(index, data)
        if rejection is not None:
            rows.append(
                {
                    "workload": label,
                    "tree_sha256": verified.get("tree_sha256"),
                    "supported": False,
                    "rejection_reason": rejection,
                    "v4_projected_bytes": None,
                    "v5_projected_bytes": None,
                    "saving_vs_v4_bytes": 0,
                    "semantic_index_roundtrip_exact": False,
                    "physical_payload_records_unchanged": True,
                    "max_member_read_amplification": float(locality["max_member_read_amplification"]),
                }
            )
            continue
        assert baseline is not None and candidate is not None
        baseline_bytes = int(baseline["projected_archive_bytes"])
        candidate_bytes = int(candidate["projected_archive_bytes"])
        rows.append(
            {
                "workload": label,
                "tree_sha256": verified.get("tree_sha256"),
                "supported": True,
                "rejection_reason": None,
                "blob_rows_elided": int(candidate["blob_rows_elided"]),
                "blob_table_msgpack_bytes_elided": int(candidate["blob_table_msgpack_bytes_elided"]),
                "v4_projected_bytes": baseline_bytes,
                "v5_projected_bytes": candidate_bytes,
                "saving_vs_v4_bytes": baseline_bytes - candidate_bytes,
                "semantic_index_roundtrip_exact": bool(candidate["semantic_index_roundtrip_exact"]),
                "physical_payload_records_unchanged": bool(candidate["physical_payload_records_unchanged"]),
                "max_member_read_amplification": float(locality["max_member_read_amplification"]),
            }
        )
    comparable = [row for row in rows if row["supported"]]
    unsupported = [row for row in rows if not row["supported"]]
    zero_regressions = all(int(row["saving_vs_v4_bytes"]) >= 0 for row in comparable)
    exact = len(unsupported) == 0 and all(
        row["semantic_index_roundtrip_exact"] and row["physical_payload_records_unchanged"] for row in comparable
    )
    return {
        "workloads": len(rows),
        "rows": rows,
        "supported_workloads": len(comparable),
        "unsupported_workloads": len(unsupported),
        "unsupported_reasons": sorted({str(row["rejection_reason"]) for row in unsupported}),
        "all_semantic_roundtrips_exact": exact,
        "zero_projected_byte_regressions_vs_v4": zero_regressions,
        "strict_improvement_count": sum(int(row["saving_vs_v4_bytes"]) > 0 for row in comparable),
        "aggregate_saving_vs_v4_bytes": sum(int(row["saving_vs_v4_bytes"]) for row in comparable),
    }


def run(work_root):
    work_root = Path(work_root)
    old = V4._project_v4
    V4._project_v4 = _project_v5
    try:
        result = V4.run(work_root / "target")
    finally:
        V4._project_v4 = old
    matrix = _all15_projection(work_root)
    result["schema"] = "cmpct-v030-c25cc01-self-describing-blobtable-oracle-v3"
    result["contract"].update(
        {
            "blob_table_in_control": False,
            "blob_table_reconstruction": "bounded sequential scan of unchanged authenticated r24 physical records",
            "physical_blob_header_semantic_owner": True,
            "physical_payload_records_changed": False,
            "all15_projection_required": True,
            "unsupported_predecessor_shapes_fail_closed": True,
            "release_credit": False,
        }
    )
    result["all15"] = matrix
    result["gate"]["all15_projection_complete"] = matrix["workloads"] == 15
    result["gate"]["all15_predecessor_shape_supported"] = matrix["unsupported_workloads"] == 0
    result["gate"]["all15_semantic_roundtrips_exact"] = matrix["all_semantic_roundtrips_exact"]
    result["gate"]["zero_projected_byte_regressions_vs_v4"] = matrix["zero_projected_byte_regressions_vs_v4"]
    result["gate"]["passed"] = bool(
        result["gate"]["passed"]
        and matrix["workloads"] == 15
        and matrix["unsupported_workloads"] == 0
        and matrix["all_semantic_roundtrips_exact"]
        and matrix["zero_projected_byte_regressions_vs_v4"]
    )
    result["claim_boundary"] = (
        "Research-only exact representation estimate. Unsupported predecessor v4 S_PACK shapes are durable "
        "negative evidence and receive zero promotion credit rather than being relabeled as source failures. "
        "A strict target signal plus a fully supported all-15 non-regression matrix authorizes only canonical "
        "grammar/reader productization prerequisites; hostile parsing, recovery, native, Android, selector timing "
        "and final release authority remain mandatory."
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
    print(json.dumps({"candidate": result["candidate"], "competitors": result["competitors"], "all15": {k: v for k, v in result["all15"].items() if k != "rows"}, "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("self-describing blob-table experiment failed exact all-15 non-regression")


if __name__ == "__main__":
    main()
