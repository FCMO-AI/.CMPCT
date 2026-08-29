from __future__ import annotations

"""Research-only search for a lower-overhead <=8x r24 micro-pack layout before C25CC01.

The first locality-safe encoder A/B proved the important architectural point: bounding each micro-pack by
``raw_pack_bytes <= 8 * smallest_member_bytes`` makes the encrypted-like C25CC01 candidate locality-eligible and
fast enough, but the simple ascending greedy grouping adds enough physical/control overhead to miss Zstd-19 size.
This oracle keeps exactly the same frozen locality invariant and ordinary r24 semantics while comparing several
identity-free deterministic binning strategies. It asks whether the byte loss is inherent to the locality law or
mostly an avoidable packing-efficiency artifact.

No strategy may use workload names, paths, frozen hashes or benchmark identity. Every candidate is strongly
verified and passed through the real C25CC01 wrapper. This is target-scoped research evidence only; even a win must
later survive canonical implementation, all-15 no-regression, recovery/native/Android and final release authority.
"""

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import time

from benchmarks import v030_c25cc01_locality_safe_pack_oracle as SAFE
from cmpct import builder as B
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_r24_compact_control_profile as PROFILE

LOCALITY = 8
STRATEGIES = ("ascending_greedy", "descending_greedy", "best_fit_desc", "size_class")


def _eligible(self):
    refs = {}
    for row in self.files:
        if row[1] != R24.K_FILE or not row[6] or row[6][0] != R24.S_BLOB:
            continue
        refs.setdefault(bytes(row[6][1]), []).append(row)
    buckets = {}
    for h, rows in refs.items():
        c = self.cands.get(h)
        if c is None or c.deflates or len(c.raw) > self.micro_pack_max_file:
            continue
        if not any(x in B.TEXT_EXT for x in c.hints):
            continue
        ext = next((x for x in sorted(c.hints) if x in B.TEXT_EXT), ".text")
        buckets.setdefault(ext, []).append((h, c))
    return refs, buckets


def _fits(rows, target, h, c):
    sizes = [len(x[1].raw) for x in rows]
    sizes.append(len(c.raw))
    total = sum(sizes)
    return total <= target and total <= LOCALITY * max(1, min(sizes))


def _groups(items, target, strategy):
    if strategy == "ascending_greedy":
        ordered = sorted(items, key=lambda hc: (len(hc[1].raw), hc[0]))
        out = []
        cur = []
        for h, c in ordered:
            if cur and not _fits(cur, target, h, c):
                out.append(cur); cur = []
            cur.append((h, c))
        if cur: out.append(cur)
        return out
    if strategy == "descending_greedy":
        ordered = sorted(items, key=lambda hc: (-len(hc[1].raw), hc[0]))
        out = []
        cur = []
        for h, c in ordered:
            if cur and not _fits(cur, target, h, c):
                out.append(cur); cur = []
            cur.append((h, c))
        if cur: out.append(cur)
        return out
    if strategy == "best_fit_desc":
        ordered = sorted(items, key=lambda hc: (-len(hc[1].raw), hc[0]))
        bins = []
        for h, c in ordered:
            choices = []
            for index, rows in enumerate(bins):
                if _fits(rows, target, h, c):
                    used = sum(len(x[1].raw) for x in rows) + len(c.raw)
                    choices.append((target - used, index))
            if choices:
                _slack, index = min(choices)
                bins[index].append((h, c))
            else:
                bins.append([(h, c)])
        # Stable physical publication order independent of benchmark identity.
        return sorted(bins, key=lambda rows: (len(rows[0][1].raw), rows[0][0]))
    if strategy == "size_class":
        classes = {}
        for h, c in items:
            size = max(1, len(c.raw))
            cls = size.bit_length() - 1
            classes.setdefault(cls, []).append((h, c))
        out = []
        for cls in sorted(classes):
            ordered = sorted(classes[cls], key=lambda hc: (len(hc[1].raw), hc[0]))
            cur = []
            for h, c in ordered:
                if cur and not _fits(cur, target, h, c):
                    out.append(cur); cur = []
                cur.append((h, c))
            if cur: out.append(cur)
        return out
    raise ValueError(strategy)


