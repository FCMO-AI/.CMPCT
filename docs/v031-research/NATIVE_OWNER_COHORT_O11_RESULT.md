# O11 — native owner-bounded grouped extraction: hosted result

Date: 2026-10-24 UTC
Status: **RESEARCH CANDIDATE VERIFIED ON LINUX — NOT A SHIPPING EXTRACTOR**

## Source / prospective custody

- Repository: `FCMO-AI/.CMPCT`
- Original source-exact PR parent: #335 `501a063ee665950b4363f532c0a044f4ef3ee4eb`.
- Preregistered **before implementation** in `NATIVE_OWNER_COHORT_O11_PREREG.md`, commit `1c7fdad74d8a4edae3a2353c7c67649f222a97ec`.
- Measured implementation HEAD: `9bf668b2c93ca89a9a9475d971fd4015e36eec9b`.
- New experimental C source Git blob `7cfb914bb254ab240a8f12165b67e0cb344bb56a`.
- GitHub Actions [run 40078228541](https://github.com/FCMO-AI/.CMPCT/actions/runs/40078228541), job `120826112741`: **SUCCESS**.
- Hosted original artifact [12553887202](https://github.com/FCMO-AI/.CMPCT/actions/runs/40078228541/artifacts/12553887202); exact ZIP SHA-256 **`3fb332be0f47ee98b5f28925980bca53763b5f7d27614edb82242119fc0e237c`**, identical to GitHub-reported digest. Embedded `result.sha256` matches the unmodified raw `result.json`.
- 72 source-exact full output trees over three cohorts; 3 repeated balanced blocks × 8 invocations × 3 cohorts. Each output leaf SHA-256 was compared independently with the original Builder input. **No mismatch**. Raw 72 rows are in original artifact, not recomputed synthetic data.

## Charged whole-C-consumer results

All four arms use the **same installed CMPCT Python Builder**, the **same archive per cohort**, and **the same single Rust native shared library** on one Linux runner. Times include process startup, archive opening, native API operations, physical file creation and independent subprocess completion. Per-process RSS uses `/proc/self/status:VmHWM` instead of inherited `getrusage` maxima. Values below are medians of six observations per mode, not product-wide forecasts.

| Cohort / arm | Wall ms | Child CPU ms | Process VmHWM KiB |
|---|---:|---:|---:|
| PACK 512: O7 eager serial | 185.075 | 184.790 | 3,390 |
| PACK 512: O7 eager group | 19.360 | 19.148 | 3,426 |
| PACK 512: O10 stream | 168.666 | 168.430 | 3,378 |
| **PACK 512: O11 bounded owner** | **17.244** | **17.039** | **3,398** |
| PACK 2048: O7 eager serial | 979.779 | 979.252 | 4,946 |
| PACK 2048: O7 eager group | 76.219 | 75.971 | 5,202 |
| PACK 2048: O10 stream | 490.017 | 489.708 | **4,322** |
| **PACK 2048: O11 bounded owner** | **68.331** | **68.093** | 4,632 |
| RAW 128 × 256KiB: O7 eager serial | 32.459 | 32.264 | 35,906 |
| RAW 128 × 256KiB: O7 eager group | 32.547 | 32.334 | 35,968 |
| RAW 128 × 256KiB: O10 stream | 16.546 | 16.338 | 2,660 |
| **RAW 128 × 256KiB: O11 bounded owner** | **16.530** | **16.332** | **2,648** |

Archived input characteristics:

- PACK 512: 512 × 768 B = 393,216 reconstructed bytes; CMPCT archive **8,375 B**; **2** actual Zstd-owner batch operations.
- PACK 2048: 2,048 × 768 B = 1,572,864 reconstructed bytes; archive **33,051 B**; **7** actual Zstd-owner batch operations, independently exercising multiple owners.
- RAW 128: 128 × 262,144 B = 33,554,432 reconstructed bytes; archive **33,565,260 B**; **0** batch operations and 128 streamed fallbacks. The absence of grouping is *required* for the RAW negative/control.

**Measured decision:** against unchanged streaming O10, bounded-owner O11 is **9.78× faster** on PACK 512 and **7.17× faster** on held-out PACK 2048; on RAW 32MiB, wall time is effectively tied (16.530 vs 16.546 ms) and caller RSS remains at the O10 scale (2,648 vs 2,660 KiB) rather than O7's ~35,906 KiB (**13.56× larger** than O11). All three balanced rounds preserve the PACK timing advantage; no trial was excluded.

O11 is also ~11% faster than the eager group consumer on both PACK cohorts under these specific test-client semantics, but that is **not isolated decoder speed**: allocation and file-publication order/strategy differ, and six observations are insufficient for a universal superiority claim. Source archive bytes are identical across modes, not newly compressed.

## Boundedness, verified semantics and counterexamples

- O11's largest actual staged output in either PACK cohort: **261,888 bytes per owner operation**; inherited ABI imposes <=16MiB output, <=1,024 requests and <=16MiB physical compressed/decoded source. Caller stage is freed after every group, while a separate 64KiB buffer handles fallbacks. The native decoded owner and compressed payload can coexist with staged output; the **true complete process-memory ceiling is larger than stage alone**.
- Hostile preexisting leaf test: **PASS**. O11 refused a symlink leaf pointing to an external canary, which remained byte-identical. This does not prove safe arbitrary nested filesystem extraction.
- **Negative:** on PACK 2048, O11 uses **4,632 KiB**, 310 KiB more than O10 streaming's 4,322 KiB. The buffer/metadata costs are real; this is a Pareto tradeoff, not a free RSS win across all data.
- On PACK 512, client RSS is nearly tied across arms (3,378–3,426 KiB), so its small differences are not material memory evidence.
- On RAW 32MiB, O11 does not batch: no implication that Zstd batching universally improves arbitrary content.
- Complexity: the simple owner grouping loop is O(number_of_entries²) in the worst case (capped 4,096 entries), and the Rust Reader has separately budgeted parse/codec allocations. No unbounded global data cache, but do not advertise constant total memory independent of all metadata.
- Output files are committed sequentially; on later failure previous leaves may remain. No whole-tree atomic publication, complete RAW SHA verification across mutable source, source descriptor/namespace race safety, filesystem metadata semantics or Windows/macOS tests. It is a **research-only POSIX root-level consumer**, not productized archive extraction.
- Raw `result.json` exposes C client mode labels `serial` and `group` for the two O7 controls; its summary labels those arms `serial_eager` and `group_eager`. These are unambiguous aliases, not two different runs.

## Independent audit and counterfactual

Separate read-back of the original ZIP verified its SHA-256, embedded JSON digest, all 72 rows' source SHA / logical byte / member identity, six samples per mode/cohort and batch bounds. In each of 3 rounds, O11's wall was 0.101–0.102× O10 on PACK 512, 0.139× on PACK 2048, and approximately tied on RAW. Results are observation-specific.

The cheapest earlier discriminator is a *same-archive* PACK activation check plus one RAW-negative sample: it establishes both mechanisms execute and avoids a misleading "no batching" benchmark like inherited O8. A second lesson is the user-facing value of charging **both** owner's transient buffer and the broader Rust decode budget rather than presenting a 64KiB client buffer as whole-process memory.

**Decision:** ADVANCE research candidate; keep production promotion BLOCKED. Next meaningful gate is an authentically verified, descriptor-root whole-tree materializer with global decode/output budgets, source-mutation guarantees and adversarial filesystem semantics—not tuning a few more milliseconds from this evidence client. No normative Discovery Engine or release-policy modification earned.
