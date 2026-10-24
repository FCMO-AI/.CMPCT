# v0.31 Win32 / APFS namespace admission — exact-owner integration O0

Date: 2026-10-24 UTC. **Prospective preregistration before source composition.**
Status: SCIENTIFIC INTEGRATION QUESTION; not a release/promotion decision.

## Frozen source owners and question

- Apple APFS source owner: PR #334, HEAD `be60184c76bd89da7d2f31614717e174393907fc`, branch `agent/phased1-v031-apfs-normalization-alias-20261024`. Parent for this branch; native Apple O1/O2 source is preserved.
- Windows source owner: PR #332, HEAD `dff03d03fa7d9c7e8b3c26c002e74c8cd49fa2af`, branch `agent/phased1-v031-win32-member-namespace-court-20261024`.
- Common product ancestor: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Released product v0.30.0, physical format revision 24.
- One question: **Can the exact Windows and macOS destination namespace guards operate in a single Reader, preserving all original specialized courts and byte-distinct POSIX extraction?**

## Hypothesis, simpler control and kill conditions

Minimal composition, not policy redesign: copy the Windows `canonical_windows_extraction_key` helper exactly alongside the unchanged Apple `macos_comparison_component`; add the original Windows-only checks/import into Apple Reader without altering Apple's normalization and logical-hardlink guard. Import each owner's tests and exact Windows workflow unchanged; add a tri-platform union court on Linux, Windows, macOS calling BOTH originals on one installed product.

Strong simpler control: separate independent green PRs #332 and #334. This is insufficient for promotion because changes overlap in `reader.py` and `path_policy.py` and may conflict. The combined SHA, not either owner SHA, must actually run.

Kill/narrow if any original control fails, if a platform guard runs on the wrong host, if the source implementation of either owner is weakened, or if any output tree differs on legitimate POSIX cases. Classify CI installation/host problems separately from product regressions. The union court itself must not hide failed subprocesses with pipelines, skips, catch-all exception handlers or edited assertions.

## Predictive evidence matrix (before results)

- `tests/test_path_policy.py`: shared portable lexical control, all hosts.
- `tests/test_v031_windows_member_namespace.py`: full original Windows owner suite, including actual Windows extraction/device/drive/case checks; Linux/macOS POSIX positive preservation and stdlib derivations.
- `tests/test_v031_apfs_namespace.py`: full original APFS owner suite, including actual Mac normalization and hardlink exact-owner cases, non-Mac POSIX positive preservation.
- The new union workflow must bind all three to exact Git HEAD, install the authentic CMPCT package, execute on `ubuntu-latest`, `windows-latest`, `macos-latest`, and expose skipped-by-platform counts rather than claiming all tests ran everywhere.
- Re-read exact-head general/native/CI. Do not accept an administrative SUCCESS on `zip-parity` as a benchmark unless substantive performance jobs executed. Release/general suite inherited failures stay visible.

## Alternatives / exported costs / negative scope

Alternative: globally normalize/rewrite r24 archived names, rejected for loss of POSIX fidelity. Alternative: new filesystem comparator/rewrite, rejected: changes owner semantics and increases risk before first compositional falsification. Existing Windows prefix implementation uses repeated prefix joins (potential depth-dependent cost); Apple uses node IDs. This union does **not** claim bounded optimal performance or a complete filesystem-collation model. Neither guard solves pre-existing symlink/reparse-point TOCTOU, moved directory-identity containment, 8.3 aliases, or exact APFS native Unicode-9 table equivalence. No on-disk representation, ABI, Builder, Writer, frozen benchmarks, thresholds or release gates change.

Decision requires authentic hosted tri-platform test on one SHA; previous owner successes are controls only. Preserve any failures and report genuine missing evidence.
