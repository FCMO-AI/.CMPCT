# O126 / A08 — Windowed temporal XOR ownership: preregistered hypothesis falsified

Date: 2026-10-25 UTC. **Research/oracle evidence only, NOT CMPCT product evidence.** Pre-result prediction committed at `9efbe912f08e68e4ce82a1f0506bd550a4dffbb9` before the script was introduced. Canonical released CMPCT remains v0.30.0 / r24; v0.31 development is separate.

## Problem and baseline

A08 asks whether a generation history is a useful *physical information relation* rather than only an operational series of snapshots. A four-generation file-owned window could reconstruct a selected state with <=4x logical decode, unlike full-history solid or unwindowed per-file temporal frames, but it pays extra frame boundaries and checkpoints. It must beat **same-window raw** and **independent-snapshot** controls within that locality class; full-history solid and XOR journal remain essential smaller-or-larger nonlocal controls.

## Insight and hypothesis

Predict >=5% smaller **complete charged research-container bytes** on BOTH stationary sparse changes and shared-epoch changes versus the strongest control with max selected-generation decoded bytes <=4x. This claim is deliberately much narrower than general temporal compression, actual revision-24 publication or range-read optimization. All candidate descriptor, checkpoint, compressed frame and integrity bytes must be included.

## Exact experimental provenance and alternatives

- Exact uploaded instrument Git blob: `1fc307ed76d782a7bb08cb8904c7bcc0d99acd6a`. Local SHA-256: `eae384e0b97d3299916fadd11a38726457eb21481a90fe4aacf6410fa187795c`.
- Locally executed with Python and true `zstd -19`; raw JSON SHA-256: `eeadd8974b315abbb285f49ea0ddd348da576c3cdef296895712a19e9c56d2f8`. **Local execution measured; hosted independent reproduction pending until exact-head CI completes.**
- Five deterministic families, 12 generations each: `sparse`, `shared_epoch`, `rotate`, `independent` (8 files x 4,096 B each) and structurally held-out `heldout` (16 files x 8,192 B).
- Seven fixed arms: per-generation snapshot, solid history, per-file raw timeline, per-file XOR timeline, per-generation XOR journal, 4-generation raw windows, and the candidate 4-generation XOR windows.
- An **actual self-contained research binary** charges a 40 B header, 16 B/file names, 32 B SHA per generation/member, 16 B per compressed frame descriptor and every `zstd -19` byte. It is **not a valid CMPCT r24 archive**.
- Every binary is parsed and Zstd-decompressed; all 12 generation/member rows are reconstructed through an independent inverse and verified against both the immutable source and serialized SHA-256 table. No actor receives original family bytes as gifted decoder-side data. The source is identical across all arms.
- Max selected-generation logical decompression is charged against entire frames required by each representation, including preceding generations. All original per-frame input bytes are charged; no free decoded cache, selective Zstd seek or uncounted prototype dictionary.

## Direct local measurements (complete stored bytes)

| Family | Snapshot <=1x | Solid <=12x | Journal XOR <=12x | Window raw <=4x | Window XOR <=4x | Candidate vs strongest <=4x |
|---|---:|---:|---:|---:|---:|---:|
| stationary sparse | 396,804 | **37,248** | 37,929 | **103,868** | 104,183 | **-0.30% (LOSS)** |
| shared epoch | 396,804 | 39,907 | **37,309** | **105,915** | 107,438 | **-1.44% (LOSS)** |
| rotated structure | 396,804 | 36,630 | 396,804 | **102,838** | 201,077 | **-95.53% (LOSS)** |
| independent | **396,804** | 396,491 | 396,804 | 397,152 | 397,152 | **-0.09% (LOSS)** |
| held-out broader edits | 1,579,652 | 157,526 | **148,448** | **417,771** | 424,672 | **-1.65% (LOSS)** |

All arms returned correct byte-identical history and SHA-verified every member. The other original arms `per_file_raw` and `per_file_xor` were also executed and remain in raw JSON; on rotated data, unwindowed `per_file_raw` reached 36,621 B (12x maximum logical decode). Per-generation XOR journal yielded the global minimum on the held-out family (148,448 B). These stronger nonlocal controls cannot be hidden as they invalidate a generic best-storage claim.

**Predeclared decision: `PREDECLARED_HEADROOM_NOT_SHOWN`.** Both named positive cases lost to the same-window *non-XOR* arm; the 5% threshold was not approached.

## Mechanism diagnosis / alternatives considered

