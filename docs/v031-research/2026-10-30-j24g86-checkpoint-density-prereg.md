# J24G86 — charged authenticated checkpoint-density O0 (preregistration)

2026-10-30 UTC. Research-only; no production, format, version, release, or benchmark changes. Independent temporal representation question after three Writer session/cache activations. Released base is main SHA 80c358f8824ec1b20d349c92ed94c898090969b0, v0.30.0/r24.

## Primary hypothesis and strict research criterion
Can inserting ordinary r24 **complete signed index checkpoints** at fixed interval K shorter than the inherited generation-64 checkpoint cut worst-case decoded signed deltas for a cold Reader open by >=2x while adding <=5% to complete archive bytes at BOTH 8,192 and 32,768 members? Try K in {8,16,32}. If none passes both constraints, retire **ordinary dense full-index snapshots on these two real deletion histories** as a general answer; no claim about other representation families or workloads. The 5% number is only an O0 research triage condition, never a release threshold.

## Physical source and controls
Use previously authenticated J24G83 original-hosted 65-footer physical CMPCT archives (8,192 middle deletes, 32,768 tail deletes); detached outer ZIP SHA256 6d0542f0938740a0d82acb0e3f1a57a46fffc9ecafcc6c4bea79187cc607e016. They were independently audited in #833, but this experiment must personally confirm the original physical index/header SHA256, all signed footers and parent pointers, exact 63 deletion operations, and last generation full checkpoint. Do not trust receipts alone. Historical K=64 and optional per-op snapshot K=1 serve as controls. Ignore Writer-session speedup when evaluating this different family.

## Charged mechanism and alternative explanations
Rebuild actual full effective index at each hypothetical periodic checkpoint, retaining unchanged blob descriptors and every member metadata field. Serialize with normal MessagePack, charge the full independent authenticated footer and compressed body, minus the original real delta footer/body replaced. Use fully charged Zstandard compression levels 1,3,19 and select the best encoded candidate as a generous oracle, not a free gifted payload. Prefix and delta offsets remain consistent in the derivation; do not claim actual materialized r24 checkpoint archive. Count cold-open delta applications for generations 1..63, not seconds; do not count theoretical reduction as measured host speed. Large index bytes may outweigh replay savings; real compression may instead make a snapshot surprisingly cheap.

## Falsification, safety and scope
Before accepting any result, verify one independent invariant (file count and exact final index hash), and deliberately reject corrupted signed footer data. No CMPCT import is needed for a detached binary referee. A strong original baseline could still win. Negative result must remain scoped to these same-input physical data and regular full checkpoints; do not generalize to factorized temporal indexes. No changes to frozen benchmark, selector, comparator, evaluator, Reader/Writer, checksum/recovery, resource or release controls. No product promotion. Only a surviving candidate may earn later hosted, physically materialized Reader/preflight/recovery and CPU/RSS/byte validation.

## Ownership
No concurrent PR owns this exact fully charged periodic checkpoint cost tradeoff; #800/#344 own other snapshot/replay questions, #834 frontcoded path index representation, #836 Writer cache, #574 discovery STATE. Do not change those surfaces. Main has precedence. Retain original file-source SHA, assumptions, negative outcomes, and cheapest decisive next step.
