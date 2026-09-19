# v0.30 G04 guarded-inverse selection bound — 2026-09-15

Authority branch: `agent/v030-authoritative-integration`.

This is a deterministic derivation from the current shipping guard and already-preserved ML record-shape evidence. It is not a runtime measurement and earns no release credit.

For the dominant `neutral_hostile_v1/09_ml_artifacts` delimiter record, preserved evidence reports:

- segment count = `45,979`;
- maximum segment length = `27`;
- unique segment lengths = `12`;
- logical size = `1,048,576 B`.

Current `entropygraph_v030_canonical_final._banded_delimiter_inverse` computes:

- `cell_scans = count * max_len = 45,979 * 27 = 1,241,433`;
- `band_python_ops = len(active_counts) * count + sum(active_counts)`;
- the banded path is rejected when `band_python_ops * 4 > cell_scans`.

Even before charging the non-negative `sum(active_counts)` term, the lower bound is:

- `band_python_ops >= 12 * 45,979 = 551,748`;
- `4 * band_python_ops >= 2,206,992 > 1,241,433 = cell_scans`.

Therefore the current guard **must reject the banded arm on this exact dominant ML record** and route to `_bulk_from_parsed`. This conclusion does not depend on timing noise or the unknown active-count distribution.

Decision consequence: the guarded-banded shipping wrapper cannot, by construction, recover the dominant ML record through its banded arm on the already-measured record shape. Any observed difference versus the reviewed bulk-v1 control can only come from the parsed fallback implementation (for example avoiding reparsing/intermediate movement), not from banded reconstruction. Do not interpret a green semantic test or the existence of the guarded implementation as evidence that the ML runtime debt has been attacked materially.

The exact-archive A/B now queued on the branch compares the shipping guarded implementation to the reviewed bulk-v1 predecessor and will measure whether the fallback-level changes have meaningful complete-extraction value. A stronger next mechanism, if needed, should target the actual structural pathology: empty/short rows collapse the global dense prefix, while tens of thousands of segments make per-row/per-band Python work expensive. A credible alternative should recover a dense prefix over the active/non-empty subset or move the ragged transpose into a genuinely lower-overhead primitive, while preserving the existing descriptor/resource bounds and exact bytes.

Claim boundary: deterministic control-flow/operation-count derivation only. No product speedup, regression, archive-byte change, threshold change, or release status is claimed here.
