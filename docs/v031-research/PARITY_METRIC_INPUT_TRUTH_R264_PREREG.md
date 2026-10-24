# Preregistration — v0.31 r24/ZIP release-gate measured-input honesty

Status: prospective / scientific-evidence and evaluator-hardening experiment. Source baseline: `agent/phased3-v031-salvage-v031-fingerprint-source-composition-20261023@2825253a2b40386df173b7f5497abffbe6539f91`; checker blob `390ecda99cd6de8f30502709ca0f6a527cfcddf2`. The source owner of the composition is PR #302. No modification to the owning PR or frozen release policy.

## Question and falsifier

Can malformed *measured values* in a structurally valid `cmpct-zip-parity-v1` report produce a green result from `tools/check_performance_regression.py`, even when no valid comparison was measured?

The current implementation converts `bytes` with `int()`, durations with `float()`, and evaluates `rel > 5% and absolute > 3ms`. Predictions before implementation:
- `NaN` or positive infinity in a base median, `NaN` in a candidate median, and zero/negative base medians can reach green despite there being no meaningful measured duration (Python comparison behavior).
- A candidate `bytes=-1`, bool, or fractional value can pass as a falsely smaller archive; an empty corpus map can pass vacuously.
- A well-formed matched input and unchanged semantically valid numbers must retain the incumbent verdict, including strict **zero-byte** size regression and conjunctive **5%/3ms** timing rules.
- Missing corpus/layer/field data already errors and must continue to fail closed, not be silently ignored.

## Mechanism and controls

Add a small input-validation boundary to the comparison evaluator: require non-empty matched corpus sets, positive integral non-bool complete archive bytes, finite positive numeric non-bool create/extract medians in both library and CLI layers. Reject invalid evidence *before* comparing. Use Python's finite/positive checks, not string coercion or rounding. Preserve comparator thresholds and report semantics exactly for valid inputs.

Strong simpler control: rely on exporter JSON and trust workflow. Rejected: invalid numbers are admitted by Python JSON and `float` and can arise from instrumentation, missing measurements or fixture corruption; an evaluator must refuse a vacuous green.

## Independent test and kill condition

Add a focused self-contained pytest court with paired valid/invalid JSON reports and a direct invocation of the **actual** evaluator entrypoint, not a copied algorithm. Expect invalid evidence to raise an explicit `ValueError` / nonzero exit, and valid evidence to preserve passing/failing verdict at threshold boundaries.

Kill/narrow on any legitimate benchmark report rejected, any valid regression normalized away, changed threshold, changed schema/corpus, or a second evaluator interpretation that disagrees on valid inputs. Preserve the negative behavior of inherited source in preregistration rather than rewriting baseline history.

## Source / portability / cost boundary

No archive/codec/format/release/source-fingerprint changes. This is evidence-integrity, not a compression/performance win. The branch is stacked on PR #302; a performance run comparing it with PR #302, if triggered, **does not** establish scanner performance against v0.31 development. Exact-head hosted status must be read separately. Do not edit `docs/discovery/STATE.json` (distinct active owner). This preregistration is recorded before tests and implementation.
