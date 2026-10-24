# CMPCT O16 — genuine r24 opaque envelope around frozen BDC: negative strict-size decision

Date: 2026-10-24
Scientific disposition: **RETIRE the naive opaque-r24-envelope route for a dual strict external size win**. Keep direct bounded-drift integration open; never infer general BDC failure.

## Exact source and hosted evidence
- Owner scientific prereg: `benchmarks/history/2026-10-04-v031-bounded-drift-coordered-court-prereg.json`, frozen blob `f8e53f058a1c123ea4665b730c45f5619eb93d5f`.
- O16 prospective prereg committed **before script** at `df055d684857a748ed4c1fd722eef1328e21328e`.
- BDC frozen research positive: PR #236, run [39925132930](https://github.com/FCMO-AI/.CMPCT/actions/runs/39925132930), artifact 12489775120.
- Genuine current canonical r24 incumbent: PR #239, run [39929731385](https://github.com/FCMO-AI/.CMPCT/actions/runs/39929731385).
- O16 exact execution source `f131e9ba19fdd3a9801be0e1c8f45536b4dd701f`; successful [Actions run 40098303164](https://github.com/FCMO-AI/.CMPCT/actions/runs/40098303164), job 120885072047, raw artifact 12560874620. All hosted workflow steps passed, including Git blob custody and independent arithmetic/correctness judge.
- Raw, original output reconstructed from the hosted log is durably recorded in `benchmarks/history/2026-10-24-v031-bdc-r24-opaque-envelope-o16.json`, including the full per-corpus Builder stats, CPU/wall diagnostic and original physical SHA-256.

## Decisive complete stored bytes

| Pinned identical-original-data corpus | Frozen BDC sibling | Actual r24 archive carrying only this sibling | Net wrapper carrying cost | Pinned complete Zstd-19 | Outer archive minus Zstd-19 | Result |
|---|---:|---:|---:|---:|---:|---|
| Shifted | 1,687,989 B | **1,689,515 B** | +1,526 B | 1,694,674 B | **−5,159 B** | Strict byte win survives |
| Boundary | 72,841 B | **73,765 B** | +924 B | 73,097 B | **+668 B** | **Strict byte win LOST** |

Both original BDC sibling SHA-256 fingerprints matched the previously frozen hosted scientific receipts exactly. The unchanged Builder created two genuine r24 archives from one opaque `coordered-sibling.bin` input per corpus. The unchanged Reader `verify()` and `extractall()` returned exactly the frozen sibling bytes; the decoded original BDC filesystem manifest was byte-identical to its source manifest. The research runner therefore **succeeded** while the scientific size prediction for both strict wins **failed**.

### Mechanism: not just a guessed r24 header
The Builder's recorded `data_bytes` permits an arithmetic decomposition of the wrapper:

| Corpus | Original sibling payload | Builder `data_bytes` | Physical record/payload delta | r24 final minus `data_bytes` | Total net carrying cost |
|---|---:|---:|---:|---:|---:|
| Shifted | 1,687,989 | 1,688,437 | +448 | +1,078 | **+1,526** |
| Boundary | 72,841 | 72,905 | +64 | +860 | **+924** |

The observed deltas are consistent with seven 64-byte blob headers for Shifted and one for Boundary, but these components are inferred from Builder summaries, not separately instrumented physical record offsets in this activation.

The frozen Boundary BDC had just **256 B** of external strict-win headroom. The real r24 wrapper charged **924 B**. To regain strict external size superiority **without modifying the underlying sibling**, a representation would have to reduce the observed complete Boundary r24 output by **at least 669 B** (strictly below 73,097 B). That is **72.4% of the observed 924-byte net wrapper cost**. This is a necessary byte-budget target for *this* route, not a lower bound for redesigned direct grammars.

## Truth boundaries / negative knowledge
- **Proved:** naive opaque r24 encapsulation cannot preserve *both* frozen external strict-byte wins under the actually measured unchanged r24 Builder/Reader behavior.
- **Not proved:** that BDC itself loses to Zstd-19, to canonical selection under native filesystem semantics, or that a direct compact r24-compatible representation is impossible.
- **Especially not proved:** that the resulting r24 file natively exposes the original filesystem. It contains **one opaque nested file**, requiring an additional BDC decoder. The r24 archive and original tree do **not** have equivalent exposed semantics; these measured bytes are a deliberately generous compatibility-cost oracle, not product evidence.
- **CPU/wall/RSS:** one research process only; no ABBA or full-product comparison. Frozen BDC O16 combined diagnostic create wall was ~0.474 s Shifted / ~0.0965 s Boundary. Process peak ~100,220 KiB for the entire Python process, not an incremental/r24-vs-BDC RAM measurement. Existing PR #239 creation-cost debt remains independently relevant.
- **Integrity:** the r24 file and nested bytes round-trip with verification; this run did not independently exercise all hostile parser, recovery, concurrency, or portable filesystem cases.
- **Independent BDC decoder memory debt:** research `decode_all()` in blob `ed3165ce7fea3021e12220e409d972dd3cffd5b9` retains all member byte buffers. `MAX_MEMBERS=4096` and per-member `MAX_DECODE_UNIT=8 MiB` admit an analytic **32 GiB** maximum cumulative output before shared contexts/allocator overhead. This is a source-derived upper bound, not measured RSS or a claim about the released reader; future productization must provide globally bounded streaming/owner processing.

## PARETOBONK / counterfactual discriminator
The cheapest discriminating observable was actual whole-container bytes **after real Builder framing**, not hypothetical per-blob headers or more friendly BDC variants. A zero-source-change one-file r24 wrap already refutes a proposed simple compatibility-first product path in Boundary. More simulation would not overturn this exact measured fact. This is a scoped **scientific negative** and changes the architecture choice; it earns **no discovery-policy rewrite** from one case and **zero product/release credit**.

## Coordination and executable next action
Owner #236 retains frozen BDC science; owner #239 retains the canonical r24 control. This isolated child owns only O16, and it has not modified their source or the shared `docs/discovery/STATE.json`.

The cheapest next **unclaimed** frontier is a direct-format/admission feasibility bound that avoids redundant r24 envelope/index overhead while using the same authenticated filesystem/Member-SHA facts. It must evaluate exact original-file access semantics (not opaque file semantics), cold selective reads, total reader work/RSS, integrity and recovery, generic bounded admission, create CPU/wall and complete bytes against *both* authentic r24 and pinned Zstd controls. Do not implement a new codec/format before deriving a path capable of preserving at least the 669-byte Boundary deficit under comparable complete semantics. Baseline may win. No merge or release promotion from O16.