Windowing itself imposes ~24 or ~48 compression frames, unlike one solid frame. For stationary sparse histories, Zstd-19 already exploits repeated unchanged bytes inside the 4-generation raw window: manually replacing them with XOR zeros saved no complete bytes once boundaries were charged. For rotated data, XOR creates dense pseudo-random residuals and catastrophically loses (201,077 vs 102,838 B under the exact same physical ownership). These are observations for this fixed corpus, not a proof of universal behavior.

A simpler **raw-window** strategy is stronger in every exercised family under <=4x decode. The full-history solid or per-file timeline often wins in bytes at **12x** decoded work. Thus the current mechanism must not be promoted or used to justify another close XOR-window threshold search. Any reopening needs a new information/ownership boundary, broadly discoverable applicability, or a different access/proof architecture—**not** another friendly seed.

## Falsifiability and stronger checks

Independent CI workflow `.github/workflows/v031-o126-a08-temporal-window.yml` locks the exact source blob, executes actual Zstd, independently validates the five families, 35 arms, complete charged-byte equation, 4x bound, provenance, exact per-member reconstruction and unchanged primary decision thresholds. A hosted Actions green will prove the research reproduction, NOT a product win. Failure of source SHA, checksum parity, one frame length, assertion, strong comparator or hosted equivalence suspends the claim.

## Costs and limitations

Local parent+child creation wall/CPU recorded in raw JSON, but not used to rescue losses; one-run per arm includes subprocess startup and is not a repeat-median product benchmark. RSS, I/O, random seek, update write-amplification, native-platform behavior, actual CMPCT archive bytes, full filesystem metadata, varying path cardinality, deletion, generations/recovery and adversarial inputs remain unmeasured. The prototype fixes file length and stable file set; these simplify the hypothesis and limit generality. Strong negative even under this favorable model is useful but does not retire *all* temporal information models.

## Safety, integrity, compatibility and release

No Builder/Reader/native parser, public format, release gate, threshold, benchmark corpus, CI evaluator, version, source owner or publication contract was changed. No semantic concessions: decoder verifies identical input and SHA, fallback wins. Research result is not a released storage capability.

## Counterfactual / Discovery Engine

The **same-window raw Zstd control** is the cheapest prospective discriminator: it wins all five tested cases and would have falsified an XOR-specific advantage before any implementation. This may save future A08 oracle effort but does not justify changing general Discovery Engine policy from one bounded negative. `docs/discovery/STATE.json` remains untouched while #440 owns reconciliation. No concurrency collision was found; A02/#465, A03/#458 and A05/#469 operate on separate factor/program questions.

## Future leverage and highest-value next action

**Retire this specific four-generation XOR-window family for current promotion.** Converge the already-measured Reader/Builder integrity and runtime owner PRs rather than extending friendly temporal variants. A genuinely different A08 study would need a weaker-cost update/search or cross-generation proof primitive and held-out evidence that justifies carrying cost; do not schedule it by default. Report current exact-head CI separately; scientific results are not release receipts.

## Hosted original court and independent audit (post-result, append-only)

The original source-exact hosted Linux execution [O126 Actions #40241060666](https://github.com/FCMO-AI/.CMPCT/actions/runs/40241060666), head `2e5dc7ca6c15e532c42e6e0ec31a04cf99f11532`, finished **SUCCESS**, ran actual Zstd-19 and printed `O126_DECISION=PREDECLARED_HEADROOM_NOT_SHOWN` and `O126_INDEPENDENT_RECEIPT_AUDIT=PASS`. The independent auditor checked 5 families x 7 arms, 35 complete binary packets, every frame charge, every generation SHA, the four-generation maximum decoded-work bound and strongest admissible and unconstrained comparators. Raw hosted artifact [#12616762305](https://github.com/FCMO-AI/.CMPCT/actions/runs/40241060666/artifacts/12616762305), artifact-ZIP SHA-256 `2adfc72cfa9e213f97b868d7d119c1c5de7cb4af346d4c538bf0423cd1aca7a2` (GitHub retention through 2027-01-23). This hosted execution independently confirms the research classification, not a core CMPCT improvement.

**Disproof** stands as specified: two positive families each lost to a simpler control; no acceptance-threshold change, cherry-picking or uncharged decoder information was used. **Quality-ratchet:** retain original comparator and loss data even when alternate information models are explored; this narrow family is retired pending genuinely new headroom/ownership evidence. CI topology and Engineering Evidence are separately non-scientific gates, not oracle scores; their failures, when present, require faithful dossier/workflow repair rather than weakened functional checks.
