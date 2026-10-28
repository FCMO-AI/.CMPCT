# J24K12a — hosted Windows receipt source-normalization repair

Date: 2026-10-28 UTC. Addendum **after** scientific test of original code HEAD `3c0432585a7c01d43a731debcad6ff3efeef9c07`, **before** altering experiment code. Do not rewrite or erase the original receipts.

## First scientific decision remains binding

[Original three-host court](https://github.com/FCMO-AI/.CMPCT/actions/runs/40661616005) decisively **did not** meet the preregistered >=1.20x complete Reader-open+Q64 CPU/wall performance threshold. Valid independently audited Ubuntu and macOS measurements show the Python-safe Reader **wins**: 4,096 STORED streams with Q64-tail, Ubuntu control 300.365ms vs batch 338.919ms (control/batch 0.886x), macOS 322.267ms vs batch 357.734ms (0.901x). No reinterpretation of speed or new threshold is authorized. The original negative must survive the repair.

## Host evidence failure isolated

Windows compiled, installed the wheel, built authentic signed r24 archives, ran all 12 cells/120 observations, and rejected the reauthenticated length lie in both paths. Its separate audit failed at **`AssertionError: reader_sha256`**, before inspecting raw observations. This is an **instrument source-custody inconsistency**, not a Reader or product failure: the experiment hashes the installed source bytes as checked out; Windows Git and wheel source may contain CRLF, whereas the second-root auditor hashes Git's LF blob. Existing CI's exact source verification correctly normalizes line endings, but the new receipt SHA did not. Correct this by computing a canonical LF byte hash for the receipt and checking against the exact Git blob on all hosts; never skip or weaken source checks.

Additionally, `zipfile.ZipInfo.create_system` defaults to host-dependent values (Windows 0 versus POSIX 3). Freeze it to 3 in this deterministic fixture and set explicit `external_attr`, eliminating an unrelated fixture byte difference across hosts. Both arms on each host already consumed the same true ZIP; this change improves cross-host source control, not performance credit or scientific predicates.

Windows CPU time can quantize to zero for short operations. Preserve zero as a measured instrument limitation (not a positive speedup); the criterion on Q64 still requires positive CPU evidence. Linux/macOS complete comparisons already falsified the family without using that Windows clock.

## Repair boundaries and next scientific court

Change only the new J24K12 **science instrument** and (if needed) its independent auditor's exact source canonicalization; no product Reader/scanner/codec/validator/frozen test/benchmark/version/format edits. Preserve 12 cells, Q1/Q8/Q64, every individual sample, unsafe signed mutation rejection, five forged receipt rejections, source/execution SHA, preregistered >=1.20x both-axis threshold, independent audit strictness, whole-session charging, and original 3-host run link. Re-run on three hosts at new exact HEAD, report measured results (including expected negative), and never call passing scientific infrastructure a product gain.
