# O53 — Descriptor-bound Writer source admission × serialized Writer/salvage composition

**Date:** 2026-10-25 UTC. **Status:** scientifically **SUPPORTED for the tested exact source**, draft product-correctness candidate, not merged or released. No numeric version, on-disk format, official performance, or Discovery Engine promotion.

## Exact authority, immutable prediction and source provenance

- Parent: [PR #311](https://github.com/FCMO-AI/.CMPCT/pull/311), `agent/phased3-v031-salvage-writer-cross-owner-composition-r265-20261023@c1e75370281ca6b721ef10edf1ed15e6c5ef48f7`; inherited `src/cmpct/transactions.py` blob `a3b9c3375ed19f0b37d40ee47ead7b5d5b8905ee`.
- Independent source-admission owner: [PR #406](https://github.com/FCMO-AI/.CMPCT/pull/406), O51 helper blob `130638744d26dbf71a3ddd49b2545db9eb933ed4`, original unmodified nine-case test blob `b6e7a75f900171b85647a6d7ef06bd765101e041`.
- Historical actual-source negative: O49 [PR #404](https://github.com/FCMO-AI/.CMPCT/pull/404), [run 40157632143](https://github.com/FCMO-AI/.CMPCT/actions/runs/40157632143), unconnected POSIX FIFO blocks historical `Path.read_bytes()` update. O51 isolated three-host [run 40159802389](https://github.com/FCMO-AI/.CMPCT/actions/runs/40159802389) is *independent*, not integrated proof.
- The O53 prospective hypothesis and disproof were **committed before source mutation**: `docs/v031-research/2026-10-25-o53-writer-source-lease-composition-prereg.md` at `73fd55d594eb130dc8225a0b26a5f1ef738524d3`. The preregistration remains unchanged.
- O53 branch `agent/phased2-v031-o51-salvage-writer-union-o53-20261025`; [draft PR #409](https://github.com/FCMO-AI/.CMPCT/pull/409), stacked on #311 without modifying other owner branches.
- Exact combined Writer Git blob `79ea9e423d155b106f40cd0811075c69ff04f105`. Diff against parent modifies only **28 inserted / 1 deleted lines** of product code in `src/cmpct/transactions.py`: copy O51's unmodified descriptor helper and replace the old `read_bytes();stat()` admission expression. Existing `@_serialized_writer`, held OS lock, checked Reader/append/inode, salvage scanner, CLI, codec/native and r24 format are retained.
- Original #311 composition test `tests/test_v031_salvage_writer_union_r265.py` blob `15d536c08bd5d428e6ef2f77871ba5f7e465215f` unchanged; original O51 test copied byte-identically. New O53 source+lock tests `tests/test_v031_writer_source_lease_union_o53.py` blob `d866cb988c6c08f4f909b2aa397c954da5cded82`.

## Primary question and actual result

Can O51's nonblocking file-descriptor source admission operate **inside** #311's cooperative serialized Writer and preserve physical salvage, already committed generation, source identity and exact file bytes?

**Result: YES for the tested Linux/macOS/Windows configurations and generated corpus, with explicit POSIX-only limitations.** The exact installed-package/three-host court on **HEAD `cf5d4de7a4181db79dc90da8788ff384cc45e27c`**, [GitHub Actions run 40161785974](https://github.com/FCMO-AI/.CMPCT/actions/runs/40161785974), is **SUCCESS in all three jobs**.

| Host / CPython 3.11 | Cases collected | Real PASS | Legitimate POSIX-only SKIP | FAIL |
| --- | ---: | ---: | ---: | ---: |
| Ubuntu 24.04 | 15 | **15** | 0 | 0 |
| macOS 14 | 15 | **15** | 0 | 0 |
| Windows 2025 | 15 | **7** | 8 | 0 |

Each job binds the exact Writer/Reader/CLI blobs and original owner test SHA, installs CMPCT with `pip install .`, verifies that `cmpct.transactions` and `cmpct.reader` resolve outside the checkout under `site-packages`, runs real pytest, and then independently checks nonzero JUnit execution counts and expected platform skips. These are **37 actually executed assertions-bearing pytest cases across hosts**, not 45 PASS and not a benchmark.

**Decision-changing interactions exercised**:

1. A real no-writer FIFO source inside the serialized Writer fails without hanging and preserves both the *complete archive SHA* and the forensic physical candidate set; a subsequent legitimate Writer update succeeds, demonstrating released lease. The child process is bounded by a timeout.
2. A competing Writer child process cannot bypass an already held POSIX kernel lock. After the lease is released, it commits an exact r24 update, which the genuine Reader SHA-verifies.
3. An actual delete → descriptor-bound update → rename sequence preserves latest reader namespace, exact payload and SHA integrity while older physical header candidates remain **`verification=unverified`**, **`generation_membership=unknown`**. A forensic candidate list is never upgraded into an authenticated membership claim.
4. **Stronger control: real immutable #311 parent source** is loaded from `git show c1e7537:src/cmpct/transactions.py` into an isolated Python module using genuine installed `cmpct` dependencies. Parent and O53 both update copied archives from identical source data. The test asserts complete on-disk archive **byte identity** after (a) small regular update, (b) >4×CHUNK content-defined chunking update and (c) a second CDC update with a one-byte perturbation. Genuine Reader checks the r24 CDC storage row and exact reconstructed bytes and performs strong verification. This controls against a synthetic/stub comparator and extends beyond a single small RAW case.
5. The untouched O51 original nine cases test regular update, unwritten FIFO, symlink→regular, real AF_UNIX socket source, pre-open path pivot to FIFO, post-open regular-path pivot preserving source-fd metadata, directory refusal, symlink→FIFO refusal, and stable-source complete archive byte parity against its historical source-admission primitive.
6. The two original #311 tests preserve committed namespace behavior, historical forensic claims, and access to forensic read-only enumeration while a cooperative Writer lease is held.

### Hosted raw artifact custody

The substantive run `40161785974` / exact source HEAD `cf5d4de7a4181db79dc90da8788ff384cc45e27c` uploaded per-host JUnit and raw stdout (not just a workflow conclusion):

| Host | Job ID | Artifact ID | Uploaded ZIP SHA-256 |
| --- | --- | --- | --- |
| Ubuntu 24.04 | `121074752791` | `12586129502` | `f315655773f8b0989f07a5c1c13b0ace05e61f6ec629c36082b7d8d0f678d99b` |
| macOS 14 | `121074752244` | `12585924812` | `13017b40f485c6d416cf6d85f4fa51f4ea67a6bd2ddad0711ad51790f14b8a5f` |
| Windows 2025 | `121074752374` | `12586404094` | `1be5e18da8e5292751e955f7ddef025cc14879f78debad5d53e8666764432759` |

The full per-case logs report the original and new cases, 15/15 on Linux and macOS, 7/15 and 8 explicit skips on Windows, and successful artifact upload. Source hash remains `79ea9e423d155b106f40cd0811075c69ff04f105`. A later documentation-only HEAD requires its own exact-head CI reconciliation; **do not replace the actual result-bearing `cf5d4de7` claim with unexecuted future proof**.

## Inherited and release-gate scope

At initial observation on the result-bearing source HEAD `cf5d4de7`: specialized O53 **SUCCESS**; original #311 cross-owner Writer/salvage **SUCCESS**; prior salvage candidate **SUCCESS**; version discipline **SUCCESS**; CI topology **SUCCESS**; native core **SUCCESS**; continuous fuzzing **SUCCESS**; R36 attribution **SUCCESS**. Generic suite was still running when this record was drafted, and engineering evidence initially **FAILED exclusively on missing required PR-description `Evidence` and `Future leverage` headings**, not on product source; PR description was amended without disabling or changing the evaluator. The official r24/ZIP workflow had administrative SUCCESS, but no new substantive speed-parity proof is claimed absent inspection of actual performance job. Final documentation-head evaluation must be checked separately.

## Negative evidence, strongest self-critique and exported costs

- Historical #311 alone retains the O49 no-writer FIFO blocking issue. O53 adds source admission under lease; **does not claim full immutable source bytes**. An adversary modifying data in place during read with coincidentally identical size/mtime/ctime may evade `fstat` boundaries (including ABA). Network/exotic filesystem `open` and `read` may block despite `O_NONBLOCK` handling.
- The source helper still materializes the entire file in memory. More `open`/`fstat` calls have overhead; O51 measured small *primitive-only* micro costs, which are not the whole-product create/update or release performance floor. CPU, wall, RSS, temporary I/O, crash/cross-writer liveness and p99 economics remain to be measured.
- Windows named-pipe/AF_UNIX/POSIX FIFO cases are correctly marked SKIP, never PASS. Network share and ReFS behavior are unmeasured.
- No full parallel noncooperating writer or attacker-owned kernel model; advisory locks require cooperation. Source changes before snapshot and immutable-source capture are not resolved.
- Cross-host first-pass tests used synthetic data; they do not establish generality or 1.0 15/15 compression superiority.
- Existing Reader format r24, release v0.30.0 and no-regression comparator remain unchanged. Neither the specialized scientific workflow nor broad green tests alone authorize merge or release.

## Counterfactual and discovery decision

The cheapest decisive earlier discriminator was testing a *real non-writer FIFO while the original #311 serialized archive lock was held*. That result would have immediately exposed that source admission must be an owned part of the transaction contract, not a separate precheck. O49 previously established the liveness mechanism and O51 proved the safe descriptor candidate; O53 shows those mechanisms coexist with #311's owner architecture. This is transferable engineering knowledge but not repeated evidence of Discovery Engine policy failure; **no discovery-policy or `docs/discovery/STATE.json` mutation** was earned.

## Next promotion frontier

Request review from #311 and #406 owners using the exact source/CI receipts; preserve both owner branches. Close final-head CI (including generic/general, restored engineering-evidence PR description, original Writer/salvage, portability, native/fuzz). Run actual whole-product same-input update timing/CPU/RSS/bytes and the official frozen release-parity gate before any promotion; retain zero-byte deterministic archive-size tolerance. Check source-error abort and multiwriter liveness on the composed Writer, and bounded large-source RSS. If the composite remains superior, choose one legitimate integration lineage rather than carrying another permanent parallel Writer implementation. **PR #409 stays DRAFT / NO MERGE / NO VERSION / NO RELEASE.**
