# J24H03 — source-exact Windows Builder × dependency-ordered Reader composition (preregistration)

**Status: FROZEN BEFORE ALL J24H03 SOURCE/COURT EDITS, 2026-10-27 UTC.**
**Not a release or merge authorization.** Public v0.30.0; revision 24 unchanged.

## Authority and ownership
- Stack from J24H02 owner #621 at `becb9587d8eeaf3024e88c28859e6adc7a8cd4b7`; its Reader blob `243b46d68211a2b125e07f7c92966535f5f0bdc9` is inherited EXACTLY from #262 at `24f4de54a86f4aef33a1bf684e504a04bcea5ad5`.
- The Builder owner is O47 #401 at `29d9688ae6bff6d1eccc27f019893866abe5b5c3`, Builder blob `6f60dfe63742ff4b777f959a15d6fb828ae29610`. The original current stack's Builder blob is `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- This J24H03 stack must transplant the FULL exact Builder blob from #401 without editing either owner's branch or changing Reader/Writer/Validator/Codec. A source-exact merge-of-capabilities experiment, not independent reinvention.
- J24H02's original Writer append_rename physical archive and negative/positive Reader experiment are inherited unchanged. The last hosted run #40587548886 reported Ubuntu/macOS PASS and Windows Builder source-identity failure before Reader comparison.

## Falsifiable primary question
Does the real O47 Builder's Win32 `os.stat` physical identity acquisition, composed byte-exactly with the real #262 Reader's dependency-ordered hardlink materialization, reconstruct first-party Writer `append_rename` forward hardlinks with correct bytes AND shared OS inode identity on Windows while retaining authentic Ubuntu/macOS behavior?

### Prospective prediction
1. On all three hosted OS, two genuine source hardlink paths are serialized as one `K_FILE` owner and one `K_HARDLINK` alias; a third same-byte but **independent** file stays separate. J24H02 requires one regular/one alias and a Writer rename that sorts alias before owner.
2. The unmodified J24H02 historical Reader controls must still reject the signed forward-alias journal archive; the candidate inherited Reader must accept, verify, selectively read and extract with `os.path.samefile` true. Exact archive bytes and SHA must be shared by historical/candidate Reader subprocesses on each platform (NOT a cross-platform fixed hash: OS source metadata may legitimately differ).
3. On Ubuntu/macOS, Builder output must retain original J24H02 physical archive SHA `b608efbb0b11bc6a42c1c1299fc5fde94e303120e0c685f96cff6fc99d08eee9` under the same Builder/Writer inputs (if environment-dependent metadata changes this comparison remains a substantive negative to diagnose, never a silent pass).
4. Original O47 full test must run **unchanged** on all three hosts and must prove distinct equal-byte input is not silently merged.
5. No format version, schema, SHA/CRC, source-tree semantics, integrity gate, historical controls or benchmark thresholds change. No product credit from CI status alone.

### Cheapest decisive court
- A bounded three-host GitHub Actions job checks out the precise event HEAD and archived #261 historical Reader HEAD `3b852473cda137b8333fd0f214e1d4bcaf0788a3`; it installs source-authentic Python packages and captures raw receipts.
- Reuse J24H02's three-process Builder → Writer → historical negative → composed candidate positive oracle **unmodified**.
- Reuse #401's two-case O47 test **byte-for-byte**; lock its Git blob `6c00ae49eea075957453d6d7238d988add6eedee`.
- Source-lock new candidate Builder to `6f60dfe63742ff4b777f959a15d6fb828ae29610`, Reader to `243b46d68211a2b125e07f7c92966535f5f0bdc9`, historical Reader to `e716233403dabd0966863c45635e18fa5ac6afb8`. Bind event commit, stash per-host raw receipts even if tests fail.
- Preserve direct historical full-archive identity if environment supports it; record any divergence without conflating expected Win32 changed semantics with random regression.

## Stronger alternative, opposing explanation, kill conditions
- Simpler control: run #401 alone (O47), #262 alone (forward extract) and J24H02 independently; these already prove each part separately, but not their **joint** Windows product path. The joint court must produce new information or be retired.
- Alternative explanation: O47's Builder update might not be sufficient after Writer append_rename on Windows, or #262 may assume POSIX-specific inode/link behavior despite `os.link` support. A cross-source test distinguishes both.
- Kill/narrow on a same-byte distinct source coalesced, incorrect type/owner, incorrect signed journal generation, any archived hash mismatch between historical/candidate readers, changed Reader blob, partial/truncated output, incorrect inode, invalid archive accepted, predecessor refusal absent, native import/install failure unresolved, or any host failing.
- Zero-input test size advantage is **not** claimed; corrected Win32 archive may differ from the old Windows copy-only output because the prior output lost user inode semantics.
- Whole-product costs remain unknown: additional Win32 `os.stat` per regular entry, #262 alias planning memory, extract/read/open CPU/wall/RSS, temp I/O, preexisting-target path race, symlink/directory pivot, network filesystems, native cross-language parity and official release benchmark.

## Coordination
#401, #262 and #621 are existing owner PRs. New J24H03 branch must target #621 and remain DRAFT; no changes to those owners, no `docs/discovery/STATE.json` mutation, no force pushes, no unrelated promotion. After real evidence, communicate complete source SHA and negative/positive receipts to owners and issue #619; no duplicate fix/merge without owner consent.

## Outcome discipline
This file records predictions, not results. Append outcome/lesson in a separate result note after an exact-head observed run. CI queueing or skips are not scientific evidence. If the negative is explained by infrastructure, amend only infrastructure prospectively; do not alter immutable historical experiments or broaden a success claim.
