# O49 — authentic Writer FIFO source availability falsifier (negative product evidence)

Date: 2026-10-25 UTC. **CONFIRMED SOURCE-BOUND PRODUCT AVAILABILITY DEFECT; NO FIX; NO RELEASE.**

## Prospective evidence
Frozen development base `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; original Writer `src/cmpct/transactions.py` blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`. The real code reads `source.read_bytes()` before testing `source.stat()`; a FIFO with no writer can wait forever at open. [Issue #403](https://github.com/FCMO-AI/.CMPCT/issues/403) supplied a prospective independent cheap primitive observation, and preregistered scientific contract landed at commit `53b4c50cc99d7e3ae0909da649fd4848c789650b` BEFORE this product experiment was implemented. Original Writer code and release law untouched.

## Decisive installed product court
[Actions run 40157632143](https://github.com/FCMO-AI/.CMPCT/actions/runs/40157632143) at exact research HEAD `fc9d30fb022ae2f00b47b8e2882414a2c61f1d50`. Each job installs CMPCT externally into site-packages, verifies `cmpct.transactions.__file__` is not under the checkout, logs Writer blob and checks JUnit.

Ubuntu job `121062302951`: **2 passed (3.12s)**. macOS `121062302793`: **2 passed (3.22s)**. Windows `121062302968`: **1 passed, 1 POSIX-only skipped (0.14s)**.

The first case on every host creates and verifies a real revision-24 archive, invokes real CLI `python -m cmpct update` with a regular-file source, then checks exact changed payload and strong Reader verification. On POSIX the second case calls `os.mkfifo()` to create a real FIFO with no writer and invokes the exact real CLI update in a *separate killable process*. The child fails to terminate inside the prospective **3.0s** bound and must be killed. The original archive's complete SHA-256 and last valid member remain unchanged. A green scientific court here **proves the negative**, not a healthy Writer.

### Direct supported claim
On Ubuntu 24.04 and macOS 14 with the exact installed historical Writer/CLI, a transaction update from a real FIFO with no writer fails to return within 3.0s whereas ordinary updates complete normally. This is a high-confidence availability/denial-of-service risk at the source-open boundary. The test does not establish arbitrary remote exploitability, persistent corruption, or all filesystem/device scenarios.

## Product and cost accounting
No production source was changed. No CPU/wall or archive-size improvement, no remediation, and no release confidence credit. The only measured bound is the deliberately short 3.0s child-process timeout. The exact normal update confirmed strong valid-byte reconstruction. Windows POSIX special test skipped explicitly; no Win32-pipe inference.

## Alternatives and next disproof
A naive pre-open `source.lstat()` / mode check rejects stable FIFOs but can be bypassed by source replacement between check and open; do not claim complete TOCTOU protection. A descriptor-bound, nonblocking open/typed `fstat` and full source-byte custody must be assessed against allowed symlink semantics, regular-file update behavior, crash-atomic footer policy, Writer leases, and owned branches #247/#295/#304/#311. An owner-controlled candidate can be evaluated with these original tests changed prospectively to require *prompt deterministic rejection* (not timeout), plus hostile replacement races and identical regular-file parity. No evaluator, archived negative, or thresholds may be weakened.

## Discovery and concurrency
This is a different `transactions.py` surface from Builder O48 and Win32 Builder hardlink #401, not a duplicate product implementation. Current scientific outcome upgraded Issue #403 from unverified hypothesis to **confirmed scoped real-product negative**; retain historical text as the preregistered prediction. This episode requires no change to global Discovery Engine policy or stale state cache. Its highest-value next action belongs to Writer source-admission owners, not more FIFO timeouts.

**Research PR #404 remains DRAFT. No merge, no code productization, no release.**
