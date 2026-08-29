from __future__ import annotations

"""Research-only A/B oracle for locality-safe r24 micro-pack grouping before C25CC01.

The current compact-control profile preserves the shipping r24 physical payload span byte-for-byte. Exact evidence
therefore correctly rejects source archives whose S_PACK records require >8x decoded context for a selected member.
This oracle tests the smallest architectural intervention that can actually change that fact: keep ordinary r24
semantics and codecs, but group micro-pack members so every generated pack satisfies the frozen <=8x decoded-context
law by construction. The production encoder is NOT changed here.

The policy is identity-free. Within each ordinary extension bucket, candidates retain the mature deterministic
(size, digest) ordering. A pack is flushed before either the existing byte target would be exceeded or the resulting
raw pack would exceed 8 * the smallest logical member in that pack. Since r24 S_PACK reads decode the complete owning
blob, that condition is a direct proof of the selected-member amplification bound for micro-packs. Deferred nested
container packs are unchanged and can still make a workload ineligible; such losses are preserved.

For each frozen workload the oracle builds current shipping r24 and the locality-safe A/B candidate, strongly verifies
both trees, attempts the real C25CC01 wrapper, and records byte regressions rather than hiding them. The encrypted-like
target is additionally remeasured against ZIP/Deflate-9 and solid Zstd-19 in rotated rounds. This lane grants no
release or selector credit; a useful result only authorizes productizing the encoder policy and rerunning ordinary
release authority.
"""

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from cmpct import builder as B
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

TARGET_SUFFIX = "07_incompressible_and_encrypted_like"
ROUNDS = 5
LOCALITY = 8


def _locality_safe_micro_packs(self):
    """Research clone of Builder._build_micro_packs with one additional representation-derived flush law."""
    refs = {}
    for row in self.files:
        if row[1] != R24.K_FILE or not row[6] or row[6][0] != R24.S_BLOB:
            continue
        h = bytes(row[6][1])
        refs.setdefault(h, []).append(row)

    eligible = []
    for h, rows in refs.items():
        c = self.cands.get(h)
        if c is None or c.deflates or len(c.raw) > self.micro_pack_max_file:
            continue
        if not any(x in B.TEXT_EXT for x in c.hints):
            continue
        eligible.append((h, c))

    buckets = {}
    for h, c in eligible:
        ext = next((x for x in sorted(c.hints) if x in B.TEXT_EXT), ".text")
        buckets.setdefault(ext, []).append((h, c))

    for ext, items in sorted(buckets.items()):
        items.sort(key=lambda hc: (len(hc[1].raw), hc[0]))
        group = []
        used = 0
        smallest = None

        def flush(rows):
            if not rows:
                return
            buf = bytearray()
            slots = {}
            for h, c in rows:
                off = len(buf)
                buf += c.raw
                slots[h] = (off, len(c.raw))
            # This is the exact representation invariant under test. Singletons trivially satisfy it.
            min_member = min(max(1, ln) for _h, (_off, ln) in slots.items())
            if len(buf) > LOCALITY * min_member:
                raise RuntimeError("locality-safe micro-pack construction violated its own bound")
            ph = self.add_content(bytes(buf), ".cmpct-pack")
            for h, (off, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [R24.S_PACK, ph, off, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)

        for h, c in items:
            size = len(c.raw)
            candidate_smallest = max(1, smallest if smallest is not None else size)
            candidate_used = used + size
            if group and (
                candidate_used > self.micro_pack_target
                or candidate_used > LOCALITY * candidate_smallest
            ):
                flush(group)
                group = []
                used = 0
                smallest = None
            if not group:
                smallest = size
            group.append((h, c))
            used += size
        flush(group)


@contextmanager
def _patched_micro_pack_builder():
    original = B.Builder._build_micro_packs
    B.Builder._build_micro_packs = _locality_safe_micro_packs
    try:
        yield
    finally:
        B.Builder._build_micro_packs = original


def _candidate_build(source: Path, archive: Path) -> tuple[dict, dict, float]:
    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with _patched_micro_pack_builder():
        stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
    build_s = time.perf_counter() - started
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"locality-safe candidate r24 verification failed: {verified!r}")
    return stats, verified, build_s


def _shipping_build(source: Path, archive: Path) -> tuple[dict, dict, float]:
    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
    build_s = time.perf_counter() - started
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"shipping r24 verification failed: {verified!r}")
    return stats, verified, build_s


