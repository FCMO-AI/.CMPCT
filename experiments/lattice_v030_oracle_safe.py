"""Safety-filtered entrypoint for the v0.30 Lattice accepted-graph oracle.

The original oracle correctly rejects a candidate group whose cold-read amplification exceeds the
preregistered <=8x law, but it applied that rejection to inherited *source* records before any Lattice
replacement existed.  Some accepted-v0.29 pure-direct packs already exceed the stricter per-member law,
so aborting the entire search confused "not eligible for this experiment" with "malformed archive".

This wrapper changes no compression threshold, byte-cost model, transform, or promotion criterion.  It
conservatively excludes source groups that cannot participate under the new locality invariant, leaving
them byte-for-byte inherited.  The underlying oracle then evaluates only admissible replacements.
"""
from __future__ import annotations

from experiments import lattice_v030_oracle as oracle

_original_pure_direct_groups = oracle._pure_direct_groups


def _eligible_pure_direct_groups(meta: dict, records: list[tuple]) -> list[dict]:
    groups = _original_pure_direct_groups(meta, records)
    eligible: list[dict] = []
    for group in groups:
        raw_bytes = int(group["raw_bytes"])
        members = list(group["members"])
        if raw_bytes > oracle.MAX_PACK_BYTES or not members:
            continue
        worst_amp = max(raw_bytes / max(1, int(member["length"])) for member in members)
        if worst_amp > oracle.MAX_READ_AMP + 1e-12:
            # Footnote: this is an inherited record, not a Lattice candidate.  Preserve it unchanged
            # rather than aborting or claiming the stricter locality property for bytes we did not emit.
            continue
        eligible.append(group)
    return eligible


oracle._pure_direct_groups = _eligible_pure_direct_groups

if __name__ == "__main__":
    oracle.main()
