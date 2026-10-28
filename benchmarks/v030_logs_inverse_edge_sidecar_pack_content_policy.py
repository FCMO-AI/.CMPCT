from __future__ import annotations

"""Path-invariant admission overlay for the strict Logs sidecar-pack winner.

The original sidecar-pack oracle proved the representation can cross v0.29 + ZIP +
Zstd-19 simultaneously, but its research scanner uses filename suffixes to classify
compressed sidecars and loose logs. That is not benchmark identity, yet it is still too
path-dependent for canonical admission. This instrument changes *only* discovery and
packing policy:

- gzip/XZ/Zstd are identified from bytes and a bounded successful decode, never suffixes;
- inverse edges require exact decoded bytes + SHA equality to any non-compressed member;
- ordinary non-compressed members are segmented by the same <=8 MiB / <=8x law;
- retained compressed members are grouped only by detected codec family;
- the old writer, reader, timing boundary, competitor measurement, tree verification and
  v0.29/ZIP/Zstd gates are reused unchanged.

A green result is a productization prerequisite, not release credit. It proves the strict
Logs mechanism survives removal of filename-derived admission before canonical grammar,
recovery/native/Android and all-15 authority work.
"""

import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path

import zstandard as zstd

from benchmarks import v030_logs_inverse_edge_sidecar_pack_oracle as OLD

MAX_DECODE_UNIT = OLD.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = OLD.MAX_MEMBER_AMPLIFICATION
CODEC_RANK = {"zstd": 0, "gzip": 1, "xz": 2}


def _detect_codec(raw: bytes) -> str | None:
    if raw.startswith(b"\x1f\x8b"):
        return "gzip"
    if raw.startswith(b"\xfd7zXZ\x00"):
        return "xz"
    if raw.startswith(b"\x28\xb5\x2f\xfd"):
        return "zstd"
    return None


def _decode(codec: str, raw: bytes) -> bytes:
    if codec == "gzip":
        out = gzip.decompress(raw)
    elif codec == "xz":
        out = lzma.decompress(raw)
    elif codec == "zstd":
        out = zstd.ZstdDecompressor().decompress(raw, max_output_size=MAX_DECODE_UNIT)
    else:
        raise RuntimeError(f"unsupported content-detected codec: {codec}")
    if len(out) > MAX_DECODE_UNIT:
        raise RuntimeError("content-detected inverse output exceeds decode-unit bound")
    return out


def _scan_and_edges(stage: Path) -> tuple[list[dict], dict[int, tuple[int, str]], dict]:
    rows: list[dict] = []
    for path in sorted(item for item in stage.rglob("*") if item.is_file()):
        raw = path.read_bytes()
        codec = _detect_codec(raw)
        rows.append({
            "rel": path.relative_to(stage).as_posix(),
            "raw": raw,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).digest(),
            # Keep the legacy field so the unchanged writer can serialize the same row shape;
            # admission below never reads it.
            "suffix": path.suffix.lower(),
            "content_codec": codec,
        })

    plain_by_identity: dict[tuple[int, bytes], list[int]] = {}
    for index, row in enumerate(rows):
        if row["content_codec"] is None:
            plain_by_identity.setdefault((row["size"], row["sha256"]), []).append(index)

    candidates: dict[int, list[tuple[int, int, str]]] = {}
    decoded_sidecars = 0
    decoded_bytes = 0
    for source_index, row in enumerate(rows):
        codec = row["content_codec"]
        if codec is None:
            continue
        try:
            plain = _decode(codec, row["raw"])
        except Exception:
            # Magic collision or malformed compressed input remains an ordinary direct member;
            # malformed content must never become an inverse dependency.
            row["content_codec"] = None
            continue
        decoded_sidecars += 1
        decoded_bytes += len(plain)
        key = (len(plain), hashlib.sha256(plain).digest())
        for target_index in plain_by_identity.get(key, ()):
            if plain == rows[target_index]["raw"]:
                candidates.setdefault(target_index, []).append((CODEC_RANK[codec], source_index, codec))

    edges: dict[int, tuple[int, str]] = {}
    for target_index, options in candidates.items():
        _rank, source_index, codec = min(options)
        edges[target_index] = (source_index, codec)
    return rows, edges, {
        "policy": "content-signature-plus-exact-decoded-identity-v1",
        "uses_path_or_suffix_for_codec_admission": False,
        "decoded_sidecars": decoded_sidecars,
        "decoded_sidecar_plain_bytes": decoded_bytes,
        "inverse_edges": len(edges),
        "inverse_edge_targets": [rows[index]["rel"] for index in sorted(edges)],
        "inverse_edge_sources": [rows[edges[index][0]]["rel"] for index in sorted(edges)],
        "inverse_edge_codecs": [edges[index][1] for index in sorted(edges)],
    }


