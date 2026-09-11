# ONE-G0.2 Relation Writer Envelope V3 initial-source invalidation — 2026-09-09

The initial V3 implementation at source lineage ending `ef0e06b8382347fa80186d0f6d0a46d6ff8566f0` is **scientifically inadmissible for promotion**.

Hostile review found an accounting defect before hosted evidence was accepted: the first content-derived lane was selected using `source[block_start]` and `target[block_start]`, then the selected lane plus two additional lanes were read, while the counter charged only three source/target pairs. Unless the selected lane happened to be zero, actual probe traffic was four pairs per block rather than the preregistered three.

This is an evidence-accounting defect, not a scientific HOLD. No thresholds, matrix cases, semantic rules, incumbent, or representation logic are changed in the correction.

The admissible correction must make the seed pair itself the first charged probe (`lane0 = 0`), derive only the remaining two lanes from that pair, and continue to charge exactly six bytes per 64-byte version block = `0.046875x` of the combined two-version input.

Any CI output bound to the invalid source is debugging evidence only.
