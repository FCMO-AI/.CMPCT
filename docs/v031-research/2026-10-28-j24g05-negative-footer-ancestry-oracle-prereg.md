# J24G05 — Prospective failed-ancestry memoization oracle for exact r24 recovery

**PREREG FIRST / EXPERIMENTAL SCIENCE ONLY.** Parent J24G04b [PR #647](https://github.com/FCMO-AI/.CMPCT/pull/647) exact result-bearing HEAD `d6930bad7cc3831a86fb59d04dfe918c75f030d9`, hosted [run 40638411124](https://github.com/FCMO-AI/.CMPCT/actions/runs/40638411124), actual unchanged published Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Source is authoritative. No product, release, version, benchmark or reader mutation.

## Decisive inherited evidence

On real Builder archives with 32/128/256 individually SHA-authentic orphan delta footers appended after its authentic checkpoint, the genuine Reader made 529, 8257, 32897 decoder calls (exact 1+N(N+1)/2) and reconstructed the original same bytes, with median wall 1.5805, 45.262, 194.512ms respectively. Same-size nonmagic suffix required one decode and ~0.15ms, so ordinary byte scanning alone cannot account for the result. The original flawed assertion that valid Builder had no tail footer is permanently preserved as failed first CI run 40638195302; correction prereg J24G04b precedes this result.

## Primary question / predicted outcome

Can a *transient per-open scientific wrapper around the ORIGINAL* `CMPCT._index_from_footer` memoize every ancestor visited in an **unsuccessful** candidate chain, so later backward-scan candidates that are themselves known-invalid need no decoder re-entry? The wrapper must delegate to the original index replay on previously unseen candidates, observe the actual original decoder calls, and mark positions invalid **only after** the delegated original replay returns None. For the same invalid suffix chains, decoder calls should become N+1 for N=32/128/256 (33,129,257), with identical chosen valid original footer and member content. No semantic parser, decoder, journal replay or release code changed.

A different explanation is that wrapper/context overhead erases decoding savings despite fewer calls, or caching incorrectly marks older valid checkpoints invalid. Test both directly. The negative-ancestor cache is a research oracle (not a shipping solution) and does not establish correct handling under concurrent archive mutation or all malformed transaction schemas.

## Stronger controls and kill conditions

- Real Builder original checkpoint (N=0), real `append_rename` committed valid delta, and matched equal-size no-FMAGIC garbage tail must produce **identical** selected footer, delta depth, logical exact bytes and SHA in original vs wrapped Reader.
- Flat, individually SHA-authentic no-op delta footers each with `prev=0`, same N and physical size as the nested chain, must stay O(N); both readers must choose same older valid Builder footer. This isolates parent-edge traversal from mere authentic-footer count.
- The wrapper may memoize only failed candidate ancestry; never cache a successful checkpoint or change the original decode payload/result.
- On N=256 require decoder calls <= N+1 and median measured Reader open+read+verify wall at least 2x faster than original over 3 repetitions. This is a bounded *oracle information gate*, not release economics; if not met, narrow or kill this cache approach. Exact archive size, baseline wall/CPU, source identity, temporary memo cardinality and process-independent timing must be disclosed.
- Any reconstructed byte, selected footer, delta depth, authenticity, read range or verify difference is a hard falsifier.
- No claim of reduced absolute peak RSS, whole product performance, security patch or shipping compression improvement; a future product variant must account memory and concurrent mutation and integrate with #358/#365 owners.

## Causal cost frame / counterfactual

J24G04b already demonstrates N(N+1)/2 source calls with O(N) frame bytes. At N=256 the appended tail adds exactly 256*(13 payload+68 footer)=20,736 bytes, but drives 32,896 extra decoder invocations. A cache proving invalid ancestry after the *first* failed scan can reduce repeated SHA/parsing to O(N) while leaving older authentic recovery intact. If this wrapper works, an earlier observable of actual decoder call multiplicity would have justified direct product work after a single bounded court rather than duplicating valid-journal replay optimization.

## Coordination and final decision

#358 (valid journal replay) and #365 (resource ceilings) own related Reader change surfaces; this study deliberately edits no Reader files. J24G04b remains immutable source negative/positive evidence. `docs/discovery/STATE.json` untouched. A positive scientific oracle only justifies a separately preregistered source-level candidate with resource budget and cross-host adversarial proof; not a merge or release.
