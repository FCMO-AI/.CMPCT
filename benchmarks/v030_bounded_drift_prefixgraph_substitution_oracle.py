from __future__ import annotations

"""Research-only bounded-drift-for-PrefixGraph substitution oracle.

This court asks one narrow execution-ownership question: on the four workloads where
current v0.30 allows PrefixGraph to enter the r25 tournament, can a complete-semantics
bounded-drift sibling replace the PrefixGraph contender while leaving G0-G4 unchanged?

No canonical grammar, selector, threshold, reader, version, or release authority changes.
"""

import hashlib
import json
from pathlib import Path
import struct
import tempfile
import time

import zstandard as zstd

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import neutral_hostile_determinism_repair_v6 as NEUTRAL_REPAIR
from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from experiments import entropygraph_v030_bounded_drift_container_v1 as BDC
from experiments import entropygraph_v030_canonical_final as CANONICAL
from experiments import entropygraph_v030_product_fs as FS
from experiments.entropygraph_v030_prefixgraph_process_executor import (
    PrefixGraphProcessExecutor,
    SUPPORTED_PREFIX_LEVEL,
)

MAGIC = b"CMPNXBS1"
HEADER = struct.Struct("<8sQQQ32s")
TRAILER = struct.Struct("<32s")
MANIFEST_LEVEL = 12

# Frozen current-authority source-content identities from final external run 35770822484.
# These constants are evidence guards only; they never participate in encoding or admission.
SPECS = (
    ("neutral_hostile_v1", "02_office_workspace", "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57", False),
    ("resemblance_hostile_v1", "01_shifted_versions", "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd", True),
    ("resemblance_hostile_v1", "03_boundary_churn", "3238446efaef2a70a5c08d722bdc9dac3ac7c1c99ae3cde8093fae1481ad4b3d", True),
    ("resemblance_hostile_v1", "04_deflate_family", "527a9e356e923e5bcc26566a8f677a7f7277af1577493e09c2bdca1b6d17154a", False),
)

DECISIVE_KEYS = {
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("resemblance_hostile_v1", "03_boundary_churn"),
}
DECISIVE_SPECS = tuple(spec for spec in SPECS if (spec[0], spec[1]) in DECISIVE_KEYS)
if {(spec[0], spec[1]) for spec in DECISIVE_SPECS} != DECISIVE_KEYS:
    raise RuntimeError("selected-row oracle decisive-set drift")


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _treehash(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for rel, data in sorted(files.items()):
        rb = rel.encode("utf-8")
        h.update(len(rb).to_bytes(4, "little"))
        h.update(rb)
        h.update(len(data).to_bytes(8, "little"))
        h.update(data)
    return h.hexdigest()


def _source_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(p for p in root.rglob("*") if p.is_file())
    }


def _encode_semantic_sibling(manifest_raw: bytes, content: bytes) -> bytes:
    """Physically charge full filesystem-v1 semantics around one already-built BD container."""
    manifest_stored = zstd.ZstdCompressor(level=MANIFEST_LEVEL).compress(manifest_raw)
    header = HEADER.pack(MAGIC, len(manifest_raw), len(manifest_stored), len(content), _h(manifest_raw))
    body = header + manifest_stored + content
    return body + TRAILER.pack(_h(body))


