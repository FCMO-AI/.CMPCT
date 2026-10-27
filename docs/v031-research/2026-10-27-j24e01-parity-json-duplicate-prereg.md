# J24E01 — prospective duplicate-key release evidence falsifier

Status: preregistered before comparator mutation, 2026-10-27 UTC.

## Authority and baseline

CMPCT released v0.30.0 / r24 remains immutable. Isolated branch on the exact owner candidate PR #306 at `84bcd4144e3cf95bbc66a9cb3df8c7c101b89bb9`, currently `tools/check_performance_regression.py` Git blob `2cea1b4d0cfe52259e5bc6b870c8207b4c889610`. PR #306 owns finite/nonnegative/integral measured-input validation and legal policy-option validation; PR #328 owns full-PR performance admission. Neither source owner branch is modified. This is a different *serialization ambiguity* at the evidence ingestion boundary.

## Question, prediction, and falsifier

Can a syntactically valid JSON benchmark report contain duplicate mapping keys that cause `json.loads` to silently discard a timing/size regression or an entire corpus, producing false release PASS? The inherited evaluator uses `json.loads(path.read_text(...))` without `object_pairs_hook`; normal Python decoding retains only the last duplicate value. Prospectively predict that a duplicate `create_s_median` with first value 0.107 and last 0.100, or a duplicated `corpora` mapping, will make an otherwise serious candidate regression vanish and yield PASS against an unchanged base. The clean unique-key +7%/+7ms input must still FAIL; exact A/A must PASS.

Reject the hypothesis if the actual inherited comparator rejects duplicates, or if a proposed strict duplicate-key guard breaks valid unique-key reports, changes any 0-byte/5%+3ms policy semantics, changes source/workload identity, or invents lower-layer product credit. Do not soften existing legitimate source-custody/CI requirements.

## Mechanism and alternatives

Cheapest control: trust JSON producer or only check top-level keys; neither forbids duplicate keys in nested corpus/layer/metric mappings. Selected small bounded decoder guard: use Python `json.loads(..., object_pairs_hook=...)` to reject duplicate members at **every** object depth, without normalizing or ignoring any duplicate. Preserve default parsing/exception behavior for ordinary unique-key mappings and unchanged comparator semantics. This is a defensive evidence-ingestion improvement, not compression, Reader, Writer or archive format work. A stronger independent test must use the *actual comparator CLI* and raw JSON strings containing duplicate pairs; Python dict-based test construction would erase the problem before reaching the evaluator.

## Evidence ladder and debt

1. Static baseline: current owner source and Python JSON semantics. 2. Dynamic negative: original owner comparator on a raw duplicate-key report. 3. New direct regression: invalid duplicates rejected, clean matched A/A PASS and true 7%+7ms FAIL; at least nested metric and corpus-map variants. 4. Exact-head GitHub-hosted source-bound independent tests, plus generic CI honesty. Maintain all original fixture/source identities; no official performance speedup or release approval claimed.

## Concurrency, release and public safety

No conflicting open PR specifically owns JSON duplicate benchmark report admission; PR #306 remains metric-policy owner and #328 remains performance-admission composition owner. This separate branch/PR is stacked for owner reconciliation, not a silent overwrite. No changes to immutable `docs/V030_RELEASE_LOCK.json`, frozen corpus, timing bounds, format r24, release v0.30.0 or public marketing. All test values are synthetic. **No merge, release, or policy change** is requested from this experiment.
