# O212 — Same-effective-index sparse geometry admission: hosted result

**UTC evidence boundary:** 2026-10-27. **Status:** product candidate and hosted correctness evidence, **NOT merged/released**.

## Authority, original negative and preregistration

Released CMPCT is v0.30.0 / revision-24; v0.31 research is unreleased. Owner O193 [PR #521](https://github.com/FCMO-AI/.CMPCT/pull/521) exact parent `392112ce859db5a7f85be593c82d1cabc1f5131f`; incumbent Reader blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`, incumbent strict validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`.

The independently hosted original negatives are O198 [#532 / run 40381593089](https://github.com/FCMO-AI/.CMPCT/actions/runs/40381593089) and O202 [#539 / run 40390902146](https://github.com/FCMO-AI/.CMPCT/actions/runs/40390902146): ordinary Python Reader accepts checksum-consistent invalid sparse extent lengths and returns incorrect nonzero-range bytes while full read/verify succeed; native Rust and existing Python strict validator reject corrected root-versioned variants. O205 #542 measured ~17.12ms incremental **separate preflight** for one 4GiB / 4096-extent profile; O208 #546 falsified filename-reopen source identity and also proved inode identity alone does not imply byte immutability. Those are **inherited** controls, not new measurements or new product claims.

This experiment preregistered its primary question, simpler controls, predictions, kill/acceptance criteria **before any O212 code/test change** at commit `3db4edb1745ed731d2f6fd54969caab718e47e63`, [pre-registration](2026-10-27-o212-sparse-same-index-prereg.md).

## Candidate and deliberate scope

[Draft PR #560](https://github.com/FCMO-AI/.CMPCT/pull/560) is stacked on O193. Candidate Reader blob `ee598eec46531c4da44d90d37b67f783b0ab3299`, unchanged strict validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`.

Within the already-existing normal-path canonical path admission scan, check each S_SPARSE K_FILE's geometry against existing `validation._validate_storage` using the **same effective index already loaded by the Reader**. This rejects mismatched declared extent length vs total referenced blob logical sizes, invalid offsets/ordering, overlaps, bad blob references and out-of-file extents **before mmap/reads**. No extra pathname open, separate validator clone, new persistent index, codec, physical layout or on-disk revision. On early invalid-index failure, the original source file handle is closed. The index is validated **once per open**, not for each range read.

The narrow guard does **not** upgrade all other storage/index grammar to strict preflight, authenticate in-place post-admission source writes, prevent same-inode truncation, or prove arbitrary archive resource bounds. This draft does not supersede other Reader/salvage/transaction owner PRs.

## Hosted installed-source scientific acceptance

**Substantive CI:** [GitHub Actions 40435476060](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435476060), exact product/test/workflow HEAD `084bca3613ad9c9ace94a2b18d3cb48a6776225a`, **3/3 host jobs SUCCESS**.

| Host | Actual installed test suite | Independent source custody |
|---|---|---|
| macOS 14 | **14 PASSED / 2.38s** | Reader+validator installed bytes equal committed source |
| Ubuntu 24.04 | **14 PASSED / 2.86s** | Reader+validator installed bytes equal committed source |
| Windows Server 2022 | **14 PASSED / 2.50s** | Reader+validator installed bytes equal committed source |

Installed Reader SHA256 normalized CRLF: `7a7234be1974e2bb76ba8b8f7656c803e9932c5129da05074d53c44ebf2e6b95`; installed strict validator SHA256: `0c77dceeac0ae518b2e72f3dad8925c03225e8cb7b81b3f799a3f0c8de41e0eb`.

Artifact IDs from original hosted run (all head SHA `084bca...`):
- [macOS #12704351156](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435476060/artifacts/12704351156), artifact digest `sha256:49df9fa8a3ac36a3be654bc5f80d2ccb4bbf9805c6d46ced2476422409dcc197`.
- [Ubuntu #12704261407](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435476060/artifacts/12704261407), digest `sha256:96171baf05bf77bc81192bd5d671d7df7fa6dad2097da76037339f6ee2f1c336`.
- [Windows #12703891663](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435476060/artifacts/12703891663), digest `sha256:fa291b3803d3e3aaa52baa3082dd0e00e2e8ae308621ad1f6f793df5c4639a82`.

**Scope of 14 regression tests:** valid sparse with holes and physical blob reuse (full SHA via CMPCT.verify, read/range, extract); three declared-length 1/2/5 malformations rejected at opening with unchanged archive SHA; authenticated footer index with contradictory geometry (valid primary, invalid latest) rejected; ordinary direct RAW S_BLOB unchanged; 64 valid sparse extents random-access; six distinct malformed sparse geometry/references rejected without writes; and a valid **4GiB logical / 4096-extents** revision-24 archive with independently computed logical SHA, preflight and multiple actual Reader `read_range` slices. That giant smoke intentionally **does not** allocate/read/verify the full 4GiB with Reader; prior O196/O197 separate full-product courts remain independent controls.

The GitHub artifact names may contain a synthetic pull-request merge SHA. The source/CI attribution above uses the actual PR head SHA `084bca...` from the workflow run's `head_sha` and the checked-out HEAD witness, not the artifact-name merge SHA.

## Independent artifact bytes audit

The original three 935/937-byte GitHub artifact ZIPs were downloaded separately and inspected using Python `zipfile`, with full ZIP SHA256 equality against GitHub's published artifact digests and CRC checks. An independent consistency instrument checked that all three receipts contain the identical original checked-out HEAD `084bca...`, exact Reader blob `ee598e...`, unchanged strict validator blob `51c284...`, identical test blob `df70e2...`, and `src/cmpct/reader.py` as **the only production file changed**; each archived pytest log independently reports `14 passed`. **Independent audit result: PASS for 3/3 artifacts, 42 total test successes.** Audit JSON SHA256 `1f2cbbc74b4a992d82b2d80e77e1dd2b03d68010bc731e05e8dbff026491e46d`, kept with the automation's original downloadable evidence; the immutable GitHub artifacts above are the long-term public source. This independently audits **receipts**, not full product reconstruction or test source execution in a second environment.

## Original infrastructure negative preserved

The first [O212 run 40435203483](https://github.com/FCMO-AI/.CMPCT/actions/runs/40435203483) failed at **pytest collection**, before product assertions: `tests/conftest.py` imported unrelated historical `experiments` packages unavailable from the isolated installed package's Python path (`ModuleNotFoundError: experiments`). This is not a product test red. In the subsequent workflow-only commit `084bca...`, the specialized job copies the **exact unchanged test file bytes** to `RUNNER_TEMP` and runs pytest there, without the unrelated canonical v0.30 research conftest. The ordinary CMPCT general suite continues to use the historical conftest. No test data, assertion, corruption oracle, benchmark, comparator or resource ceiling was relaxed.

## Evidence limits and pending gates

The specialized hosted green is **product-candidate correctness evidence for the exact cases above**, not general release readiness. No complete same-source 4GiB ZIP64 **after this guard** has been measured yet. Existing S_CDC geometry research is separately owned by O201 #534 and must not be conflated. The full generic suite, Native Core, fuzzing, recovery under malformed generation chains, source mutation/truncation, resource ceilings, cold-open CPU/RSS, temp-I/O and public release documentation remain separately gated. Need exact-final-head generic CI reconciliation after this *documentation-only* commit; do not infer prior head check status applies automatically.

One-sentence causal conclusion: **validation logic was already present; joining it to the Reader's actual effective index before exposing range reads closes the reproducible S_SPARSE metadata discrepancy for tested signed-wire cases, without a new pathname identity gap.** Its product-wide integration and economic adequacy are still unearned.

## Next executable action

1. On the documentation HEAD, recheck specialized exact-head CI plus generic/fuzz/native; preserve failures. No benchmark or source law changes.
2. Owner O193 #521 reviews and reconciles this patch with current Reader and source-lifetime/export/publication branches; if carrying cost/material test debt is acceptable, integrate only with all parent correctness guards.
3. Run authentic Builder-derived 4GiB/4096-extents exact-head ZIP64 full SHA/CRC/Info-ZIP and cold-open CPU/wall/RSS, include hostile checkpoint and same-UID archive-mutability tests.
4. If high-extent admission overhead or source identity undermines the result, preserve regression and narrow/revert; do not downgrade strict validator.

No Discovery policy/STATE write, format change, merge or release in O212.