def _decode_semantic_sibling(blob: bytes) -> tuple[bytes, list[bytes]]:
    if len(blob) < HEADER.size + TRAILER.size:
        raise ValueError("short bounded-drift semantic sibling")
    body, trailer_raw = blob[:-TRAILER.size], blob[-TRAILER.size:]
    (trailer,) = TRAILER.unpack(trailer_raw)
    if _h(body) != trailer:
        raise ValueError("bounded-drift semantic sibling digest mismatch")
    magic, manifest_raw_n, manifest_stored_n, content_n, manifest_digest = HEADER.unpack_from(body, 0)
    if magic != MAGIC:
        raise ValueError("bounded-drift semantic sibling magic mismatch")
    pos = HEADER.size
    end_manifest = pos + manifest_stored_n
    end_content = end_manifest + content_n
    if end_content != len(body):
        raise ValueError("bounded-drift semantic sibling length mismatch")
    manifest_raw = zstd.ZstdDecompressor().decompress(
        body[pos:end_manifest], max_output_size=FS.MAX_MANIFEST_BYTES
    )
    if len(manifest_raw) != manifest_raw_n or _h(manifest_raw) != manifest_digest:
        raise ValueError("bounded-drift semantic manifest identity mismatch")
    return manifest_raw, BDC.decode_all(body[end_manifest:end_content])


def _bind_members_to_manifest(manifest_raw: bytes, members: list[bytes]) -> dict[str, bytes]:
    decoded = FS.decode_manifest(
        manifest_raw,
        max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANONICAL.MAX_MANIFEST_ENTRIES,
    )
    available: dict[tuple[int, bytes], list[bytes]] = {}
    for member in members:
        available.setdefault((len(member), _h(member)), []).append(member)
    bound: dict[str, bytes] = {}
    for rel, (size, digest) in decoded["regular"].items():
        bucket = available.get((int(size), bytes(digest)))
        if not bucket:
            raise RuntimeError(f"missing bounded-drift content for {rel}")
        bound[rel] = bucket.pop()
    if any(bucket for bucket in available.values()):
        raise RuntimeError("bounded-drift sibling contains unowned regular content")
    return bound


def _build_source(work: Path, suite: str, name: str) -> Path:
    root = work / "source-root"
    root.mkdir(parents=True, exist_ok=True)
    if suite == "neutral_hostile_v1" and name == "02_office_workspace":
        # The frozen Office identity belongs to the accepted repair-v6 substrate. Bind that
        # producer/normalizer before measuring bounded drift; candidate semantics are unchanged.
        NEUTRAL_REPAIR.install_generation_hooks(NEUTRAL)
        NEUTRAL.corpus_office(root)
        NEUTRAL_REPAIR.normalize_workload(root / name)
    elif suite == "resemblance_hostile_v1" and name == "01_shifted_versions":
        HOSTILE.shifted_versions(root)
    elif suite == "resemblance_hostile_v1" and name == "03_boundary_churn":
        HOSTILE.boundary_churn(root)
    elif suite == "resemblance_hostile_v1" and name == "04_deflate_family":
        HOSTILE.deflate_family(root)
    else:
        raise RuntimeError(f"unknown substitution-oracle workload: {suite}/{name}")
    return root / name


def _prefixgraph_complete_operation_locality(archive: Path) -> dict:
    """Measure the actual r25 filesystem-control + user-content context for every regular user member.

    PrefixGraph admission preflight prices only graph-record context.  This court compares complete user
    operations, so it must also charge the authenticated filesystem manifest that resolves a user path to
    the underlying content identity.  Reuse the canonical profile reader instead of inventing a second
    PrefixGraph model.
    """
    manifest_raw, manifest_stats = CANONICAL._read_profile_member(archive, FS.FILESYSTEM_MANIFEST)
    content_identities = CANONICAL._profile_content_identities(archive)
    decoded, _encoding = CANONICAL.MANIFEST_ADMISSION.decode_from_content_identities(
        manifest_raw,
        content_identities=content_identities,
        max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANONICAL.MAX_MANIFEST_ENTRIES,
    )
    manifest_context = int(manifest_stats["decoded_context_bytes"])
    rows = []
    worst = 0.0
    for rel, (expected_size, expected_digest) in sorted(decoded["regular"].items()):
        raw, content_stats = CANONICAL._read_profile_member(archive, rel)
        if len(raw) != int(expected_size) or hashlib.sha256(raw).digest() != bytes(expected_digest):
            raise RuntimeError(f"PrefixGraph complete-operation identity mismatch for {rel}")
        content_context = int(content_stats["decoded_context_bytes"])
        decoded_context = manifest_context + content_context
        amplification = decoded_context / max(1, len(raw))
        worst = max(worst, amplification)
        rows.append(
            {
                "path": rel,
                "logical_bytes": len(raw),
                "filesystem_manifest_decoded_context_bytes": manifest_context,
                "content_decoded_context_bytes": content_context,
                "decoded_context_bytes": decoded_context,
                "decoded_context_amplification": amplification,
            }
        )
    return {
        "max_member_read_amplification": worst,
        "filesystem_manifest_decoded_context_bytes": manifest_context,
        "passed": worst <= 8.0,
        "rows": rows,
        "accounting_source": "canonical-profile-filesystem-manifest-plus-content-v1",
    }


