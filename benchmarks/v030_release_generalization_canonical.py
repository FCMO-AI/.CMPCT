from __future__ import annotations

"""Canonical-byte authority for the frozen v0.30 15-workload release gate.

The historical generalization harness owns the frozen 15 source trees, accepted-v0.29 row bytes and numeric
release thresholds.  The shipping v0.30 product, however, has a deliberately different stats schema because it
builds genuine canonical r24 and r25 complete products.  This adapter therefore keeps the two evidence domains
separate instead of pretending canonical product stats are the old research-candidate dictionary.

For every workload we independently rebuild the accepted v0.29 floor on the *original* benchmark tree, then build
the actual ``entropygraph_v030_release_product`` and project only measured facts into the historical harness.  In
particular, ``v029_research_floor_bytes`` from the staged r25 tree is never substituted for the accepted historical
v0.29 bytes.  That distinction is release-critical because the staged r25 tree includes filesystem-manifest
semantics that the frozen historical substrate did not.
"""

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import time

from benchmarks import v030_release_generalization as B
from experiments import entropygraph_v030_release_product as CANON
from experiments import entropygraph_v030_geometry_overlay_g04 as HIST_G04


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _r24_selected_member_amplification(archive: Path) -> float:
    """Measure normative r24 locality on the largest regular user-visible member.

    The release contract intentionally uses one deterministic selected member for both r24 and r25: the largest
    regular user-visible member.  Measuring every tiny packed file and then taking the worst ratio would answer a
    different question and can explode on r24 small-file packs even though the normative selected-member operation
    is local.  We still observe the real public ``CMPCT.read`` operation and charge every blob context it touches;
    no build-time proxy and no missing-field default is allowed.
    """
    original = CANON.CMPCT

    class TrackingR24(original):
        def __init__(self, path):
            super().__init__(path)
            self.observed_blob_ids: set[int] = set()

        def _blob(self, idx):
            self.observed_blob_ids.add(int(idx))
            return super()._blob(idx)

    with TrackingR24(archive) as reader:
        regular = [row for row in reader.files if row[1] == CANON.R24_CODEC.K_FILE]
        if not regular:
            raise RuntimeError("canonical r24 locality measurement found no regular user-visible member")
        row = max(regular, key=lambda item: (int(item[4]), str(item[0])))
        rel, _kind, _mode, _mtime, size, _digest, _storage = row
        reader.observed_blob_ids.clear()
        raw = bytes(reader.read(rel))
        if len(raw) != int(size):
            raise RuntimeError(f"canonical r24 locality read length drift for {rel!r}")
        decoded = sum(int(reader.blobs[idx][1]) for idx in reader.observed_blob_ids)
        return max(len(raw), decoded) / max(1, len(raw))


def _normalize_product_stats(
    product: dict,
    historical_bytes: int,
    historical_stats: dict,
    archive: Path,
    product_create_s: float,
) -> dict:
    """Project measured canonical product facts into the immutable historical gate schema.

    Promoted structural terminals intentionally expose a smaller product-native stats surface than the historical
    research tournament.  Legacy fields used only for evidence reporting are therefore derived from the *actual
    published archive* rather than assumed present.  The release timing is always the caller-observed complete
    ``CANON.build`` wall time, so promoted preflights/terminals cannot accidentally hide dispatch work by reporting
    a narrower internal timer.
    """
    r25 = product.get("r25") if isinstance(product.get("r25"), dict) else {}
    g04 = r25.get("g04") if isinstance(r25.get("g04"), dict) else {}
    g04 = dict(g04)
    # The historical create-time comparator must be the exact original-tree accepted-v0.29 build, never the
    # staged-r25 research floor.  Keep it inside the legacy location only because B's diagnostic helper reads it.
    g04["v029"] = dict(historical_stats)

    final_revision, final_profile = CANON._revision_for_archive(archive)
    final_revision = int(final_revision)
    if final_revision == 24:
        max_amp = _r24_selected_member_amplification(archive)
    elif final_revision == CANON.REVISION:
        observed = r25.get("max_selected_member_read_amplification")
        if not isinstance(observed, (int, float)):
            # Promoted revision-25 terminals (for example compact-control/logs) own their own locality proof and
            # do not necessarily carry the mature tournament's nested r25 receipt.  Ask the public operation for
            # one deterministic selected-member measurement instead of defaulting locality to zero.
            members = [row for row in CANON.list_members(archive) if row.get("kind") == "file"]
            if not members:
                raise RuntimeError("canonical r25 product locality measurement found no regular user-visible member")
            selected_member = max(members, key=lambda row: (int(row.get("size", 0)), str(row.get("path", ""))))
            _raw, read_stats = CANON.read_member_with_stats(archive, str(selected_member["path"]))
            observed = read_stats.get("decoded_context_amplification")
        if not isinstance(observed, (int, float)):
            raise RuntimeError("canonical r25 product omitted selected-member locality accounting")
        max_amp = float(observed)
    else:
        raise RuntimeError(f"canonical product emitted unexpected revision {final_revision!r}")

    selected = product.get("selected")
    if not isinstance(selected, str) or not selected:
        # ``selected`` is a historical diagnostic label, not an admission input.  Bind it to the independently
        # parsed published profile so a new structural terminal cannot crash authority merely by omitting a
        # research-tournament-only stats key.
        selected = f"canonical-r{final_revision}:{final_profile}"

    g04_bytes = int(r25.get("g04_bytes", product["archive_bytes"]))
    prefixgraph_bytes = r25.get("prefixgraph_bytes")
    return {
        **product,
        "selected": selected,
        "portfolio_create_s": float(product_create_s),
        "v029_bytes": int(historical_bytes),
        "g04_bytes": g04_bytes,
        "g04_selected": r25.get("g04_selected", "not-attempted"),
        "prefixgraph_contract_eligible": bool(r25.get("prefixgraph_contract_eligible", False)),
        "prefixgraph_admitted": bool(r25.get("prefixgraph_admitted", False)),
        "prefixgraph_reject_reason": r25.get("prefixgraph_reject_reason", "not-attempted"),
        "prefixgraph_bytes": int(prefixgraph_bytes) if isinstance(prefixgraph_bytes, int) else None,
        "saving_vs_g04_bytes": g04_bytes - int(product["archive_bytes"]),
        "max_dependency_depth": int(r25.get("max_dependency_depth", 0)),
        "max_selected_member_read_amplification": max_amp,
        "selection_materialization": "same-filesystem-atomic-move",
        "selection_extra_payload_write_bytes": 0,
        "g04": g04,
        "prefixgraph_locality": r25.get("prefixgraph_locality"),
        "historical_v029_measurement": "independent-original-tree-build",
        "canonical_product_stats": product,
    }


