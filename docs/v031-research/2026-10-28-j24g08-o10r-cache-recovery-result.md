# J24G08 — O10R resource guard versus J24G06 cache: signed orphan-tail recovery incompatibility

**Status 2026-10-28 07:30 UTC:** original exact-source [hosted court #40650224329](https://github.com/FCMO-AI/.CMPCT/actions/runs/40650224329) **SUCCESS** on source-experiment HEAD `b1bf168918c70426387c8ec8f571a9ed226d793b`. Preregistered hypothesis **CONFIRMED in the measured Ubuntu/Python 3.11 scope**. The further artifact-retention commit changes **only the workflow**, not the product or research instrument; its own exact-head CI must be judged separately. **No product change, merge, release, or r24/v0.30 version claim.**

## Decision in one sentence

An existing strict O10R signed-generation *depth exception* can prevent an authentic **older committed** generation from being recovered after a newest **SHA-valid but orphaned** footer chain, whereas the #650 negative-ancestry cache can still recover it. Therefore mechanical composition of O10R's raise into #650 is **not a lossless solution** to the >16k cache work cliff without resolving the explicit resource-vs-availability contract.

## Exact sources, preregistration, same-input custody

- First immutable prospective prediction: `023b2b3f1544073be2214dafe64b040b9ccd29c5`; see [preregistration](2026-10-28-j24g08-o10r-cache-recovery-prereg.md).
- Unmodified #650 installed Reader: Git blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`, source SHA-256 `a2a21beb7bba19ad3422f0b95ff814663e7b4b33302e2b539bf8e8a127e5f101`.
- Unmodified #365 installed O10R Reader: Git blob `2402721258531a56cfa2a53dcbd81874fd6c1f76`, source SHA-256 `0f7f0a4070850fca9dc250bb86cedc230beb4fb859bfb3746dffe297d64c3f06`.
- Ubuntu 24.04, CPython 3.11, independent installed venv wheels; `site-packages` contents byte-identical to both pinned Git objects. A single #650 Builder + genuine Writer `append_rename` produced the *same physical* r24 specimens subsequently read by both Readers.
- Reproducible [test instrument](../../research/j24g08_depth_cache_fallback_court.py), [source-bound GitHub workflow](../../.github/workflows/v031-j24g08-o10r-cache-fallback-court.yml), full raw logs and JSON in hosted artifact `12799695604` (SHA-256 of artifact ZIP `c83766adae8d2bbc51f19bf60bf273d58107d354161c24e4ef2ccff40febc383`).
- Logical payload SHA-256 unchanged across successful cases: `6f34e399762df0125958764aa107cbb6c143f87e8a0876fac4a1fd08ac23b4ca`. The authentic first Writer commit footer was located at offset **1009**.

## Direct results (actual `_decode_generation_payload` call count)

| Exact physical case | Parser limit | #650 cache-only | #365 O10R |
| --- | ---: | --- | --- |
| Genuine signed generation depth 1 | 2 | RECOVERED / 2 calls | RECOVERED / 2 calls |
| Genuine signed generation depth 2 | 2 | RECOVERED / 3 | RECOVERED / 3 |
| Genuine signed generation depth 3 | 2 | RECOVERED / 4 | **ResourceLimitError / 3** |
| SHA-valid chained orphan 4 after genuine depth-1 Writer | 2 | **RECOVERED previous commit / 6** | **ResourceLimitError / 3** |
| SHA-valid chained orphan 140 after genuine Writer | default 128 | **RECOVERED previous commit / 142** | **ResourceLimitError / 129** |
| **Same physical** orphan 140, relaxed depth | 256 | RECOVERED / 142 | RECOVERED / **9,872** |
| 140 independent, unchained SHA-valid orphan footers | 2 | RECOVERED / 142 | RECOVERED / 142 |

All recovered results verified exact logical bytes, SHA-256, range read, `verify()`, selected footer and generation depth. The two disputed orphan cases retained the same physical SHA-256 between Readers: `b21d5d405dd6e1a54f116c72ded56220cccc28534d68b3ba33bede535b1d88b8` (4) and `6726853294bba328d5dcbb2373d628efbaade1a62122339126998a92a7d55447` (140). In both, the older authentic commit at 1009 remained physically present and readable by #650.

At relaxed depth 256, O10R generated **9,872** genuine decodes versus #650's **142** on identical 140-footer input (approximately **69.52×** more decodes), confirming the previous O(N²) mechanism remains without memoization when resource refusal is removed. The flat 140-footer control stayed O(N) on both Readers.

## Causal explanation and strongest negative

O10R raises at `depth > max_delta_depth` from inside `_index_from_footer`; the exception escapes `_latest_generation` without considering an older authentic footer. This limit is *intentional protection* against over-limit authenticated chains, and the depth-3 valid-generation control confirms it works. The conflict is not evidence that O10R generally corrupts data: it **refuses** extraction. The tradeoff is recovery **availability** under an attacker-constructed append tail.

The cache-only #650 Reader conversely recovers the older committed generation and avoids O(N²) for N=140, but **ignores** a deliberately configured depth ceiling in its existing code (valid depth-3 under configured limit 2 still succeeds). The #650 limit remains one of memory, *not* proven work. Neither owner on its own satisfies both guarantees.

The stronger claim that this is a universally unavoidable tradeoff is **not proven**. A bounded proof-aware scanner or compressed invalid-ancestry certificate may preserve both within realistic resource budgets. Likewise, no new remotely exploitable issue, source-mutating behavior, non-Linux parity, full peak RSS or full product benchmark outcome is demonstrated here.

## Alternatives and falsification conditions

1. **Mechanical O10R-depth guard in #650:** rejected as a no-regression recovery fix by the direct same-file court. It may still be chosen as an *explicitly documented fail-closed resource policy*, but cannot be silently credited with both fallback and availability.
2. **Simply raising cache cap:** not a general resource bound; O(N²) cliff is deferred, not removed.
3. **Partially admitting failed positions:** may reduce the immediate cap cliff; it does not guarantee bounded worst-case work for arbitrary untrusted chains. Prior #655 analytic control already constrains this.
4. **Proof-driven invalid-ancestry scan / bounded decode:** promising unimplemented hypothesis. Needs a generic membership proof for already-rejected ancestors, no false positives, a bounded physical-memory/exported-work law, correctly distinguished valid too-deep generation versus malformed tails, and stable-source or explicit mutation-boundary semantics.
5. **Global operation decode budget:** an honest explicit error bounds worst-case work, but still forfeits availability if a malicious tail consumes budget before the old checkpoint. Do not call it a full solution.

## Counterfactual and transferable lesson

The original #655 proposal already identified O10R as a potential composition. A source-level check for an exception in `_index_from_footer` and absence of an exception handler in `_latest_generation` could have flagged the availability risk **before** an implementation; the hosted exact-source court was necessary to establish actual first-party Writer/recovery behavior and rule out a harmless alternate fallback. Future resource-guard compositions should first distinguish **rejecting a candidate** from **aborting the entire recovery search**. This is a local experiment-design lesson, not enough repeated evidence to amend global Discovery Engine policy or thresholds.

## Next owner decision

Deliver exact result to #365, #650 and #655. Avoid a duplicate Reader implementation; propose a single explicit owner for a prototype of a **certificate-backed bounded negative-ancestry scanner**, plus cheap step-count and source-stability controls before broad product benchmark. The currently strongest target remains a bounded, exact, work-efficient Reader that keeps the previous genuine Writer generation readable after invalid post-commit tails.

No `docs/discovery/STATE.json` change: the file's current v0.30/bootstrap frontier is staleable cache and this narrow result is fully linked from the owner PRs. No separate CMPCT project-state database should be created here.
