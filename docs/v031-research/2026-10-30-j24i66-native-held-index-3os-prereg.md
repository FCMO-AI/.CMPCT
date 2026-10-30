# J24I66 — Independent three-host native held-index custody court (preregistration)

**State:** prospective, frozen before implementation. **Authority:** CMPCT AGENTS.md and v0.31 native/format/release/discovery law. **Base:** PR #847 exact `c5d26ab113bd3edf830711da3612b31fa54d613b` (stacked on #844 and #807). **Source/format:** Rust native r24; no ABI/format/product source mutation authorized in this episode. **Owner:** phased3 J24I66. **Do not merge/release from this experiment.**

## Single primary question
Does the #847 C ABI native `cmpct_verify_complete` preserve a single authenticated member-table identity across **a stable same-inode A→B rewrite** on *each* of Ubuntu 24.04, macOS 15 ARM and Windows 2025, rather than merely on Ubuntu? These OSes have materially different file-sharing/loading semantics. Can independent positive controls and a same-handle restoration control rule out an unsupported generic I/O failure?

## Baseline and existing owner boundary
#846 is a real Ubuntu-only negative: pre-fix C ABI returned success for opened A after valid B overwrote its inode. #847 has Ubuntu green on code HEAD 70a6fdeb… and final doc HEAD c5d26ab…; the original 386-byte frozen A/B archive vectors and independent physical evidence were preserved in J24I63. #850/#852/#854 own **installed-wheel**, macOS architecture and packaging; this episode owns only standalone Rust cdylib C ABI portability, not shipping wheel or SDK compatibility. #574 owns shared Discovery Engine state. #853/#848 own Reader journal/replay economics; no overlap.

## H1 and independent controls
Reuse the **already authenticated** two immutable 386-byte, revision-24 r24 RAW archives from J24I63, each with the same 64-byte payload but a different signed primary/tail index member name. Pin SHA-256: A `5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d`; B `9528d510467ae30694d0ea7d69b0ca6b4896e84ebc99f399d498843f1aca79bc`.

Expected controls on each host:
1. Fresh C-ABI A and B handles separately `verify_complete=(0,1)`; C ABI calls report a real count.
2. Hold a C-ABI A handle; overwrite that **same filesystem object** with all B bytes using a separate write handle, no rename/truncation; prove dev/inode, path and size continuity and the *new* on-disk SHA B. Then `verify_complete` on old handle returns `(-7,0)`, while a newly opened B handle succeeds.
3. Restore A in-place; the original A handle may again succeed only when its authenticated 68-byte opening header is restored. Fresh A must succeed. A too-small or malformed buffer must not produce a false success.
4. Direct standalone CLI `cmpct-native verify` on both valid fixtures, if supported on host; do not weaken/skip this on a host merely to make CI green.
5. Record provider OS, runner architecture, source SHA, fixture digests, Rust/C ABI result triples and physical inode/size observations in a per-host JSON artifact. Strict independent aggregator requires all 3 corresponding exact-source artifacts and expected positive/negative values.

## Cheapest decisive rung / cost
**No new compression mechanism, new corpus or full product benchmark.** Run a fixed 2×386-byte fixture with the **actual Rust cdylib** on three GitHub hosted runners (one Cargo release build each). Target new workflow and pure stdlib Python instrument only. Stronger same-process dual-ABI and historical negative already exist on Ubuntu. A local C/Python ownership oracle would be weaker than the actual Rust C ABI. No performance speed, memory, archive-byte or release credit is possible from this rung.

## Disproof, controls, ambiguity, scope
Any host with A/B positive-control failure, inability to perform same-inode stable rewrite while preserving identity, mismatch of source/fixture fingerprint, C ABI success on held stale A, nonzero verified count on error, incorrect restoration behavior, missing output/CI run, or unsupported native library is a **scientific FAIL/INCONCLUSIVE** with cause reported; never skip that host. Distinguish platform I/O constraint, runner infrastructure and actual integrity failure. If Windows sharing semantics prohibit mutation while the Rust descriptor is open, that is meaningful portability behavior, not automatic product regression. The expected Linux green is a preexisting control, not independent invention credit.

Keep format revision 24, frozen benchmarks/thresholds, native ABI, reader correctness and existing tests unchanged. The test covers only **stable between-call** mutation, not simultaneous same-inode write races, snapshots, installed wheel or Python public verify parity. No compression gain, release, version or global policy claim. This material episode ends with provider-backed green/red and per-host identity receipts, or an explicit evidence blocker. Do not duplicate a current sibling implementation.
