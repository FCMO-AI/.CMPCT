# ONE-G0.2 multi-buffer SHA prototype provenance pin

This note is frozen before the first result-bearing hosted execution and corrects one wording ambiguity in `ONE_G02_AUTH_TREE_MULTIBUFFER_SHA_PREREG_2026-09-07.md` without changing its hypothesis, matrix or decision gate.

The external prototype is **Intel Multi-Buffer Crypto for IPsec v2.0 at exact commit `4f808234a91e87147a4f26167df40f3fd7c7f0c6`**. The v2.0 tag currently resolves to that commit, but Git tags are references and should not be treated as intrinsically immutable. Hosted evidence must clone/fetch and checkout the full commit SHA above, then verify `git rev-parse HEAD` before building.

No moving external branch, shortened SHA or later v2.0 tag retarget is accepted as the same experiment.

**Execution marker (scientifically neutral):** the result-bearing run must occur after the workflow was corrected to the repository's latest-head PR classifier/concurrency contract and after the two closed scalar auth-tree workflows were retired from automatic execution. This marker changes no candidate bytes, benchmark matrix, gate or external prototype pin.
