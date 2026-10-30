# J24G69 — source-exact same-input DELETE replay comparison

Date: 2026-10-30 UTC.
Status: **DECISIVE SCIENTIFIC NARROWING: GENERAL_SUBSUMES_SIMPLE under the preregistered *mechanism-level* cost rule.**
No product source change, format mutation, release, or product-performance claim.

## Immutable prediction and ownership

[Preregistration](2026-10-30-j24g69-sameinput-delete-prereg.md) was committed FIRST at SHA 4305d9a1f98ff6cf921bbe8ea24dd1dec2fa9de8. This independent child of [#811](https://github.com/FCMO-AI/.CMPCT/pull/811) compares two already-existing research algorithms on identical in-memory 63-operation DELETE histories. Source: #811 HEAD afdce3f3e598db402deba4c2dfde50a8de3f3e10, simple source blob dde3bbf0f4816adcfb552b83e579d8de09c86c19, original source blob 03743ca2a06c022c2ec64243a90fe373cf91e899. General contender is the **unchanged and SHA-attested** [#808](https://github.com/FCMO-AI/.CMPCT/pull/808) HEAD 41cd7f88d9fede55a495f36e78126b26eff85880, oracle blob 7657a41d11f2b3c8136c0b69cfe62401f9b19ccb.

The preregistered economic discriminator: if the general factoring implementation is within 15% wall time of specialized bisect/pop at N=2,048, D=63, middle-deletion on >=2/3 hosts and uses no more than +1 MiB measured traced peak allocation, prefer one general mechanism instead of adding a separate product fastpath. Conversely, >=20% simple win on >=2 hosts with bounded traced peak would justify preserving the specialized productization candidate. No timing thresholds or fixtures were revised after observing results.

## Original exact-head provider evidence

[Original Actions run #41019980941](https://github.com/FCMO-AI/.CMPCT/actions/runs/41019980941) finished **SUCCESS on Ubuntu 24.04, macOS 14 and Windows 2022** on exact measured HEAD 1d748e03babae9c201e3b14af3b312013a8ce050. Each job completed the source attestation, Python 3.11 installed checkout, 9 cases, same-input exact parity and detached receipt/tamper arithmetic.

Original provider ZIP artifacts independently downloaded and audited outside the runners:
- [Ubuntu #12960658365](https://github.com/FCMO-AI/.CMPCT/actions/runs/41019980941/artifacts/12960658365), provider ZIP SHA-256 203ac93b1d09735ade5615d62984f501d5525081e8116e33bae1ae8f0a68274d; full result-file SHA-256 928a457f4d936bbc1508e776e90d24865ce004d3b08f8ff308ebb6b618affdeb.
- [macOS #12961575871](https://github.com/FCMO-AI/.CMPCT/actions/runs/41019980941/artifacts/12961575871), ZIP SHA-256 1e40617e427eba64838b9255faa2c488e7e436bb801d0ba3e4d46e00acf5ea0d; result SHA-256 b61c78ae4f676dabc0f2b7e9f9c62640dfc271577a9b6f71f8bad4d3ae8821bf.
- [Windows #12960723213](https://github.com/FCMO-AI/.CMPCT/actions/runs/41019980941/artifacts/12960723213), ZIP SHA-256 e8287361e47f774ae9e0e6d11baba610e71395c09a52844d481312d7160fc822; result SHA-256 c471ad7a2481ad4d2eae9d8569c77cc712f18c59a47cd8bbe11b55595c69eead.

The detached local post-download auditor compared each ZIP to GitHub's provider SHA, read the original JSON, independently recomputed raw SHA, nine case medians and ratios, ensured all 648 raw measured rows' output-index hashes matched the corresponding reference and competitor blob identity, checked input preservation and ABBA block count/order. It rejected a modified sample's checksum. This is independent of the runner's in-workflow arithmetic but **not an independent physical archive interpreter**; the workload is synthetic and data generation is owned by the research script.

## Measured reference case — N=2,048 surviving, D=63, middle DELETE

Both algorithms include their own deep-copy, admissibility checks, final representation reconstruction and CPU/wall measurements. Startup is excluded, and both consume identical within-host input MessagePack.

| Host | Simple median wall | General median wall | General/simple | Prospectively classified |
|---|---:|---:|---:|---|
| Ubuntu | 4.292 ms | 4.571 ms | 1.0651x | General within 15% |
| macOS | 4.732 ms | 6.352 ms | 1.3424x | Simple faster; noisy |
| Windows | 6.039 ms | 6.576 ms | 1.0890x | General within 15% |

**Decision: GENERAL_SUBSUMES_SIMPLE for immediate architecture priority, 2/3 hosts.** This is NOT a claim that general executes faster. Simple is marginally faster in all three reference cases; on Ubuntu and Windows its 6.5% and 8.9% gains do not pass the 20% carrying-cost discriminator. The general approach covers mixed ops and sparse signed metadata, while the simple path refuses them.

## Complete N/position adversarial sweep

Shown values are median general/simple wall ratio; >1 means simple faster.

| Host | 2,048 front/middle/tail | 8,192 front/middle/tail | 32,768 front/middle/tail |
|---|---|---|---|
| Ubuntu | 1.0596 / 1.0651 / 1.0770 | 1.0853 / 1.0653 / 1.0844 | 1.0716 / 1.0733 / 1.1092 |
| macOS | 1.2008 / 1.3424 / 1.1183 | 1.1465 / **0.9861** / 1.0088 | 1.0382 / 1.0189 / **1.2402** |
| Windows | 1.0810 / 1.0890 / 1.0777 | 1.0867 / 1.0791 / 1.1061 | 1.1126 / 1.1164 / 1.1283 |

Nine exact cases per platform; 216 raw timings per host (648 total) across alternating ABBA blocks: 8 blocks/position at 2,048, 6 at 8,192, 4 at 32,768. All 27 cases preserved original MessagePack semantic parity and unmodified source input. General supports signed sparse metadata in the semantic adversary and specialized DELETE correctly falls back to original. Unsupported operation errors retain parity.

## Strongest counterexamples and cost limits

- Mac 2,048/middle shows a **34.24% apparent** benefit for simple, but its eight per-block paired ratios span **0.576–1.599**: substantial instability, not a defensible universal 34% win.
- At Mac 8,192/middle the general contender slightly wins (ratio 0.9861); Mac 32,768/tail favors simple materially (1.2402). These are preserved contradictions, not threshold gardening.
- Peak tracemalloc values are practically identical between contenders, differing **80 B** in every case; both peaks are dominated by deep-copy input. The 1 MiB preregistered admission test passes, but the instrument has insufficient sensitivity to support an RSS or production memory-efficiency claim.
- No physically emitted CMPCT archive, native xattr restoration, hardlinks, footer recovery, 64th checkpoint, Reader integration/monkeypatch, RSS, cold I/O, build/read/extract, ZIP/Zstd or release-floor measurement was performed in this investigation.
- Historical J24G67 14.78–16.23x **Reader-monkeypatch** and J24G64 7.64–9.31x **mixed replay-only** results remain separately scoped. This same-input direct comparison must not be conflated with either.

## Decision, counterfactual, and owner continuity

The simple specialization does **not** currently pay for a separate product fastpath, but retains its measured research seed and fallback tests. Prioritize the general [#808](https://github.com/FCMO-AI/.CMPCT/pull/808) mechanism under the legitimate Reader and safety owner [#795](https://github.com/FCMO-AI/.CMPCT/pull/795), and use [#811](https://github.com/FCMO-AI/.CMPCT/pull/811) as lower-complexity adversarial control. [#810](https://github.com/FCMO-AI/.CMPCT/pull/810) and [#813](https://github.com/FCMO-AI/.CMPCT/pull/813) retain physical signed-metadata/checkpoint responsibilities. No collision or sibling mutation occurred.

Next valuable gate: installed Reader A/B against the same genuine physical archive, with full correctness, xattrs, hardlinks, hostile footer recovery, checkpoint64, CPU/wall, RSS and complete stored bytes. The simple path can be reconsidered if that gate reveals stable significant *product-level* gains. No change to shared Discovery STATE, owned by #574; no evidence-backed policy rewrite earned. A transferable prospective method is to require same-input, same-layer head-to-head competition before choosing between two measured seeds from disjoint benchmarks.

**Product evidence: no change. Research evidence: 648 raw observations, 3/3 hosted success, 3 original provider ZIPs independently audited; decision changed. CI/evidence enablement: source exactness and hostile receipt checks. Unmeasured: physical and product integration/release. Promotion credit: zero.**

## Post-result paired-block noise sensitivity (2026-10-30 UTC)

A **separate local audit of the downloaded original ZIP receipts** inspected the eight ABBA pairs for the preregistered N=2,048 middle-delete case. This is exploratory sensitivity of the existing measurements, **not a new preregistered test nor a replacement for the frozen median rule**. Per-block ratio uses each block's median factored wall divided by its median simple wall, rather than dividing whole-host pooled medians.

| Host | All eight per-block factored/simple ratios | Empirical block bootstrap interval (2.5–97.5%) |
|---|---|---|
| Ubuntu | 1.068, 1.060, 1.055, 1.020, 1.077, 1.073, 1.064, 1.071 | 1.055–1.076 |
| macOS | 1.155, **0.576**, 1.025, **1.599**, **0.725**, 1.376, 1.417, 1.432 | **0.725–1.503** |
| Windows | 1.080, 1.102, 1.089, 1.094, 1.083, **0.951**, 1.050, 1.079 | 1.056–1.096 |

Bootstrap procedure: on the **unchanged original block samples**, draw eight blocks with replacement 10,000 times via Python `random.seed(27)` independently per host, divide each resample's median of the eight factored block medians by its median of the eight simple block medians; report empirical 2.5/97.5 percentiles. This is a **block-resampled sensitivity interval**, not a formal confidence interval about all machines or runs. It treats blocks as exchangeable even though ABBA order, temporal drift and filesystem caches may be dependent; only eight blocks exist. On this observed batch the fraction of resamples with ratio <=1.15 was Ubuntu 1.000, macOS 0.3909, Windows 1.000. Do not overinterpret those proportions as calibrated probabilities of future host behavior.

**Causal refinement:** Ubuntu and Windows show a narrow and fairly stable 5–10% specialized edge, whereas macOS' 34% pooled-median advantage is not robust to plausible resampling of the same eight blocks. Thus the preregistered 2/3 architectural economy decision is not a claim that the simple approach never wins. A later fully installed same-file Reader court can overturn it. The previous J24G67 15× standalone speedup against original remains valid, but does not justify an additional separate production path against the stronger general control by itself.
