"""Canonical CMPCT v0.30 product implementation with isolated revision-25 profile state.

The reviewed implementation body is preserved in ``entropygraph_v030_canonical_final_impl.py`` and executed
*inside this public module's global namespace* while its Geometry, PrefixGraph, reader, admission and shared-
portfolio imports are temporarily routed to private canonical module namespaces. Ordinary research modules
therefore keep their historical CMPNX identities, while public canonical helpers retain normal Python dependency
injection/monkeypatch behavior because their ``__globals__`` is this module rather than a hidden re-export target.

Footnote: executing the preserved source here is deliberately different from importing it and copying function
objects afterward. Re-exported functions keep the hidden module's globals, so callers replacing a public reader
or candidate provider would appear to patch the canonical API while the operation silently used another object.
One execution namespace plus isolated dependencies removes both hazards without rewriting the reviewed product
implementation or introducing a second handwritten archive grammar.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_profile_isolation as _ISOLATION

_WRAPPER_DOC = __doc__
_IMPLEMENTATION_PATH = Path(__file__).with_name("entropygraph_v030_canonical_final_impl.py")

_ISOLATION.assert_research_modules_unchanged()
with _ISOLATION.canonical_import_context():
    _SOURCE = _IMPLEMENTATION_PATH.read_bytes()
    # Footnote: compile the preserved implementation as a module but execute it in *this* module dictionary.
    # Functions/classes therefore resolve later global substitutions through the public canonical namespace,
    # while the import statements executed right now bind only the isolated release-profile dependencies.
    exec(compile(_SOURCE, str(_IMPLEMENTATION_PATH), "exec"), globals(), globals())

# Keep the public wrapper's architectural explanation instead of exposing the preserved implementation's older
# module docstring. The executable implementation itself remains unchanged below the source boundary.
__doc__ = _WRAPPER_DOC
PROFILE_ISOLATION = _ISOLATION
IMPLEMENTATION_SOURCE = _IMPLEMENTATION_PATH

# No ordinary research module is mutated after initialization. The preserved implementation's historical
# ``_revision25_profile_context`` now snapshots/restores private clone state only; those assignments are
# idempotent inside the isolated graph and invisible to concurrent research calls.


# Preserve the historical byte-at-a-time delimiter implementation as an independent oracle.  The canonical
# private profile can use a bulk transpose because the transform grammar is identical: only how the same bytes
# are moved in memory changes.  The shared-rehab/byte-identity gates therefore remain capable of falsifying this
# optimization rather than comparing two copies of the same new implementation.
_PRESERVED_DELIMITER_FORWARD = SHARED.G.O.delimiter_forward
_PRESERVED_DELIMITER_INVERSE = SHARED.G.O.delimiter_inverse


def _bulk_delimiter_forward(raw: bytes, delimiter: int) -> bytes:
    """Emit the exact DGO1 transform with its dense rectangular prefix transposed in C-level slices."""
    O = SHARED.G.O
    if not 0 <= delimiter <= 255 or len(raw) > O.MAX_OVERLAY_RECORD:
        raise ValueError("invalid Geometry overlay delimiter input")
    parts = raw.split(bytes((delimiter,)))
    lengths = [len(part) for part in parts]
    max_len = max(lengths, default=0)
    if len(parts) > O.MAX_DELIMITER_SEGMENTS or len(parts) * max_len > O.MAX_DELIMITER_CELL_SCANS:
        raise ValueError("Geometry overlay delimiter work budget exceeded")

    out = bytearray(b"DGO1")
    out.append(delimiter)
    O._put_varint(out, len(parts))
    for length in lengths:
        O._put_varint(out, length)

    # Every row participates in columns below min_len. Materialize that rectangular prefix row-major once,
    # then append each strided column using bytearray slicing implemented in C. Ragged tails retain the exact
    # historical loop, so arbitrary empty/unequal fields preserve byte identity without a second grammar.
    min_len = min(lengths, default=0)
    if min_len:
        rectangle = b"".join(part[:min_len] for part in parts)
        for column in range(min_len):
            out.extend(rectangle[column::min_len])
    for column in range(min_len, max_len):
        for part in parts:
            if column < len(part):
                out.append(part[column])
    return bytes(out)


def _bulk_delimiter_inverse(encoded: bytes, logical_size: int) -> bytes:
    """Invert DGO1 with the same bounded grammar while bulk-transposing the common rectangular prefix."""
    O = SHARED.G.O
    if (
        not encoded.startswith(b"DGO1")
        or len(encoded) < 6
        or logical_size < 0
        or logical_size > O.MAX_OVERLAY_RECORD
    ):
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")

    lengths: list[int] = []
    logical_members = 0
    for _ in range(count):
        length, pos = O._get_varint(encoded, pos)
        if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        lengths.append(length)
        logical_members += length
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    max_len = max(lengths, default=0)
    if count * max_len > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    rows = [bytearray(length) for length in lengths]
    min_len = min(lengths, default=0)
    cursor = 0
    if min_len:
        dense_bytes = count * min_len
        dense = body[:dense_bytes]
        rectangle = bytearray(dense_bytes)
        for column in range(min_len):
            start = column * count
            rectangle[column::min_len] = dense[start : start + count]
        for index, row in enumerate(rows):
            start = index * min_len
            row[:min_len] = rectangle[start : start + min_len]
        cursor = dense_bytes

    for column in range(min_len, max_len):
        for index, length in enumerate(lengths):
            if column < length:
                if cursor >= len(body):
                    raise RuntimeError("short Geometry overlay delimiter body")
                rows[index][column] = body[cursor]
                cursor += 1
    if cursor != len(body):
        raise RuntimeError("Geometry overlay delimiter trailing body")
    return bytes((delimiter,)).join(bytes(row) for row in rows)


# Patch only the isolated canonical graph/reader references. Research modules remain untouched and therefore
# continue to provide the original byte oracle. Both writer and reader must use the same exact transform bytes.
SHARED.G.O.delimiter_forward = _bulk_delimiter_forward
SHARED.G.O.delimiter_inverse = _bulk_delimiter_inverse
if getattr(POLICY.R.G04, "O", None) is not None:
    POLICY.R.G04.O.delimiter_inverse = _bulk_delimiter_inverse


def _parallel_overlay_retained_graph(graph_path: Path, overlay_path: Path) -> dict:
    """Apply G0-G4 auditions concurrently while preserving the owner's deferred-verification contract."""
    source_format, _source, graph_meta, graph_records = SHARED.strict._read_source_records(graph_path)
    users = SHARED.O._record_member_lengths(graph_meta, len(graph_records))

    def audition(item):
        record_id, record = item
        return SHARED.G._audition_record(record_id, record, users[record_id])

    if graph_records:
        worker_count = min(4, len(graph_records))
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="cmpct-v030-g04") as pool:
            outcomes = list(pool.map(audition, enumerate(graph_records)))
    else:
        worker_count = 0
        outcomes = []

    records = [row[0] for row in outcomes]
    transforms = [row[1] for row in outcomes]
    auditions = [row[2] for row in outcomes]
    annotated_meta = dict(graph_meta)
    annotated_meta["overlay_source_format"] = source_format
    write_stats = SHARED.G._write_overlay(annotated_meta, records, transforms, overlay_path)
    # Match SHARED._overlay_retained_graph exactly: the owning portfolio first prices complete bytes and locality.
    # Full logical verification is paid only if the overlay wins both gates. Eager verification here both broke the
    # return-shape contract and reintroduced the losing-candidate decode work that canonical scheduling removes.
    return {
        "source_format": source_format,
        "records": records,
        "transforms": transforms,
        "auditions": auditions,
        "write_stats": write_stats,
        "verified": None,
        "verification_state": "deferred-until-byte-and-locality-win",
        "audition_workers": worker_count,
        "audition_scheduler": "bounded-ordered-thread-pool-v1",
        "delimiter_transpose": "bulk-rectangular-prefix-v1",
    }


