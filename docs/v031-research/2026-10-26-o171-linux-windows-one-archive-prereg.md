# O171 preregistration — one authentic Linux r24 tree archive on Windows

Date: 2026-10-26 (UTC). **PREDICTION BEFORE IMPLEMENTATION AND RESULTS.**

## Exact source and prior evidence
Base/source head: `04fac08a342fd14fceae61b84c0c096429a0694b` (O168). Released format remains r24, v0.30.0. O165 (#503) already builds one genuine Linux archive with 10 physical entries, including three relative symlinks and one ordinary-file hardlink group, and proves Ubuntu→macOS portability. O168 (#505) proves reverse macOS→Ubuntu. **Neither proves a Windows receiver.** O117/Win32 namespace and O167 metadata ownership exist; do not duplicate implementation or alter their branches. Source/receiver use an exact-head independently installed package and O165's existing original production script.

## Primary scientific question
Can an **unchanged Linux-produced r24 archive** be verified and extracted on a genuine Windows runner with the same regular-file byte hashes, directory set, symlink relative targets and hardlink equivalence class? Treat unsupported host policy honestly: successful `verify` alone is not an extraction success; a safe explicit refusal is a portability capability gap rather than corruption. This is *not* a universal NTFS portability, security or metadata-fidelity claim.

## Competing actions and choice
- Another two-POSIX-host roundtrip: saturated by O162/O165/O168; no new frontier.
- Win32 Reader/mtime/symlink implementation: other owners (#504/#507) and larger unbounded product risk.
- Independent **one-existing-binary Windows receiver**: a new OS/filesystem execution frame, low-cost decisive falsifier, no change to source, format or existing courts. Chosen.
- Archive rebuild on Windows: rejected; loses cross-host identity and may hide failure.

## Baseline and falsifiable predictions
P1: Ubuntu O165 producer's original r24 byte SHA-256/length is exactly preserved through upload/download on the Windows runner; no Windows Builder runs. If transport identity differs, the experiment is invalid.
P2: genuine installed Windows `cmpct verify` succeeds on identical bytes. If this fails, record actual command/error, not a portability PASS.
P3 (strong): `cmpct extract` succeeds and original 10 entries retain type, raw regular-file bytes, three relative symlink targets (allow *separator spelling* translation only, never target substitution) and original same-file hardlink class. No lower-semantic projection is accepted as full cross-host PASS. Record whether NTFS physical symlinks/hardlinks actually exist. Symlink-creation privilege and filesystem capability must be recorded; if a host cannot represent them, record `HOST_UNSUPPORTED`, not PASS.
P4: the source archive remains unchanged after Reader verification/extraction.

## Scope boundaries and competing explanations
Strongest simpler control: archive SHA, installed-path/HEAD-source identity and `verify` before materialization. Alternative explanations for failure: Windows symlink privilege, path policy, filesystem support, test apparatus/CLI invocation, missing native optional runtime, or a real Reader portability defect. Classify by actual stderr, host API observations and source artifacts, not guessed causes. Neither executable-bit/mode equivalence, symlink inode modes, timestamps, uid/gid, ACL/xattrs, crash safety nor concurrent namespace adversaries are part of the claim. No evaluator, benchmark, release gate, historic file or product code may change to turn a fail green.

## Exact evidence ladder, decision, disproof
Use one Ubuntu creation job -> artifact SHA/receipt -> independent Windows install/extract job with raw JSON receipt, CLI stdout/stderr and direct `os.lstat`/`os.path.samefile` observations. Both jobs record exact Git HEAD; the Windows receiver cross-checks producer's `source_blobs` and source SHA. Run before expensive release tests. Full PASS requires P1–P4; otherwise preserve failure/inconclusive with explicit cause. A true negative directs the relevant Reader/Win32 owner toward a bounded fix and separate promotion court; a true positive expands supported **scenario-specific** portability evidence only. No canonical merge or v0.31 release is authorized.
