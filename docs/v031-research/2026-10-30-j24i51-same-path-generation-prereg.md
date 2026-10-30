# J24I51 — same-path, same-inode signed journal generation authority court

**2026-10-30 UTC · PREREGISTRATION BEFORE IMPLEMENTATION.** Parent: [#807](https://github.com/FCMO-AI/.CMPCT/pull/807) `0b80ecb9b1742a6c20756f4c9e8e097103881cb4`. Independent narrow semantic falsifier of a future direct Python→native complete-verify bridge. No native product, Python Reader, release/format/ABI, frozen benchmark, or policy changes.

## Baseline / competing explanations
J24I50e/f on the parent proves late pathname reopen can select another physical archive. This does **not** answer whether *unchanged pathname and inode* can still select different **committed generations**. The Python Reader replays latest authenticated revision-24 footer/journal generations, while Rust `Archive::open` currently parses the authenticated primary index only; its documented recovery support is incomplete. An explicit independent pathname API can still be correct for its narrower contract.

## Prospective discriminating test
Start from the **same committed, Builder-independent** `tests/conformance/v24-wavflac.json` vector used by the parent, preserving exact original SHA and prefix. On a copy, apply exactly two **public** Writer operations:
1. `transactions.append_update` of a deterministic new non-WAV member to the same archive. Expect Python latest `delta_depth==1`, two live content-owning files, complete verification success, new member observable; the native C ABI opened afterwards should still successfully verify the *one original primary* member, and enumerate only its original name.
2. `transactions.append_delete` of the original WAV member, without changing the pathname or inode. Expect Python `delta_depth==2`, one live new member, and successful full verification. Native `cmpct_verify_complete` should still return success for one **different** original member from the primary generation. Assert names explicitly, not merely equal counts. The original archive prefix and physical file identity must remain unchanged; footer generation evidence must be present.

Controls: native verifies the unmodified source; Python sees the unmodified source; public Writer returns valid generations; repeat verification on the exact same pathname; original golden is unchanged. Use the already-built native C ABI test harness, not a new fake parser, and preserve the parent tests.

## Decision / disproof
- If the predictions hold, **do not** replace already-open Python `CMPCT.verify()` by a newly pathname-opened native verification even without a pathname race: success may authenticate a different signed generation. Productization needs generation-equivalent owned-source verification or an explicitly narrower standalone API. This is **not** a claim the current C ABI is corrupt or that callers have already been wired unsafely.
- If Rust refuses a journal archive or observes the latest generation, the proposed mismatch is falsified or narrowed; preserve actual outcomes rather than changing the expected contract.
- If public Writer cannot create a legitimate signed generation or a current test requires a fixture rewrite, stop that local implementation, attribute the failure, and use the simpler read-only source audit instead.

No product speed, benchmark, full recovery, Windows swap, concurrent in-place mutation, or release credit is earned. Do not turn this into a blanket claim that all native operations must replay journals; this is a specific verification-contract bridge discriminator.
