# ONE-G0.2 — fused multi-Law opportunity gate hostile review

**Date:** 2026-09-08  
**Status:** pre-result hostile review  
**Experiment:** `ONE_G02_MULTI_LAW_GATE`

## Bob / hostile reviewer

### 1. Fingerprints are not proof

The gate treats repeated FNV64 values only as nomination evidence. A collision may spend downstream work but may never emit an exact-reuse Law without byte-exact proof. Any future integration that treats the fingerprint as identity invalidates this experiment's safety argument.

### 2. Zero relations must not duplicate simpler Law

A dominant add8 delta of zero is a run/repeat shape. A dominant xor value of zero at the bounded lag is repeat/reuse evidence. Launching arithmetic/resemblance search for those cases would inflate candidate count while pretending to discover additional information. The candidate explicitly suppresses those duplicate nominations.

### 3. Retained payload accounting is a lower bound, not RSS

The retained-feature metric charges raw fingerprint/offset pairs, two 256-bin u64 histograms and the lag ring. It does not claim Python object memory or allocator overhead. A green result therefore cannot claim peak-RSS improvement. The next native carrying-cost experiment must measure implementation memory or provide an appropriately exact native-state accounting.

### 4. Bounded fingerprint state can miss late opportunity

The 256-entry fingerprint cap is deliberate resource control. Once the gate has seen more than 256 distinct chunks it stops retaining new first sources, so a late repeat whose first occurrence arrived after saturation can be missed. The frozen positive generators are required to exercise useful transfer without human workload labels, but they are not an impossibility proof for arbitrary late reuse. Any required miss in the matrix is HOLD, and future work should specifically attack adversarial late-reuse transfer before broad authority.

### 5. Negative controls are not the world

`random`, `compressed_like`, and `false_pattern` are deterministic mechanism-level controls, not a substitute for broad real media/already-compressed corpora. ADVANCE only earns a native integrated experiment. It does not establish real-world false-positive rate or mature-compressor density.

### 6. One source pass can still be too expensive

The core hypothesis here is semantic/resource nomination, not speed. Updating two 256-bin histograms, a lag ring and a fingerprint on every byte may be a poor native carrying cost even though source traffic is one pass. If ADVANCE, the next falsifier must charge actual CPU/wall and compare useful bytes eliminated per added compute. If that native gate loses, the correct response is sampling/deferred features or a cheaper observable, not arguing that one pass is intrinsically efficient.

### 7. No benchmark-label leakage

The generator family is used only by the independent adjudication oracle. `observe_multi_law_gate()` receives bytes only. A future dispatcher keyed by extension, filename, corpus identity or benchmark family would violate the F-01 constraint.

### 8. No reader or wire claim

The candidate emits booleans/support estimates only. It changes no stored ONE bytes, reader opcode, reconstruction work, access amplification, authentication, recovery or portability. A green result cannot move a Genesis comparator cell on its own.

## Strongest surviving criticism

The fixed lag-64 xor signal is intentionally narrow. It may prove that arithmetic/resemblance evidence can share one scan, but it is not a general resemblance detector. The experiment is valuable only if the architecture remains willing to replace this signal when wider transfer evidence shows poor recall/MIY. Treat the lag as a probe, not a new sacred threshold.

## Review disposition

Admissible to run under the frozen preregistration. No result should be promoted beyond “credible one-pass nomination substrate” without exact downstream proof plus native carrying-cost/MIY evidence.