def _plan_segments(rows: list[dict], edges: dict[int, tuple[int, str]]) -> tuple[list[list[int]], float, int]:
    # Any ordinary non-compressed logical member is eligible; names/extensions are irrelevant.
    candidates = [
        index for index, row in enumerate(rows)
        if row.get("content_codec") is None and index not in edges
    ]
    segments: list[list[int]] = []
    current: list[int] = []
    current_bytes = 0
    for index in candidates:
        size = int(rows[index]["size"])
        proposed = current + [index]
        proposed_bytes = current_bytes + size
        min_member = min(int(rows[item]["size"]) for item in proposed)
        if current and (
            proposed_bytes > MAX_DECODE_UNIT
            or proposed_bytes > int(MAX_MEMBER_AMPLIFICATION * max(1, min_member))
        ):
            segments.append(current)
            current = [index]
            current_bytes = size
        else:
            current = proposed
            current_bytes = proposed_bytes
    if current:
        segments.append(current)

    max_amp = 1.0
    max_unit = 0
    for segment in segments:
        decoded = sum(int(rows[index]["size"]) for index in segment)
        max_unit = max(max_unit, decoded)
        for index in segment:
            max_amp = max(max_amp, decoded / max(1, int(rows[index]["size"])))
    if max_amp > MAX_MEMBER_AMPLIFICATION or max_unit > MAX_DECODE_UNIT:
        raise RuntimeError(f"content-policy segment locality failed: amp={max_amp} unit={max_unit}")
    return segments, max_amp, max_unit


def _plan_direct_groups(
    rows: list[dict],
    edges: dict[int, tuple[int, str]],
    raw_segments: list[list[int]],
) -> list[list[int]]:
    raw_owned = {index for segment in raw_segments for index in segment}
    derived_targets = set(edges)
    direct = [index for index in range(len(rows)) if index not in derived_targets and index not in raw_owned]
    derived_by_source = OLD._derived_targets_by_source(edges)
    groups: list[list[int]] = []
    families = sorted({str(rows[index].get("content_codec") or "opaque") for index in direct})
    for family in families:
        current: list[int] = []
        for index in [item for item in direct if str(rows[item].get("content_codec") or "opaque") == family]:
            proposed = current + [index]
            if current and not OLD._group_is_safe(rows, proposed, derived_by_source):
                groups.append(current)
                current = [index]
                if not OLD._group_is_safe(rows, current, derived_by_source):
                    raise RuntimeError("single content-classified direct member violates locality")
            else:
                current = proposed
                if not OLD._group_is_safe(rows, current, derived_by_source):
                    raise RuntimeError("content-classified direct grouping violates locality")
        if current:
            groups.append(current)
    return groups


def run(work_root: Path) -> dict:
    # Keep one semantic owner for archive framing/timing/verification. Swap only the three
    # research planning hooks, then restore them even if the decisive experiment fails.
    old_scan = OLD.BASE._scan_and_edges
    old_segments = OLD.BASE._plan_segments
    old_groups = OLD._plan_direct_groups
    OLD.BASE._scan_and_edges = _scan_and_edges
    OLD.BASE._plan_segments = _plan_segments
    OLD._plan_direct_groups = _plan_direct_groups
    try:
        result = OLD.run(work_root)
    finally:
        OLD.BASE._scan_and_edges = old_scan
        OLD.BASE._plan_segments = old_segments
        OLD._plan_direct_groups = old_groups
    result = dict(result)
    result["schema"] = "cmpct-v030-logs-sidecar-content-policy-v1"
    result["admission_policy"] = "content-signature-plus-exact-decoded-identity-v1"
    result["uses_path_or_suffix_for_admission"] = False
    result["release_credit"] = False
    result["domination_audit"] = {
        "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
        "diagnosis": "D5",
        "radicality": "R2",
        "saturation_triggers": ["S6"],
        "research_priority_score": 98,
        "pre_mortem": "the strict Logs win may disappear once filename-derived codec/family admission is removed",
        "builder": "reuse identical archive/timing/verifier with byte-signature codec classification and exact decoded-content edges",
        "hostile_review": "even a green policy-invariant research archive is not canonical grammar or native/Android parity",
        "terminal_decision": "PROMOTE_NEXT_PREREQUISITE" if result["summary"]["release_floor_four_way_win"] else "REHABILITATE_DEBT",
        "next_decisive_test": "encode the same content-derived grouping in the recoverable canonical Logs profile and prove Python/native/Android reader parity" if result["summary"]["release_floor_four_way_win"] else "measure which path-invariant grouping/segmentation change consumed the v0.29 or competitor margin",
    }
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
