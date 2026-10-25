# O87 result — genuine Builder output FIFO availability failure (2026-10-25 UTC)

**Disposition:** `PRODUCT_AVAILABILITY_NEGATIVE_CONFIRMED` for two POSIX destination forms; **no product fix, no merge/release credit**.

## Exact custody and preregistration

- Repository: `FCMO-AI/.CMPCT`; original composite Builder owner PR #442, head `7efcc51154b64fd6394ddffaab599760659f6c91`.
- Original unmodified Builder Git blob: `64b0cd21ad54ce7c8e8c6f5847b3c613fff6511c`.
- Independent O87 evidence-only PR: #445, preregistration commit `f5bd32b9bdcdc27735dc154a023d4ee800368637`; executed exact test/workflow HEAD `71aa3c1930be64100d4e0d209cbeb4757378f8da`.
- Frozen original instrument blob: `ad39cdfec28b3a48b6092144e5e1457045a09ea4`.
- Genuine installed CPython 3.11 CMPCT, outside checkout on both hosts. No product, reader, codec, native, format, benchmark, historical baseline or comparator changes.

## Decisive hosted negative

[Run 40202046940](https://github.com/FCMO-AI/.CMPCT/actions/runs/40202046940), two independent jobs:

| Host | JUnit result | Existing regular archive control | External unwritten FIFO | External symlink to unwritten FIFO |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04 | **3 PASS / 0 SKIP / 0 FAIL** | Completed, archive verified and payload exact | Genuine Builder child exceeded **8-second** hard timeout | Genuine Builder child exceeded **8-second** hard timeout |
| macOS 14 | **3 PASS / 0 SKIP / 0 FAIL** | Completed, archive verified and payload exact | Genuine Builder child exceeded **8-second** hard timeout | Genuine Builder child exceeded **8-second** hard timeout |

All cases were actually executed. The negative markers were checked from raw pytest logs by the CI audit step. The tests use `subprocess.run(..., timeout=8)`, which kills the target child on timeout; the parent process never writes to the FIFO. Source payload remains intact and both FIFO kinds remain FIFOs/symlinks. The real Builder completes for the matched external regular output and `CMPCT.verify()`/content-read passes.

Raw artifacts:
- Ubuntu artifact **12602096962**, SHA-256 archive `40deedb83168f4030544d24abe2d506e8dc94116958ae21d506501032349286c`.
- macOS artifact **12601419223**, SHA-256 archive `1970e8edfe071487d932fd7f0f1e613d87827e291f1aa527caf765cc1f1e2007`.

Raw job IDs: Ubuntu `121195082856`; macOS `121195082722`. The exact-head audit recorded `3/3` each and the product/source/instrument Git blob identities above.

## Causal explanation and limits

The O84 `Builder.build` path resolves output containment, calls `os.stat(out)`, but accepts an existing nonregular output without rejection (its physical alias guard only considers multi-linked regular targets). After building a fully materialized archive it calls `Path.write_bytes()`. POSIX opening a FIFO for writing without a reader can block. The genuine product outcome matches that mechanism on two independent hosts. A matched regular-file child excludes a general slow-builder explanation within the tested fixture and deadline.

This proves **caller-visible >8 s nontermination**, not mathematical indefinite blocking or all-filesystems portability. Windows named pipes, special devices with readers, source-tree mutation races and intentional stream semantics were not tested. The negative shows an availability issue, not corrupt archived bytes, not measured throughput, and not universal metadata failure.

## Alternatives and owner product repair contract

- A narrow output-kind preflight before expensive encoding (reject anything whose resolved existing target is not a regular file) is the simplest proposed intervention, but **not implemented here**. It must be reviewed for historical symlink/regular admission and caller-facing error semantics.
- A late failure check after building still permits wasted CPU and does not safely prevent blocking at publication.
- O75 temp-file replace is not an automatic fix because O78 proved changes to inode, hardlinks, existing output xattrs and authorization.
- An open-descriptor/fully transactional destination design may solve races but has greater complexity and requires separate hostile, portability, I/O/durability and release evidence.
- A more general nonregular class (including character devices) could cause different observable behavior; it is **unmeasured product hypothesis** and should not be declared a failure solely from a primitive `/dev/null` experiment.

## Counterfactual, decision, and handoff

A single real POSIX FIFO-output child plus matched normal-output control would have detected this failure immediately when O81 output admission was designed; the earlier O84 direct Python-primitive probe correctly pointed to it but could not establish CMPCT product behavior. The prospective lesson is to check type/identity at **both** the source and destination boundaries when a format claims filesystem fidelity; a path-containment check alone is not output-type admission. This is a local engineering lesson, **not evidence for modifying the Discovery Engine policy**.

**Next owner action:** #439/#442 should triage existing-output type admission, add a bounded nonregular destination negative to the authoritative Builder court, preserve normal complete-archive parity and output-path semantics, and remeasure overhead plus full release prerequisites. This research branch must not be merged as though it fixes the product. `docs/discovery/STATE.json` remains under #440 and untouched.
