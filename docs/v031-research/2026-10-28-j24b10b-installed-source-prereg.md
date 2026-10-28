# J24B10b — Prospective installed source byte identity hardening

**Date:** 2026-10-28 UTC. **Scope:** strengthen source custody only; preserve original J24B10 measured run `40760729066` and original `ed6376252e943cb4a9535d5b9cdde65e273834f8` unchanged in Git history.

## Motivation / measurement boundary

J24B10 first court measured the sparse quota overrun in all three hosted OS, and logged exact `git rev-parse HEAD`, the actual Python Reader module location and a SHA-256 of its installed bytes. However it did not explicitly assert *installed module bytes equal those checked out at the intended source commit*. The package install was from checkout, but that stronger relationship was a hypothesis rather than a verified invariant. This is an evidence-custody concern, **not** new science or reason to reinterpret the positive defect result.

## Prospective check

Before running original court cases, compare the `CMPCT` Reader's actual imported `inspect.getfile(CMPCT)` byte contents to the exact checkout `src/cmpct/reader.py` file, requiring a distinct site-packages path and binary equality after **LF/CRLF-only normalization**. Record both raw SHA-256 values, normalized SHA-256 and installed path in the original receipt. Preserve all J24B10 original archives, mutation, output bytes, refusal conditions, external Zstd independent referee, run matrix and disproof thresholds **unchanged**. The instrument must fail closed if imported Reader is the checkout source, or byte content genuinely differs; don't claim tested product version from `git rev-parse HEAD` alone.

## Alternatives, falsifier, expected decision

The cheap control would be trusting `pip install .` followed by looking at module paths; this does not prove byte identity. Direct byte comparison is stronger with small implementation cost. If Windows checkout CRLF is the only discrepancy, normalize only line endings as an explicit exception and report raw hashes; do not trim arbitrary bytes or ignore semantic differences.

**Falsifier:** any host imports checkout code instead of installed wheel, installed Reader differs after LF/CRLF normalization, or original material data results change. If any, keep that negative and diagnose before attributing science to released Reader. A positive check strengthens the original defect's source provenance; no product fix or release claim.

This addendum does not overwrite the original frozen scientific preregistration, original result logs, thresholds or comparators. Do not alter product/Reader/validator source or Discovery policy.
