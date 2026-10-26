# O153 prospective court — charge transactional ZIP publication against original direct export

Date: 2026-10-26 UTC. Status: **preregistered before implementing the court or observing its measurements**. Evidence lane only; no product, format, threshold, or release mutation.

## Authority and independent owners
- Canonical v0.31 source line remains `agent/v031-development`; released product v0.30.0/r24.
- Frozen direct publication source: O140 [#488](https://github.com/FCMO-AI/.CMPCT/pull/488) `d8b69758dbcbb66fe28fa7cf59598916df160d2d`.
- Independently implemented sibling repairs: O149 [#492](https://github.com/FCMO-AI/.CMPCT/pull/492) `ca01d885fedc8ffc343b9c3c624eddd134158452`; O150 [#491](https://github.com/FCMO-AI/.CMPCT/pull/491) `48bbb41661f8b19d369c50b06bec1018cd4400e9`.
- O143 [#489](https://github.com/FCMO-AI/.CMPCT/pull/489) is the immutable failure-atomicity negative. O151 [#493](https://github.com/FCMO-AI/.CMPCT/pull/493) already establishes identical small ZIP bytes but new-output mode and symlink differences; **do not duplicate its mode-arbitration question**.

## Primary question
What complete **ordinary successful-export costs** do the two staged Reader implementations incur versus the exact O140 direct writer, on identical authentic r24 archive bytes, on **the same runner** with controlled execution boundaries? Is either candidate economically dominated once publication semantics are accounted for?

## Mechanism and preregistered predictions
- Both staged designs preserve the inner ZIP serializer and should produce ZIP bytes identical to O140 for each exact archive; a byte difference is a correctness/regression signal, not a tradeable speed win.
- Each candidate needs up to a complete ZIP of temporary filesystem space during the operation and substitutes the destination inode on success. The direct control writes into the public path. O149 uses umask-derived mode; O150's private mode is known from O151, so no newly claimed mode-discovery credit.
- For large file outputs, the staged designs should not duplicate input decode or payload serialization; *whether* wall time, process CPU, RSS, temporary-file work, and output I/O remain competitive is **unknown**.
- For many small files, metadata/open/rename overhead can dominate; the exact magnitude is **unknown**.
- Alternative explanations: runner variability, warm filesystem caches, process startup, Zstd decoder initialization, input manifest variation, output mode/filename effects, and device writeback timing.

## Experiment and strong simpler controls
- One reproducible tree per family: many tiny regular files; mixed large structured/pseudorandom regular files. Build an authentic r24 archive using the same fixed O140 Builder. All three Reader source trees use the **same resulting archive bytes**, no separate per-engine generation.
- Same runner and fixed dependency/Python environment. For each family and both absent/existing regular output, measure O140/O149/O150 in balanced rotating/reversed order with **seven fresh child-process observations per candidate**. Record independently: parent process wall; child library-only wall; child CPU; peak RSS when available; output byte count/hash; prior and resulting output inode; destination permissions; own-source hash; staging residues. Keep every repetition, not only summary medians. No library/proc-start conflation.
- Capture full archive/input identity and installed Reader Git blob; test original source tree, not a hand-reimplemented approximation. Validate the resulting ZIP contents independently with stdlib `zipfile` and compare complete ZIP SHA-256 between candidates and O140 for the exact scenario.
- The design is a **focused export-cost court**, not the frozen complete release-parity matrix. It may reject a candidate locally but cannot earn full release promotion.

## Decision and kill/narrow conditions
- Any mismatch in emitted ZIP bytes/member contents, existing regular path corruption on success, source mutation, unexpected public/temp residue, or false source identity rejects that measured observation as product evidence and requires causal diagnosis.
- A repeatedly confirmed large-output wall regression satisfying both the repository's 5% relative and 3ms absolute release timing threshold is **local timing debt**, not automatic holistic release failure. Smaller/inconsistent differences remain ambiguous; no cherry-picking.
- Process wall includes Python startup but library wall excludes startup; compare each separately. RSS is per fresh process; do not interpret it as incremental allocation without a baseline. Temporary-file space and actual IO are not interchangeable.
- Keep O143 negative and O149/O150 positive acceptance intact. No product edits, release, version bump or changed success evaluator.
- If mechanisms are equivalent within noise, report as such; choose based on safety/semantic policy and code simplicity, not manufactured benchmark superiority.

## Ownership and continuation
Independent economics/control lane only; do not edit competing Reader implementations. Preserve source SHA, raw JSONL, tools, workflow run ID and artifacts. Reconcile with owners [#491](https://github.com/FCMO-AI/.CMPCT/pull/491), [#492](https://github.com/FCMO-AI/.CMPCT/pull/492), and comparator [#493](https://github.com/FCMO-AI/.CMPCT/pull/493). At most one bounded measurement campaign; do not multiply adjacent thresholds/fixtures without a decision-changing reason.

**Disproof of thesis:** material cost of staged publication is smaller or larger than predicted once charged; ambiguous reproducibility is a legitimate result. **Promotion boundary:** complete inherited semantics and frozen same-runner full parity remain mandatory elsewhere.