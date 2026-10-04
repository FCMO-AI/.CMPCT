from __future__ import annotations

"""Research-only A/B: stable file-table locality packing + implicit pack-map control.

The locality-safe C25CC01 frontier already proved that <=8x physical packing is feasible and
fast on the encrypted-like workload, but its size is still above Zstd-19. The latest pack-map
receipt shows why metadata remains expensive: 1,400 S_PACK members are spread across 200
packs and *zero* packs form contiguous file-table runs under size-sorted packing.

This oracle tests the complementary representation law: preserve canonical file-table order
inside each identity-free extension bucket and flush only when the existing micro-pack target
or the exact <=8x decoded-context invariant would be violated. For near-incompressible tiny
members, this should preserve essentially the same payload cost while allowing compact control
to encode pack membership as dense file-index runs instead of 1,400 explicit/delta indices.

No benchmark identity, path literal, frozen hash, or workload label participates in policy.
The candidate must strongly verify to the same logical tree, expand its compact pack-map back
to the exact ordinary r24 semantic index, preserve <=8x locality, and beat both ZIP and Zstd-19
in bytes and complete creation time before this research lane reports a strict-four-way signal.
It grants zero product or release credit.
"""

import argparse
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

import msgpack

from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from benchmarks import v030_c25cc01_locality_pack_strategy_oracle as STRAT
from benchmarks import v030_c25cc01_packmap_control_oracle as PACKMAP
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import builder as B
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE
from experiments import entropygraph_v030_release_product as PRODUCT

LOCALITY = 8
ROUNDS = 5


