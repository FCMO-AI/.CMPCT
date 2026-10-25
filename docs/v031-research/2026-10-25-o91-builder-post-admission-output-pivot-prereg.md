# O91 preregistration — destination identity after Builder admission

**Date:** 2026-10-25 UTC. **Type:** negative, scientific-only, prospective v0.31 research. **Status:** preregistered *before* the instrument, CI workflow or results. No canonical product change.

## Exact source and ownership

Stack exclusively on O90 #448 at initial HEAD `1beb733da61da8e1c562e7c3190b1f18f1cc45d1`, installed Builder source blob `bfb37fcd06e6ff05742606ece365348150f477fc`. O90 owns static destination type admission; O81/O84 own source alias and filesystem fidelity; O75/O78 own alternative output publication semantics. This episode **does not implement** any competing fix. There is no `docs/discovery/CONCURRENCY_PROTOCOL.md` or `tools/discovery_claims.py` at the inspected development HEAD; open PRs and exact branch claims have been checked.

## Baseline and narrow scientific question

O87 (installed Linux/macOS) proved unconnected FIFO and symlink-to-FIFO output blocking. O90 introduces an early `os.stat(out)` type rejection, followed by `scan()`, expensive compression and finally `Path.write_bytes` resolving the **name again**. O90 explicitly makes no race-free guarantee. The remaining evidence gap is whether a genuine installed O90 Builder can (a) **successfully clobber a one-link source member** and (b) **block again on a swapped-in FIFO**, even though the initially admitted external destination was an ordinary, independent regular file.

## Predictions and independent controls

1. Same tree / no interfering actor: installed O90 completes a build to an existing independent regular output, verifies/extracts exactly, and leaves source bytes unchanged.
2. After all initial admission and real `Builder.scan()` complete, independently coordinated actor atomically replaces the external regular output pathname with a symlink pointing to a one-link file inside the source root. The existing Builder then follows the new link on final `write_bytes`, returns success, and changes source bytes. Source hardlink count is one; the original output inode was disjoint. The affected bytes and route are preserved as an adversarial **negative**, not a legitimate archive output.
3. Same schedule, but actor atomically renames an unconnected FIFO onto the admitted output pathname. Installed O90 Builder exceeds a bounded subprocess deadline, while matched regular-file control completes. Parent harness must never hang.

Use only synthetic temporary files, an independent adversarial thread with explicit synchronization after original scan, and a disposable subprocess with timeout for potential FIFO blocking. Run on Linux and macOS. Do not mutate product, inherited tests, evaluators, comparator/release thresholds, source fixtures or benchmark law.

## Disproof / narrower outcomes

If actual installed product revalidates the final opened destination, either adversary can be refused: narrow/retire predicted failure. A timeout in **regular control** or failure to complete the actor barrier makes experiment invalid, not positive. If only one pivot reproduces, report the two outcomes separately. If a monkeypatch bypasses the real initial O90 stat check or real scan, invalidate the run. Control tests must run unmodified Builder core; synchronization may wrap its `scan` method only *after* executing the original scan, without substituting archive data/compression or `write_bytes`. Timing deadline proves only an observed >N seconds, not an infinite hang.

## Alternatives, scope and output

Static rechecking reduces but does not eliminate pathname lifetime races; descriptor-bound output ownership, no-follow opening, staged-and-replace publication and a different target-inode identity contract are independent architecture classes with documented tradeoffs (O75/O78). Choose neither via this lower-rung test. Full product economics, inode preservation, crash durability, arbitrary malicious filesystem, Windows device semantics and release quality remain unmeasured. Preserve JUnit logs and exact installed source provenance in GitHub Actions. Return a discriminating result to O90/O84 owners without editing their branches. No format revision/version bump/release; no STATE.json write unless a decision changes and repository frontier reconciliation is needed.
