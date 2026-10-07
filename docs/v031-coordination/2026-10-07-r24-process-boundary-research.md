# v0.31 R24 process-boundary research — Linux-only candidate control

**Status:** research evidence, not canonical evaluator, format, product or release authority. **Date:** 2026-10-07.

## Primary question
Can an evaluator bound *descendant execution* by changing the process-capability model instead of indefinitely extending Python source-receipt attestation? Earlier exact-parent falsifiers demonstrated that authenticating the primary worker does not transitively authenticate a grandchild that builds an output.

## Hypothesis and falsifier
For an isolated Linux-only R24 research worker, a fail-closed kernel filter installed **before any measured product import** could prevent all new process/exec paths while retaining legitimate same-thread-group pthreads. Disproof is any successful post-install descendant process, ordinary thread creation failure, a source/byte mutation in an independently verified benign product, or inability to apply the filter to preexisting threads.

## Experiment and direct observations
A local research-only Linux CPython 3.13 harness exercised kernel-enforced process/exec denial via libseccomp with filter synchronization, denied process-like clone/fork/exec and allowed CLONE_THREAD. In isolated children, standard subprocess, posix_spawn, fork, direct fork/clone syscalls and exec attempts failed; ordinary threading succeeded and attempted process creation from an inherited guarded thread failed.

The same source-faithful controlled experiment invoked the unchanged R24 parent Git blob `e3a5f2a13f8553dcdd87a5f0b566dc00ab9ec2a4`. A synthetic product spawning a foreign Python grandchild reproduced the previously accepted false success without the kernel control. With the kernel control installed before the product import, the canonical parent instead reported a child failure, and the synthetic output and custody sidecar were absent. A benign source-pinned synthetic product still produced identical output.

A separate paired local compatibility court imported an immutable archived Linux wheel with exact Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044` and package-owned native core SHA-256 `439045987871fdf167ac241b1ca0250dbc2058345392fec15629b1c080f86a7e`. Both guarded and unguarded arms produced byte-identical 105,469-byte archives and exact reconstructed source trees, with five alternating pairs at one compression worker and five at four workers. These short local tests are not the formal v0.31 product-economics or hosted v8 court.

## Evidence and limits
The local guarded-process prototype (SHA-256 `ed5e84b2d9704e21bf41c2fdc145a0a095640356f3f2143d76931c3da94a81bb`) and canonical-parent court (SHA-256 `fbd7157abbe23637ec46295cf4df2d8819b712fd21ac472e38d85d14d520953a`) were not landed as repository executable source: an ordinary source-create attempt was blocked before mutation. Therefore the above is a scoped research report, not an independently reproducible repository-hosted result.

**The boundary is limited:** Linux syscall filtering is not an attestation of the Python source or native shared objects, does not police pre-existing descendants/external helpers, and does not cover macOS or Windows. Source/file/bytecode provenance, exact package-native dependency fingerprints, input/output identity and real-product no-subprocess assumptions still require independent verification. It must fail closed if the filter cannot install and may alter behavior if legitimate product code needs external processes. No change to release thresholds, selectors, format, comparator or court is authorized.

## Subsequent decisive product-path falsifier — RETIRE blanket denial

**Same activation, later evidence.** The first small installed-wheel compatibility court happened not to trigger dictionary training. It was therefore insufficient evidence of general product neutrality.

A larger independently materialized same-input source tree (scale 8; four encode workers) changed the result decisively. The unguarded **exact Builder preimage** `663ef0922992b1fbb8f19e6eea88d55c10a56044` and the same package-owned native binary built and extracted a valid **806,254-byte** CMPCT archive. The guarded arm failed before emitting an archive: `PermissionError: [Errno 1] Operation not permitted: '/usr/bin/zstd'`.

This is not a random unrelated subprocess. Current `Builder._train_dictionary` at the exact preimage invokes the external `zstd --train-fastcover=...` CLI once the unchanged eligibility gate has at least 16 sufficiently large text candidates and at least 96 KiB of sample bytes. The seccomp guard correctly blocks that legitimate `posix_spawn`. Removing the trainer, changing admission, suppressing the failure, or excluding its real work from performance accounting would weaken CMPCT semantics and cannot rescue the proposed evaluator.

**DECISION:** **REJECT blanket process creation/exec denial as a generally product-neutral v8 control**. It remains a narrowly useful negative-control instrument for synthetic products explicitly known not to require descendant work. A legitimate product evaluator must instead preserve and authenticate required descendants (including the zstd executable and its I/O/work/cost), or separately productize an exact in-process dictionary trainer with equivalent fully charged behavior—neither has been established here.

The earlier benign small-corpus evidence, Python-thread preservation, and hostile grandchild denial remain valid *at their original scope* but are not general promotion evidence. No product/format/release credit; the formal hosted v8 product court remains pending.

## PARETOBONK decision
Three previous activations had repeatedly explored Python import/path/bytecode custody. This is a deliberate **different-frame test**: constrain operating-system process creation rather than add another metadata-only receipt. A bounded Linux-only path is supported only for a no-descendant negative control; the later actual Builder dictionary-training falsifier retires blanket denial as a general evaluator. The next frontier is authenticated, charged, legitimately required descendants or a strictly equivalent in-process trainer—not another metadata receipt.

**Next:** reconcile current R24 ownership and source-custody requirements, land an executable bounded evaluator only through ordinary authorized source writes, then run the fixed candidate-neutrality and independent complete-product court. Preserve the existing highest scientific priority on bounded drift and Issue194. No product or release credit.
