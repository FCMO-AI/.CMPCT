# O198 — source-exact codec-aware held-out CDC falsifier

**Date:** 2026-10-26 UTC  
**Status:** DECISION-CHANGING RESEARCH NEGATIVE; NOT PRODUCT/RELEASE EVIDENCE.  
**Ownership:** Existing Draft PR #516; native owner PRs #228/#501 and published v0.30.0/r24 unchanged.

## Prospective question and controls

[Preregistration in PR #516](https://github.com/FCMO-AI/.CMPCT/pull/516#issuecomment-6422392213), comment `6422392213`, predates implementation and hosted execution.

O197 proved genuine native CDC chunk reuse after insertion on high-entropy siblings using an **uncompressed unique-byte + 64 B/header proxy**; native lost on many unshifted edits. Its optimistic representation result could collapse once actual independently compressed payloads and logical references are charged. O198 asks whether the same source-exact C mechanism retains an advantage against **the best of fixed256, fixed512, fixed1024** on new entropy/repetitive/mixed families using **per-chunk zlib-6 compressed bytes** rather than raw bytes.

This is an exact C source experiment, not a `CMPCT.Builder`, `S_CDC`, final archive, codec-portfolio or official benchmark.

## Source and hosted result

- Exact experimental head: `dd4d7214e4f0e68002cb34006ba261861b51786a`.
- [Result-bearing GitHub Actions run 40366867609](https://github.com/FCMO-AI/.CMPCT/actions/runs/40366867609), `source-exact-zlib6-proxy` **SUCCESS**, all result-bearing steps completed.
- [Raw artifact 12671615363](https://github.com/FCMO-AI/.CMPCT/actions/runs/40366867609/artifacts/12671615363), download SHA-256 **`2422bdc6e8671623813b2d68553020c3cdea9a0d3da38df0d07cc6891a92c115`**, includes `source.txt`, `output.txt`, `results.json`.
- Source-exact native C: `native/cmpct_cdc.c` Git blob **`a6253beece20ce8aad3cdb605a6d9fcaa50d9364`**.
- Reused, unchanged authenticated native wrapper: `research/o197_native_cdc_mutation_court.py` blob **`9bd08886560e0845d73cf7d0882d9b12b49d7962`**.
- New `research/o198_cdc_codec_aware_oracle.py` blob **`bf2329647e31987e2a21314de65555c9d648310a`**. Workflow `.github/workflows/v031-o198-cdc-codec-proxy.yml`.
- 3 deterministic unseen structural families × 2 seeds/family × 3 offsets × 2 edits = **36 paired scenarios**. Each input and sibling is 3 MiB; originals and variants are identical across policies.
- Source SHA-256 collision guarded for every chunk; each physical chunk independently zlib-inflated and independently indexed complete reconstruction of both logical files verified. **No mismatch**.

### Honest charged micro accounting

For each original+sibling pair:
```
proxy_bytes = sum(zlib.compress(unique_chunk, level=6) sizes)
            + 64 B * number of unique physical chunks
            + 32 B * number of logical chunk references
```
Also recorded 16 and 64 B/reference sensitivity, largest decode unit, one-pass CPU and wall (not repeated enough to credit timing). Fixed control is chosen *retrospectively per scenario* from three sizes, so it is a deliberately gifted strong control, **not** a claim of practical generic selection. The non-equivalent control `zlib.compress(base+sibling,6)` is verified for exact reassembly and recorded separately; its monolithic streaming semantics are NOT a random-access competitor and it is not part of the winner decision.

### Measured outcomes (CDC savings versus best fixed proxy)

Positive means less counted storage for CDC; negative means CDC exported more bytes.

| Held-out structure/edit | N | CDC wins / losses | Median savings | Range |
|---|---:|---:|---:|---:|
| High-entropy / 1-byte shift | 6 | **6 / 0** | **+19.051398%** | +5.962909% to +44.770819% |
| High-entropy / 1-byte overwrite | 6 | 1 / **5** | **−11.584506%** | −21.490241% to +3.637816% |
| Repetitive / shift | 6 | 4 / 2 | +1.586828% | −17.632081% to +1.849803% |
| Repetitive / overwrite | 6 | 0 / **6** | **−30.991268%** | −31.087420% to −5.716112% |
| Mixed entropy / shift | 6 | 2 / 4 | **−0.001037%** | −22.714588% to +0.001497% |
| Mixed entropy / overwrite | 6 | 0 / **6** | **−50.146993%** | −58.211169% to −21.309657% |

**Main negative:** the useful shifted high-entropy CDC mechanism is **not** a universal win once compressed chunks and reference counts are charged. Repetitive and mixed files sharply narrow the payoff. In particular, an admission classifier based on *shift detected* alone is insufficient; structural compressibility and stronger fixed controls change the ranking. An entropy-only gate also cannot separate shifted from unshifted mutations in high-entropy data.

### Independent adversarial checks

An independently implemented local C reference rebuilt the historical SplitMix64 gear table from its published seed; its first and last constants matched the authentic source. Before looking at O198 results, this reference reproduced the **full O197 historical 72-case sign counts and medians** (−14.060593% / 33 of 36 losses for overwrite; +19.791695% / 28 of 36 wins for shifts), an important algorithm-fidelity cross-check. The local independent runner then reproduced **all 36 O198 primary savings bytes, percentages, and selected stronger fixed-control names** exactly versus the downloaded hosted JSON. This local check is independent of GitHub's build path, though it reuses the same mathematical CDC specification and deterministic workloads. No second hosted OS/compilation or product implementation is claimed.

For the primary conclusion, changing the modeled logical reference charge from 32 B to 16 B or 64 B preserved each family's median sign and win/loss count in the local independent analysis. The result is not a fragile choice of 32 B/entry.

## Scientific decision, strongest counterargument, and disposition

**Decision:** preserve CDC as a useful exact opt-in mechanism for shifted high-entropy relatives; **do not enable its C helper unconditionally in the distributed product** on this evidence. O196/O196b already proved that the helper is currently *absent* from the ordinary wheel and reproduced ABBA source paths; O198 does not revise that truth. The shipped fixed fallback is allowed to win.

**Strongest counterargument/uncertainty:** a full CMPCT codec portfolio may compress each individual chunk differently from zlib-6, and metadata/index layout may change the ranking. The corpus contains just two seeds per structural regime, not arbitrary field data; 3 positions per seed are dependent perturbations. The ideal per-case choice exploits hindsight and assumes sibling relationships are known. No cost of discovering candidate relatives, metadata indexes, actual CPU/RSS/temporary I/O, cold/selective reads, native wheel loading, final archive storage or ZIP64/portability was measured. The standalone solid-zlib control has weaker/random-access-incompatible semantics. This is **research proxy** evidence only, and no product speedup, release credit, or general compression ratio should be asserted.

**Counterfactual discriminator:** one compressed-chunk, mixed-entropy overwrite/shift control would have killed the proposed *unconditional* native promotion before paying for packaging or release parity. The prospective signal is not just an insertion; it requires evidence that shifted reuse cannot already be encoded cheaply by ordinary compression. This is a local lesson, not grounds to rewrite Discovery Engine or release law.

**Next cheapest action:** before another native default/product benchmark, preregister a tiny **prospective, generic and fully charged admission test** on truly unseen paired and hostile *unrelated* files. Account for pair discovery, sample/scan/index CPU and bytes, false positives, false negatives, optional native buffer copies, and workload-family generalization. Retire default native if no cheap general signal survives. If the signal survives, proceed to *real installed* Builder/Reader complete-archive, repeat-CPU/wall, peak RSS/temp-I/O, read/selective amplification, integrity and multiplatform packaging evaluation. Preserve official O185 ABBA red evidence and O175 cache scan-thrash debt.

No production source, format, CI comparator, frozen benchmark, evaluator threshold, release lock, version, other PR branch or shared discovery state was modified by this research.