def _wrap(candidate: Path, wrapped: Path) -> dict:
    try:
        stats = dict(PROFILE._write_profile(candidate, wrapped))
    except PROFILE.ProfileNotEligible as exc:
        return {"eligible": False, "reason": str(exc)}
    verified = PROFILE.strong_verify(wrapped)
    if not verified.get("ok"):
        raise RuntimeError(f"C25CC01 strong verification failed after locality-safe packing: {verified!r}")
    return {
        "eligible": True,
        "archive_bytes": int(wrapped.stat().st_size),
        "saving_vs_candidate_r24_bytes": int(stats["saving_vs_r24_bytes"]),
        "locality": stats["locality_admission"],
        "tree_sha256": verified.get("tree_sha256"),
    }


def _build_all(root: Path) -> dict[str, Path]:
    return CORPUS._build_all(root)


def _find_suffix(roots: dict[str, Path], suffix: str) -> tuple[str, Path]:
    rows = [(name, path) for name, path in roots.items() if name.endswith(suffix)]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one workload ending {suffix!r}, got {[name for name, _ in rows]!r}")
    return rows[0]


def _all15(work: Path, roots: dict[str, Path]) -> dict:
    rows = []
    candidate_regressions = []
    wrapped_regressions = []
    eligible = []
    for name in sorted(roots):
        source = roots[name]
        shipping = work / "shipping" / f"{name}.cmpct"
        candidate = work / "candidate" / f"{name}.cmpct"
        wrapped = work / "wrapped" / f"{name}.cmpct"
        _ss, shipping_verified, shipping_build_s = _shipping_build(source, shipping)
        _cs, candidate_verified, candidate_build_s = _candidate_build(source, candidate)
        if shipping_verified.get("tree_sha256") != candidate_verified.get("tree_sha256"):
            raise RuntimeError(f"locality-safe r24 changed logical tree for {name}")
        profile = _wrap(candidate, wrapped)
        shipping_bytes = int(shipping.stat().st_size)
        candidate_bytes = int(candidate.stat().st_size)
        row = {
            "workload": name,
            "shipping_r24_bytes": shipping_bytes,
            "candidate_r24_bytes": candidate_bytes,
            "candidate_delta_vs_shipping_bytes": candidate_bytes - shipping_bytes,
            "shipping_build_s": shipping_build_s,
            "candidate_build_s": candidate_build_s,
            "tree_sha256": candidate_verified.get("tree_sha256"),
            "compact_control": profile,
        }
        if candidate_bytes > shipping_bytes:
            candidate_regressions.append(name)
        if profile.get("eligible"):
            eligible.append(name)
            wrapped_bytes = int(profile["archive_bytes"])
            row["wrapped_delta_vs_shipping_bytes"] = wrapped_bytes - shipping_bytes
            if wrapped_bytes > shipping_bytes:
                wrapped_regressions.append(name)
        rows.append(row)
    return {
        "rows": rows,
        "workloads": len(rows),
        "candidate_byte_regressions": candidate_regressions,
        "wrapped_byte_regressions": wrapped_regressions,
        "compact_control_eligible": eligible,
        "compact_control_eligible_count": len(eligible),
    }


