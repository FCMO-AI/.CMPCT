# R275 preregistration — installed desktop package candidate custody (2026-10-24)

## Frozen observed baseline
The exact PR #345 HEAD `33c4ef777542039ab3c1b97797e5ac8ca31af96a` has [installed-native-package run 40092067140](https://github.com/FCMO-AI/.CMPCT/actions/runs/40092067140). Linux/macOS/Windows installed-package jobs all SUCCESS and 15 CPython 3.10–3.14 compatibility jobs SUCCESS, but the final desktop-package-evidence job (ID 120867346749) FAILED before it could aggregate artifacts. The workflow invokes `experiments.entropygraph_v030_release_lock_strict --print-fingerprint` before aggregation. That historical strict front door rejects `docs/V030_RELEASE_LOCK.json` because the published manifest has an empty `required_receipts` array, whereas its validation requires a nonempty list. This is an inherited **release-era / prospective-candidate authority mismatch**, not demonstrated native product failure. Historical v0.30 manifest blob `988a7b05ad4e0833fac0453de74133b38f890f87` is immutable.

## Primary question / prediction
Can the already-present prospective v0.31 source fingerprint (`tools/check_v031_candidate_fingerprint.py`) bind the exact PR head and allow the existing three-platform installed-wheel evidence aggregator to execute, without modifying release-lock history, the wheel, the native implementation, smoke assertions, platform matrix, or release gates?

**Prediction:** an exact-head hosted run reaches all platform evidence and produces one `cmpct-v031-desktop-package-evidence-v1` record with SHA/head and fingerprint tied to the candidate source, and 3 OS artifact names tied to the same head. All existing smoke/ABI/dependency assertions remain active.

**Kill / disproof:** any true native smoke or installed-library failure, missing/mismatched wheel or platform artifact, missing prospective required path, historical lock modification, incompatible fingerprint/head, unsuccessful exact-head aggregator, or admitted foreign-head artifact forbids promotion. Failure of the aggregate after the prospective binding is a new narrow diagnostic, not permission to remove assertions.

## Stronger controls / alternatives
Do not mutate the old published v0.30 manifest merely to satisfy the old CLI. Do not reclassify failed aggregate as passing because the 18 feeder jobs passed. Reuse the prospectively validated source identity already in General Tests. Preserve original installed-wheel/canonical codec assertions and CPython/OS matrix; make artifact-name/source SHA check explicit.

## Evidence and scope
Changes confined to installed-package CI, a source-custody regression test, and this prereg. Product, format revision 24, historical v0.30 release receipt, performance comparator/threshold/corpus, reader/writer and native ABI unchanged. CI cost is existing 18-job matrix plus aggregate. No release or v0.31 product credit from this evidence repair. Separate canonical-development A/B performance remains mandatory.

## Ownership
This is an isolated child branch of #345 and does not edit #345 or other owners. Reconcile child/parent current heads before integrating. Discovery `STATE.json` remains a staleable cache, not a lock.
