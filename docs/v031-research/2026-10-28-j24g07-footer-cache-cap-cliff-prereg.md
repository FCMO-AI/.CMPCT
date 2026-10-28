# J24G07 — Prereg: bounded failed-footer cache's above-cap work cliff

**Date: 2026-10-28 UTC. PRE-RESULT / pre-instrument registration.** Product owner #650 at exactly `10a6bc150cfa0ceb8608ee826dc09650ca3f4e3d`, Reader blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`. Released main remains `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24. Independent evidence-only branch `agent/phased2-v031-j24g07-footer-cache-cap-cliff-20261028`. No Reader/product/format/version/frozen benchmark/Discovery policy edits.

## Primary falsifiable question

Does the candidate cache's limit `len(known_bad)+len(seen)<=16_384`, despite bounding *retained* positions, allow a new worst-case CPU-replay cliff when a SHA-authentic invalid ancestry chain has more than 16,384 footers? #650's genuine 103.71x result at N=256 is immutable evidence. It cannot by itself prove asymptotic/hostile resource bounds above N=16,384.

**Preimplementation static derivation:** For the exact J24G04 chain (first no-op delta `prev=0`; each subsequent points to previous orphan), on candidate N>M=16,384, the first orphan head has N visited positions and cannot be cached; the next has N-1, etc, until head length M finally fits and admits M negative positions. Subsequent heads skip. Predicted actual decoder calls:
`C(N<=M)=N+1`, `C(N>M)=[N(N+1)-M(M+1)]/2+M+1`.
At N=16,384 predicted 16,385 calls; N=16,400 predicted **278,665**; flat same-size SHA-valid orphan footers remain N+1. At N=16,448 predicted 1,067,041. This is an *oracle-level source deduction*, not a measured product result.

## Cheaper truthful experiment

Reuse exactly the authentic installed #650 Candidate Reader, first-party Builder, original J24G04 signed orphan FTR grammar, `FTR.pack` and `sha(payload)`. Because J24G04's research-only generator deliberately asserts N<=256, create a new **research helper** with identical grammar but a higher bounded count; do not modify or bypass the original frozen J24G04 experiment, runtime validator, or release gates. Generate N=16,384 and N=16,400 linked orphan chains, a same-total-byte all-flat footer control N=16,400, and a same-byte neutral no-magic tail. On each compare exact full archive bytes/hash, first-party checkpoint selection, depth, `read`, `read_range`, `verify`, genuine decoder invocation positions and unique count. Predict 16,385 vs 278,665 vs 16,401 vs 1 calls respectively. Raw wall and process CPU per case with repeated same-worker runs, RSS when available, but no broad performance claims from this microcourt. Limit N<=16,400 to avoid unbounded resource spend.

## Strongest simpler control / alternatives / kill

Simpler control: 16,384 just below memory ceiling, no magic appended tail of identical size, and a same-size flat collection whose no-op delta footers reference zero (no overlapping ancestry). Plausible alternative explanations: a bounded generation validator rejects >16k before replay, a different source path caps candidate scans, the cached set admits a subset even on overflow, or system I/O dominates wall while decoder calls change. **Kill/narrow** if actual decoder counts depart from predicted formula; preserve raw negative evidence, do not change the evaluator. If formula matches but wall is not materially higher, report computation amplification only, not a confirmed service-level CPU denial. The legitimate Builder checkpoint must always remain selected and verified in every case. Any wrong content / changed footer selection is a separate correctness defect, not an optimization win.

## Product decision and limits

If confirmed, reject a claim that a 16,384-entry cache bounds worst-case *work*. Owner should evaluate a mechanism that preserves immutable-source recovery and limits both work and retained memory without reducing false-positive checks or archive semantics. Candidate #650 remains an unmerged seed with a real below-cap gain; no automatic product promotion, merge, release or format change. Original/candidate full comparative benchmark, Windows/macOS, in-place source mutation (#654), peak RSS, full release matrix are separate. Record result in an append-only follow-up; do not rewrite the prediction. No direct mutation of #650, #651, or any concurrent owner branch. Discovery `STATE.json` is staleable and not rewritten by this experiment.
