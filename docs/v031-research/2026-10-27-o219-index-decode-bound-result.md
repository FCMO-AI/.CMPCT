# O219 — Same-wire MessagePack decode changes the native-admission decision

Date: 2026-10-27 UTC. **Measured lower-rung research result. Not a shipping Reader claim.**

## Prediction and provenance
The preregistered question/threshold is immutable at `c76e0b2f5b54ecbaffafa0adf0e14759b2c52a37`. Parent O218 #577 was pinned at `6372e780be99a31f5ea21b7a3c74fde92cf0bc45`; unchanged original native C Git blob `a54f15181d9dbe667b9e8c9d52e927b09c80152f`, O218 Python oracle `0639d777be782909cbf7dd9c8553a358933b81ba`, original strict validator `51c2849061f99a4afeddb7666956b24566ce7de0`.

O218 measured >3x native micro improvement over its O216-like loop. O219 tests whether that remains >=2x when every candidate must pay `msgpack.unpackb` on *exactly the same deterministic wire*.

## Direct hosted result
GitHub Actions exact source head `408c968840d88c063e7d5d18cb25c5a030b51bb9`, [run #40465427133](https://github.com/FCMO-AI/.CMPCT/actions/runs/40465427133), **SUCCESS** in Ubuntu 24.04 Python 3.11 and 3.13. Both executed 4 profiles × 3 algorithms × 17 paired rounds = 204 samples per Python version, 408 total, with randomized method order, per-call decode/check CPU and wall, same wire SHA per profile, original C unchanged and completely separate receipt auditor **1,132 PASS per host / 2,264 combined**.

Observed medians, milliseconds; ratio is **(decode+O216-like) / (decode+native)**, not full Reader speedup.

| Python | References / physical owners | O216-like total ms | Native total ms | Total ratio | Decode fraction of O216-like |
|---|---|---:|---:|---:|---:|
| 3.11 | 65,536 / 1 | 3.479 | 0.816 | 4.265x | 8.4% |
| 3.11 | 65,536 / 65,536 | 6.886 | 4.138 | 1.664x | 53.0% |
| 3.11 | 262,144 / 1 | 15.120 | 3.228 | 4.684x | 7.8% |
| 3.11 | 262,144 / 262,144 | 30.431 | 20.156 | 1.510x | 56.9% |
| 3.13 | 65,536 / 1 | 4.375 | 0.933 | 4.688x | 5.7% |
| 3.13 | 65,536 / 65,536 | 9.310 | 5.456 | 1.706x | 49.7% |
| 3.13 | 262,144 / 1 | 17.613 | 3.878 | 4.542x | 5.7% |
| 3.13 | 262,144 / 262,144 | 39.967 | 25.012 | 1.598x | 52.2% |

**Preregistered decision: `WHOLE_INDEX_ORACLE_BELOW_2X`.** The 262,144 high-repeat arms pass 2x; high-diversity arms **fail** on both Python versions. Native remains a real potential optimization but has no general >=2x decode-inclusive advantage for these two important structural families. No threshold was changed to rescue the interpretation.

## Artifacts and audit
- Python 3.11 [GitHub artifact #12716665306](https://github.com/FCMO-AI/.CMPCT/actions/runs/40465427133/artifacts/12716665306), GitHub ZIP SHA-256 `12d9a2974631cebd790b018f35239aa41853780bfcecdcc391e5df8a29b9e623`, raw JSON SHA-256 `80d7d66bac05c26838007cc077b8a1db03fb9f5129cba875994c92f5d90ec436`.
- Python 3.13 [GitHub artifact #12715747890](https://github.com/FCMO-AI/.CMPCT/actions/runs/40465427133/artifacts/12715747890), GitHub ZIP SHA-256 `8f42dee266d51490e245801aef7f52a4350e1a75e1cb5634d9662609032a0b9d`, raw JSON SHA-256 `d468a1b73c77b53baf37d5c3a58984a1b5514326402ff26a7f550b7552187fd0`.
- The independent auditor validates every paired repeated arm, clock sum, reported median/ratio, identity, decision and schema: 1,132 checks per host, 0 discrepancies. Hosted evaluator and audit passed. An independent third implementation of the *entire Reader* was not run.

## Causal interpretation and strongest counterargument
The observed high-diversity MessagePack wire requires material distinct blob-row parsing. Even if scanning Python references costs much less in C, the parser still builds all its decoded Python objects. When the wire has one repeated owner, that parse is cheap and native dominates. For all distinct owners, decode can be more than half of O216-like combined time, so it dominates the remaining work and constrains achievable total speedup. The result does **not** show that C is universally uneconomic; the high-repeat total 4.5x advantage is genuine at this tier.

The strongest counterargument is that O216-like Python is a proxy, not the actual O216 validation implementation and its complete Reader read. This experiment excludes zstd decompression, blob header sanity, footer replay, filesystem IO, source construction, process startup, memory/RSS, native build wheel/portability burden and official complete-product economics. The artifact is **same-wire in-process cost attribution only**. It does not prove the native candidate is safe to adopt or make release claims.

## Decision and counterfactual
The cheapest prospective discriminator was to charge mandatory index decode to the function-level speedup *before* designing a CPython C extension product port. The O218 micro result remains valid, but this higher-rung proxy **narrows** promotion rationale: prefer shared proof/index structure or parser+validator fused ownership for high-diversity archives, and require genuine installed Reader ABBA before a native port is promoted. A different representation that avoids constructing many redundant Python rows remains a genuinely different-worldview option.

The result changed the scientific next step, not discovery policy. No `docs/discovery/STATE.json` edit while #574 owns its reconciliation. This is an independently preregistered replication/cost-composition of a different question, not a rewrite of O218's positive micro result.

## Handoff
Coordinate with owners #577 O218 and #569 J24C02. Do **not** claim a sixfold full Reader win; do **not** retire native universally. Prospective next product test: same signed r24 archive, original O216 and candidate with exact C, evaluate full cold open/list/selective/extract, RSS, CPU, negative hostile variants, packaging/ABI/Windows/macOS and full release gates. If generic benefit is still marginal after costs, retire the CPython-specific productization route in favor of format-agnostic proof/index alternatives.

Source head during evidence: `408c968840d88c063e7d5d18cb25c5a030b51bb9`. This result-note commit will change the HEAD; successful source-exact workflow on the new HEAD must be observed separately before any exact-final-HEAD statement.
