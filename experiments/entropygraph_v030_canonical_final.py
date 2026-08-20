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

    # Every row participates in columns below min_len.  Materialize that rectangular prefix row-major once,
    # then append each strided column using bytearray slicing implemented in C.  Ragged tails retain the exact
    # historical loop, so arbitrary empty/unequal fields preserve byte identity without a second grammar.
    min_len = min(lengths, default=0)
    count = len(parts)
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
        # ``dense`` is column-major; one strided assignment per column recreates the row-major rectangle.
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


# Patch only the isolated canonical graph/reader references.  Research modules remain untouched and therefore
# continue to provide the original byte oracle.  Both writer and reader must use the same exact transform bytes.
SHARED.G.O.delimiter_forward = _bulk_delimiter_forward
SHARED.G.O.delimiter_inverse = _bulk_delimiter_inverse
if getattr(POLICY.R.G04, "O", None) is not None:
    POLICY.R.G04.O.delimiter_inverse = _bulk_delimiter_inverse


def _parallel_overlay_retained_graph(graph_path: Path, overlay_path: Path) -> dict:
    """Apply the owning G0-G4 auditions concurrently while preserving exact record order and bytes.

    Each physical-record audition is pure with respect to every other record: the semantic owner remains
    ``SHARED.G._audition_record`` and complete archive pricing remains unchanged.  The previous release path paid
    these independent Zstd/Geometry tournaments serially *after* the attempt-5 graph was already available; on
    the frozen ML workload that represented roughly thirty seconds of avoidable wall time.  A bounded ordered
    thread pool changes scheduling only.  ``pool.map`` preserves input order, and the existing shared-rehab gate
    still requires the resulting complete archive to be byte-identical to the serial reference implementation.

    Four workers are deliberately a fixed ceiling rather than ``os.cpu_count()``: hosted and local machines may
    expose very different logical-CPU counts, while release resource behaviour should remain bounded and boring.
    Small graphs use no more workers than records.
    """
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
    verified = SHARED.G.strong_verify(overlay_path)
    return {
        "source_format": source_format,
        "records": records,
        "transforms": transforms,
        "auditions": auditions,
        "write_stats": write_stats,
        "verified": verified,
        "audition_workers": worker_count,
        "audition_scheduler": "bounded-ordered-thread-pool-v1",
        "delimiter_transpose": "bulk-rectangular-prefix-v1",
    }


# Only the private canonical clone is patched. Historical/research imports keep their serial implementation,
# which gives the shared-rehab workflow an independent byte-for-byte oracle instead of moving both sides at once.
SHARED._overlay_retained_graph = _parallel_overlay_retained_graph

_PRESERVED_STRONG_VERIFY = strong_verify


def _r25_build(staged_root: Path, out: Path) -> dict:
    """Build the r25 tournament while leaving final complete-product verification to this canonical parent."""
    started = time.perf_counter()
    with _revision25_profile_context():
        stats = dict(RC.build(staged_root, out, post_publish_verify=False))
    # Footnote: RC still strong-verifies every candidate that can win and proves the selected bytes survive its
    # atomic publication. Only RC's *second* published-path logical pass is deferred. ``build`` below resolves
    # this replacement through the shared module globals and always calls canonical ``strong_verify`` after the
    # exact r24-vs-r25 winner is published, so every user-visible product still receives that final proof once.
    return {**stats, "create_s": time.perf_counter() - started}


def strong_verify(archive: Path) -> dict:
    """Strong-verify canonical r25 in one content pass plus one authenticated manifest binding pass.

    The shared release reader already reconstructs every profile member, authenticates payload and logical
    identities, authenticates the complete content-graph tree, and enforces locality. The filesystem manifest is
    then read and bound to those authenticated metadata identities. Re-reading every regular member afterward
    proves the same bytes a second time and is deliberately avoided here.
    """
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

    # Footnote: ``POLICY.strong_verify`` is the byte proof; ``_validated_manifest`` is the semantic binding.
    # The latter compares every manifest regular-file (size, SHA-256) identity with the authenticated profile
    # metadata, so the already verified content graph and the user-visible filesystem description cannot diverge.
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
