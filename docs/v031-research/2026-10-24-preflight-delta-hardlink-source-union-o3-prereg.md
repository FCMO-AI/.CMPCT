# O3 — cross-owner bounded preflight CPU integration preregistration

Date: 2026-10-24 UTC. Source-only integration, preregistered **before product mutation**. Owner: isolated integration branch; no changes to the heads of #342 or #346.

## Locked source and scientific question
- Base hardlink-graph owner [#342](https://github.com/FCMO-AI/.CMPCT/pull/342) exact HEAD `a480d7ae2f1480f15e73eda2b04e48b1a75e66b1`; existing `validation.py` blob `6c629ab504504a50fbbf8d1ae9e4cf0b31757a05`.
- Indexed delta owner [#346](https://github.com/FCMO-AI/.CMPCT/pull/346) exact HEAD `fb887d8610dced551acf5a84778ba539d08dac59`; `validation.py` blob `58a71ae97837d7158a6a853653ef58818d0b1ee8`.
- Historical unoptimized `_apply_delta` at baseline `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, `validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`.
- Mechanically checked: the entire historical `_apply_delta` definition on #342 remains byte-identical to the baseline and its file has no `heapq` or `_apply_delta_indexed`. The two changes occupy distinct semantic sections: signed journal replay versus hardlink terminal-owner validation.

**Primary question:** Can one real validator source carry both bounded authenticated transaction replay and bounded hardlink owner-chain validation while preserving all original signed r24 positive/adversarial cases, exact source provenance and return/exception semantics?

## Smallest defensible mutation
Start from #342, preserve its entire module byte-for-byte except: add one `heapq` import and transplant the complete source-exact `_apply_delta_indexed` plus replacement `_apply_delta` from #346. No manually recomposed algorithm or altered limits. Do not modify released format, benchmark comparator, Reader, Builder, native ABI, recovery rules or frozen test inputs. Candidate must equal `#342 source + exact #346 delta replay block`; abort if an owner head has drifted.

## Falsifiers and evidence
Run **both** owners' existing independent controls on the **same head**: signed r24 journal replay randomized/property tests and historical-vs-candidate source-exact ABBA; plus valid/hostile signed hardlink graphs, old missing-owner/cycle/type/row-order regressions and inherited strict signed-tree preflight. Use one exact-checkout GitHub Actions workflow, preserve raw logs, provenance, identities and artifacts. A green unit test does not prove production parity. Include the full O2 signed delta memory negative (**+42.77% traced allocation at N=4096**) and #342 star overhead (**~6–7%**) as explicit debt, not as excuses to weaken input or evaluator. If either fails, leave draft and do not merge.

## Concurrency and closure
No force-push, no update to owner branches, no `docs/discovery/STATE.json` overwrite. Standalone branch/PR, exact-head CI before any promotion. The next activation must recheck newer #342/#346 heads and rebase/reconcile rather than silently overwriting. No release/format/version increment. This integrates **two proven mechanisms**, not proof of universal dominance.