# Only the private canonical clone is patched. Historical/research imports keep their serial implementation,
# which gives the shared-rehab workflow an independent byte-for-byte oracle instead of moving both sides at once.
SHARED._overlay_retained_graph = _parallel_overlay_retained_graph


def _overlapped_release_candidate_build(
    root: Path,
    out: Path,
    *,
    post_publish_verify: bool = True,
    defer_preselection_verify: bool = False,
) -> dict:
    """Build PrefixGraph beside G0-G4 without changing exact candidate bytes or winner selection.

    PrefixGraph reads the immutable staged tree and writes a separate temporary artifact. It has no dependency on
    G0-G4's retained graph, so paying the two complete candidate builds serially is pure wall-time duplication.
    G0-G4 deliberately stays on the calling thread because its shared portfolio owns spawned v0.29 workers;
    PrefixGraph alone uses one bounded background worker.

    The canonical parent may additionally set ``defer_preselection_verify=True``. In that composition only,
    temporary r25 candidates are priced by exact complete bytes and PrefixGraph locality, while their full logical
    decode is deferred until the outer r24-vs-r25 selector has published the one actual product winner. The parent
    always strong-verifies that winner before ``build`` returns. Standalone candidate callers keep the historical
    verify-before-publication behavior by default. Thus losing temporary candidates stop paying whole-tree decode
    cost without weakening the released-artifact integrity boundary or changing one archive byte.
    """
    started = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    expected_tree = RC.treehash(root)

    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-release-candidate-", dir=out.parent) as td:
        temp = Path(td)
        g04_path = temp / "g04-or-v029.cmpct"
        pg_path = temp / "prefixgraph.cmpct"
        pg_contract_eligible, pg_reject_reason = RC._prefixgraph_eligibility(root, expected_tree)
        pg_stats = None

        if pg_contract_eligible:
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="cmpct-v030-prefixgraph") as pool:
                pg_future = pool.submit(RC.PG.build, root, pg_path)
                # Keep G0-G4 on this thread: its internal multiprocessing/spawn boundary remains exactly where
                # it was before this scheduling optimization, while independent PrefixGraph CPU overlaps it.
                g04_stats = RC.G04.build(root, g04_path)
                pg_stats = pg_future.result()
        else:
            g04_stats = RC.G04.build(root, g04_path)

        g04_verify = None if defer_preselection_verify else RC._verify_component(
            g04_path, expected_tree, "G0-G4 candidate"
        )
        g04_bytes = g04_path.stat().st_size
        v029_bytes = int(g04_stats["v029_bytes"])
        if g04_bytes > v029_bytes:
            raise RuntimeError("monotone G0-G4 candidate exceeded accepted v0.29 floor")

        pg_admitted = False
        pg_verify = None
        pg_locality = None
        pg_bytes = None
        if pg_contract_eligible:
            assert pg_stats is not None
            pg_bytes = pg_path.stat().st_size
            if pg_bytes < g04_bytes:
                if not defer_preselection_verify:
                    pg_verify = RC._verify_component(pg_path, expected_tree, "PrefixGraph candidate")
                pg_locality = RC._prefixgraph_locality(pg_path)
                pg_admitted = bool(pg_locality["passed"])
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
            selected = "g04-overlay" if g04_stats["selected"] == "geometry-overlay-g04" else "v029-fallback"
            selected_verify = g04_verify

        if not defer_preselection_verify and selected_verify is None:
            raise RuntimeError("standalone canonical candidate lost its mandatory preselection verification")
        selected_bytes = selected_path.stat().st_size
        selected_physical_sha256 = RC._sha256_file(selected_path)
        os.replace(selected_path, out)
        published_physical_sha256 = RC._sha256_file(out)
        if out.stat().st_size != selected_bytes or published_physical_sha256 != selected_physical_sha256:
            raise RuntimeError("published v0.30 release candidate bytes changed during atomic publication")

        if post_publish_verify:
            final_verify = RC._verify_component(out, expected_tree, "Published v0.30 release candidate")
            final_verify = dict(final_verify)
            final_verify["publication_logical_verification_deferred"] = False
        elif selected_verify is not None:
            final_verify = dict(selected_verify)
            final_verify["publication_logical_verification_deferred"] = True
        else:
            final_verify = {
                "ok": None,
                "verification_state": "deferred-to-canonical-parent",
                "tree_sha256": expected_tree,
                "publication_logical_verification_deferred": True,
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
            "candidate_scheduler": "g04-main-plus-one-prefixgraph-worker-v2",
            "preselection_logical_verification": (
                "deferred-to-canonical-parent" if defer_preselection_verify else "performed"
            ),
            "selection_materialization": "same-filesystem-atomic-move",
            "selection_extra_payload_write_bytes": 0,
            "selection_publication_physical_sha256": published_physical_sha256,
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
                "complete-artifact system tournament; independent candidate construction may overlap, while "
                "PrefixGraph and G0-G4 savings are never added or claimed simultaneously"
            ),
        }


