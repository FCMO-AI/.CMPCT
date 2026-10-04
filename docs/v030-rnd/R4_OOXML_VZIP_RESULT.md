# v0.30 R4 Office: existing S_VZIP on content-valid OOXML

**Status:** POSITIVE REPRESENTATION SEED / CONTENT-DRIVEN ADMISSION + HOSTILE FALLBACK REQUIRED  
**Authority branch:** `agent/v030-authoritative-integration`  
**Source head:** `96702aac39a2f8f617d5788ef101ec1a35778f6e`  
**Hosted run/job:** `34637723567` / `103389637372` — SUCCESS  
**Artifact:** `10278724244`, digest `sha256:af3bab9ef381498ff7c84202648e3631c623c2ff65d17991c92fe081c16cbc99`  
**Shipping credit:** none

## Mission lock

Office is the single largest frozen Genesis density loss for v0.30 versus accepted v0.29: about `+9.49 MB`. Historical physical attribution shows Office is genuinely stream-federation-heavy: about 82% of logical bytes are conservatively dependent on the v0.25 stream pool. The canonical r24 reader already understands authenticated/range-aware `S_VZIP`, but the r24 Builder's discovery path defers only `.zip` and `.whl`; valid OOXML packages named `.docx`, `.xlsx`, and `.pptx` therefore bypass an existing representation that is already readable and native-conformance-gated.

Hypothesis:

> If valid OOXML containers are routed through the unchanged existing `S_VZIP` representation, a large fraction of the Office density deficit disappears without inventing a new reader-visible mechanism.

Disproof required exact reconstruction. The oracle built two path-length-matched copies of the same frozen Office workload: a non-virtual control with OOXML renamed to an equal-length unknown suffix, and a probe with the same six files renamed to equal-length `.zip` paths solely to route the unchanged Builder through existing `S_VZIP`. Both archives were extracted, names restored, and required to reproduce the original content tree exactly. This is an instrumentation trick, not a suffix-based product proposal.

## Result

| Metric | Non-virtual control | Existing S_VZIP probe |
|---|---:|---:|
| complete r24 archive | **15,445,474 B** | **6,460,534 B** |
| creation wall | **0.0921 s** | **1.7890 s** |
| extraction wall | 0.0165 s | 0.0391 s |
| S_VZIP logical files | 0 | **6** |
| recipes | 0 | **6** |

Net saving from representing the six existing OOXML containers with the already-defined S_VZIP semantics:

- **8,984,940 B**;
- **58.17%** of the non-virtual control archive;
- exact source-content reconstruction after restoring original names.

This is almost the entire ~9.49 MB Office deficit identified after Genesis. It is not yet a same-product final Office result because the probe changes paths to enter the existing discovery branch and does not charge a generic content-signature scanner. But the magnitude is far beyond threshold noise: the representation itself is clearly relevant.

Creation cost rises by ~1.70 s in this diagnostic. That cost must be measured again with a bounded signature/central-directory gate because the current experiment deliberately forces all six containers into full recipe construction. Even this unoptimized cost is qualitatively different from returning to the very expensive mature v0.29 search frontier.

## Hostile result: real Builder hardening debt

The receipt-preserving v2 oracle also fed an invalid file beginning with ZIP-like bytes to the current suffix-routed `.zip` path. It was **not virtualized**, but the Builder raised:

`BadZipFile: File is not a zip file`

instead of delegating the file to opaque ordinary storage.

That is a real hardening debt. A future content-driven scanner must treat parse failure as a clean non-candidate/fallback, not as a build abort. The first v1 OOXML oracle went red precisely because this hostile control ran after the useful Office measurement and erased the receipt; v2 preserves both facts independently.

## What this proves

The evidence supports a research-only content-driven admission experiment for the **existing** S_VZIP representation:

1. all six frozen Office OOXML containers reconstruct exactly through the unchanged existing representation;
2. the physical saving is ~8.98 MB, enough to explain almost all of the Office gap;
3. no new reader opcode/mechanism is necessary for this seed;
4. native/range semantics already exist for S_VZIP and therefore provide a much shorter path to product evidence than creating a new Office-specific reader surface;
5. the current filename-suffix discovery boundary, not the underlying representation, is a major blind spot on this workload.

## What this does not prove

No shipping or canonical-format credit is granted.

The next implementation must **not** dispatch on `.docx/.xlsx/.pptx` names. Admission must be content-driven and bounded: cheap ZIP signature/structure observation, safe central-directory validation, exact recipe proof, then economic competition against opaque storage. Parse failures must fall back cleanly. The experiment must also preserve current member/range locality, recovery, native parity and filesystem semantics.

The probe does not prove that every valid ZIP-like container should be virtualized. Existing Builder economics and the historical v0.25 thresholds show why that would be dangerous: some already-compressed containers have no reusable streams and can lose after recipe metadata/proof work. Content recognition is only an opportunity gate; representation still has to win.

## Decision

**Advance existing-S_VZIP content discovery as the current Office R4 seed.**

The decisive next experiment is a research-only wrapper that:

1. sniffs all regular files by bounded content, independent of extension;
2. safely validates only plausible ZIP containers and catches malformed candidates as opaque fallback;
3. routes valid candidates through the unchanged S_VZIP path;
4. preserves original logical paths externally;
5. charges observation/proof CPU, bytes inspected and recipe work;
6. runs Office plus unrelated ZIP/media/already-compressed hostile controls;
7. compares complete archive bytes, create/read/selective work and failure behavior against unchanged r24/v0.30 substrate.

Only after that passes should the discovery change be considered for `src/cmpct/builder.py`. The result is a discovery/productization opportunity, not permission to special-case Microsoft Office formats.
