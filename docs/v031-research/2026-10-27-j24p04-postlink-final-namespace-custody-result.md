# J24P04 — exact installed Reader: authentic at linkat is not perpetual pathname custody

Date: 2026-10-27 UTC. **Science / bounded security-contract result only**, not a product improvement or release credit. Existing overwrite Issue #528 remains open. J24F11/J24F12's fresh-leaf authenticated-inode publication mechanism remains **valid at its kernel linearization point**.

## Source/execution provenance
- Owner branch: PR [#566](https://github.com/FCMO-AI/.CMPCT/pull/566), stacked on #559 `dd723d128b5a020f154b4c9f7d37c6eedc929f24`. All source/product changes on #566 are **zero**.
- Immutable *prospective* J24P04 preregistration: commit `7cccb4e2d36001cd2a3672f778c010cb30c53c28`, `docs/v031-research/2026-10-27-j24p04-postlink-namespace-custody-prereg.md`. The original J24P03 independent two-step named-stage result is documented in the neighboring result note and hosted #40443470125.
- Exact result-bearing installed Reader Git blob `83c6600fa6cc951c1e6a136d239a39bb2c5d836b`, unmodified from J24F12. Reused genuine Builder-independent revision-24 author `research/j24f04_raw_chunk_immutable_transfer.py` (blob `a8a33193554b61d2affdabea54b363a51ec87f3b`) for fixed S_CHUNKS and S_CDC, with authentic indexed SHA-256.
- Exact science-plus-negative-auditor source HEAD `cc2d3d51f3fae7c51c6609cda03f79dc0757df0e`: source-authenticated installed-package Ubuntu 24.04 nonroot [J24P04 Actions #40448430829](https://github.com/FCMO-AI/.CMPCT/actions/runs/40448430829) **SUCCESS**. GitHub original artifact [#12709616288](https://github.com/FCMO-AI/.CMPCT/actions/runs/40448430829/artifacts/12709616288) ZIP SHA-256 `b5deac0478c39a23af84da236adbc1c8d9eb9b2e0fd21f7bfbfd61cb07a4c66c`; original `result.json` SHA-256 `6e1f327cfc2513896d320d37ddbf8d12ab6a9315f16607877e56789205148868`.
- The final documentation-only commit is **not itself** the science source SHA. Re-run/check exact final HEAD independently before claiming final-HEAD scientific green.

## Causal experiment / strongest controls

`research/j24p04_postlink_reader_court.py` invokes genuine `CMPCT.extractall(metadata=False)` with original installed source. The only scheduling wrapper calls the original real `_publish_unnamed_chunk_fd(fd, parentfd, leaf)`, then checks `(dev,ino)` and SHA of the newly linked leaf against the still-open verified fd **before** optionally spawning an independent same-UID subprocess. In hostile trials, that process renames the *already successfully published final leaf* to a quarantine path, creates a second same-size foreign inode under the final name, and finishes before control returns from the wrapper. The real extraction call then returns normally. The wrapper does **not** replace `linkat`, SHA computation, real kernel pathname operations, the Reader method, or the archive validator. The mechanism explicitly tests **post-publication pathname mutation**; it is not a failure of `linkat` itself.

| Real installed Linux r24 mode | No actor at return | Same-UID post-link actor at return |
| --- | --- | --- |
| S_CHUNKS, parent `0700` | Authenticated fd inode + SHA | Foreign inode + SHA, method success |
| S_CHUNKS, parent `0300` | Authenticated fd inode + SHA | Foreign inode + SHA, method success |
| S_CDC, parent `0700` | Authenticated fd inode + SHA | Foreign inode + SHA, method success |
| S_CDC, parent `0300` | Authenticated fd inode + SHA | Foreign inode + SHA, method success |

**8/8 focused hosted controls pass**: 4 no-actor authentic outputs and **4/4 genuinely separate-process postlink namespace substitutions**, all while installed `extractall` returned success. In every case the real link syscall linked the original authenticated inode; in hostile cases the quarantine retained that original valid inode and the final path resolved to the foreign content. All hosted links used actual `AT_EMPTY_PATH`; actor and parent both ordinary Linux UID 1001. There is no uncontrolled race-probability or remote-exploit claim.

Independent `research/j24p04_receipt_audit.py` reconstructs deterministic logical payload hashes without importing the court, checks physical identity, actor UID, decisions and strict JSON structure: **160 checks PASS**. A separate audit-falsifier `research/j24p04_receipt_mutants.py` induced 7 independent dishonest/invalid receipt mutations and verified all **7/7 rejected** on the same hosted exact science source. These are receipt-integrity checks, not additional Reader attack repetitions.

Further differently rooted *kernel-only* Linux trial (not installed Reader) used direct libc `linkat` plus a separate process at UID 65534 on **overlayfs and tmpfs**, for both `0700` and `0300`: 8/8 expected identical outcomes. It strengthens the kernel-level semantic generality but does not extend the Reader product claim to another OS.

## Scientific disposition, scope and strongest negative

- **PRESERVE:** fresh destination `O_TMPFILE -> linkat(fd, final leaf)` binds publication to the verified physical inode *at the linearization instant*. The earlier J24F11 J24F12 8-case security claim is not falsified.
- **FALSIFY THE STRONGER UNQUALIFIED CLAIM:** in a namespace writable by an equal-authority competing process, successful `extractall()` return cannot by itself prove that the final filename still identifies that original inode. Pathname identity is time- and threat-model-dependent. Making an additional final `stat` or SHA observation is also susceptible to subsequent mutation.
- **INDEPENDENT J24P03 NEGATIVE REMAINS:** `O_TMPFILE -> visible stage -> second pathname rename` can publish a foreign inode even *during* the intended overwrite syscall; this is a different, strictly weaker failure, not to be confused with post-link mutation.
- **NO CLAIM:** no proof of arbitrary source corruption, privilege escalation, remote exploit, unbounded runtime attack probability, unsafe `linkat` source authenticity, Windows/macOS or native Reader behavior, or universal impossibility of secure replacement. A different authority boundary could prevent the actor; it has not been implemented or measured.

## Counterfactual / reusable discriminator

The earliest sufficient distinction is **verified fd bytes** vs **physical inode chosen by a particular syscall** vs **later pathname mapping**. The previous J24P03 named-stage experiment already invalidated an intermediate-source rename architecture; J24P04 was warranted only to keep a prospective design from overclaiming *post-return* namespace ownership when preserving the direct-fd fresh-leaf win. Threat model comes before an implementation choice. This is a technical local lesson, **not an evidence-backed need to change the general Discovery Engine or its state cache**.

## Costs, release debt and next decision

Research made no changes to `src/`, `native/`, `tests/`, `benchmarks/`, format revision or v0.30.0 release. The added evidence uses installed source, actual kernel calls, deterministic archives and receipts. It does not measure create/storage bytes, Reader CPU/wall/RSS, cold-open/range locality, syscall overhead, durability/power failures, cross-host portability or complete CI. Neither this research nor an administrative-green workflow permits merge or release.

**Next engineering fork:** formally specify distinct security contracts for (a) fresh leaves in trusted vs peer-writable namespaces and (b) overwrite of existing leaves; decide whether a controlled destination namespace, fail-closed refusal, or other true physical-identity publication primitive can satisfy an *achievable*, explicit contract. Do not spend another activation on the already-falsified named-stage+rename variant. Keep security, performance, format and owner PR integration gates intact. Reconcile with Issue #528 and original #557/#559 owners.
