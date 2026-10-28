# J24C11 — negative-control C proof did not execute; CPU resolution repaired without changing J24C10

Date: 2026-10-28 UTC. **Scientific decision: H1 PATH_EQUIVALENCE_CONFIRMED; H2 AGGREGATE_CPU_RESOLVED. Original J24C10 Q=1 NOT_PROMOTABLE.**

## Claim boundary, prospective freeze, source and independent evidence

- Research-only [J24C11 PR #656](https://github.com/FCMO-AI/.CMPCT/pull/656) stacks on parent J24C10 [#652](https://github.com/FCMO-AI/.CMPCT/pull/652) at `c93014c4801a145879206e40ff760a86becb8727`. It modifies only preregistration, instrument/referee and CI; **no CMPCT product file, native binary algorithm, format, release version or frozen J24C10 evaluator changed.**
- Preregistration [J24C11](2026-10-28-j24c11-negative-control-path-falsifier-prereg.md), standalone commit **`dddca44c1f3de8ec62949219fdf6784d27c20f44`**, preceded instrument implementation. The original Q=1 no-debt criterion remains unchanged.
- Measured code, workflow and independent referee **HEAD `33a3c632691e5378967ba85a98860e845de60240`**, [Actions #40646045954](https://github.com/FCMO-AI/.CMPCT/actions/runs/40646045954): three installed-wheel Python3.11 jobs Ubuntu24.04/macOS14/Windows2022 **SUCCESS**, retained scoped inherited integrity checks, genuine optional ABI3 module loaded, primary native admission unchanged.
- Experimental design: same installed wheel, signed r24 deterministic input and same Reader object for both arms. Toggle only module-global optional proof function `_uniform_stride` (enabled/disabled); count calls to the Reader's proof dispatcher using a **common spy in both arms**. Eight paired ABBA cycles, four aggregate blocks/cycle, 8192 early calls or 16 late ragged calls/block, 64 raw blocks/host, **192 total**, with original SHA and independent literal expected answers, CPU+wall, source and reader identity. This is a different repeated-call question from original Q=1, not a replacement decision.
- Original hosted artifacts, **ZIP SHA-256 checked independently from GitHub**:
  - Ubuntu [#12798235305](https://github.com/FCMO-AI/.CMPCT/actions/runs/40646045954/artifacts/12798235305), `921018a28ae73b103903d3823c2921a9622ec237bd6fdfb8f5c608864f97b388`.
  - macOS [#12797432344](https://github.com/FCMO-AI/.CMPCT/actions/runs/40646045954/artifacts/12797432344), `b8f6cec094541b5d4836cb66e2ab947d6b903ebf1509a49a0c084973b2f035f6`.
  - Windows [#12797299857](https://github.com/FCMO-AI/.CMPCT/actions/runs/40646045954/artifacts/12797299857), `58f4d75575c2feb2847aceae9c5766ecc90d720241939949bfb4c12b27a16cc9`.
- The per-host independent referee verified strict/candidate raw receipt arithmetic, all 64 output digests, 8 exact ABBA cycles, aggregate CPU, same wire per profile, **zero** C proof-dispatch calls and rejected a malicious receipt with a forged call. After downloading original artifacts, a differently rooted cross-host check independently reconstructed expected 16-byte *logical* answers and offsets, verified all 192 original observations, rederived medians, protected against a deliberately tampered local ZIP, and matched hosted results. **This is receipt verification, not independent product execution.**

## Exact measurements (strict Python-witness-disabled vs witness enabled)

**This is repeated-call metrology, not Q=1 product speed.** Higher wall ratio (>1) means witness faster. CPU was measured with `time.process_time_ns` over complete batches; no process startup was included.

| Host | Path / Q | Strict wall median | Witness wall median | Wall ratio | Aggregate CPU resolved? | C proof calls |
|---|---|---:|---:|---:|---|---|
| Ubuntu | 65,536 one-owner **early**, 8192 calls | 22.452533 ms | 22.482111 ms | 0.998684x | YES | **0 / 0** |
| Ubuntu | 262,144 ragged **late**, 16 calls | 219.181385 ms | 219.972796 ms | 0.996402x | YES | **0 / 0** |
| macOS | early, 8192 calls | 23.909855 ms | 21.522958 ms | 1.110900x | YES | **0 / 0** |
| macOS | ragged, 16 calls | 287.936563 ms | 286.460709 ms | 1.005152x | YES | **0 / 0** |
| Windows | early, 8192 calls | 22.077300 ms | 22.000800 ms | 1.003477x | **YES** | **0 / 0** |
| Windows | ragged, 16 calls | 273.094950 ms | 273.123450 ms | 0.999896x | **YES** | **0 / 0** |

Windows process CPU is **not fabricated as zero**: median early strict and witness were both **15.625 ms**, and ragged strict 273.4375 ms vs witness 265.6250 ms. The aggregate window produces nonzero CPU measurements, satisfying only the preregistered observability condition; **the 15.625-ms quantization remains too coarse to infer a <5% early-CPU difference**. The original Q=1 Windows CPU evidence remains unresolved, not repaired retroactively.

All outputs match literal data independently of the Reader; all scope-specific inherited tests PASS. The optional C scanner still drives the Reader constructor admission; the new uniform read-time proof was *never called* in either negative-control arm.

## Causal conclusion, contradictory observations and immutable original negative

**J24C11 falsifies the hypothesis that actual native stride-proof execution caused the J24C10 early/ragged Q=1 negatives, on these precise exercised control paths.** The code cannot charge time to a function not invoked on either arm; source shows early `start*2<size`, ragged [4,1,2] fails first/middle/penultimate size screening. The new repeated-call A/B is nearly tied on both ragged hosts and Ubuntu early; macOS early paradoxically favors the witness by 11.09% despite zero proof calls, consistent with non-mechanistic measurement variation / other timing effects. This does **not** prove a unique source of original Q=1 variance.

The immutable [J24C10 original run #40641105382](https://github.com/FCMO-AI/.CMPCT/actions/runs/40641105382) **still fails** prereg no >5% debt: macOS 65k/one early wall ratio **0.863201x** (+15.85% slowdown), macOS 262k/ragged late **0.943964x** (+5.94%), Windows Q=1 CPU unresolved. The J24C10 late uniform wall wins remain real (>=3.618x on 3 hosts). These contradictory observations must coexist; J24C11 neither changes the frozen threshold nor authorizes promotion of #652.

## Cross-platform source identity: raw Windows SHA divergence is a newline conversion

Git canonical `src/cmpct/reader.py` blob at this code HEAD: `b66e37755c329113a5f22a80cb8ef68bf54be579`.
The genuinely installed Linux/macOS Python source SHA-256 is `987c4e624ab17f58c8fbbeb0428d5c2925980024eeb4b1966050fb39eb05eba7`. Windows installed source is `4c789af31b6735d58fef5af4494034dcf32c116e77b10fd3cfd934686e01831b`.

**Independent exact-byte calculation from the same canonical Git source:**
- Canonical LF UTF-8 SHA-256 = `987c4e624ab17f58c8fbbeb0428d5c2925980024eeb4b1966050fb39eb05eba7`.
- Replacing each LF with CRLF, no other source changes, SHA-256 = `4c789af31b6735d58fef5af4494034dcf32c116e77b10fd3cfd934686e01831b`.

Thus the raw installed-file hashes differ because of **Windows CRLF checkout/wheel bytes**, *not* a different Python program for this source. Future source-exact cross-host audits should bind Git blob or normalize line endings carefully, while preserving actual installed raw hashes and never pretending raw bytes are identical.

## Scope, limits and future action

A positive exact-path outcome provides **causal falsification** and improved Windows CPU metrology only. It is not a performance optimization, a new compression mechanism, full product benchmark, cross-platform release proof, verification of real user corpora, nor recovery/extraction/semantic-mutation gate. The repeated Q=8192/Q=16 court cannot establish that the original Q=1 no-regression veto is false; that frozen failure is preserved. The highest-value next step is *not* more proof-family threshold gardening: preserve the late uniform research seed with explicit debt; shift to authenticated representation/ownership or broadly applicable nonuniform selective-range indexing, with full Reader D5 product costs and inherited hostile tests. Consider fusing stride witness into existing native admission only if a fresh honest oracle first charges per-member memory and all files' precomputed metadata. O221b lazy Q4 negative remains valid. No Discovery policy lesson earned beyond this bounded prospective lesson; #574 `STATE.json` not changed.

## Handoff

J24C11 scientific question is **decision-complete** at the causal research rung. Both original PRs remain draft; no merge/release/format version changes. Before integration, recover live #641/#652/#583 ownership, review exact HEAD/source and latest checks; do not copy new claims into canonical product state or excuse source-pinned historical CI failure. This result document is a later evidence-only commit, so CI on its new HEAD must be rechecked separately from the proved `33a3c632` code+test source.


## Evidence-dossier CI correction (later documentary HEAD)

The first evidence-only final-document commit `1569c59470626e5adeed8ffa605e870a1baaf52f` had **Engineering Evidence FAILURE**, [Actions #40646479059](https://github.com/FCMO-AI/.CMPCT/actions/runs/40646479059), because the draft PR description used noncanonical heading labels. Its product/experiment source and original three-host scientific receipts were not implicated. The original CI failure remains immutable. The draft PR body was corrected to contain every exact heading required by `tools/check_pr_evidence.py`, its disproof/quality-ratchet markers and full factual content, without altering the checker or a success threshold. **A fresh GitHub Actions run on the subsequent documentary HEAD is required before treating this CI gate as closed.** Source-exact positive J24C11 result remains tied solely to `33a3c632`.