def _target_timing(work: Path, source: Path) -> dict:
    samples = []
    sizes = {"cmpct": set(), "zip": set(), "zstd": set()}
    trees = set()
    for rep in range(ROUNDS):
        order = ["cmpct", "zip", "zstd"]
        order = order[rep % 3 :] + order[: rep % 3]
        current = {}
        for kind in order:
            if kind == "cmpct":
                candidate = work / f"candidate-{rep}.cmpct"
                wrapped = work / f"wrapped-{rep}.cmpct"
                started = time.perf_counter()
                _stats, verified, _build_s = _candidate_build(source, candidate)
                profile = _wrap(candidate, wrapped)
                elapsed = time.perf_counter() - started
                current[kind] = {
                    "eligible": bool(profile.get("eligible")),
                    "archive_bytes": int(wrapped.stat().st_size) if profile.get("eligible") else None,
                    "create_s": elapsed,
                    "tree_sha256": verified.get("tree_sha256"),
                    "reason": profile.get("reason"),
                }
            elif kind == "zip":
                current[kind] = EXT._zip(source, work / f"target-{rep}.zip", work / f"zip-out-{rep}")
            else:
                zwork = work / f"zstd-work-{rep}"
                zwork.mkdir(parents=True, exist_ok=True)
                current[kind] = EXT._tar_zstd(
                    source,
                    work / f"target-{rep}.tar.zst",
                    work / f"zstd-out-{rep}",
                    zwork,
                )
        if current["cmpct"]["eligible"]:
            sizes["cmpct"].add(int(current["cmpct"]["archive_bytes"]))
        sizes["zip"].add(int(current["zip"]["archive_bytes"]))
        sizes["zstd"].add(int(current["zstd"]["archive_bytes"]))
        trees.add(str(current["cmpct"]["tree_sha256"]))
        samples.append({
            "cmpct_eligible": current["cmpct"]["eligible"],
            "cmpct_create_s": float(current["cmpct"]["create_s"]),
            "zip_create_s": float(current["zip"]["create_s"]),
            "zstd19_create_s": float(current["zstd"]["create_s"]),
            "cmpct_reason": current["cmpct"].get("reason"),
        })
    all_eligible = all(row["cmpct_eligible"] for row in samples)
    cmpct_bytes = next(iter(sizes["cmpct"])) if all_eligible and len(sizes["cmpct"]) == 1 else None
    zip_bytes = next(iter(sizes["zip"]))
    zstd_bytes = next(iter(sizes["zstd"]))
    cmpct_s = statistics.median(row["cmpct_create_s"] for row in samples)
    zip_s = statistics.median(row["zip_create_s"] for row in samples)
    zstd_s = statistics.median(row["zstd19_create_s"] for row in samples)
    return {
        "rounds": ROUNDS,
        "all_cmpct_profile_eligible": all_eligible,
        "cmpct_bytes": cmpct_bytes,
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "median_cmpct_complete_create_s": cmpct_s,
        "median_zip_create_s": zip_s,
        "median_zstd19_create_s": zstd_s,
        "size_deterministic": len(sizes["cmpct"]) <= 1 and len(sizes["zip"]) == 1 and len(sizes["zstd"]) == 1,
        "tree_deterministic": len(trees) == 1,
        "strict_four_way_win": bool(
            cmpct_bytes is not None
            and cmpct_bytes < zip_bytes
            and cmpct_bytes < zstd_bytes
            and cmpct_s < zip_s
            and cmpct_s < zstd_s
        ),
        "samples": samples,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = _build_all(work_root / "corpus")
    if len(roots) != 15:
        raise RuntimeError(f"expected exact 15-workload corpus, got {len(roots)}")
    all15 = _all15(work_root / "all15", roots)
    target_name, target_root = _find_suffix(roots, TARGET_SUFFIX)
    target = _target_timing(work_root / "target", target_root)
    target_row = next(row for row in all15["rows"] if row["workload"] == target_name)
    gate = {
        "experiment_valid": all15["workloads"] == 15 and target["size_deterministic"] and target["tree_deterministic"],
        "target_compact_control_eligible": bool(target_row["compact_control"].get("eligible")),
        "target_strict_four_way_win": target["strict_four_way_win"],
        "zero_candidate_r24_byte_regressions": not all15["candidate_byte_regressions"],
        "zero_wrapped_byte_regressions": not all15["wrapped_byte_regressions"],
    }
    # This is a diagnostic lane. A valid negative result is success; promotion remains closed unless every stronger
    # predicate is independently true and ordinary release authority later accepts the canonical implementation.
    gate["passed"] = gate["experiment_valid"]
    return {
        "schema": "cmpct-v030-c25cc01-locality-safe-pack-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_selector_change": False,
            "production_encoder_change": False,
            "format_revision_change": False,
            "locality_ceiling": LOCALITY,
            "policy_inputs": ["extension_bucket", "logical_member_size", "micro_pack_target", "content_digest_tiebreak"],
            "forbidden_policy_inputs": ["benchmark_name", "workload_label", "content_hash_identity", "file_path_literal", "frozen_pack_hash"],
        },
        "all15": all15,
        "target": {"workload": target_name, **target},
        "gate": gate,
        "claim_boundary": (
            "Research-only encoder A/B. A green diagnostic proves only that the exact 15-workload experiment ran. "
            "No release/selector credit is granted; any useful policy must be promoted into the canonical encoder, "
            "revalidated for bytes/runtime/recovery/native/Android, and pass strict final authority."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-locality-safe-pack-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-locality-safe-pack.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = {
        "candidate_byte_regressions": result["all15"]["candidate_byte_regressions"],
        "wrapped_byte_regressions": result["all15"]["wrapped_byte_regressions"],
        "compact_control_eligible_count": result["all15"]["compact_control_eligible_count"],
        "target": {k: v for k, v in result["target"].items() if k != "samples"},
        "gate": result["gate"],
    }
    print(json.dumps(summary, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("locality-safe pack oracle invalid")


if __name__ == "__main__":
    main()