def _stable_file_table_builder(self):
    refs, buckets = STRAT._eligible(self)
    row_index = {id(row): i for i, row in enumerate(self.files)}

    for ext, items in sorted(buckets.items()):
        # Canonical semantic order only. The digest is a deterministic tie-break for aliases whose
        # first logical row is equal; no pathname or benchmark identity is consulted.
        ordered = sorted(
            items,
            key=lambda hc: (
                min(row_index[id(row)] for row in refs[hc[0]]),
                hc[0],
            ),
        )
        groups = []
        cur = []
        for h, c in ordered:
            if cur and not STRAT._fits(cur, self.micro_pack_target, h, c):
                groups.append(cur)
                cur = []
            cur.append((h, c))
        if cur:
            groups.append(cur)

        for rows in groups:
            buf = bytearray()
            slots = {}
            for h, c in rows:
                off = len(buf)
                buf += c.raw
                slots[h] = (off, len(c.raw))
            min_member = min(max(1, ln) for _h, (_off, ln) in slots.items())
            if len(buf) > LOCALITY * min_member:
                raise RuntimeError("stable file-table packing violated <=8x construction invariant")
            ph = self.add_content(bytes(buf), ".cmpct-pack")
            for h, (off, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [R24.S_PACK, ph, off, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)


@contextmanager
def _patched():
    old = B.Builder._build_micro_packs
    B.Builder._build_micro_packs = _stable_file_table_builder
    try:
        yield
    finally:
        B.Builder._build_micro_packs = old


def _candidate_once(source: Path, root: Path, tag: str) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    archive = root / f"{tag}.cmpct"
    started = time.perf_counter()
    with _patched():
        PRODUCT._locality_bounded_r24_build(source, archive)
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"stable-order r24 verification failed: {verified!r}")

    index, data, _physical = PROFILE._source_r24_parts(archive)
    locality = PROFILE._audit_s_pack_locality(index)
    if float(locality["max_member_read_amplification"]) > LOCALITY:
        raise RuntimeError(f"stable-order candidate violated locality: {locality!r}")

    compact = PACKMAP._packmap_compact(index)
    standard = PACKMAP._restore_standard(compact)
    expanded = CONTROL._expand_index(
        standard,
        version=int(index["v"]),
        features=list(index["features"]),
    )
    if expanded != index:
        raise RuntimeError("stable-order pack-map failed exact semantic-index roundtrip")

    envelope = {"x": list(index["features"]), "c": compact}
    raw = msgpack.packb(envelope, use_bin_type=True)
    level, comp = PACKMAP._compress(raw)
    framing = R24.HDR.size + R24.FTR.size
    projected = framing + 2 * len(comp) + len(data)
    elapsed = time.perf_counter() - started

    contiguous, delta = compact["u"]
    return {
        "projected_bytes": int(projected),
        "complete_create_s": float(elapsed),
        "tree_sha256": verified.get("tree_sha256"),
        "locality": locality,
        "raw_control_bytes": len(raw),
        "compressed_control_bytes_per_copy": len(comp),
        "control_level": int(level),
        "contiguous_pack_groups": int(contiguous),
        "delta_pack_groups": int(delta),
        "s_pack_members": sum(
            1
            for row in index["files"]
            if row[1] == R24.K_FILE and row[6] and int(row[6][0]) == R24.S_PACK
        ),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)

    samples = []
    candidate_sizes = set()
    candidate_trees = set()
    zip_sizes = set()
    zstd_sizes = set()
    membership_shapes = set()
    locality_peaks = set()

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
                current[kind] = EXT._tar_zstd(
                    source,
                    rep_root / "target.tar.zst",
                    rep_root / "zstd-out",
                    zwork,
                )
        c = current["cmpct"]
        candidate_sizes.add(int(c["projected_bytes"]))
        candidate_trees.add(str(c["tree_sha256"]))
        zip_sizes.add(int(current["zip"]["archive_bytes"]))
        zstd_sizes.add(int(current["zstd"]["archive_bytes"]))
        membership_shapes.add((int(c["contiguous_pack_groups"]), int(c["delta_pack_groups"])))
        locality_peaks.add(float(c["locality"]["max_member_read_amplification"]))
        samples.append({
            "cmpct_create_s": float(c["complete_create_s"]),
            "zip_create_s": float(current["zip"]["create_s"]),
            "zstd19_create_s": float(current["zstd"]["create_s"]),
        })

    deterministic = (
        len(candidate_sizes) == len(candidate_trees) == len(zip_sizes) == len(zstd_sizes) == 1
        and len(membership_shapes) == 1
        and len(locality_peaks) == 1
    )
    cmpct_bytes = next(iter(candidate_sizes))
    zip_bytes = next(iter(zip_sizes))
    zstd_bytes = next(iter(zstd_sizes))
    cmpct_s = statistics.median(x["cmpct_create_s"] for x in samples)
    zip_s = statistics.median(x["zip_create_s"] for x in samples)
    zstd_s = statistics.median(x["zstd19_create_s"] for x in samples)

    # One final build supplies the structural receipt fields without trusting timing samples.
    structural = _candidate_once(source, work_root / "structural", "candidate")
    strict = bool(
        deterministic
        and cmpct_bytes < zip_bytes
        and cmpct_bytes < zstd_bytes
        and cmpct_s < zip_s
        and cmpct_s < zstd_s
    )
    return {
        "schema": "cmpct-v030-c25cc01-stable-order-packmap-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "format_revision_change": False,
            "locality_ceiling": LOCALITY,
            "semantic_index_roundtrip_exact": True,
            "two_authenticated_control_copies_retained": True,
            "policy_inputs": ["canonical_file_table_order", "extension_bucket", "logical_member_size", "micro_pack_target", "content_digest_tiebreak"],
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
        },
        "samples": samples,
        "gate": {
            "experiment_valid": deterministic,
            "strict_four_way_signal": strict,
            "passed": deterministic,
        },
        "claim_boundary": (
            "Research-only target-scoped representation evidence. A strict signal authorizes only the next "
            "productization prerequisite; canonical reader/native/Android/all-15/recovery/final authority remain mandatory."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-stable-order-packmap-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-stable-order-packmap.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "competitors": result["competitors"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("stable-order pack-map experiment could not be measured safely")


if __name__ == "__main__":
    main()
