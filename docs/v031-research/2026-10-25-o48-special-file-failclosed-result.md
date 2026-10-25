# O48 — Unsupported special entries must not produce a falsely complete r24 archive

Date: 2026-10-25 UTC.
Decision: **BASELINE SILENT-OMISSION DEFECT CONFIRMED; FAIL-CLOSED CANDIDATE VALIDATED IN INSTALLED THREE-HOST FOCUSED COURT; NOT RELEASED**.

## Source identity and prospective custody

Canonical published v0.30 main: `80c358f8824ec1b20d349c92ed94c898090969b0`. Unreleased development base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Baseline Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`.

Prospective prediction was committed first as `docs/v031-research/2026-10-25-o48-special-file-failclosed-prereg.md` in `af8f2233685b98f44ea28e653e0c9888ab318318`, before test construction and before product mutation. The original focused test bytes were run on the unchanged baseline and product candidate.

At source commit `865f49229f11c2770670d574f79d26c2655727bf`, the candidate changed one unsupported-type dispatch in `src/cmpct/builder.py`; new Builder Git blob `4c13d7b6a890ef27ba5a92bf3afe152345cf1078`. No format, parser, codec, Reader, Writer, native ABI, comparator or release law changed. The later focused-test hardening commit `c788cc8c39f285b3690ce7e5d7bbea513e3ba44a` retains that exact product blob.

## Decisive original-source negative (product semantics)

GitHub Actions [baseline run 40156871185](https://github.com/FCMO-AI/.CMPCT/actions/runs/40156871185), true clean-installed source from HEAD `18fb90582db64b8300e3a9b1054cc88632f930c4`:

- Ubuntu: **2 failed, 1 passed**; both real `os.mkfifo` and bound `AF_UNIX` cases printed `Failed: DID NOT RAISE OSError`.
- macOS: **2 failed, 1 passed**, same actual original failure.
- Windows: **1 passed, 2 skipped**, solely because POSIX FIFO and AF_UNIX fixture support was not assumed on Win32.
- All three successfully constructed and extracted the valid ordinary tree; this verifies the runner was exercising the actual installed Builder rather than failing at unrelated imports.
- The original source therefore could return success for a tree containing valid filesystem names it did not store. This was *silent omission*, not a collision in SHA-256, corrupted decode, or compression-performance regression.

This negative is preserved, not relabeled pending after the fix.

## Candidate result with original tests

GitHub Actions [candidate run 40156930147](https://github.com/FCMO-AI/.CMPCT/actions/runs/40156930147) on Builder product commit `865f49229f11c2770670d574f79d26c2655727bf`:

- Ubuntu: **3/3 passed**.
- macOS: **3/3 passed**.
- Windows: **1 passed / 2 justified skips**.
- Actual source identity and imports outside the repository checkout are recorded in every job log.

The candidate rejects any entry not recognized as directory, symlink or regular file during scanning, before `Builder.build` writes its output archive. This is an intentional refusal to create an incomplete archive; it does **not** reconstruct FIFO, sockets or devices.

## Held-out adversarial extension and CLI behavior

A later source-bound expansion preserves the fixed Builder blob and adds an end-user CLI subprocess test ensuring an already existing output file is left byte-identical if a source contains a FIFO. It also renames hostile special entries to lexically sort *after* ordinary entries, so the unsupported rejection occurs after earlier valid scans rather than only on an immediate first entry.

In the final test-bearing [run 40157214920](https://github.com/FCMO-AI/.CMPCT/actions/runs/40157214920) at `c788cc8c39f285b3690ce7e5d7bbea513e3ba44a`, genuine installed package results:
- Ubuntu: **4/4 PASSED**; `0.10s` focused execution.
- macOS: **4/4 PASSED**; `0.15s`.
- Windows: **1 PASSED / 3 SKIPPED** (the three use non-Windows POSIX FIFO/socket primitives); `0.08s`.
- CLI failure is nonzero and contains the refusal diagnostic. The byte-for-byte old destination is preserved. Valid trees still get repeat-deterministic archive SHA, strong Reader verify and exact restoration, including a symlink on POSIX.

These focused measurements are *not* create/extract throughput claims; runtime overhead and memory for large trees remain unmeasured.

## Alternatives, semantics, scientific boundary

Supporting special files in r24 requires a defined reversible wire and portable extraction model absent from this format. An explicitly lossy mode with disclosures is possible but creates product/API burden unearned by current evidence. The smallest truthful behavior is fail-closed by default.

The new behavior deliberately rejects trees previously accepted while silently dropping information. This is an improved success contract, not greater file-type capability. Stable input-tree snapshots and races against hostile concurrent changes are not solved. POSIX special files were tested only on hosted Linux/macOS; Windows special-file semantics, mounted network filesystems and other OS types are unmeasured.

Full release requires reconciling exact-head General Tests, native, fuzz, official r24/ZIP performance, actual installed package and any source-fingerprint checks. Administration-only GitHub workflow success or skipped jobs receive no credit. At this result cutoff, the dedicated focused court is fully result-bearing and passing; full general/performance checks remain separately tracked via GitHub. This draft authorizes **no merge/tag/release**.

## Concurrent ownership

[PR #401](https://github.com/FCMO-AI/.CMPCT/pull/401) owns the Win32 regular-file physical-hardlink `os.stat` repair, in the same Builder scan block. An explicit [coordination comment](https://github.com/FCMO-AI/.CMPCT/pull/401) was sent. Neither branch was overwritten. Integration requires a separate exact-source composition with both semantics preserved. No discovery STATE cache or policy change was earned.

A separate credible yet **unverified CMPCT product** hypothesis was opened as [Issue #403](https://github.com/FCMO-AI/.CMPCT/issues/403): Writer `append_update()` reads the source before checking its type and may block on a FIFO. The only direct experiment so far is a killable `Path.read_bytes()` FIFO primitive timeout; this is **not** an authenticated CMPCT transaction test and carries no product proof. It belongs to the Writer owners.

## Discovery result and counterfactual

Primary question: can r24 create an apparently valid archive that omits source FIFO/socket paths? **YES**, directly reproduced on two POSIX platforms with unchanged installed source. Candidate fail-closed admission repairs that bounded claim in the demonstrated cases. The cheapest prospective discriminator was a typed filesystem walk (or single FIFO + successful Builder build); full frozen benchmark matrices could not have discovered a missing file-type semantic if inputs contained none. The current discovery engine policy already demands cheapest semantic falsification before expensive matrices; no policy rewrite was needed.

Next unclaimed high-leverage action: reconcile the full exact-head gates, and when their outcome permits, verify intentional composition with Win32 hardlink repair PR #401. Keep the separate Writer special-source blocking hypothesis unproven until an installed true transaction experiment.