def _row(suite: str, name: str, expected_tree: str, expected_pg_selected: bool, work: Path) -> dict:
    source = _build_source(work, suite, name)
    source_files = _source_files(source)
    source_tree = _treehash(source_files)
    if source_tree != expected_tree:
        raise RuntimeError(
            f"{suite}/{name} source identity drift: {source_tree} != {expected_tree}"
        )

    staged = work / "staged"
    prepared = CANONICAL._prepare_profile_tree(source, staged)
    manifest_raw, regular_sources, _stats = FS.capture_filesystem_manifest(
        source,
        max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=CANONICAL.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CANONICAL.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CANONICAL.MAX_MANIFEST_ENTRIES,
    )
    if prepared["source_manifest_raw"] != manifest_raw:
        raise RuntimeError("candidate/control filesystem-v1 source semantics drift")
    members = [path.read_bytes() for path, _rel in regular_sources]

    bd_started = time.perf_counter()
    bd_error = None
    bd_blob = None
    bd_content = None
    bd_facts = None
    try:
        bd_content = BDC.encode_container(members)
        bd_blob = _encode_semantic_sibling(manifest_raw, bd_content)
    except ValueError as exc:
        # Only bounded resource refusal is a valid fallback. Correctness/integrity failures below
        # are scientific failures and must never be converted into benign candidate unavailability.
        bd_error = repr(exc)
        bd_blob = None
        bd_content = None
    bd_create_s = time.perf_counter() - bd_started

    if bd_blob is not None and bd_content is not None:
        decoded_manifest, decoded_members = _decode_semantic_sibling(bd_blob)
        restored = _bind_members_to_manifest(decoded_manifest, decoded_members)
        if decoded_manifest != manifest_raw or _treehash(restored) != source_tree:
            raise RuntimeError("bounded-drift semantic sibling changed source semantics")
        facts = [BDC.member_resource_facts(bd_content, i) for i in range(len(members))]
        # The semantic sibling must charge the decoded filesystem manifest too.  BDC's
        # member facts intentionally know only about the shared content context, while
        # this court claims equal filesystem semantics.  PrefixGraph locality is also a
        # decoded-context metric, so excluding manifest bytes here would undercharge the
        # bounded-drift side of the same-semantics comparison.
        semantic_rows = [
            {
                "logical_size": fact.logical_size,
                "decoded_context_bytes": len(manifest_raw) + fact.decoded_context_bytes,
                "max_decode_unit_bytes": max(len(manifest_raw), fact.max_decode_unit_bytes),
                "member_read_amplification": (
                    len(manifest_raw) + fact.decoded_context_bytes
                ) / max(1, fact.logical_size),
            }
            for fact in facts
        ]
        bd_facts = {
            "filesystem_manifest_decode_bytes": len(manifest_raw),
            "max_member_read_amplification": max(
                row["member_read_amplification"] for row in semantic_rows
            ),
            "max_decode_unit_bytes": max(
                row["max_decode_unit_bytes"] for row in semantic_rows
            ),
        }
        corrupted = bytearray(bd_blob)
        corrupted[len(corrupted) // 2] ^= 1
        try:
            _decode_semantic_sibling(bytes(corrupted))
        except Exception:
            pass
        else:
            raise RuntimeError("bounded-drift corruption was not rejected")

    staged_tree = CANONICAL.RC.treehash(staged)
    pg_contract_eligible, pg_contract_reason = CANONICAL.RC._prefixgraph_eligibility(staged, staged_tree)
    if not pg_contract_eligible:
        raise RuntimeError(
            f"{suite}/{name} current PrefixGraph contract eligibility drift: {pg_contract_reason}"
        )

    pg = CANONICAL.RC.PG
    if pg.__name__ != "experiments._v030_canonical_prefixgraph" or pg.build.__module__ != pg.__name__:
        raise RuntimeError("current PrefixGraph semantic-owner drift")
    pg_path = work / "prefixgraph.cmpct"
    pg_started = time.perf_counter()
    with PrefixGraphProcessExecutor() as executor:
        pg_stats = dict(executor.submit(pg.build, staged, pg_path).result())
        pg_receipt = dict(executor.last_receipt or {})
    pg_create_s = time.perf_counter() - pg_started
    if pg_receipt.get("semantic_owner") != pg.__name__:
        raise RuntimeError("PrefixGraph child semantic-owner drift")
    if int(pg_receipt.get("prefix_level", -1)) != SUPPORTED_PREFIX_LEVEL:
        raise RuntimeError("PrefixGraph child level drift")
    if pg.treehash(staged) != staged_tree:
        raise RuntimeError("PrefixGraph staged-tree identity drift")
    pg_verify = dict(pg.strong_verify(pg_path))
    if not pg_verify.get("ok") or pg_verify.get("tree_sha256") != staged_tree:
        raise RuntimeError("PrefixGraph strong verification failed")
    pg_admission_locality = dict(CANONICAL.RC._prefixgraph_locality(pg_path))
    if not pg_admission_locality.get("passed"):
        raise RuntimeError("PrefixGraph admission-preflight locality failed")
    pg_locality = _prefixgraph_complete_operation_locality(pg_path)
    if not pg_locality.get("passed"):
        raise RuntimeError("PrefixGraph complete-operation locality failed")

    g04_path = work / "g04.cmpct"
    g04_started = time.perf_counter()
    g04_stats = dict(CANONICAL.RC.G04.build(staged, g04_path))
    g04_create_s = time.perf_counter() - g04_started
    CANONICAL.RC._verify_component(g04_path, staged_tree, "G0-G4 substitution control")

    pg_bytes = pg_path.stat().st_size
    g04_bytes = g04_path.stat().st_size
    current_pg_selected = pg_bytes < g04_bytes
    if current_pg_selected != expected_pg_selected:
        raise RuntimeError(
            f"{suite}/{name} current tournament-fidelity drift: "
            f"pg={pg_bytes} g04={g04_bytes} expected_pg_selected={expected_pg_selected}"
        )

    bd_bytes = None if bd_blob is None else len(bd_blob)
    bd_resource_safe = bool(
        bd_facts is not None
        and bd_facts["max_member_read_amplification"] <= 8.0
        and bd_facts["max_decode_unit_bytes"] <= 8 * 1024 * 1024
    )
    bd_eligible = bd_bytes is not None and bd_resource_safe
    projected_bytes = g04_bytes if not bd_eligible else min(g04_bytes, bd_bytes)
    current_bytes = min(g04_bytes, pg_bytes)
    substitution_nonregressing = projected_bytes <= current_bytes
    pg_winner_preserved = (not current_pg_selected) or (
        bd_eligible and bd_bytes is not None and bd_bytes <= pg_bytes
    )

    return {
        "label": f"{suite}/{name}",
        "source": {
            "files": len(source_files),
            "logical_bytes": sum(map(len, source_files.values())),
            "tree_sha256": source_tree,
            "filesystem_v1_bytes": len(manifest_raw),
            "selected_manifest_encoding": prepared["selected_manifest_encoding"],
            "selected_manifest_bytes": int(prepared["selected_manifest_bytes"]),
        },
        "bounded_drift": {
            "available": bd_blob is not None,
            "resource_safe": bd_resource_safe,
            "eligible_for_substitution": bd_eligible,
            "archive_bytes": bd_bytes,
            "create_s": bd_create_s,
            "error": bd_error,
            "physical_sha256": None if bd_blob is None else hashlib.sha256(bd_blob).hexdigest(),
            **(bd_facts or {}),
        },
        "prefixgraph": {
            "archive_bytes": pg_bytes,
            "create_s": pg_create_s,
            "physical_sha256": hashlib.sha256(pg_path.read_bytes()).hexdigest(),
            "max_member_read_amplification": pg_locality["max_member_read_amplification"],
            "filesystem_manifest_decoded_context_bytes": pg_locality[
                "filesystem_manifest_decoded_context_bytes"
            ],
            "locality_accounting": pg_locality["accounting_source"],
            "admission_preflight_max_member_read_amplification": pg_admission_locality[
                "max_member_read_amplification"
            ],
            "operation_rows": pg_locality["rows"],
            "stats": pg_stats,
        },
        "g04": {
            "archive_bytes": g04_bytes,
            "create_s": g04_create_s,
            "selected": g04_stats.get("selected"),
        },
        "decision": {
            "expected_current_pg_selected": expected_pg_selected,
            "prefixgraph_contract_eligible_same_run": pg_contract_eligible,
            "current_pg_selected_same_run": current_pg_selected,
            "current_tournament_bytes": current_bytes,
            "projected_bd_plus_g04_bytes": projected_bytes,
            "substitution_delta_bytes": projected_bytes - current_bytes,
            "substitution_nonregressing": substitution_nonregressing,
            "pg_winner_preserved_or_improved": pg_winner_preserved,
        },
    }


def run(out_path: Path, *, decisive_only: bool = False) -> dict:
    rows = []
    specs = DECISIVE_SPECS if decisive_only else SPECS
    with tempfile.TemporaryDirectory(prefix="cmpct-bd-pg-substitution-") as td:
        root = Path(td)
        for index, spec in enumerate(specs):
            work = root / f"row-{index:02d}"
            work.mkdir()
            rows.append(_row(*spec, work))

    survives = all(
        row["decision"]["substitution_nonregressing"]
        and row["decision"]["pg_winner_preserved_or_improved"]
        for row in rows
    )
    result = {
        "schema": "cmpct-v030-bounded-drift-prefixgraph-substitution-oracle-v1",
        "question": (
            "Can complete-semantics bounded drift replace the PrefixGraph contender on every "
            "current PrefixGraph-eligible row while G0-G4 remains unchanged?"
        ),
        "rows": rows,
        "court_scope": "decisive-prefixgraph-winners" if decisive_only else "all-prefixgraph-eligible-controls",
        "decision": (
            "SUBSTITUTION_RUNG_SURVIVES" if survives else "SUBSTITUTION_RUNG_FALSIFIED_OR_NARROWED"
        ),
        "survives": survives,
        "release_credit": False,
        "claim_boundary": (
            "Research-only same-run contender-substitution oracle. The bounded-drift sibling is "
            "noncanonical; no shipping selector, reader, recovery, native, Android, external-frontier, "
            "runtime-gate, version, merge, tag, publish, or release credit is created."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-survival", action="store_true")
    parser.add_argument(
        "--decisive-only",
        action="store_true",
        help="run only the preregistered current PrefixGraph-winning Shifted + Boundary rows",
    )
    args = parser.parse_args()
    result = run(args.output, decisive_only=args.decisive_only)
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.require_survival and not result["survives"]:
        raise SystemExit("bounded-drift-for-PrefixGraph substitution did not survive the preregistered court")


if __name__ == "__main__":
    main()
