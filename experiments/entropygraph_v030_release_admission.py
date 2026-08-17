"""Release-only admission policy for PrefixGraph inside the v0.30 system tournament.

The research selector originally reused ``PrefixGraph._read()`` to compute locality after building a candidate.
That helper is correct for a small oracle, but it materializes every payload and therefore does not belong in a
promoted memory-bounded selection path.  This module replaces both release-time eligibility and locality
accounting without changing PrefixGraph bytes:

- eligibility is decided from directory metadata before the expensive builder starts;
- the total logical family admitted to the current in-memory PrefixGraph encoder is capped at 256 MiB;
- post-build locality is computed from authenticated metadata only through the strict streamed reader preflight;
- no payload is read merely to decide the <=8x locality gate.

Footnote: the 256 MiB ceiling is an *encoder admission* bound, not a decoder grammar limit. PrefixGraph's current
research encoder loads all family members to price anchors; a future streaming encoder may safely raise this
ceiling after proving bounded memory without changing the on-disk representation.
"""
from __future__ import annotations

from pathlib import Path

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


def prefixgraph_locality(archive: Path) -> dict:
    """Compute decoded-context locality from authenticated metadata without reading candidate payload bytes."""
    POLICY.install_policy()
    stream, meta, _payload_start, _offsets, _tail_authenticated = POLICY.R._pg_open(archive)
    stream.close()
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
        else:  # pragma: no cover - strict policy preflight rejects unknown kinds first.
            raise RuntimeError("unknown PrefixGraph record during locality accounting")
        worst = max(worst, amp)
        rows.append({"record": index, "kind": kind, "decoded_context_amplification": amp})
    return {
        "max_member_read_amplification": worst,
        "prefix_records": prefix_records,
        "passed": worst <= MAX_MEMBER_READ_AMP,
        "rows": rows,
        "accounting_source": "authenticated-metadata-only",
        "payload_bytes_materialized_for_locality": 0,
    }
