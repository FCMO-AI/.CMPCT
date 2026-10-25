# O106 — Genuine Reader extraction blocks on a pre-existing FIFO output leaf

**Date:** 2026-10-25 UTC  
**Decision:** `CONFIRMED_SCOPED_POSIX_AVAILABILITY_FAILURE` (research evidence).  
**Promotion:** no product change, no merge, no release, no new format or API contract.  
**Prediction frozen first:** [O106 preregistration](2026-10-25-o106-reader-fifo-extract-prereg.md), commit `5c0a66d22ea3b2fc0ab727749e0c3c9cafcf1cce`, prior to product test and hosted results.

## Exact source, work surface and controls

- Canonical repository: `FCMO-AI/.CMPCT`; prospective v0.31 source authority: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Released v0.30.0 and physical format revision 24 unchanged.
- Original Reader `src/cmpct/reader.py` Git blob: `e716233403dabd0966863c45635e18fa5ac6afb8`; Builder Git blob: `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Fixed instrument `tests/test_v031_o106_reader_fifo_extract_court.py`, Git blob `69c6e8e43a89d712f404fac3471be9b9b963ffd3`, at result-bearing commit `d195340fae03a8ca664de661a695b82f47a0dcba`.
- Exact test method: genuine installed CMPCT `Builder(root, workers=1)` creates a revision-24 archive from an independent 4,096-byte SHAKE256 pseudo-random binary source; `CMPCT.verify()`, full `read()`, and a real `S_BLOB` selection are checked before testing extraction.
- Three independent disposable Reader child processes on **one identical physical archive** per host: extract into a fresh destination; extract into pre-existing ordinary regular-file leaf; extract into pre-existing unwritten FIFO leaf. Parent enforces eight seconds per child. All normal controls compare exact source SHA-256 and exit status; FIFO timeout must also show `O106_CHILD_INDEX_OPENED` on child's captured stdout to separate archive-open/startup from destination operation.
- Cross-platform evidence deliberately restricted to Ubuntu 24.04 and macOS 14. Windows named pipes, network filesystems and live adversarial namespace races are out of scope.

Source member SHA-256, identical on both hosts: `d453c131a94baf31e3092e63981bb1fb789ffe7041b612122cc84e4fa2fbdb12`. Host-specific physical archive SHA-256 differs because of unnormalized captured filesystem metadata; within each host all three arms match **exactly**.

## Direct scientific observations (same-input replicated)

Final tightened instrument executed through [Actions #40224687119](https://github.com/FCMO-AI/.CMPCT/actions/runs/40224687119) on source-exact result-bearing HEAD `d195340fae03a8ca664de661a695b82f47a0dcba`.

| Host | Fresh destination | Existing regular leaf | Unconnected FIFO leaf | Exact physical archive for all three arms |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04 | reconstructed identical bytes | reconstructed identical bytes | child exceeded **8 s** timeout | `a7150dd566898747fb9862959be3403dc3423740e9b5a02b78aea206fb37c96e` |
| macOS 14 | reconstructed identical bytes | reconstructed identical bytes | child exceeded **8 s** timeout | `970ad3fed49f4a9d3a8db664c38d78c1856b773e0368b996b31588c8cef012d1` |

Each host: **3 executed / 3 scientific PASS / 0 FAIL / 0 SKIP**. These scientific PASS outcomes prove the preregistered **product failure**, not a safe Reader. The original FIFO remains a FIFO, and original source bytes remain unchanged. The captured child marker `O106_CHILD_INDEX_OPENED` is required within the FIFO timeout handler; neither observed block is simply an import or index-open delay.

The earlier source-exact pilot [Actions #40224313966](https://github.com/FCMO-AI/.CMPCT/actions/runs/40224313966) likewise returned three scientific passes on each host, but used independently rebuilt source archives across trials. That weaker physical-input pairing was corrected prospectively without changing the prediction, timeout or expected outcome. The intermediate one-archive [Actions #40224466371](https://github.com/FCMO-AI/.CMPCT/actions/runs/40224466371) also completed **3/3** on each host.

### Durable machine evidence and digest

- Ubuntu final artifact **#12611220404**, digest `sha256:6e53d3d2fa6603db46cbeb5b116a50f5dc324693f9a41cdf60169d375ff6e6ad`, JUnit, raw console, instrument/blob identities and JSON receipt.
- macOS final artifact **#12610732242**, digest `sha256:4ef4a8f8a126d4965fccd3b1d76de5ec21680cfe87e562e09e9997b4aa16cc28`, corresponding JUnit/log/result files.
- Test logs include `O106_CASE`, `O106_REAL_READER_FIFO_TIMEOUT=CONFIRMED` and `O106_AUDIT`; first two control rows report `reconstructed_exact`; FIFO row reports `timeout_expected_hypothesis`.

## Mechanism and alternatives

Released Reader `extractall()` writes normal `S_BLOB` members using `os.open(full, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|..., mode)`. Under POSIX, opening an unconnected FIFO write-only **without O_NONBLOCK** waits for a reader. The direct installed-product comparison and source behavior jointly support that explanation; no per-syscall trace is claimed. A simpler POSIX FIFO microprobe would not earn product evidence. A platform-wide assertion or remote exploit claim is unwarranted.

Existing PR #269 (Reader static destination symlink containment) checks pre-existing symlink components and non-directory *ancestors* via `lstat`; source inspection shows no explicit nonregular **leaf** prohibition in that preflight. Whether the *modified #269 Reader* reproduces O106 has **not** been experimentally executed in this research, and must be distinguished from the confirmed pristine-Reader result. Builder FIFO behavior (#445/#448) is a separate issue.

## Strongest negative, counterfactual and limits

The ordinary leaf remains compatible, so rejecting **all** preexisting output objects would needlessly regress functionality. Replacing every leaf atomically instead would change inode identity, hardlink, xattr, permissions and crash semantics, and may not address a symlinked ancestor; this cannot be silently promoted as a shortcut. Our tests measure **availability until an 8 s timeout**, not infinite blocking, overwrite of an external target, exploitability, or complete output-namespace race safety.

**Disproof rule:** a source-exact installed Reader promptly rejects the FIFO, or a matched ordinary control times out/fails, would falsify/narrow the observation. No such event occurred on these two runners. No workload-specific mechanism or adjusted evaluator threshold was used.

**Counterfactual discriminator:** the static `O_WRONLY` FIFO semantics was predictive, but only an installed product with an identical-archive regular-output control could prove the Reader path was truly reached. That is a reusable experiment-design lesson, **not** sufficient repeated evidence for Discovery Engine policy changes.

## Convergence handoff

Inform Reader destination owner #269 and composition owners (#294/#381) that normal direct `S_BLOB` (and potentially `S_SPARSE`) extraction into existing FIFO leaves requires an explicit fail-closed type contract or carefully designed nonblocking descriptor opening. Preserve previous ordinary regular-file output behavior and refusal of symlink/hardlink external aliases. `S_CHUNKS`/`S_CDC` use separate temporary-file publication and need separate semantic treatment. Prove any candidate on authentic same-input filesystems and cross-platform controls, then account for reader/extractor CPU, metadata and inode semantics, and eventual full release gates.

**Decision:** `CONFIRMED_SCOPED_POSIX_AVAILABILITY_FAILURE` — implementation deferred to existing Reader safety ownership, no product/release credit. O106 research lane is decision-complete; return to higher-value different-family product/convergence work.
