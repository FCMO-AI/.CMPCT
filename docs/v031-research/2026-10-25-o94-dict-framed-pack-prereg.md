# O94 prospective research — dictionary-framed S_PACK physical ownership (2026-10-25)

**Authority:** exploratory representation oracle only. Released v0.30.0 / archive revision 24 and unmerged v0.31 remain unchanged.

## Current evidence and distinct question

O70 PR #426 found an authentic 687.911x selected decode-work amplification when reading 64 bytes in an eight-ZIP mixed-size pack; splitting owners incurred +2,122 complete archive bytes and substantial creation-wall cost. O73/O74 PR #429 tested two-pack ownership and failed a held-out locality bound. Native S_PACK O1 PR #319 measured 256 shared-pack 64-byte reads at 39.4573 ms versus 0.2456 ms for a one-decode gifted immutable snapshot oracle (160.68x conditional headroom) and explicitly retained the strong-per-read SHA contract.

A *different* representation hypothesis is a shared, decoder-visible compression dictionary plus **individually independently decodable members**. This changes reference/ownership boundaries, not an arbitrary grouping threshold. It might preserve cross-member redundancy while containing selected decode-unit size. No decoded blob cache, implicit stale authorization or source-mutation behavior is assumed.

## Prospective falsifiable decision

Compare **exactly the same ordered source bytes** in four research structures:
(A) one monolithic Zstd frame;
(B) each file as an independent Zstd frame without a shared dictionary;
(C) per-file Zstd frames using one **genuine corpus-trained** Zstd dictionary;
(D) grouped equal-size segments / conventional packing, when instrumented.

Charge **all** physical compressed payload bytes; dictionary bytes once; **at least** 48 bytes of physical owner/index/hash metadata per frame and 48 bytes for the shared dictionary root; no compressor oracle facts are free. Model full-SHA integrity on each independently decoded owner; separately state that selected-member SHA cannot automatically provide the inherited whole-pack tamper rejection for *unselected* owners. This is an information-boundary change and cannot earn product correctness/semantic equivalence from timings alone.

Corpus controls: deterministic multiple distinct structural distributions, including a shared-template/independent-variation family and a high-entropy hostile/no-benefit family, plus a held-out perturbation. Use at least one distinct file ordering. Capture complete bytes, create CPU/wall excluding process startup when possible, selected physical decoded bytes, measured selected decode work, and independent exact round-trip/SHA checks. Record raw observations, tool/library versions, source parameters and negative outcomes.

**Hypothesis H1**: dictionary frames lower decoded work for selected small members by >=10x versus one big pack on positive corpus while remaining within +5% of charged complete packed representation bytes. **Kill/narrow:** if same-input genuine dictionary-trained complete bytes exceed +5%, if corpus-specific win fails held-out perturbation, if dictionary cost dominates, if integrity/read contract changes invalidate the comparator, or if an ordinary non-dictionary per-member control is stronger after complete accounting. This bound is purely research triage, **not** a release waiver: promotion retains the canonical zero-byte same-input release parity rule and official performance gates.

## Stronger controls / external debt

Keep the original shared-pack owner (strongest size/control) and independent frames (strongest simple locality/control); never compare different file trees or count only stream payloads. Training work must be recorded separately and charged before proposing an admission/creator policy. Compare actual source-specific library/CLI codecs, avoid simulated winners. Zstd dictionary compression is mature external technology; a favorable oracle alone is not novelty or CMPCT product capability.

## Concurrency and ownership

This branch owns only its independent scientific oracle, exact receipts and bounded conclusions. It does not modify #319 native shared-blob work, #426/#429 physical ZIP cohorts, #442/#451 Builder/source integrity, codec, Reader, Builder, native ABI, r24, frozen benchmarks or release policy. Before any late write check current Git state and avoid a duplicate PR. Any positive/negative outcome must be reported with source/semantic limits, and the next operator can retire the family if controls dominate.

## Execution and provenance

Pre-register before writing or running the experiment. Executable proof is under `research/v031_o94_dict_frames_oracle.py`; results under `docs/v031-research/2026-10-25-o94-dict-framed-pack-result.md` if decision-changing. No CI, runtime portability, source mutation, native ABI, platform product semantics, benchmark win or release claim until independently measured.
