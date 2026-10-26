# J24F02 result — successful post-SHA foreign-inode publication on verified chunk extraction

**Date: 2026-10-26**
**Classification: NEGATIVE PRODUCT SECURITY SCIENCE / HOSTED REAL READER — NO SHIPPING SOURCE CHANGE**
**Decision: `VULNERABILITY_REPRODUCED` on Ubuntu 24.04 and macOS 14, both independently authored r24 chunk representations.**

## Authority, exact evidence and experiment boundary

- Repository `FCMO-AI/.CMPCT`; published v0.30.0, physical grammar revision 24.
- Development base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- **Actual installed Reader Git blob:** `e716233403dabd0966863c45635e18fa5ac6afb8`. The CI source custody gate and Python Git blob re-hash verified this identity on each host.
- **Builder-independent fixed archives:** `tests/conformance/v24-chunk-maps.json`, exact blob `91141405bb10b2e1226b0652e3aa0a13ba41846c`. Each archive's complete SHA was checked before and after the experiment.
- Prediction frozen at commit `27a1ae9a59f99e29b9713c1df52a0654fd54354b`, before test source commit `1b464f975f557a50f3c52133e43866c1b76326fa`.
- Result-bearing CI head: `830612e26566d71a954fdf75d62eb8bdb65edb9d`.
- **Hosted full run:** [GitHub Actions 40368802153](https://github.com/FCMO-AI/.CMPCT/actions/runs/40368802153), two platform jobs **SUCCESS**.
- J24F01 PR #486 is the strongest inherited positive baseline: 28 source-bound static output-leaf/corruption controls over Ubuntu/macOS. It expressly did **not** test concurrent stage-name substitution.
- O181 PR #514 is the independently proven analogous ZIP-export *different* endpoint. It is not evidence that verified chunk extraction is affected; J24F02 supplies that missing direct proof.

The first hosted run retained complete per-case JSON in the job stdout, audited separately from the harness. Its upload-artifact step warned that its relative glob matched no files, **so no downloadable raw JSON artifact is claimed for that original run**. A subsequent workflow-only receipt-path correction at `34377da8025197253651c2c68b07c26424e0c31e` requires absolute workspace output and nonempty file; its new exact-head run is independent pending evidence until actually checked.

## Primary question and mechanisms

The shipping `CMPCT._extract_chunked_verified` hashes all staged bytes and checks the signed logical SHA, then closes `mkstemp`'s original file descriptor and publishes via `os.replace(tmp, full)`. The original **verified inode** and the later **path name** have no atomic ownership link. A writer permitted to change the containing directory can rebind that name in between.

J24F02 uses an instrumented rendezvous at the actual Reader's final `os.replace` call, with original Reader source unchanged. At that point it confirms the staged regular file has precisely the original indexed length and SHA. It launches a separate child process to **rename the real staged inode to a quarantine name**, retaining its bytes and inode, and to **create a same-length different-SHA regular file at the original stage name**. The unmodified original `os.replace` then executes. This is a deterministic race, not an uncontrolled stress/luck trial. Positive control is ordinary extraction of the exact same archive by the exact same installed Reader.

## Direct results — 4 independent hosted representation/platform cases

| Host | Representation | Original indexed SHA | Published SHA | Reader return | Result |
|---|---|---|---|---|---|
| Ubuntu 24.04 | S_CHUNKS, 998 bytes | `c2798f6e3c1590b2...` | `73608b8374ae71c3...` | SUCCESS | FOREIGN BYTES |
| Ubuntu 24.04 | S_CDC, 1104 bytes | `e12c5f35853b8f6a...` | `d6c47d85a9cf0741...` | SUCCESS | FOREIGN BYTES |
| macOS 14 | S_CHUNKS, 998 bytes | `c2798f6e3c1590b2...` | `73608b8374ae71c3...` | SUCCESS | FOREIGN BYTES |
| macOS 14 | S_CDC, 1104 bytes | `e12c5f35853b8f6a...` | `d6c47d85a9cf0741...` | SUCCESS | FOREIGN BYTES |

**Every positive control reconstructed the exact original SHA and length.** Every attacked publication returned success and wrote the *child's* wrong-SHA bytes, preserving length. All original CMPCT archive SHAs were unchanged.

Distinct child actor PIDs and physical inode transitions were observed:
- Ubuntu S_CHUNKS `9441329 → 9441337`; Ubuntu S_CDC `9441348 → 9441349`; child UID 1001.
- macOS S_CHUNKS `2885235 → 2885236`; macOS S_CDC `2885241 → 2885242`; child UID 501.

The previous authentic verified inode remained accessible via a distinct quarantine name and still had the original correct bytes. This specifically rules out a mere mutation of the verified inode as the explanation. The parent only hooked the final-call rendezvous; the syscall used for final publication remained the real operating-system `os.replace`.

The audit independently extracted each case's structured job log and checked: two expected vectors, source SHA equals ordinary-control SHA, published SHA equals child-provided alternative SHA, published SHA differs from indexed original SHA, original and foreign inodes differ, no Reader exception, original CMPCT archive preserved, and separate child actor PID. **Both hosts satisfied all audit assertions**.

## Scientific interpretation and strong self-critique

- **Decisive negative:** The tested r24 verified chunked extractor's successful-return contract does not imply the published leaf represents the SHA-verified bytes when another actor can rebind the same private-stage pathname after SHA verification.
- **No generic remote exploit claim:** The child has write access to the staging directory and a deterministic scheduling rendezvous at the exact boundary. The experiment demonstrates a capability/atomicity flaw, not the likelihood of uncoordinated exploitation or privilege escalation.
- **No weakened integrity verifier:** Real archived SHA, stage SHA, source Git blob, untouched historical vector bytes and ordinary extraction control all passed. The failure is *after* successful SHA verification, in namespace publication.
- **No generalization to direct S_BLOB/S_SPARSE:** Those use different leaf-publication mechanisms and have separately owned containment issues. Windows/Android, ancestry races, symlink/hardlink alias cases, crash durability, and postpublication mutation are not covered.
- **No full-product benchmark:** Byte storage, CPU/wall, RSS, selective I/O, recovery/portability burden and maintenance were not measured. No core-release credit.
- **Instrument adversarial assumption:** The deterministic test interposes at a Python-level call, not random simultaneous scheduling; it leaves the final `os.replace` behavior real and uses a separate unprivileged child with only directory-entry authority. A higher-tier concurrency fuzz or a product candidate would still be necessary for comprehensive security assurance.
- **Recorded evidence gap:** Original run lacked downloadable artifacts because upload glob matched no files; stdout job logs are immutable external evidence. Evidence upload repair does not alter the hypothesis, source, vector, comparator or criteria.

## Decision, counterfactual, and next executable action

**Decision changed**: A previously untested concern explicitly excluded from J24F01's positive conformance scope is now demonstrated on the released Reader's actual frozen source. General lesson: *SHA verification of a temporary file and subsequent publication by its mutable name are different security obligations*. Before declaring an extractor transactional under writable-directory concurrency, look for any close/reopen or verified-inode-to-pathname handoff, then run a tiny stage-entry rebind discriminator rather than another large ordinary corrupted-archive cohort. This is a transferable prospective distinction but **does not justify editing Discovery Engine normative policy from one episode**.

The highest-leverage owner action is to treat staging namespace and publication as one physical custody boundary. Evaluate solutions under clearly declared actor capabilities (different UID directory writer, same UID process/procfd actor, privileged actor) and actual platform primitives; another `lstat` before `os.replace` leaves a check/use race. Retain J24F01 ordinary/corruption preservation; do not erase genuine frozen-archive positives. A repair must preserve prior output on integrity failure, source/index SHA, hardlinks and symlinks, portability and measured resource costs.

**Concurrency:** no competing narrow implementation owner found; #486 owns static frozen-vector publication evidence, separate security PRs own direct-leaf/ancestor issues. The result is handed to those owners via PR comments/issue, not force-written onto their branches.

**State:** research-only candidate; no shipping `src/` mutation, no r24 format, frozen controls, benchmark threshold, comparison semantics, version or release change; `docs/discovery/STATE.json` left alone because it is staleable and owned by separate reconciliations.

**Next independent executable discriminator:** Evaluate whether a private per-operation publication namespace can make the stage name inaccessible to directory-only peers across the full verification-to-commit lifetime while retaining cross-platform existing-target atomic replacement, or explicitly bound documented extraction safety to nonhostile destination directories. Any proposed fix must be tested against this frozen two-vector negative and the stronger existing direct-leaf/ancestor courts before promotion.
