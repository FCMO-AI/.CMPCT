# J24I09 — Source-staged compaction pathname rebind, result and handoff

Date: 2026-10-29 UTC  
Class: **SCIENTIFIC NEGATIVE FOR UNMERGED CANDIDATE**, not a published-release vulnerability or promotion result.

## Immutable provenance

- Product parent: [#723](https://github.com/FCMO-AI/.CMPCT/pull/723), exact `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`, `transactions.py` Git blob `8d1e46e1fdf408c1d95ce9091e25fa159f0e6264`, `builder.py` blob `387192edd783e02bf7a44a38945214bf9d6c183e`.
- Prediction immutable before implementation: `a762651302f5e9c2262fc205c2d6bb219d6ac269` ([prereg](2026-10-29-j24i09-compaction-stage-custody-prereg.md)).
- Source-installed scientific court HEAD `307e4d9d32879f95e17c0e845ffdd1f769fffdc9`; [Actions #40810399504](https://github.com/FCMO-AI/.CMPCT/actions/runs/40810399504): **SUCCESS** for scientific case, because it **confirms candidate vulnerability**.
- [Original hosted physical ZIP artifact #12869594288](https://github.com/FCMO-AI/.CMPCT/actions/runs/40810399504/artifacts/12869594288), SHA-256 `510cdec423c138f3ec502ce73d423d8ff57c9b0e2c974fa770245555af6ce471`. Contains physical source, normal archive, outside-sentinel after rebind, raw receipt, HEAD and product-source Git blob identities. ZIP CRC check PASS.
- Source-installation proof: wheel-installed Python 3.11.17 module files inside `site-packages` were byte-identical to checked-out Git code; no model-only replacement or mocked product write. A single test-only interposition swapped a closed stage path **before** calling original `Builder.build`.

## Direct measurements and observation

| Claim | Exact hosted observation |
|---|---|
| Same source, no interposition | Normal `compact_archive` returns valid 1,103-byte r24 archive, 10,432-byte exact logical content, outside sentinel unchanged |
| Stage creation and controlled substitution | `stage_created_regular=true`; `interposition_count=1`; `stage_rebound_symlink=true` |
| Unmodified product behavior | Original Builder completed without exception; `CMPCT(stage)` verify succeeded, so content checks did not protect stage inode |
| Outside write | Sentinel changed from original arbitrary bytes to **1,103-byte valid r24 archive** with SHA-256 `79e421625d6165ae75265be5ef08b5bbf1577f867f4ea0d5c6b8d695075bba73` |
| Final destination | `destination_is_symlink=true`; resolves to outside sentinel; previous destination bytes not preserved |
| Source archive | Unchanged |
| Filesystem artifacts | Zero leftover `.compact-` sibling entries |
| Court timing | Normal 2.366 ms; adversarial 1.806 ms (single observations; **not comparable performance result**) |

**Independent wire audit** (outside the original hosted test, without importing CMPCT): SHA/CRC validated ZIP; Python `struct` decoded exact revision-24 header/footer, SHA-matched both compressed indexes with system `libzstd`, decoded the single physical blob with independently checked CRC32+SHA-256, reconstructed the exact 10,432-byte member. **All three original hosted physical files**—source, ordinary output, overwritten outside sentinel—have identical complete SHA-256 `79e421625d6165ae75265be5ef08b5bbf1577f867f4ea0d5c6b8d695075bba73`, index SHA-256 `633174ff4e5c4803ba8f6e1dae21eddbc3495a417d187cdf77cc7f010193de93`, and member SHA-256 `e0d9a94da7e35c5bbcf9bd1f44c7bff58621ad4f9ca332f03091d2afc982542b`. The physical audit independently confirms file bytes, **not live destination symlink type**; that observation comes from hosted syscall results in the raw receipt.

## Causal interpretation and limits

The compactor closes the exclusive `mkstemp` descriptor, then calls `Builder.build(stage)` which reopens the mutable pathname via `Path.write_bytes`. Rebinding that name to a symlink changes where Builder's bytes go; verifying the logical archive through the same substituted pathname cannot prove the stage's inode or isolation. `os.replace(stage,dst)` ultimately publishes the substituted symlink.

**Necessary precondition:** an actor can already unlink/replace entries in the chosen destination directory. This court provides no independent privilege escalation, real-world race probability, remote exploit, different-UID sticky-directory access, or evidence of impact on released `main`. All filesystem objects were test-synthetic and nested inside a temporary directory; outside means **outside intended compaction staging**, not outside test isolation.

A separate pure POSIX syscall experiment (not CMPCT product evidence) found: `O_NOFOLLOW` rejects a symlink at reopening; **retaining the stage file descriptor alone preserves external bytes but not the final name-based publication** (which would still publish attacker symlink); an open `src_dir_fd` bound to the real private directory retained source inode identity across a concurrent parent-directory rename in its tested scenario. That suggests a repair must bind *write and publication* to authenticated staging identity, or stage in a directory whose parent/entries cannot be modified by the threatening actor.

## Decision and next action

**`VULNERABLE_STAGED_NAME_REBIND` CONFIRMED for #723 exact unmerged candidate under deterministic directory-entry rebind.** The simplest correct intervention belongs in the **existing #723 compaction owner**, NOT an independent duplicate implementation. Notification with evidence: [#723 comment 6486871643](https://github.com/FCMO-AI/.CMPCT/pull/723#issuecomment-6486871643).

Owner should make the same frozen J24I09 test reject atomically without changing outside sentinel or existing destination, and then prove live stage inode ownership, cross-host behavior, filesystem interference, resource/RSS/temp-I/O, crash safety and inherited release gates. Ordinary safe extraction remains unchanged. **Do not** treat full archive semantic verification as a replacement for file-descriptor and publication ownership.

General exact scientific HEAD suite: **782 PASS / 4 FAIL**, the four failures are v0.30 historical attribution/fingerprint assertions inherited from main, not caused by three new science/CI files. Separate Engineering Evidence passed on same HEAD after updating PR body to canonical headings; Native Core, CI Topology, Version Discipline, R36 Attribution and continuous fuzzing passed. The official performance workflow classifier reported success, **not** a new product promotion benchmark. No merge, release, version, format, frozen benchmark, Discovery STATE, product source or release policy altered.

## Counterfactual research lesson

The earliest prospective observable was visible before coding the compactor: `mkstemp` returned an exclusive descriptor but then code closed it before a name-based `Path.write_bytes` and name-based `os.replace`. That pattern identifies a general double-TOCTOU question (write identity, then publication identity). A one-case deterministic name-substitution test is cheaper than another extensive semantic archive suite for this risk. This is one result, not repeated causal evidence sufficient to change Discovery Engine policy.

**Unmeasured debt:** malicious namespace interleavings at other sites, cross-platform behavior after a fix, unprivileged non-sticky attacker ability, temporal probability, full crash/recovery, performance and resource boundedness. Scientific question decided; product remains blocked.
