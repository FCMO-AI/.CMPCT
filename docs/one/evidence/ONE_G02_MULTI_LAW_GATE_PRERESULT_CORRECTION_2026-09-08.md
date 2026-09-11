# ONE-G0.2 multi-Law opportunity gate — pre-result correction

**Date:** 2026-09-08  
**Disposition:** source `9e3e6c627c50f34476c20af148f87a2293548b11` is inadmissible for scientific adjudication.

Before a result-bearing hosted benchmark was accepted, an independent local audit found that the frozen `false_pattern` negative-control generator inserted the same aligned arithmetic ramp at every patch. That construction therefore contained genuine repeated 64-byte chunks while its oracle declared that no reuse nomination was expected.

This is an oracle/generator defect, not evidence against the candidate gate. Leaving it unchanged would punish correct exact-reuse nomination and make the negative-control contract internally inconsistent.

The correction changes only the generator: each short arithmetic patch now receives a deterministic distinct phase (`base = 7 + 29 * patch_id mod 256`) while preserving the same patch length, spacing, local arithmetic morphology, family count, sizes, repetitions, resource thresholds, false-negative threshold, negative-nomination threshold, and adjudication law.

No candidate implementation, nomination threshold, promotion threshold, reader semantic, wire format, or comparator setting changed.

Any output from source `9e3e6c627c50f34476c20af148f87a2293548b11` must therefore be ignored even if its workflow later completes. Only the corrected descendant is admissible.
