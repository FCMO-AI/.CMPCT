# J24M01g — exact-head full-suite evidence adjudication (detached)

**Research / CI-evidence integrity only; NO release or product promotion.** Evidence inspected on 2026-10-29 UTC. This reconciles the already-frozen J24M01g execution and J24M01h preregistration, not a new Reader/Builder implementation.

## Exact head and provider receipts

The parent #769 original *result-bearing* HEAD is `8c99a16257a4700d2d5a9a2989d52c694a343a99`. [Dedicated J24M01f hosted court #40917140647](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140647) completed **SUCCESS** for both research jobs, including the genuine full test order; *that green research job explicitly did not claim a green full CMPCT suite*. The original pytest process reported **806 passed, 4 failed, exit code 1**.

Provider artifacts downloaded as their actual ZIP bytes and independently SHA-256 checked:

| Source | Artifact | Provider ZIP SHA-256 |
| --- | --- | --- |
| [J24M01f original full-suite job](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140647/artifacts/12917515918) | 12917515918 | `04e649d194d8f1c351d376c564d69367e1f8afe761ac58f01b28b6987ef673bb` |
| [J24M01f focused job](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140647/artifacts/12917121235) | 12917121235 | `eb33212a189c77adc05408913e6342a08de9d54e6db55bc0685e9a92736b26dd` |
| [Independent ordinary CMPCT Tests](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140534/artifacts/12917670526) | 12917670526 | `0c17fa2186b63543d434c5752d47fd78b230bb19cd494e11066cec3fe9cea2a7` |

Detached, standard-library-only auditor used actual provider ZIPs, *without importing CMPCT*, checked `exact-head.txt`, `pytest-exit-code.txt=1`, all 810 XML testcase nodes, the **single genuine** `tests.test_j24v01_sparse_verify_streamed::test_real_256m_sparse_verification_does_not_materialize_holes` as an executed PASS, four exact failing tests, and full log agreement. All seven negative XML mutations (duplicate, missing, failure, error, skipped, not-run, malformed) were correctly rejected. The detached audit is a referee of receipts, **not an independent execution of the 256-MiB kernel resource test**.

## Four preserved non-green full-suite assertions

1. `tests/test_performance_base_native_release_custody.py::test_historical_native_materializer_is_release_fingerprinted`
2. `tests/test_public_attribution.py::test_surface_revision_records_attribution_campaign` (historical surface revision mismatch)
3. `tests/test_v030_ci_topology_split_receipts.py::test_authoritative_v2_classifier_is_release_fingerprint_driven`
4. `tests/test_v030_release_fingerprint_surface.py::test_release_fingerprint_covers_r25_oracle_and_android_custody_inputs`

All **four failing test source blobs** are byte-identical between released `main` and PR #769, and the normative `docs/V030_RELEASE_LOCK.json` blob is also byte-identical. This localizes these failures to unrelated inherited release/attribution custody assumptions on the stacked #738 lineage; it does *not* declare the failings acceptable or authorize alteration to historical release receipts or benchmarks. The general test suite [#40917140534](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140534) remains **FAILURE**, as does the [r24/ZIP performance workflow #40917140724](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140724). J24G33 #40917140762 remains RED on an inherited SHA-pinned preflight, which requires explicit version-aware owner reconciliation, not weakened checks.

## New directional falsifier preregistered, not yet hosted

J24M01h prospective prereg commit `130790608d9b4be6983bdac580268a71a7db5e92` asks whether the **same unchanged strict 128-MiB child-`VmHWM` gate** rejects a deliberately touched, *real post-exec 160MiB* resident spike (positive fail condition), while the original inherited-parent-highwater case remains under the cap. This is a distinct test of **false-negative sensitivity**, complementing the existing inherited-`ru_maxrss` **false-positive** proof. It must not import CMPCT or change the original verifier resource input. Local experimental code/run is not a committed hosted CI result, and is explicitly **UNMEASURED IN HOSTED CI**. A refused implementation tool write is not a commit.

## Collision and PARETOBONK

No new Linux anonymous-fd publication implementation was opened here: PR #566 already performed adversarial exact-kernel `O_TMPFILE` + named-stage overwrite and `renameat2` tests; #557/#559/#523 already own create-only fd-to-name no-clobber behavior. Their evidence rules out re-proposing this *named intermediate overwrite* family under a same-UID namespace writer. #749 remains an independent actual compaction verified-vs-published inode blocker. This was a search-space elimination based on inherited exact scientific evidence, not a newly executed syscall oracle. `docs/discovery/STATE.json` is staleable and owned by #574; it was intentionally untouched.

## Decision and bounded next action

**The real full-suite 256-MiB sparse verifier PASS is now positively authenticated on exact HEAD 8c99.** The scientific evaluator has earned better attribution evidence. Current documentation-only HEAD `1307906` is **not entitled to inherit an exact-head CI green label**. The next bounded test is to execute the J24M01h true-resident-spike negative proof on an authenticated Linux host with unchanged original threshold, then return to the #738/#769 owner for controlled composition. Do not change release/fingerprint rules to make four inherited assertions vanish, or allow RSS success to waive #749 physical publication security, unsupported platforms or direct-base benchmark economics.