class _CanonicalGeneralizationAdapter:
    """Minimal surface consumed by the frozen generalization harness."""

    treehash = staticmethod(CANON.treehash)
    strong_verify = staticmethod(CANON.strong_verify)

    @staticmethod
    def build(root: Path, out: Path) -> dict:
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".cmpct-v030-generalization-floor-", dir=out.parent) as td:
            historical_path = Path(td) / "accepted-v029.cmpct"
            historical_stats = dict(HIST_G04.BASE.build(root, historical_path))
            historical_bytes = historical_path.stat().st_size
            product_started = time.perf_counter()
            product = dict(CANON.build(root, out))
            product_create_s = time.perf_counter() - product_started
        return _normalize_product_stats(product, historical_bytes, historical_stats, out, product_create_s)


ADAPTER = _CanonicalGeneralizationAdapter()


def run(work_root: Path) -> dict:
    # Avoid the old import-time global swap.  Other tests/evidence modules may import B in the same interpreter,
    # so canonical adaptation is scoped to this run and always restored even when a workload fails.
    previous = B.RC
    B.RC = ADAPTER
    try:
        result = dict(B.run(work_root))
    finally:
        B.RC = previous

    revisions: dict[str, int] = {}
    profiles: dict[str, int] = {}
    for row in result["rows"]:
        archive = work_root / "archives" / row["suite"] / f"{row['name']}.cmpct"
        if not archive.is_file():
            raise RuntimeError(f"canonical generalization archive missing: {archive}")
        revision, profile = CANON._revision_for_archive(archive)
        verified = CANON.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != row["tree_sha256"]:
            raise RuntimeError(f"canonical archive verification drift: {row['suite']}/{row['name']}: {verified!r}")
        row["archive_sha256"] = _sha256_file(archive)
        row["format_revision"] = revision
        row["format_profile"] = profile
        row["canonical_magic_hex"] = archive.read_bytes()[:8].hex()
        revisions[str(revision)] = revisions.get(str(revision), 0) + 1
        profiles[profile] = profiles.get(profile, 0) + 1

    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["historical_floor_engine"] = "accepted-v029 original-tree builder via entropygraph_v030_geometry_overlay_g04.BASE"
    result["canonical_format"] = {
        "new_revision": 25,
        "fallback_revision": 24,
        "g04_magic_hex": CANON.G04_MAGIC.hex(),
        "prefixgraph_magic_hex": CANON.PG_MAGIC.hex(),
        "revisions_selected": revisions,
        "profiles_selected": profiles,
        "fallback_is_unwrapped": True,
        "exact_product_floor": "r25 must strictly beat genuine r24 bytes; ties keep r24",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-canonical-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-canonical-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "format": result["canonical_format"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("canonical v0.30 compression/generalization gate failed")


if __name__ == "__main__":
    main()
