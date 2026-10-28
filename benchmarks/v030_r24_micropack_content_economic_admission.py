from __future__ import annotations

"""Path-blind content-economic admission for locality-derived micro-packs.

Mission lock
============
The extension-bucket ablation showed that indiscriminately mixing mature text
families costs 10,954 B on Developer.  The next hypothesis is more general: the
raw bytes themselves can decide whether a locality-legal group deserves to exist.

Builder rule (frozen before measurement):
* candidate must back at least one regular S_BLOB file, be non-DEFLATE, and be no
  larger than the existing micro-pack max-file limit;
* no path, suffix, extension, corpus id or ordinal may enter eligibility/grouping;
* candidates are sorted only by (raw length, content hash);
* physical group cap is still sum(raw) <= 8 * smallest-member raw bytes;
* at each completed locality group, one Zstd-1 audition compares joint compressed
  payload bytes against the sum of each member compressed separately at Zstd-1;
* group only on a strict joint-byte win; tie/loss falls back to independent files.

This referee compares complete membership-v1 artifacts against the shared-scan
independent control and the earned extension-bucket mechanism on origin and hostile
sources.  Audition CPU/wall is charged and exposed.  Research-only: no canonical
builder, version or frozen Genesis score changes here.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_hostile_transfer as HOST
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME


class ContentEconomicBuilder(BASE.BUILDER.Builder):
    def _build_micro_packs(self):
        refs = {}
        for row in self.files:
            if row[1] != BASE.R24.K_FILE or not row[6] or row[6][0] != BASE.R24.S_BLOB:
                continue
            h = bytes(row[6][1])
            refs.setdefault(h, []).append(row)

        eligible = []
        for h in refs:
            c = self.cands.get(h)
            if c is None or c.deflates or len(c.raw) > self.micro_pack_max_file:
                continue
            eligible.append((h, c))
        eligible.sort(key=lambda hc: (len(hc[1].raw), hc[0]))

        compressor = zstd.ZstdCompressor(level=1)
        emitted_groups = []
        audit_cpu = 0.0
        audit_wall = 0.0
        auditions = 0
        rejected_groups = 0
        rejected_members = 0

        def flush(group):
            nonlocal audit_cpu, audit_wall, auditions, rejected_groups, rejected_members
            if len(group) < 2:
                return
            buf = b"".join(c.raw for _, c in group)
            smallest = len(group[0][1].raw)
            if len(buf) > int(BASE.LOCALITY_BUDGET * max(1, smallest)):
                raise RuntimeError("content-economic group exceeds 8x smallest-member law")

            c0 = time.process_time(); w0 = time.perf_counter()
            joint = len(compressor.compress(buf))
            separate = sum(len(compressor.compress(c.raw)) for _, c in group)
            audit_cpu += time.process_time() - c0
            audit_wall += time.perf_counter() - w0
            auditions += 1
            if joint >= separate:
                rejected_groups += 1
                rejected_members += len(group)
                return

            ph = self.add_content(buf, ".cmpct-pack")
            slots = {}
            off = 0
            for h, c in group:
                slots[h] = (off, len(c.raw))
                off += len(c.raw)
            for h, (start, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [BASE.R24.S_PACK, ph, start, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)
            emitted_groups.append({
                "members": len(group),
                "raw_bytes": len(buf),
                "smallest_member_bytes": smallest,
                "max_raw_amplification": len(buf) / max(1, smallest),
                "audit_joint_zstd1_bytes": joint,
                "audit_separate_zstd1_bytes": separate,
                "audit_saved_bytes": separate - joint,
            })

        group = []
        used = 0
        cap = 0
        for h, c in eligible:
            size = len(c.raw)
            if not group:
                group = [(h, c)]; used = size; cap = int(BASE.LOCALITY_BUDGET * max(1, size)); continue
            if used + size > cap:
                flush(group)
                group = [(h, c)]; used = size; cap = int(BASE.LOCALITY_BUDGET * max(1, size))
            else:
                group.append((h, c)); used += size
        flush(group)

        self._locality_derived_groups = emitted_groups
        self._content_economic_audit = {
            "eligible_members": len(eligible),
            "auditions": auditions,
            "rejected_groups": rejected_groups,
            "rejected_members": rejected_members,
            "accepted_groups": len(emitted_groups),
            "accepted_members": sum(int(g["members"]) for g in emitted_groups),
            "audition_cpu_s": audit_cpu,
            "audition_wall_s": audit_wall,
            "accepted_audit_saved_bytes": sum(int(g["audit_saved_bytes"]) for g in emitted_groups),
        }


def _arm(builder_cls, source: Path, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    b = builder_cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    archive = root / "base.cmpct"
    build = BASE._build_with(b, archive)
    index, data = BASE._parse_r24(archive)
    locality = BASE._pack_locality(index)
    verify = BASE.PRODUCT.strong_verify(archive)
    if not verify.get("ok"):
        raise RuntimeError("base strong verify failed")
    membership = root / "membership.cmpct"
    if getattr(b, "_locality_derived_groups", []):
        wrapped = SAME._candidate(archive, membership, root)
    else:
        wrapped = SAME._noop_candidate(archive, len(data), verify)
    return {
        "archive_bytes": int(wrapped["archive_bytes"]),
        "r24_bytes": int(build["archive_bytes"]),
        "groups": len(getattr(b, "_locality_derived_groups", [])),
        "group_members": sum(int(g["members"]) for g in getattr(b, "_locality_derived_groups", [])),
        "locality_pass": bool(locality["locality_pass"]),
        "max_member_amplification": float(locality["max_member_amplification"]),
        "max_decode_unit_bytes": int(locality["max_decode_unit_bytes"]),
        "strong_tree_exact": bool(verify.get("ok")),
        "payload_exact": bool(wrapped["physical_payload_exact"]),
        "tail_recovery": bool(wrapped["primary_corruption_tail_recovery"]),
        "audit": dict(getattr(b, "_content_economic_audit", {})),
    }


def _one(source: Path, root: Path) -> dict:
    independent = _arm(SAME.NoMicroPackBuilder, source, root / "independent")
    extension = _arm(BASE.LocalityDerivedBuilder, source, root / "extension")
    economic = _arm(ContentEconomicBuilder, source, root / "economic")
    inv = {
        "independent_tree": independent["strong_tree_exact"],
        "extension_tree": extension["strong_tree_exact"],
        "economic_tree": economic["strong_tree_exact"],
        "extension_locality": extension["locality_pass"],
        "economic_locality": economic["locality_pass"],
        "economic_payload": economic["payload_exact"],
        "economic_tail_recovery": economic["tail_recovery"],
    }
    return {
        "independent": independent,
        "extension": extension,
        "content_economic": economic,
        "economic_delta_vs_independent_bytes": economic["archive_bytes"] - independent["archive_bytes"],
        "economic_delta_vs_extension_bytes": economic["archive_bytes"] - extension["archive_bytes"],
        "invariants": inv,
        "invariants_pass": all(inv.values()),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    origin = work_root / "origin"
    ATTR._build_sources(origin)
    hostile = HOST._build_corpora(work_root / "hostile")
    sources = {
        "origin_developer": origin / "01_developer_repository",
        "origin_tiny_files": origin / "08_many_tiny_files",
        **{f"hostile_{name}": path for name, path in hostile.items()},
    }
    rows = {name: _one(source, work_root / "work" / name) for name, source in sources.items()}
    invariant_failures = [name for name, row in rows.items() if not row["invariants_pass"]]
    independent_losses = [name for name, row in rows.items() if row["economic_delta_vs_independent_bytes"] > 0]
    extension_losses = [name for name, row in rows.items() if row["economic_delta_vs_extension_bytes"] > 0]
    if invariant_failures or independent_losses:
        verdict = "RETIRE_CONTENT_ECONOMIC_ADMISSION"
    elif extension_losses:
        verdict = "CONTENT_ECONOMIC_SAFE_BUT_NOT_EXTENSION_PARITY"
    else:
        verdict = "CONTENT_ECONOMIC_ADMISSION_EARNS_PATH_BLIND_TRANSFER"
    return {
        "schema": "cmpct-v030-r24-micropack-content-economic-admission-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "path_signal_used": False,
        "locality_budget": BASE.LOCALITY_BUDGET,
        "audition": "zstd-level-1 joint bytes strictly smaller than sum of individual zstd-level-1 bytes",
        "sources": rows,
        "invariant_failures": invariant_failures,
        "losses_vs_independent": independent_losses,
        "losses_vs_extension": extension_losses,
        "aggregate_delta_vs_independent_bytes": sum(r["economic_delta_vs_independent_bytes"] for r in rows.values()),
        "aggregate_delta_vs_extension_bytes": sum(r["economic_delta_vs_extension_bytes"] for r in rows.values()),
        "aggregate_audition_cpu_s": sum(r["content_economic"]["audit"].get("audition_cpu_s", 0.0) for r in rows.values()),
        "aggregate_audition_wall_s": sum(r["content_economic"]["audit"].get("audition_wall_s", 0.0) for r in rows.values()),
        "verdict": verdict,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-micropack-content-economic-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-micropack-content-economic.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "aggregate_delta_vs_independent_bytes": result["aggregate_delta_vs_independent_bytes"],
        "aggregate_delta_vs_extension_bytes": result["aggregate_delta_vs_extension_bytes"],
        "aggregate_audition_cpu_s": result["aggregate_audition_cpu_s"],
        "losses_vs_independent": result["losses_vs_independent"],
        "losses_vs_extension": result["losses_vs_extension"],
        "per_source": {name: {
            "di": row["economic_delta_vs_independent_bytes"],
            "de": row["economic_delta_vs_extension_bytes"],
            "groups": row["content_economic"]["groups"],
            "audit": row["content_economic"]["audit"],
        } for name, row in result["sources"].items()},
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
