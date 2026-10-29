# J24G54b — confirmed in-range signed fsmeta misbinding after a valid journal delete

**Observation cutoff: 2026-10-29 22:41 UTC.** **Result: CONFIRMED / TWO-HOST PHYSICAL PRODUCT CANDIDATE DEFECT.** Experimental source only, no product correction, merge, version, format, benchmark or release. Research branch is stacked on #783 source `47ddedbeb844a8d59e9d142910c6705301214ce0`. Preregistration `054f0b3630f08de8f20c701682112a1122f0d177` predates new test/referee work. [PR #786](https://github.com/FCMO-AI/.CMPCT/pull/786), [issue #787](https://github.com/FCMO-AI/.CMPCT/issues/787).

## Question, evidence rung and direct outcome

Can `preflight_archive()` **accept** a correctly signed and committed journal archive while associating its sparse xattr with the wrong surviving path, solely because a stale ordinal remains inside bounds? **Yes, on Ubuntu 24.04 and macOS 14** in an actual Builder/Writer/installed-package test. This is a materially different outcome from J24G54a's out-of-range false rejection, and cannot be resolved by merely clamping/dropping out-of-range signed attributes.

Authenticated initial sorted files: `a-early.bin`, `b-delete.bin`, `c-owned.bin`, `z-late.bin`. Builder captures a real binary native xattr on `c-owned.bin`, at initial ordinal 2. Actual `append_delete("b-delete.bin")` commits a signed journal delta. The surviving sorted index is `a-early.bin`, `c-owned.bin`, `z-late.bin` (indices 0,1,2). Reader remaps that same signed attribute to `c-owned.bin` at 1, runs `verify()==3`, and strictly restores the native binary xattr to `c-owned.bin` and not `z-late.bin`. **But** preflight **accepts** (`files=3`) while its independently inspected effective index still binds the signed xattr to `z-late.bin` at old ordinal 2. A no-xattr control with identical name/delete topology has empty metadata maps on both paths and passes.

<preflight semantic vs Reader> here means comparing effective index metadata returned by `validation._load_effective_index` with Reader's effective index, not that the public `preflight_archive()` response exposes an xattr map (it only exposes counts). No physical xattr misapplication by Reader is claimed in this case. It is a **structural preflight semantic misbinding/false validation** even though its high-level return value alone hides the discrepancy.

## Exact-head hosted evidence and independent physical referee

[Actions #40967564092](https://github.com/FCMO-AI/.CMPCT/actions/runs/40967564092) at source-exact commit `6731d72fee1bc8f174f9b68eefe76b4c003187c4`: **Ubuntu 24.04 SUCCESS, macOS 14 SUCCESS**, each 6/6 installed tests PASS including unchanged four J24G54a cases plus both J24G54b cases. Installed Reader, Validation, Transaction Writer and Builder matched checkout source bytes, with Git blobs identical to inherited #783 product. Each host also ran two **independent** physical referees, neither importing CMPCT. J24G54a referee rejected **5/5** tampered physical inputs; J24G54b referee rejected **4/4** tampered physical inputs (source/checkpoint/delta/footer/record integrity). These are deterministic mutation checks per host, not 18 independent real-world archive samples.

Physical payload SHA-256 for the J24G54b native-xattr case was the same on both systems:
`ba203dfcdb92811b2f4dbf6e3c1b7f4661b485e8c37981b87f3d0f50b9f5d7e3`.

Evidence retained by provider:
- [Ubuntu ZIP artifact #12938718017](https://github.com/FCMO-AI/.CMPCT/actions/runs/40967564092/artifacts/12938718017), GitHub-reported SHA256 `1c482969436bbd54a178e6b69f98d26f4859fbb5860ee9f412068c3bb3d6b0cd`.
- [macOS ZIP artifact #12937304815](https://github.com/FCMO-AI/.CMPCT/actions/runs/40967564092/artifacts/12937304815), GitHub-reported SHA256 `156c59be291912bfbf574a7f1fe4e260c254f6b29b9eaf7fca63e3b908330a78`.

The independent referees ran on the hosts and authenticated the original Builder index, embedded checkpoint and actual deleted-row footer, plus physical records. ZIPs have not been separately downloaded for an additional local audit. All result claims are bounded to this exact unmerged candidate. There was no run of the published v0.30.0 wheel, no full-product benchmark, and no cross-platform privileged UID/GID restoration proof.

## Strongest negative and counterfactual

A naive future repair that merely detects `ordinal >= len(files)` would close the **out-of-range false rejection** but leave **in-range silent misbinding** untouched. The correct generalization is *logical identity-preserving effective replay shared between Reader and validator* for both acceptance and metadata meaning. The decisive prospective discriminator was deleting a middle row rather than the last, keeping stale ordinal 2 inside a final list of three. This was recognizable from the source-level structure once original J24G54a found the mismatch; J24G54b's actual first-party physical proof is the stronger validation rung.

No product improvement is claimed from a research-only test. A future owner fix must prove the path-bound signed values before/after deletion/rename/put and full 64-generation checkpoint, reject impossible same-inode xattr requirements and malformed history, and preserve archived bytes/fallback/recovery. CPU/RSS/storage and benchmark gates remain unmeasured. No change to discovery policy or shared STATE is justified by one family follow-up; #574 retains its state reconciliation ownership.

**Decision:** confirmed two distinct failure modes with one root cause, not one example. Issue #787 is an implementation/release blocker for candidate owners. Keep #783/#778/#773 branches unmodified; send this additional result to those owners.
