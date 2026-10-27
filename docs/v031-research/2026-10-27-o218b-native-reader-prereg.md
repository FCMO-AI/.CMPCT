# O218b — Prospective installed-Reader native S_CHUNKS admission court

Date: 2026-10-27 UTC
Status: PREREGISTERED BEFORE INSTRUMENT / NO PRODUCT MERGE

## Canonical baseline and parent ownership
Released main is v0.30.0 / revision 24 at `80c358f8824ec1b20d349c92ed94c898090969b0`.
The composed v0.31 Reader belongs to #569 at `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, Reader blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`; `validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`.
The native *micro-only* oracle belongs to #577, source `research/o218_fastscan.c` blob `a54f15181d9dbe667b9e8c9d52e927b09c80152f`, scientific head `6372e780be99a31f5ea21b7a3c74fde92cf0bc45`.
This branch is stacked on #577 and makes NO product-source edit, ABI declaration, format change, or release claim.

## Primary question
Can the unchanged O218 C-list scanner, used ONLY as a research-only replacement for the existing S_CHUNKS validator inside an otherwise exact installed #569 Reader, eliminate the remaining full-Reader cold-open cost demonstrated by O216, while retaining every valid/hostile outcome and original error diagnostic through fallback?

## Strongest simpler controls
A) Unmodified original `_validate_storage`, B) original O216 exception-only fast validator, C) unchanged O218 native scanner plus original validator fallback, D) deliberately unsafe no-validation timing lower bound (never a product candidate). The same authenticated r24 bytes and exact Reader source are used for all four alternatives. Cold-open constructor+close is timed; Python process launch, source archive creation and C compilation are separately disclosed. The original O215 Builder-independent writer is reused, not regenerated around candidate semantics.

## Hypothesis and decisive gate
At 65,536 and 262,144 **repeated S_CHUNKS references**, native-scanner full-Reader median cold-open wall must be at least 2.5x faster than the O216 fast Reader (weaker 3x *micro* proof does not suffice). Native overhead over deliberately unsafe full-Reader lower bound must satisfy BOTH: ratio <2x and absolute overhead <=5 ms at 65,536; ratio <2x and <=20 ms at 262,144. Strict outcomes, exception *type and message*, full read, verify, and selected range identity must match the unchanged original. A distinct-owner held-out profile is required if the original O215 archive generator permits it; otherwise mark as unmeasured, never generalize repeat-profile evidence. If native speed wins but packaged native dependency cost / Windows/macOS remains unmeasured, result is SCIENCE_ONLY and requires productization debt.

## Alternative explanations
The O218 micro gain may disappear behind MessagePack unpack, pathname canonicalization, mmap, and Python import. CPython extension cold import can dominate low-ref opens. A C loop can return False on oversized but valid inputs, forcing original fallback; this is allowed for correctness but may remove speed gains. Repeated-ref synthetic profiles may be atypical. Native extension binary, build/wheel burden, memory, and portability can overturn a timing gain.

## Controls and adversarial cases
Preserve identical original / fast / native / unsafe runs of the existing O215 r24 authenticated fixture, no Builder use. Exercise at least the full O216 19 reference-shape/boolean/float/negative/late-error controls, plus cross-kind fallback, and inherited O215 pytest without altering their assertions. Native true is accepted only for exact built-in integer refs and fully checked blob/size conditions; native false ALWAYS delegates to the unchanged original validator. Record SHA identities of installed module and repository; any source drift invalidates the experiment. Record repeated raw wall and CPU in isolated workers with counterbalanced order, plus process-level peak RSS if available. Preserve all arms and negatives even when kill condition fires.

## Explicit non-claims and stop/next
A research-time CPython extension injection is neither stable ABI productization nor a cross-platform guarantee. No compiled product artifact or official full release benchmark is earned by this test. If whole-Reader speed does not clear both thresholds, retire C-list admission as a complete near-term remedy and reopen format/proof/ownership framing. If it clears, hand off an exact-source candidate to #569 for a separate costed portability/packaging and three-host composition; no modification of #569 without owner coordination. Do not edit Discovery STATE (state reconciliation #574 owns it). Historical O216/O217 negatives and O218 micro remain immutable. The experiment may produce a negative decision with GREEN scientific evidence.

## Counterfactual to examine after result
Would inspecting the complete Reader cost rather than just the original `_validate_storage` micro have revealed that a C scanner is / is not worthwhile earlier? Record only a prospective transferable discriminator. No policy change based on one result.
