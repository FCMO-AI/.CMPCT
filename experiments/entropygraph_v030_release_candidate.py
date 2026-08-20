"""Authoritative v0.30 complete-artifact release-candidate tournament.

This module is the system-level v0.30 selector. It does **not** add independent research savings
arithmetically. Instead it builds complete, independently verifiable artifacts and publishes the exact
smallest *release-eligible* one:

1. ``G04.build`` produces the monotone Mosaic path: accepted v0.29 fallback plus the full G0-G4 pre-fallback
   Geometry overlay, so this candidate can never be larger than accepted v0.29.
2. PrefixGraph is auditioned only when its public oracle contract can represent the exact live tree.
3. A PrefixGraph artifact must additionally satisfy the release-wide <=8x per-member decoded-context law.
4. Standalone tournament callers verify any candidate that can still win through the strict streamed reader.
   The canonical r24/r25 parent may instead defer those logical passes because it strongly verifies the one final
   product winner before returning; exact byte pricing and locality admission are never deferred.
5. The smaller admitted complete artifact wins; exact ties conservatively retain the G0-G4/v0.29 path.

The tournament is intentionally useful before PrefixGraph is internalized as a native Mosaic graph edge. It
answers the release-system question honestly—what complete archive would v0.30 choose for this workload?—while
keeping the stronger single-grammar composition goal as an optimization path. No combined Geometry+PrefixGraph
saving is claimed unless a future one-artifact ablation proves it.

Footnote: candidates are created in a sibling temporary directory and the winner is published with
``os.replace``. A physical SHA-256 proves the selected bytes survived publication unchanged. Standalone builds
retain candidate admission verification and re-open the published path through the strict release reader. The
canonical r24-vs-r25 parent can explicitly defer the candidate logical passes because the r25 artifact is itself
only an inner contender; the parent performs the authoritative strong verification after exact r24/r25 selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from experiments import entropygraph_v030_geometry_overlay_g04 as G04
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_reader_policy as READER

MAX_MEMBER_READ_AMP = 8.0


def treehash(root: Path) -> str:
    return G04.treehash(root)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prefixgraph_eligibility(root: Path, expected_tree: str) -> tuple[bool, str | None]:
    """Apply the frozen PrefixGraph representation envelope before paying its expensive anchor tournament."""
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        return False, "no-regular-files"
    if len(files) > PG.MAX_FILES:
        return False, "file-count-ceiling"
    if any(path.is_symlink() for path in files):
        return False, "symlink-not-representable"
    if any(path.stat().st_size > PG.MAX_FILE_BYTES for path in files):
        return False, "file-size-ceiling"

    pg_tree = PG.treehash(root)
    if pg_tree != expected_tree:
        return False, "tree-identity-contract-mismatch"
    return True, None


def _prefixgraph_locality(archive: Path) -> dict:
    """Measure conservative decoded-context amplification needed for one PrefixGraph member."""
    meta, _payloads = PG._read(archive)
    records = meta["records"]
    worst = 0.0
    prefix_records = 0
    rows: list[dict] = []
    for index, desc in enumerate(records):
        if not isinstance(desc, list) or len(desc) != 6:
            raise RuntimeError("malformed PrefixGraph record during locality accounting")
        kind, base, usize, _csize, _payload_sha, _logical_sha = desc
        usize = int(usize)
        if kind == "direct":
            amp = 1.0
        elif kind == "prefix":
            base = int(base)
            if not 0 <= base < len(records) or records[base][0] != "direct":
                raise RuntimeError("PrefixGraph locality saw non-direct depth-1 base")
            anchor_usize = int(records[base][2])
            amp = (max(0, usize) + max(0, anchor_usize)) / max(1, usize)
            prefix_records += 1
        else:
            raise RuntimeError("unknown PrefixGraph record during locality accounting")
        worst = max(worst, amp)
        rows.append({"record": index, "kind": kind, "decoded_context_amplification": amp})
    return {
        "max_member_read_amplification": worst,
        "prefix_records": prefix_records,
        "passed": worst <= MAX_MEMBER_READ_AMP,
        "rows": rows,
    }


def _verify_component(path: Path, expected_tree: str, label: str) -> dict:
    result = READER.strong_verify(path)
    if not result.get("ok") or result.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{label} failed strict streamed logical-tree verification: {result!r}")
    return result


def strong_verify(archive: Path) -> dict:
    result = dict(READER.strong_verify(archive))
    if result.get("ok"):
        with archive.open("rb") as stream:
            magic = stream.read(8)
        result["release_candidate_representation"] = (
            "prefixgraph"
            if magic == PG.MAGIC
            else "g04-overlay"
            if magic == G04.MAG
            else "accepted-v029-fallback"
        )
    return result


def extract(archive: Path, dst: Path, *, max_output_bytes: int = READER.DEFAULT_MAX_EXTRACT_BYTES) -> None:
    READER.extract(archive, dst, max_output_bytes=max_output_bytes)


def build(
    root: Path,
    out: Path,
    *,
    post_publish_verify: bool = True,
    defer_preselection_verify: bool = False,
) -> dict:
    """Build the exact release tournament with an explicit canonical-parent verification deferral seam.

    Defaults preserve the standalone safety boundary: viable candidates are strongly verified before selection
    and the published winner is verified again through the public reader path. The canonical r24/r25 parent sets
    both ``post_publish_verify=False`` and ``defer_preselection_verify=True`` because this r25 artifact is only an
    inner candidate; the parent strongly verifies the exact final r24/r25 winner before ``build`` returns.

    Deferral never changes candidate bytes, exact size comparison, PrefixGraph locality admission, tie behavior,
    or physical publication identity. It removes only logical decode passes for artifacts that cannot themselves
    escape the enclosing canonical tournament.
    """
    started = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    expected_tree = treehash(root)

    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-release-candidate-", dir=out.parent) as td:
        temp = Path(td)
        g04_path = temp / "g04-or-v029.cmpct"
        pg_path = temp / "prefixgraph.cmpct"

        g04_stats = G04.build(root, g04_path)
        g04_verify = None if defer_preselection_verify else _verify_component(g04_path, expected_tree, "G0-G4 candidate")
        g04_bytes = g04_path.stat().st_size
        v029_bytes = int(g04_stats["v029_bytes"])
        if g04_bytes > v029_bytes:
            raise RuntimeError("monotone G0-G4 candidate exceeded accepted v0.29 floor")

        pg_contract_eligible, pg_reject_reason = _prefixgraph_eligibility(root, expected_tree)
        pg_admitted = False
        pg_stats = None
        pg_verify = None
        pg_locality = None
        pg_bytes = None
        if pg_contract_eligible:
            pg_stats = PG.build(root, pg_path)
            pg_bytes = pg_path.stat().st_size

            if pg_bytes < g04_bytes:
                pg_locality = _prefixgraph_locality(pg_path)
                pg_admitted = bool(pg_locality["passed"])
                if pg_admitted and not defer_preselection_verify:
                    pg_verify = _verify_component(pg_path, expected_tree, "PrefixGraph candidate")
                if not pg_admitted:
                    pg_reject_reason = "locality-ceiling"
            else:
                pg_reject_reason = "complete-artifact-not-smaller"

        if pg_admitted and pg_bytes is not None and pg_bytes < g04_bytes:
            selected_path = pg_path
            selected = "prefixgraph"
            selected_verify = pg_verify
        else:
            selected_path = g04_path
            if g04_stats["selected"] == "geometry-overlay-g04":
                selected = "g04-overlay"
            else:
                selected = "v029-fallback"
            selected_verify = g04_verify

        if not defer_preselection_verify and selected_verify is None:
            raise RuntimeError("standalone release tournament selected an unverified candidate")

        selected_bytes = selected_path.stat().st_size
        selected_physical_sha256 = _sha256_file(selected_path)
        os.replace(selected_path, out)
        published_physical_sha256 = _sha256_file(out)
        if out.stat().st_size != selected_bytes or published_physical_sha256 != selected_physical_sha256:
            raise RuntimeError("published v0.30 release candidate bytes changed during atomic publication")

        if post_publish_verify:
            final_verify = dict(_verify_component(out, expected_tree, "Published v0.30 release candidate"))
            final_verify["publication_logical_verification_deferred"] = False
        elif selected_verify is not None:
            final_verify = dict(selected_verify)
            final_verify["publication_logical_verification_deferred"] = True
        else:
            final_verify = {
                "ok": None,
                "tree_sha256": expected_tree,
                "publication_logical_verification_deferred": True,
                "verification_owner": "canonical-r24-r25-parent-final-winner",
            }
        final_verify["publication_physical_sha256"] = published_physical_sha256

        return {
            "selected": selected,
            "archive_bytes": selected_bytes,
            "v029_bytes": v029_bytes,
            "g04_bytes": g04_bytes,
            "g04_selected": g04_stats["selected"],
            "prefixgraph_contract_eligible": pg_contract_eligible,
            "prefixgraph_admitted": pg_admitted,
            "prefixgraph_reject_reason": pg_reject_reason,
            "prefixgraph_bytes": pg_bytes,
            "prefixgraph_locality": pg_locality,
            "saving_vs_v029_bytes": v029_bytes - selected_bytes,
            "saving_vs_g04_bytes": g04_bytes - selected_bytes,
            "tree_sha256": expected_tree,
            "portfolio_create_s": time.perf_counter() - started,
            "selection_materialization": "same-filesystem-atomic-move",
            "selection_extra_payload_write_bytes": 0,
            "selection_publication_physical_sha256": published_physical_sha256,
            "preselection_logical_verification": "deferred-to-canonical-parent" if defer_preselection_verify else "performed",
            "post_publish_logical_verification": "performed" if post_publish_verify else "deferred-to-canonical-parent",
            "max_dependency_depth": int(pg_stats.get("max_dependency_depth", 0)) if selected == "prefixgraph" else 0,
            "max_selected_member_read_amplification": (
                float(pg_locality["max_member_read_amplification"])
                if selected == "prefixgraph" and pg_locality is not None
                else float(g04_stats.get("max_selected_member_read_amplification", 0.0))
            ),
            "g04": g04_stats,
            "prefixgraph": pg_stats,
            "g04_strong_verify": g04_verify,
            "prefixgraph_strong_verify": pg_verify,
            "selected_strong_verify": selected_verify,
            "final_strong_verify": final_verify,
            "reader_authority": "v030-release-streaming-policy-v1",
            "claim_boundary": (
                "complete-artifact system tournament; PrefixGraph and G0-G4 savings are not added or claimed "
                "simultaneously unless a future one-artifact composition proves them"
            ),
        }


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.30 complete-artifact release-candidate tournament")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack")
    p.add_argument("source", type=Path)
    p.add_argument("archive", type=Path)
    p = sub.add_parser("verify")
    p.add_argument("archive", type=Path)
    p = sub.add_parser("extract")
    p.add_argument("archive", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("--max-output-bytes", type=int, default=READER.DEFAULT_MAX_EXTRACT_BYTES)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    else:
        extract(args.archive, args.destination, max_output_bytes=args.max_output_bytes)
        print(json.dumps({"ok": True}, indent=2))


if __name__ == "__main__":
    _main()
