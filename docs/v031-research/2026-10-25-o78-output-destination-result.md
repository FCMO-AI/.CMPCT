# O78 — Authentic Builder destination semantic falsifier: exact hosted result

**Research-only. 2026-10-25 UTC. NO merge, format, performance, release or product-code credit.** Stacked on [O75 owner #432](https://github.com/FCMO-AI/.CMPCT/pull/432) exact parent `878268e48be8a33ff6d5305ad25f22659cc6918d`.

## Prospective hypothesis and source custody

Immutable prospective real-Builder preregistration `100bdcb6944e7429431874071612c3d2ecdc7998`, `docs/v031-research/2026-10-25-o78-output-destination-prereg.md`, explicitly disclosed a preceding *stdlib-only local primitive probe*. Its findings did **not** count as preregistered CMPCT evidence. Experimental source head `a971fca33224ce28160c9583bf77f1350e32bd60`; installed candidate Builder Git blob `d92c78119e9613b2c3ae1886a8fba841dc313fca`; authentic previous Builder code at `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b:src/cmpct/builder.py`, Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. Instrument Git blob `aa50dec87d6673a0a4055c7c4ecc5101cccae2da`. Actual CI installed CMPCT non-editably and loaded the true historical code by Git object, not a rewritten simulation.

## Original hosted receipts — source exact

[Actions run 40189118918](https://github.com/FCMO-AI/.CMPCT/actions/runs/40189118918), job `121156138575`: completed **SUCCESS**; Ubuntu 24.04, `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`, non-root UID 1001, CPython 3.11. Raw [GitHub artifact 12596523070](https://github.com/FCMO-AI/.CMPCT/actions/runs/40189118918/artifacts/12596523070), independently downloaded ZIP SHA256 `7dbdcdd3c5fa0179975b97487061ac4a3f61d6b224f55c19bb1b7526e8`. Original `result.json`, JUnit, court log, commit and test source hashes preserved. **5 actual cases PASS; 0 skipped, 0 failed.** Each successful build emits the same complete r24 archive SHA256 `311e67a98ef2c24aaba04869393b04390a710e0a72cfeb1769e2179902e5e42b`; authentic `CMPCT.verify()==2` and `read('a.txt')` pass for successful builders.

| Existing destination | Authentic old Builder | Installed O75 Builder | Implication |
|---|---|---|---|
| ordinary regular file | inode retained after overwrite | inode changed by replacement | path/inode identity differs |
| symbolic link to alias | symlink remains; referent alias updates to new archive | output path becomes regular; original symlink referent alias remains previous archive | alias/namespace contract differs |
| hardlinked alias | alias updates to new archive | alias remains old archive; output points to new inode | shared physical identity broken |
| user xattr `user.cmpct_o78=keep-me` | xattr preserved on destination | xattr `<MISSING>` | **silent loss of existing output metadata** |
| read-only `0444` archive in writable parent | `PermissionError`, old archive remains | succeeds replacing output with valid new archive, retains 0444 bits | historical write authorization not preserved |

No O75 temporary stage files were left behind in these cases. The **positive O75 failure-atomic publication** remains valid under its previous controlled write/rename errors; O78 falsifies only **unqualified equivalence to old-output filesystem semantics**.

## Decision and semantic carrying cost

The highest-severity result is that correct new CMPCT bytes and a green Reader verification do **not** imply preservation of the prior output artifact's xattrs, aliased inode relationships or write authorization. This is separate from preserving *source* filesystem xattrs inside the archive. A plain `os.replace()` logically replaces the destination inode and cannot update all hardlink aliases in place. Mode-bit copying alone is insufficient. No threshold change can solve the semantic conflict.

**Owner action:** explicitly choose fail-closed admission for incompatible preexisting targets, an opt-in/revisioned atomic publish interface, or a separately proven bounded metadata+ownership preservation policy. A security-conscious design must consider symlinks, hardlinks, UID/GID, ACLs, xattrs, immutable flags and output write permissions—without assuming that preserving all aliases is possible under a namespace swap. Reconcile these choices with original O75 write-failure tests and unchanged release parity/economic gates.

## Evidence hierarchy and self-critique

This is **installed-product/scientific negative evidence** for a real local Linux filesystem, not a cross-platform release result; no macOS/Windows, network filesystem, concurrent writer, power-loss durability or generalized POSIX contract was measured. Archive controls use synthetic files and deliberately stable source trees, so this proves no source-snapshot property. `read-only` is non-root UID1001 on the observed host; elevated-privilege users may behave differently. Some file metadata is inherently inode-associated and may be incompatible with atomic namespace replacement. No CPU/RSS/wall/cold-I/O official performance matrix was executed.

General pre-existing release-lock failures and the latest-head-only benchmark skip remain independently unresolved. Research branch has **zero product source changes** and inherits owner O75 implementation; do not merge or publish without legitimate review and gate closure.

## Counterfactual and policy

A fast stdlib inode/alias probe would prospectively warn that replacement changes destination semantics before investing in cross-platform product work; however, the actual installed historical-Builder A/B was still necessary to establish whether CMPCT itself had additional safeguards. No evidence-backed general Discovery Engine policy change earned. Discovery `STATE.json` not mutated in a concurrent agent's shared cache. Durable handoff to [O75 original owner](https://github.com/FCMO-AI/.CMPCT/pull/432#issuecomment-6397112906) preserves the decision and next discriminators.