# Canonical scheduling only. The research selector remains serial and therefore continues to provide independent
# result/byte provenance; all exact admission helpers are still owned by the private RC module.
RC.build = _overlapped_release_candidate_build

_PRESERVED_STRONG_VERIFY = strong_verify


def _r25_build(staged_root: Path, out: Path) -> dict:
    """Build exact r25 bytes; the outer canonical parent verifies only the final r24/r25 product winner."""
    started = time.perf_counter()
    with _revision25_profile_context():
        stats = dict(
            RC.build(
                staged_root,
                out,
                post_publish_verify=False,
                defer_preselection_verify=True,
            )
        )
    return {**stats, "create_s": time.perf_counter() - started}


def strong_verify(archive: Path) -> dict:
    """Strong-verify canonical r25 in one content pass plus one authenticated manifest binding pass."""
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision != REVISION:
        return _PRESERVED_STRONG_VERIFY(archive)

    with _revision25_profile_context():
        base = dict(POLICY.strong_verify(archive))
    if not base.get("ok"):
        return {**base, "format_revision": revision, "format_profile": profile}
    try:
        manifest = _validated_manifest(archive)
        user_tree = _semantic_tree_sha(manifest)
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc),
            "format_revision": revision,
            "format_profile": profile,
            "reader": "cmpct-v030-canonical-final-v1",
        }

    return {
        **base,
        "content_graph_tree_sha256": base.get("tree_sha256"),
        "tree_sha256": user_tree,
        "user_tree_sha256": user_tree,
        "format_revision": revision,
        "format_profile": profile,
        "filesystem_manifest_sha256": hashlib.sha256(manifest["raw"]).hexdigest(),
        "filesystem_entries": len(manifest["manifest"]["entries"]),
        "filesystem_semantics_verified": True,
        "regular_members_verified_by_policy_stream": len(manifest["regular"]),
        "verification_strategy": "single-content-pass-plus-authenticated-manifest-binding",
        "canonical_release_facade": "cmpct-v030-canonical-final-v1",
    }


if __name__ == "__main__":
    _main()