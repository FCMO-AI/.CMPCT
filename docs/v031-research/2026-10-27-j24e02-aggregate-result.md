# J24E02 — upstream raw-ABBA release-evidence integrity

**2026-10-27 UTC. Research / evidence-infrastructure candidate, NOT product/release promotion.**
- Parent #561 `2d0461ce3fdc07bc74fd6a0f3d09990b3b377186`; original ABBA reducer blob `6e036f75528bd892d6552b8b04f5586770ff1744`, original strict comparator blob `22172ba4465b297bba54b0120f3419abe632cbd1`.
- Frozen prereg `da642fde816a2ec7064e724ffa6417cc724a8a49`; first implementation `364b05134ce2d83acb4f1c61422c4e7dd7ba2d93`; corrected focused test-only commit `52ced8054d130d54a8fefd02d5211dd4db8424b4`.

## J24E02a — observed source-exact result

[Three-host source-exact GitHub Actions run 40438075304](https://github.com/FCMO-AI/.CMPCT/actions/runs/40438075304) **SUCCESS Ubuntu / macOS / Windows 3/3** at exact HEAD `52ced8054d130d54a8fefd02d5211dd4db8424b4`. Two focused unittest entrypoints each pass across all three operating systems (6/6 class executions, each containing all 7 hostile subcases and positive A/A + genuine red). The workflow reads the true original aggregator via `git show` from the frozen parent and compares its Git blob to `6e036...`; it similarly validates unchanged comparator `22172...`. It runs original and candidate as separate Python subprocesses on identical raw JSON artifacts and runs the actual strict downstream comparator.

**Original aggregator accepts all seven raw hostile files and yields downstream PASS:** duplicate CMPCT creation timing with first 0.107 / last 0.100; duplicate whole corpus map, duplicate ZIP bytes, ZIP-only NaN, +Infinity, -Infinity, and JSON overflow number `1e309`. The first case hides a genuine +7% / +7ms *raw report contradiction* by removing the first value, even though strict comparator #561 rejects duplicates **only after aggregation**. ZIP-only nonfinite cases do not establish a hidden CMPCT performance regression; they establish invalid evidence accepted as genuine ZIP source statistics.

**Candidate rejects all seven at the raw ingress**, before producing any aggregate file. Unchanged valid unique-key A/A source pair gives byte-identical aggregate output and comparator PASS; genuine unique-key +7%/+7ms CMPCT case remains comparator FAIL under unchanged zero-byte and joint 5%+3ms thresholds.

The first [push run 40437971300](https://github.com/FCMO-AI/.CMPCT/actions/runs/40437971300) **FAILED** because test expectation used `kind.startswith("zip-")`, mistakenly classifying duplicate ZIP bytes as nonfinite rather than duplicate-key evidence. All three jobs otherwise demonstrated actual candidate refusal. Corrected the *test oracle only* in `52ced...`, without modifying product candidate or thresholds; preserved this negative.

Original hosted artifacts:
- Ubuntu ID `12704074677`, sha256 `f4a34183f54843d0cbe14a6548827fa2a37cd79629bb4fa10fe581d2e`.
- macOS ID `12704945842`, sha256 `6d8b5ade6c5a6e6d80a11af9dd4d0cb7be4050f789cda0de8f7ecb7c6448a86c`.
- Windows ID `12704074687`, sha256 `c61ef9516a873147e81ba959d697cc6c361ae50ed800c4b3c863be9ba440aabf`.

GitHub artifact-upload SHA values are provider reports, not locally downloaded independent rehashes. Original and candidate both operate on the same raw input semantics; only evidence-ingestion logic changes.

## J24E02b — prospective stronger alternative, BEFORE implementation/hosted test

**Local language-level observation (not yet authenticated CMPCT product evidence):** Python `float("nan")` and `statistics.median([nan,nan])` produce nonfinite values; `float("0.1")` silently converts strings, and `bool` compares equal to integers in Python. The raw ABBA aggregator calls `statistics.median(float(cell[field]) ...)`, while downstream #561 validates CMPCT fields but not ZIP-only measurements. The J24E02a JSON-token fix may therefore still admit **legal JSON containing invalid typed metrics**, e.g. ZIP timing `"nan"` (string), ZIP bytes `true` or `-1`, even though source evidence is not a valid physical measurement.

**New narrow question:** Can strict typed numeric admission at the upstream report boundary close this residual false-green/invalid-evidence channel without rejecting legitimate finite numeric inputs, altering median values, changing any comparator policy, or touching format/product source?

**Predictions:** Original aggregator and J24E02a candidate admit invalid ZIP-only typed data and actual downstream #561 comparator returns PASS; J24E02b must reject all invalid numeric types and values in either `cmpct` or `zip` formats *before* aggregation. Valid integer/finite-float bytes/timing across both formats retain identical source-controlled aggregate, A/A PASS and true CMPCT 7%/7ms FAIL. Invalid `logical_bytes` and malformed corpus schema also fail early.

**Kill:** if original/J24E02a already refuses these typed ZIP adversaries, if every valid finite report is changed, if the stored-bytes 0B or timing 5%+3ms policy changes, if the extra validation requires changing the official corpus schema, or if full hosted source-exact CI fails. Alternatives: only validate ZIP values after aggregation (cannot detect typed pre-conversion string), normalize strings (semantic fiction), strengthen the downstream comparator alone (cannot re-observe raw input). Prefer a small single upstream validation pass over duplicating normalized evidence stores.

**Research tier:** adverse source-exact behavioral court, then multi-host CI; full genuine product ABBA, timing/RSS and release authority remain separately pending.

## Counterfactual discriminator and policy
The reusable prospective question for future evidence pipelines is: **At which earliest lossy transformation can raw conflicting evidence be irreversibly collapsed before the strict final gate?** Here that seam is the ABBA reducer, not the downstream comparator. No new discovery policy amendment is justified from a single episode.

## Product boundary / remaining debt
No Builder, Reader, Writer, format, real compression or recovery was changed. No full 4GiB export, official ABBA product benchmark, source tree identity proof, or release promotion occurs here. Correctness protects the provenance of numerical *evidence*, not the behavior of physical CMPCT archive semantics. Keep #561 comparator and #328 full-PR admission owners unchanged. No Discovery state mutation.


## J24E02b — completed typed-value attack (result after frozen prospective prediction)

**Exact scientific source:** `320c7e799135a6257bf1f1fede542509be4ac12b`, patched raw-aggregator Git blob `c55780c9f2d9b1784567daa8f5b40ae9421adceb`, unchanged strict comparator Git blob `22172ba4465b297bba54b0120f3419abe632cbd1`. Prospective typed-metric test commit `19e9b8d7e631ece0b27ff69144b0aeda628c14ce` preceded implementation `320c7e...`.

**[Three-host hosted run 40438290105](https://github.com/FCMO-AI/.CMPCT/actions/runs/40438290105): SUCCESS on Ubuntu, macOS, Windows, 3/3.** Independent [PR-triggered run 40438297908](https://github.com/FCMO-AI/.CMPCT/actions/runs/40438297908): 3/3 SUCCESS at the identical actual source HEAD. Each host ran all **three focused test methods** with 7 repeated-key/nonfinite-token adversarial subcases, 7 additional legal-JSON-but-invalid-type cases, and valid A/A + authentic red controls. All original raw ingestion cases **passed through the original aggregator** and returned downstream comparator PASS. The candidate rejected all fourteen raw adversarial cases before aggregate publication; candidate valid A/A output was byte-identical to original and passed; candidate +7%/+7ms valid input remained a downstream FAIL as intended. **14 distinct hostile classes**, each challenged on all 3 hosts; not 14 independent full benchmark workloads.

New typed cases: ZIP numeric string `"nan"`, ZIP `"inf"`, ZIP zero-time, ZIP `"0.1"` string-time, ZIP boolean bytes, ZIP negative bytes, CMPCT numeric string. This exposes both ZIP-only evidence poisoning and CMPCT typed-number normalization. The candidate now validates raw corpus shape, logical input byte type, both layers, both formats, archive byte type and positive finite timing **before** the original aggregate calculation. It retains original median and deterministic equality code.

**Primary scientific disposition: `ACCEPT_SCOPED_EVIDENCE_INGRESS_GUARD`; NO RELEASE PROMOTION.** The first J24E02a guard was necessary but not sufficient: syntactically legal JSON strings/bools could still launder via `float()` or Python `bool == int`. This is a prospective transferable discriminator: follow the raw evidence until its *last lossy type conversion*, rather than assuming a parser that rejects duplicate JSON keys protects every downstream provenance boundary.

[Push-run artifacts](https://github.com/FCMO-AI/.CMPCT/actions/runs/40438290105):
- Ubuntu `12705535347`, GitHub artifact sha256 `2b3628e2bc4a31c767f7c0f1c2fa5b80c1b0f2c48ad995297a6fd4010e5d107c`;
- macOS `12705545300`, provider sha256 `8d69d8d812d97b77e67eed5be4c6635e72adffa4e8a59a51ab1793a4ea39e5d1`;
- Windows `12705080848`, provider sha256 `8c21f7a4bcf5c6b1dbc2e7bb8f5534d1acda3aa0d81001c3203b3f6d94f0de78`.

These are GitHub-computed artifact digests, **not independently downloaded and rehashed receipts**. Each source-bound runner verifies actual `git rev-parse HEAD`, frozen parent aggregator blob, unchanged comparator blob, and executes original/candidate source in subprocess. Original failure 40437971300 remains attributable to wrongly classified test expectation; correction retained without modifying the source guard or thresholds.

**Remaining truth:** No full release-parity ABBA benchmark, no authentic corpus fingerprint verification, no Reader/Builder/Writer changes, no benchmark size/speed/RSS credit and no general-suite completion from this focused experiment. This cannot detect a malicious producer forging unique-key, finite, plausible-looking values. Owner integration and exact final documentation HEAD CI must be checked before any promotion.