def _builder_for(strategy):
    def build(self):
        refs, buckets = _eligible(self)
        for ext, items in sorted(buckets.items()):
            for rows in _groups(items, self.micro_pack_target, strategy):
                buf = bytearray(); slots = {}
                for h, c in rows:
                    off = len(buf); buf += c.raw; slots[h] = (off, len(c.raw))
                min_member = min(max(1, ln) for _h, (_off, ln) in slots.items())
                if len(buf) > LOCALITY * min_member:
                    raise RuntimeError(f"{strategy} violated locality construction invariant")
                ph = self.add_content(bytes(buf), ".cmpct-pack")
                for h, (off, ln) in slots.items():
                    for row in refs[h]: row[6] = [R24.S_PACK, ph, off, ln]
                for h in slots:
                    if h != ph: self.cands.pop(h, None)
    return build


@contextmanager
def _patched(strategy):
    old = B.Builder._build_micro_packs
    B.Builder._build_micro_packs = _builder_for(strategy)
    try:
        yield
    finally:
        B.Builder._build_micro_packs = old


def _build(source: Path, archive: Path, strategy: str) -> dict:
    archive.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with _patched(strategy):
        stats = dict(PRODUCT._locality_bounded_r24_build(source, archive))
    elapsed = time.perf_counter() - started
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
        raise RuntimeError(f"{strategy} r24 strong verification failed: {verified!r}")
    wrapped = archive.with_suffix(".c25cc01")
    try:
        profile_stats = dict(PROFILE._write_profile(archive, wrapped))
    except PROFILE.ProfileNotEligible as exc:
        return {
            "strategy": strategy, "r24_bytes": int(archive.stat().st_size), "r24_create_s": elapsed,
            "tree_sha256": verified.get("tree_sha256"), "eligible": False, "reason": str(exc),
        }
    pv = PROFILE.strong_verify(wrapped)
    if not pv.get("ok") or pv.get("tree_sha256") != verified.get("tree_sha256"):
        raise RuntimeError(f"{strategy} C25CC01 strong verification/tree mismatch")
    return {
        "strategy": strategy,
        "r24_bytes": int(archive.stat().st_size),
        "r24_create_s": float(elapsed),
        "tree_sha256": verified.get("tree_sha256"),
        "eligible": True,
        "wrapped_bytes": int(wrapped.stat().st_size),
        "saving_vs_r24_bytes": int(profile_stats["saving_vs_r24_bytes"]),
        "locality": profile_stats["locality_admission"],
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    roots = SAFE._build_all(work_root / "corpus")
    name, source = SAFE._find_suffix(roots, SAFE.TARGET_SUFFIX)
    rows = []
    for strategy in STRATEGIES:
        rows.append(_build(source, work_root / strategy / "candidate.cmpct", strategy))
    trees = {row["tree_sha256"] for row in rows}
    if len(trees) != 1:
        raise RuntimeError("packing strategy changed logical tree identity")
    eligible = [row for row in rows if row["eligible"]]
    best = min(eligible, key=lambda row: (row["wrapped_bytes"], row["r24_create_s"], row["strategy"])) if eligible else None
    baseline = next(row for row in rows if row["strategy"] == "ascending_greedy")
    improvement = (int(baseline["wrapped_bytes"]) - int(best["wrapped_bytes"])) if best and baseline["eligible"] else None
    return {
        "schema": "cmpct-v030-c25cc01-locality-pack-strategy-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "locality_ceiling": LOCALITY,
            "policy_inputs": ["extension_bucket", "logical_member_size", "micro_pack_target", "content_digest_tiebreak"],
            "forbidden_policy_inputs": ["benchmark_name", "workload_label", "file_path_literal", "frozen_pack_hash"],
        },
        "target": name,
        "strategies": rows,
        "best": best,
        "best_wrapped_saving_vs_ascending_bytes": improvement,
        "gate": {"experiment_valid": len(rows) == len(STRATEGIES) and len(trees) == 1, "passed": len(rows) == len(STRATEGIES) and len(trees) == 1},
        "claim_boundary": (
            "Target-scoped research search under the unchanged <=8x physical locality invariant. A smaller eligible "
            "layout proves only that packing overhead is reducible; it grants no product or release credit until "
            "canonical implementation and exact all-15/no-regression/native/Android/recovery authority."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-pack-strategy-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-c25cc01-pack-strategy.json")); a=p.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"strategies": result["strategies"], "best": result["best"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]: raise SystemExit("C25CC01 locality pack strategy oracle invalid")


if __name__ == "__main__": main()
