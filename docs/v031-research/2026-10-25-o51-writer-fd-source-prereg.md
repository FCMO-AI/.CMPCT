# O51 — Writer regular-source descriptor admission (preregistered)

Date: 2026-10-25 UTC. Product boundary: `src/cmpct/transactions.py`; exact original Git blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c` at `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. No output format change. Research negative: [O49 #404](https://github.com/FCMO-AI/.CMPCT/pull/404), installed Ubuntu/macOS run `40157632143`; unconnected real FIFO causes original `cmpct update` to hang >3 seconds.

## Prospective hypothesis and exact invariant
Open a source with `O_NONBLOCK` on POSIX, immediately check `fstat` for a regular inode and read all bytes through **that same descriptor**. An already-present FIFO must fail promptly, and replacing an observed path with a FIFO immediately before `open` must not turn a well-intentioned precheck into an indefinite blocking read. Stable regular file (including symlink-to-regular, inherited path semantics) must update an authentic revision-24 archive and preserve strong SHA verification; a separate same-bytes control is not a hardlink proxy. An unsupported source must not mutate the archive's complete SHA or last committed generation.

## Controls and falsification
Strong simplest control: preflight `lstat` followed by historical `Path.read_bytes()`. Reject this if a deterministic path-switch-before-open can still block or accept a FIFO. Other alternative: `os.open(O_NONBLOCK)` + descriptor `fstat`, chosen because it binds file type/content/metadata to the same opened object without requiring a new format or portable custom Reader. More ambitious solution: pinned handle, snapshot/sealed bytes and transaction-wide lease; independent Writer owners already occupy lease/salvage/namespace lanes. This small fix **does not** claim multi-process transaction safety, immutable bytes under adversarial concurrent in-place writes, or prevention of network FS stalls.

Kill the candidate if POSIX FIFO takes >3 seconds to refuse, archive changes after refusal, POSIX symlink-to-regular regresses, ordinary same-source archive byte parity or update semantics change, Windows ordinary updates regress, any original O49 positive control fails, or source/installed test custody is incorrect. Stronger held-out race: hook the source open to replace a regular pathname by FIFO immediately before the actual open; reject promptly. Dynamic source mutation that preserves all stat observations remains a stated limitation.

## Evidence ladder and economics
1. Compile and static source mechanism sanity; preserve original O49 negative.
2. New actual `append_update` and independent CLI subprocess installed-package POSIX/Windows tests; JUnit and source SHA recorded.
3. Cross-host inherited Writer/Reader security/general and full official ABBA parity; no release or merge until exact-head source-bound review.
4. Count extra filesystem calls and record create/update wall CPU/RSS if performance debt affects admission; normal r24 codec/size policy remains unchanged.

## Concurrency and ownership
This branch is an independent O51 source-*admission* fix stacked on frozen v0.31 development, **not** a rewrite or supersession of PRs #247/#295/#304/#311 transaction-wide lease and Writer composition, or O48/O50 Builder. A later owner must compose descriptor admission with transaction-wide leases. Do not alter those branches, frozen comparators, Discovery Engine state, thresholds, or release authority. Classify hosted failure by executed test vs infrastructure and preserve any red.
