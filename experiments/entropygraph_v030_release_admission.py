"""Release-only admission policy for PrefixGraph inside the v0.30 system tournament.

The research selector originally reused ``PrefixGraph._read()`` to compute locality after building a candidate.
That helper is correct for a small oracle, but it materializes every payload and therefore does not belong in a
promoted memory-bounded selection path.  This module replaces both release-time eligibility and locality
accounting without changing PrefixGraph bytes:

- eligibility is decided from directory metadata before the expensive builder starts;
- the total logical family admitted to the current in-memory PrefixGraph encoder is capped at 256 MiB;
- post-build locality is computed from authenticated metadata only, without reading candidate payload bytes;
- a candidate above the <=8x locality ceiling is returned as ``passed: false`` rather than becoming unreadable
  to the admission accountant itself;
- the strict release reader still independently rejects such an archive if anyone attempts to promote/read it.

That last distinction matters to historical causality.  A raw PrefixGraph representation can be logically valid
and exact-tree while still being correctly rejected by the release locality law.  The evidence ledger must be able
to record that rejection and fall back to v0.29; letting the strict reader reject metadata *before* locality can be
measured turns negative evidence into a harness crash.

Footnote: the 256 MiB ceiling is an *encoder admission* bound, not a decoder grammar limit. PrefixGraph's current
research encoder loads all family members to price anchors; a future streaming encoder may safely raise this
ceiling after proving bounded memory without changing the on-disk representation.
"""
from __future__ import annotations

from pathlib import Path

import zstandard as zstd

from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_reader_policy as POLICY

MAX_MEMBER_READ_AMP = 8.0
MAX_PREFIXGRAPH_TOTAL_LOGICAL_BYTES = 256 * 1024 * 1024


def prefixgraph_eligibility(root: Path, expected_tree: str) -> tuple[bool, str | None]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        return False, "no-regular-files"
    if len(files) > PG.MAX_FILES:
        return False, "file-count-ceiling"
    if any(path.is_symlink() for path in files):
        return False, "symlink-not-representable"

    total = 0
    for path in files:
        size = path.stat().st_size
        if size > PG.MAX_FILE_BYTES:
            return False, "file-size-ceiling"
        total += size
        if total > MAX_PREFIXGRAPH_TOTAL_LOGICAL_BYTES:
            return False, "encoder-total-logical-ceiling"

    # PrefixGraph remains a separate complete-artifact representation in v0.30. Until tree-hash ownership is
    # unified, exact equality prevents a narrower/different logical identity from entering the tournament.
    if PG.treehash(root) != expected_tree:
        return False, "tree-identity-contract-mismatch"
    return True, None


def _validate_pg_meta_for_admission(meta: object) -> dict:
    """Apply every strict PrefixGraph metadata rule except the locality verdict itself.

    The release reader owns hostile-input semantics; reuse its bounded scalar/path/digest validators so this
    admission path cannot drift into a permissive second parser.  The only intentionally deferred rule is the
    <=8x amplification comparison, because measuring that value is this module's job.
    """
    POLICY.install_policy()
    R = POLICY.R
    if not isinstance(meta, dict) or meta.get("v") != 1 or meta.get("engine") != "PrefixGraph-depth1-v1":
        raise RuntimeError("unsupported PrefixGraph metadata")
    R._tree_decl(meta.get("tree_sha256"))
    rels = meta.get("files")
    records = meta.get("records")
    if not isinstance(rels, list) or not isinstance(records, list) or len(rels) != len(records):
        raise RuntimeError("PrefixGraph file/record table declaration")
    if not 1 <= len(records) <= PG.MAX_FILES:
        raise RuntimeError("PrefixGraph record-count policy")
    seen_paths = set()
    for rel in rels:
        R._safe_relpath(rel)
        if rel in seen_paths:
            raise RuntimeError("duplicate PrefixGraph logical path")
        seen_paths.add(rel)
    for index, desc in enumerate(records):
        if not isinstance(desc, list) or len(desc) != 6:
            raise RuntimeError("malformed PrefixGraph record")
        kind, base, usize, csize, payload_sha, logical_sha = desc
        R._int(usize, "PrefixGraph logical size", maximum=PG.MAX_FILE_BYTES)
        R._int(csize, "PrefixGraph payload size", maximum=PG.MAX_FILE_BYTES + 1024 * 1024)
        R._bytes32(payload_sha, "PrefixGraph payload digest")
        R._bytes32(logical_sha, "PrefixGraph logical digest")
        if kind == "direct":
            if int(base) != -1:
                raise RuntimeError("PrefixGraph direct record has a base")
        elif kind == "prefix":
            base = R._int(base, "PrefixGraph base id", maximum=len(records) - 1)
            if base == index or records[base][0] != "direct":
                raise RuntimeError("PrefixGraph dependency depth exceeds one")
            R._int(records[base][2], "PrefixGraph anchor size", maximum=PG.MAX_FILE_BYTES)
        else:
            raise RuntimeError("unknown PrefixGraph record kind")
    if int(meta.get("max_dependency_depth", 99)) > 1:
        raise RuntimeError("PrefixGraph dependency-depth declaration")
    return meta


