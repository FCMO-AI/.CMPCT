from __future__ import annotations

"""Causal ablation for extension bucketing in the locality-derived micro-pack line.

Mission lock
------------
Hypothesis: the filename-extension bucket in LocalityDerivedBuilder is not required
for the earned physical benefit.  Keeping the exact same eligible set, size order,
8x smallest-member law, codec path and membership-v1 grammar, one path-blind bucket
should preserve semantics/locality and be no larger across origin + hostile sources.

Disproof: any invariant failure, any zero-group semantic drift, or any source where
the path-blind arm is larger under the same grammar.  This is research-only and
cannot by itself change canonical policy or release status.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_hostile_transfer as HOST
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME


class PathBlindLocalityDerivedBuilder(BASE.BUILDER.Builder):
    """Same eligibility + 8x law as BASE, but no extension-specific buckets."""

    def _build_micro_packs(self):
        refs = {}
        for row in self.files:
            if row[1] != BASE.R24.K_FILE or not row[6] or row[6][0] != BASE.R24.S_BLOB:
                continue
            h = bytes(row[6][1])
            refs.setdefault(h, []).append(row)

        eligible = []
        for h, rows in refs.items():
            c = self.cands.get(h)
            if c is None or c.deflates or len(c.raw) > self.micro_pack_max_file:
                continue
            # Preserve BASE eligibility exactly.  This ablation removes only the
            # bucket key; it does not claim extension-independent admission yet.
            if not any(x in BASE.BUILDER.TEXT_EXT for x in c.hints):
                continue
            eligible.append((h, c))

        eligible.sort(key=lambda hc: (len(hc[1].raw), hc[0]))
        emitted_groups = []

        def flush(group):
            if len(group) < 2:
                return
            buf = bytearray()
            slots = {}
            for h, c in group:
                off = len(buf)
                buf += c.raw
                slots[h] = (off, len(c.raw))
            smallest = len(group[0][1].raw)
            if len(buf) > int(BASE.LOCALITY_BUDGET * max(1, smallest)):
                raise RuntimeError("path-blind group exceeds 8x smallest-member law")
            ph = self.add_content(bytes(buf), ".cmpct-pack")
            for h, (off, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [BASE.R24.S_PACK, ph, off, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)
            emitted_groups.append({
                "members": len(group),
                "raw_bytes": len(buf),
                "smallest_member_bytes": smallest,
                "max_raw_amplification": len(buf) / max(1, smallest),
            })

        group = []
        used = 0
        cap = 0
        for h, c in eligible:
            size = len(c.raw)
            if not group:
                group = [(h, c)]
                used = size
                cap = int(BASE.LOCALITY_BUDGET * max(1, size))
                continue
            if used + size > cap:
                flush(group)
                group = [(h, c)]
                used = size
                cap = int(BASE.LOCALITY_BUDGET * max(1, size))
            else:
                group.append((h, c))
                used += size
        flush(group)
        self._locality_derived_groups = emitted_groups


def _build_arm(builder_cls, source: Path, out: Path) -> dict:
    b = builder_cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    build = BASE._build_with(b, out)
    groups = list(getattr(b, "_locality_derived_groups", []))
    index, data = BASE._parse_r24(out)
    verify = BASE.PRODUCT.strong_verify(out)
    if not verify.get("ok"):
        raise RuntimeError("ablation arm strong verification failed")
    locality = BASE._pack_locality(index)
    if groups:
        wrapped = SAME._candidate(out, out.with_suffix(".membership.cmpct"), out.parent)
    else:
        wrapped = SAME._noop_candidate(out, len(data), verify)
    return {
        "plain_archive_bytes": int(build["archive_bytes"]),
        "membership_archive_bytes": int(wrapped["archive_bytes"]),
        "group_count": len(groups),
        "group_members": sum(int(g["members"]) for g in groups),
        "physical_data_bytes": len(data),
        "build_cpu_s": float(build["build_cpu_s"]),
        "build_wall_s": float(build["build_wall_s"]),
        "max_member_amplification": float(locality["max_member_amplification"]),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "locality_pass": bool(locality["locality_pass"]),
        "strong_tree_exact": bool(verify.get("ok")),
        "tail_recovery": bool(wrapped["primary_corruption_tail_recovery"]),
        "payload_exact": bool(wrapped["physical_payload_exact"]),
    }


def _one(source: Path, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    ext = _build_arm(BASE.LocalityDerivedBuilder, source, work / "extension-bucket-r24.cmpct")
    blind = _build_arm(PathBlindLocalityDerivedBuilder, source, work / "path-blind-r24.cmpct")
    invariants = {
        "extension_locality": ext["locality_pass"],
        "path_blind_locality": blind["locality_pass"],
        "extension_tree": ext["strong_tree_exact"],
        "path_blind_tree": blind["strong_tree_exact"],
        "extension_tail_recovery": ext["tail_recovery"],
        "path_blind_tail_recovery": blind["tail_recovery"],
        "extension_payload_exact": ext["payload_exact"],
        "path_blind_payload_exact": blind["payload_exact"],
    }
    return {
        "extension_bucket": ext,
        "path_blind": blind,
        "path_blind_delta_bytes": blind["membership_archive_bytes"] - ext["membership_archive_bytes"],
        "invariants": invariants,
        "invariants_pass": all(invariants.values()),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    origin_root = work_root / "origin"
    ATTR._build_sources(origin_root)
    hostile = HOST._build_corpora(work_root / "hostile")
    sources = {
        "origin_developer": origin_root / "01_developer_repository",
        "origin_tiny_files": origin_root / "08_many_tiny_files",
        **{f"hostile_{name}": path for name, path in hostile.items()},
    }
    rows = {name: _one(path, work_root / "work" / name) for name, path in sources.items()}
    invariant_failures = [name for name, row in rows.items() if not row["invariants_pass"]]
    economic_losses = [name for name, row in rows.items() if row["path_blind_delta_bytes"] > 0]
    strict_wins = [name for name, row in rows.items() if row["path_blind_delta_bytes"] < 0]
    if invariant_failures:
        verdict = "RETIRE_PATH_BLIND_BUCKET_ABLATION"
    elif economic_losses:
        verdict = "EXTENSION_BUCKET_HAS_MEASURED_ECONOMIC_VALUE"
    else:
        verdict = "EXTENSION_BUCKET_NOT_REQUIRED"
    return {
        "schema": "cmpct-v030-r24-micropack-extension-bucket-ablation-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "eligibility_still_extension_gated": True,
        "locality_budget": BASE.LOCALITY_BUDGET,
        "sources": rows,
        "invariant_failures": invariant_failures,
        "economic_losses": economic_losses,
        "strict_path_blind_wins": strict_wins,
        "aggregate_delta_bytes": sum(int(r["path_blind_delta_bytes"]) for r in rows.values()),
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-micropack-extension-ablation-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-micropack-extension-ablation.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "aggregate_delta_bytes": result["aggregate_delta_bytes"],
        "invariant_failures": result["invariant_failures"],
        "economic_losses": result["economic_losses"],
        "strict_path_blind_wins": result["strict_path_blind_wins"],
        "deltas": {name: row["path_blind_delta_bytes"] for name, row in result["sources"].items()},
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
