# J24M01h — true post-exec child RSS spike, negative-control preregistration

**2026-10-29 UTC. Prediction frozen before implementing J24M01h instrumentation.** This is a narrowly scoped adversarial check on the unreleased test evaluator in PR #769, stacked on #738. The published v0.30.0 / format revision 24 and all product/format/release code remain untouched.

## Question and inherited exact evidence

The new J24M01f verifier resource assertion reads Linux `/proc/self/status:VmHWM` inside the actual post-exec child and preserves the original strict `peak_kib < 128 * 1024` ceiling. Its inherited-ru_maxrss control is a **false-positive discriminator**, not a test that the new metric detects a **true** high-memory child. At #769 source `8c99a16257a4700d2d5a9a2989d52c694a343a99`, hosted full-suite [run #40917140647](https://github.com/FCMO-AI/.CMPCT/actions/runs/40917140647) reports the actual sparse resource test PASS and a real suite result of 806 passed / 4 inherited release-fingerprint failures. Strongly distinguish that scientific local PASS from whole-project green.

## Primary falsifiable prediction

A fresh Linux Python child, after `exec`, which faults/touches every 4096-byte page of a **new 160-MiB allocation** and holds it alive while measuring, must report `VmRSS > 128 MiB`, `VmHWM > 128 MiB`, and `VmHWM_after - VmHWM_before >= 128 MiB`. Thus the original `<128 MiB` resource threshold must **reject** this genuine resident spike. In contrast, the already demonstrated parent-inherited `ru_maxrss` highwater with no child allocation must leave post-exec VmHWM below the cap. The independent child must not import CMPCT.

## Method, stronger controls, kill and boundaries

- Launch the artificial child via `subprocess.run([sys.executable, '-c', code])`; avoid mutating pytest parent's RSS.
- Sample `/proc/self/status` before allocation and while bytes are resident, and sample `/proc/self/statm` resident pages as a differently rooted kernel counter. Touch one byte per page; hold allocation until after both measurements. Assert strong agreement of contemporaneous VmRSS and statm, subject only to bounded small process accounting difference, not a weakened product threshold.
- Require strict POSITIVE rejection: the true child peak must fail the *same* `< 131072 KiB` predicate that the genuine sparse verifier uses, while inherited-only control must pass it. No test environment may fake `/proc` or adjust the original 256MiB sparse input, Reader, subprocess, evaluator or resource cap.
- If true 160MiB resident bytes do not cross the 128MiB VmHWM gate, or if kernel counters disagree materially, **FAIL** and do not credit the existing new measurement. If missing/invalid `/proc`, fail closed. Host observations are Linux-specific, not portable to Windows/macOS.
- This is Linux kernel/test evidence only, not new CMPCT compression, performance, memory optimization, security or release proof. Any full suite inherited failures remain failures; no merge/release promotion.
- Test one exact source path, record head/branch, actual kernel outputs and raw CI results. This local proof adds one bounded 160MiB separate-process allocation, zero product code/file-format/ABI cost and no filesystem output besides test receipts.

## Alternatives and self-critique

The former pre-exec `ru_maxrss` control already proves a false positive but not that a true bad child would be caught. Simply trusting `VmHWM` semantics is weaker than an actual injected resident spike; modifying CMPCT to allocate artificially would contaminate product behavior and violate original strict input semantics. A second `VmHWM` read is not independent memory instrumentation: simultaneous `VmRSS` and `statm` resident counters provide a grounded physical-control cross-check, though all originate in the same Linux kernel. This verifies metric directionality, not universal absence of undetected short-lived allocations or the real full-product release case.

## Promotion boundary

Keep PR #769 Draft and owner #738 as the compaction implementation lane. A PASS for this negative control can strengthen resource-evaluator evidence only. It cannot close the four inherited release/fingerprint reds, #749 verified-inode publication gap, unmeasured Windows/macOS compaction, full product economics or release gates. Reconcile against current GitHub state before further edits.
