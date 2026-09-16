from __future__ import annotations

"""Explain the 10,954-byte Developer loss from removing extension buckets.

This is a diagnostic referee. It does not propose a selector. It freezes the
Developer source and compares the exact group plans emitted by the earned
extension-bucket builder and the already-tested single-bucket ablation. For every
pack, it records member sizes and content-only observations that are available
without paths: newline/control/ASCII/zero fractions, byte diversity and cheap
Zstd-1 ratio. The goal is to identify which cross-family merges buy/lose bytes
before designing any path-blind replacement.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

import zstandard as zstd

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_extension_bucket_ablation as ABL
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME


def _content_features(raw: bytes) -> dict:
    n = max(1, len(raw))
    prefix = raw[:4096]
    pn = max(1, len(prefix))
    ascii_print = sum(32 <= b < 127 or b in (9, 10, 13) for b in prefix) / pn
    newline = sum(b in (10, 13) for b in prefix) / pn
    zero = prefix.count(0) / pn
    control = sum((b < 32 and b not in (9, 10, 13)) for b in prefix) / pn
    diversity = len(set(prefix)) / 256.0
    cheap = len(zstd.ZstdCompressor(level=1).compress(raw)) / n
    return {
        "size": len(raw),
        "ascii_fraction_4k": round(ascii_print, 6),
        "newline_fraction_4k": round(newline, 6),
        "zero_fraction_4k": round(zero, 6),
        "control_fraction_4k": round(control, 6),
        "byte_diversity_4k": round(diversity, 6),
        "zstd1_ratio": round(cheap, 6),
    }


def _capture(builder_cls, source: Path, work: Path) -> dict:
    b = builder_cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    b.scan()
    before = {
        h: (bytes(c.raw), tuple(sorted(c.hints)), bool(c.deflates))
        for h, c in b.cands.items()
    }
    b._build_micro_packs()

    # Reconstruct only the exact eligibility surface used by the earned builder:
    # small, non-DEFLATE candidates with at least one mature text hint.
    member_rows = []
    for h, (raw, hints, deflates) in before.items():
        if deflates or len(raw) > b.micro_pack_max_file:
            continue
        if not any(x in BASE.BUILDER.TEXT_EXT for x in hints):
            continue
        member_rows.append((len(raw), h, raw, hints))
    member_rows.sort(key=lambda x: (x[0], x[1]))

    buckets = {}
    if builder_cls is BASE.LocalityDerivedBuilder:
        for size, h, raw, hints in member_rows:
            ext = next((x for x in hints if x in BASE.BUILDER.TEXT_EXT), "")
            buckets.setdefault(ext, []).append((size, h, raw, hints))
    else:
        buckets = {"<single>": member_rows}

    plans = []
    for bucket, items in sorted(buckets.items()):
        group = []
        used = 0
        cap = 0

        def flush():
            nonlocal group, used, cap
            if len(group) < 2:
                group = []
                used = 0
                cap = 0
                return
            raw = b"".join(x[2] for x in group)
            comp = zstd.ZstdCompressor(level=3).compress(raw)
            plans.append(
                {
                    "bucket": bucket,
                    "members": len(group),
                    "raw_bytes": len(raw),
                    "zstd3_bytes": len(comp),
                    "zstd3_ratio": round(len(comp) / max(1, len(raw)), 6),
                    "smallest_member": group[0][0],
                    "largest_member": group[-1][0],
                    "extension_mix": dict(
                        Counter(
                            next((x for x in g[3] if x in BASE.BUILDER.TEXT_EXT), "")
                            for g in group
                        )
                    ),
                    "members_features": [_content_features(g[2]) for g in group],
                    "payload_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            group = []
            used = 0
            cap = 0

        for item in items:
            size = item[0]
            if not group:
                group = [item]
                used = size
                cap = int(BASE.LOCALITY_BUDGET * max(1, size))
                continue
            if used + size > cap:
                flush()
                group = [item]
                used = size
                cap = int(BASE.LOCALITY_BUDGET * max(1, size))
            else:
                group.append(item)
                used += size
        flush()

    work.mkdir(parents=True, exist_ok=True)
    out = work / "artifact.cmpct"
    b2 = builder_cls(source, deflate_reuse_min=0, workers=1)
    b2.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    BASE._build_with(b2, out)
    wrapped = SAME._candidate(out, work / "membership.cmpct", work)
    return {"archive_bytes": int(wrapped["archive_bytes"]), "plans": plans, "groups": len(plans)}


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    srcroot = work_root / "source"
    ATTR._build_sources(srcroot)
    source = srcroot / "01_developer_repository"
    ext = _capture(BASE.LocalityDerivedBuilder, source, work_root / "extension")
    blind = _capture(ABL.PathBlindLocalityDerivedBuilder, source, work_root / "path-blind")
    mixed = [p for p in blind["plans"] if len(p["extension_mix"]) > 1]
    return {
        "schema": "cmpct-v030-r24-micropack-extension-value-attribution-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "developer_extension_archive_bytes": ext["archive_bytes"],
        "developer_path_blind_archive_bytes": blind["archive_bytes"],
        "path_blind_delta_bytes": blind["archive_bytes"] - ext["archive_bytes"],
        "extension_group_count": ext["groups"],
        "path_blind_group_count": blind["groups"],
        "path_blind_mixed_group_count": len(mixed),
        "extension_plans": ext["plans"],
        "path_blind_plans": blind["plans"],
        "mixed_path_blind_plans": mixed,
        "verdict": (
            "EXTENSION_VALUE_ATTRIBUTED_TO_CROSS_FAMILY_GROUPING"
            if mixed and blind["archive_bytes"] > ext["archive_bytes"]
            else "EXTENSION_VALUE_NOT_YET_ATTRIBUTED"
        ),
        "policy_guard": "Diagnostic only: path/extension labels appear only in post-hoc explanation and are not promoted as selector evidence.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-micropack-extension-value-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-micropack-extension-value.json"))
    args = ap.parse_args()
    d = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {k: d[k] for k in ("verdict", "path_blind_delta_bytes", "extension_group_count", "path_blind_group_count", "path_blind_mixed_group_count")},
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
