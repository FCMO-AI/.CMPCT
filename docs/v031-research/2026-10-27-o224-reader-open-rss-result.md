# O224 — Source-exact Reader RSS custody correction: inherited child HWM; phase certificate invalid

2026-10-27 UTC. **Original hosted science and independent negative audit**, no shipping Reader, benchmark, format, release, ABI or security invariant change.

## Immutable prereg, source, hosted controls

- Preregistration (before implementation): `c630c7e15637c51895d70ad7ef3f8fd96f1a3214` ([locked question](2026-10-27-o224-reader-open-rss-prereg.md)).
- Inherited source owner J24C02 [#569](https://github.com/FCMO-AI/.CMPCT/pull/569) `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`; Reader blob **`dbd4ac576a05a47eae97e1e40de89cf1de440516`** unchanged. Research is stacked on O223 [#587](https://github.com/FCMO-AI/.CMPCT/pull/587).
- Final [O224 hosted run #40492849892](https://github.com/FCMO-AI/.CMPCT/actions/runs/40492849892), result-bearing source/test HEAD **`4e4f4d7165745f0270c2766e18a73aa354bd09bd`**, specialized `scientific-phase-memory` **SUCCESS**, actual independent auditor **`PASS_NEGATIVE_STAGE_INVALID`**. Original [artifact #12729755312](https://github.com/FCMO-AI/.CMPCT/actions/runs/40492849892/artifacts/12729755312), ZIP SHA256 **`ad1fbd332c7e60e10befa19bfde00d7a05def7161d0c64964e57f59151e20631`**, archive CRC verified independently.
- **112 original fresh-child receipts**: 72 uninstrumented strict vs unsafe omitted-validation control, 36 instrumented strict, four traced controls; 12 archive profiles; exact archive fingerprints and final `read_range` byte checks. Independent auditor checked source, 112 samples, 544 metric assertions, all preregistered decision logic and rejects missing/duplicate reports. Original runner was Ubuntu 24.04 / Python 3.12.15; exact Reader installed independently.
- Prior [O224 first run #40492150014](https://github.com/FCMO-AI/.CMPCT/actions/runs/40492150014) preserved rather than overwritten. Its first auditor **correctly failed** when Linux `VmHWM` snapshots were observed to decrease slightly between same-process stages. The corrected auditor and classifier explicitly **invalidate** phase ownership instead of smoothing samples, preserving the original preregistered no-nonmonotonicity condition.

## Decisive independent infrastructure finding

Original O223 [artifact #12723574557](https://github.com/FCMO-AI/.CMPCT/actions/runs/40484142645/artifacts/12723574557) contains **180 child PIDs but six globally nondecreasing `resource.getrusage(RUSAGE_SELF).ru_maxrss` values** (174 ties, five increases, zero decreases). Its parent builds and fully verifies each successive large archive before spawning children; `ru_maxrss` of the new exec image can inherit the parent's high-water. This made the older ~453–497 MiB child-Reader headline unsupported as a genuine per-exec memory observation, and also invalidated the zero-difference `open_only` vs `read` memory inference.

An **independently hosted** source-exact fork/exec falsifier in the final O224 workflow touched 256 MiB in the parent and launched fresh children. The next child reported **`ru_maxrss` growth +262,268 KiB** versus **its own `/proc/self/status:VmHWM` growth +116 KiB**; after parent release, the inherited `ru_maxrss` did not drop. Classification: **`RUSAGE_CHILD_INHERITS_PARENT_HWM`**. This is infrastructure/evidence-enablement truth, **not** a Reader product defect.

## Genuine installed-Reader post-open VmHWM, uninstrumented controls

At 262,144 references, source-exact new-child Reader-open median VmHWM:

| Valid r24 layout | S_CHUNKS | S_CDC |
| --- | ---: | ---: |
| Repeated single RAW owner | 27,260 KiB | 49,352 KiB |
| Eight RAW owners | 27,048 KiB | 49,284 KiB |

These values are directly observed per-exec child `/proc/self/status`, **not** inherited parent ru_maxrss. Reader open and selective tail byte pass on original signed files. This is a scoped correction of O223's inherited memory measurement, not a universal RSS bound. Other index sizes, codecs, generations, hostile inputs, readers and platform combinations remain outside this sample.

The deliberately unsafe **research-only** no-validation counterfactual saved only **+160 / −68 / +172 / −32 KiB** across those four layouts, nowhere near the frozen >=64 MiB requirement; decision **`VALIDATOR_HWM_NOT_PROVEN`**. It does **not** justify weakening or removing strict ordinary Reader admission.

## Crucial negative: stage allocation fails its preregistered invariant

Among the **112 samples**, **26 exhibited nonmonotonic within-process sampled `VmHWM`**, including **all 12 critical 262,144-reference instrumented original samples**. Largest backward movement on the original first hosted court was 308 KiB. The prospective protocol explicitly invalidated any such phase allocation. Thus the final, correct result is:

- **`INVALID_STAGE_HWM_SEQUENCE`**; no dominant phase certified.
- **`VALIDATOR_HWM_NOT_PROVEN`**; no material HWM reduction from omitting strict validation.
- **`PASS_NEGATIVE_STAGE_INVALID`**; the independent auditor approves the integrity and honest negative classification, **not** the proposed phase attribution.

Exploratory `smaps_rollup` and current `VmRSS` indicate the largest sampled allocations occur near MessagePack parsing (especially nested CDC descriptors), while the strict validator changes very little current sampled RSS. The phase-specific numbers are **non-qualifying diagnostic leads**, not a causal certification and not product evidence. No posthoc smoothing, adjusted materiality criterion, workload substitution or newly asserted performance claim is permitted.

## Limits, falsifiability and handoff

Preserve O223's exact byte/CPU/wall observations separately; this correction targets **RSS provenance only**. Preserve O216–O219's scoped mechanism evidence and hard admission guarantees. The next **cheap, independent, prospectively locked** step is to compare reproducible live/private memory after MessagePack decode with an independently rooted allocation tracer under the same wire, without relying on decreasing `VmHWM` stage readings. Investigate packed/lazy descriptor decoding only if it survives genuinely heterogeneous indexes and all decoder work/bytes/CPU/physical admission charged. Simpler may win; a zero-change product remains the baseline.

Owner notifications: [#587](https://github.com/FCMO-AI/.CMPCT/pull/587), [#569](https://github.com/FCMO-AI/.CMPCT/pull/569), [#583](https://github.com/FCMO-AI/.CMPCT/pull/583). The Discovery Engine was used to choose the lowest-cost falsifier; no reusable policy mutation was earned, no `STATE.json` shared write was attempted while #574 owns its reconciliation. **No merge/release/version/format change.**