def _decode_pg_meta_for_admission(comp: bytes, raw_size: int, expected_sha: bytes) -> dict:
    """Authenticate bounded PrefixGraph metadata without pre-rejecting its measured locality."""
    POLICY.install_policy()
    R = POLICY.R
    R._int(raw_size, "PrefixGraph metadata raw size", maximum=PG.MAX_META_BYTES)
    if len(comp) > PG.MAX_META_BYTES:
        raise RuntimeError("PrefixGraph compressed metadata bound")
    raw = zstd.ZstdDecompressor().decompress(comp, max_output_size=int(raw_size))
    if len(raw) != int(raw_size) or PG.H(raw) != expected_sha:
        raise RuntimeError("PrefixGraph metadata authentication")
    meta = R._bounded_unpack(raw, max_array_len=PG.MAX_FILES * 8 + 64, max_map_len=PG.MAX_FILES + 64)
    return _validate_pg_meta_for_admission(meta)


def _pg_meta_for_admission(archive: Path) -> tuple[dict, bool]:
    """Read one authenticated metadata copy, preserving primary<->tail recovery semantics.

    Payload bytes are intentionally untouched.  PG.strong_verify / the strict release reader remain responsible
    for complete logical verification at their existing boundaries; this helper owns only admission accounting.
    """
    size = archive.stat().st_size
    primary = None
    tail = None
    primary_error = None
    tail_error = None
    with archive.open("rb") as stream:
        try:
            header = stream.read(PG.HEADER.size)
            if len(header) != PG.HEADER.size:
                raise RuntimeError("short PrefixGraph primary header")
            magic, mcs, mus, meta_sha = PG.HEADER.unpack(header)
            if magic != PG.MAGIC:
                raise RuntimeError("not PrefixGraph archive")
            POLICY.R._int(mcs, "PrefixGraph compressed metadata", maximum=PG.MAX_META_BYTES)
            comp = stream.read(int(mcs))
            if len(comp) != int(mcs):
                raise RuntimeError("short PrefixGraph primary metadata")
            primary = (_decode_pg_meta_for_admission(comp, int(mus), meta_sha), meta_sha)
        except Exception as exc:
            primary_error = exc

        try:
            if size < PG.FOOTER.size:
                raise RuntimeError("short PrefixGraph tail")
            stream.seek(size - PG.FOOTER.size)
            footer = stream.read(PG.FOOTER.size)
            magic, mcs, mus, meta_sha = PG.FOOTER.unpack(footer)
            if magic != PG.TAIL:
                raise RuntimeError("PrefixGraph tail magic")
            POLICY.R._int(mcs, "PrefixGraph tail compressed metadata", maximum=PG.MAX_META_BYTES)
            meta_offset = size - PG.FOOTER.size - int(mcs)
            if meta_offset < PG.HEADER.size:
                raise RuntimeError("PrefixGraph tail metadata offset")
            stream.seek(meta_offset)
            comp = stream.read(int(mcs))
            if len(comp) != int(mcs):
                raise RuntimeError("short PrefixGraph tail metadata")
            tail = (_decode_pg_meta_for_admission(comp, int(mus), meta_sha), meta_sha)
        except Exception as exc:
            tail_error = exc

    if primary is None and tail is None:
        raise RuntimeError(
            f"no authenticated PrefixGraph metadata for admission: primary={primary_error!r}; tail={tail_error!r}"
        )
    if primary is not None and tail is not None and primary[1] != tail[1]:
        raise RuntimeError("conflicting authenticated PrefixGraph metadata copies")
    chosen = primary if primary is not None else tail
    assert chosen is not None
    return chosen[0], primary is None


def prefixgraph_locality(archive: Path) -> dict:
    """Compute locality from authenticated metadata and return rejection as data, never as a policy bypass."""
    meta, recovered_from_tail = _pg_meta_for_admission(archive)
    records = meta["records"]
    worst = 0.0
    prefix_records = 0
    rows: list[dict] = []
    for index, desc in enumerate(records):
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
        else:  # pragma: no cover - admission metadata validation rejects unknown kinds first.
            raise RuntimeError("unknown PrefixGraph record during locality accounting")
        worst = max(worst, amp)
        rows.append({"record": index, "kind": kind, "decoded_context_amplification": amp})
    return {
        "max_member_read_amplification": worst,
        "prefix_records": prefix_records,
        "passed": worst <= MAX_MEMBER_READ_AMP,
        "rows": rows,
        "accounting_source": "authenticated-metadata-only-admission-preflight",
        "payload_bytes_materialized_for_locality": 0,
        "recovered_from_tail": recovered_from_tail,
    }
