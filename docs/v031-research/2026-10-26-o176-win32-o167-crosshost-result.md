# O176 result — same authentic Linux archive, Win32 historical negative vs exact O167 candidate

Date: 2026-10-26 UTC. **RESULT BEARING / NARROW POSITIVE + PRESERVED HISTORICAL NEGATIVE.** Frozen preregistration: `docs/v031-research/2026-10-26-o176-win32-o167-crosshost-prereg.md`, first commit `08e78762059a6303a9a482c39d2a117b55448f36`. No historical O171 oracle, O165 producer instrument, source receipt, success threshold, format or product code was modified.

## Direct evidence / exact source

- Initial O176 result-bearing HEAD: `273f37852fd5ed668aa277a9bc3301ae6cde9814`; draft PR #511.
- Native hosted workflow: https://github.com/FCMO-AI/.CMPCT/actions/runs/40311042303
- Linux original producer job `121532002465`: **SUCCESS**, archive artifact `12644977527`.
- Windows Server 2022 same-archive differential job `121532276614`: **SUCCESS**, raw baseline/candidate/unmodified O171 JSON artifact `12643969424`.
- Original Linux r24 archive **1,935 B**, SHA-256 `a36f0cdede87603b43ddc22a61268cd74aa191f0c838389924ce8ddf1c7e8537`, unchanged before/after both consumer trials. Windows received the **same binary**; no consumer-side Builder ran.
- Producer/test Git HEAD `273f37852fd5ed668aa277a9bc3301ae6cde9814`; production Reader blob from inherited O171 `e716233403dabd0966863c45635e18fa5ac6afb8`. Frozen original O171 scientific court blob `8c943128f135607dd36abd083bf1019bc9e4433a`; O165 Linux fixture instrument blob `2fb9cf5c9ecc072a0e692a64f21b6273f0b28fd6`.
- Candidate donor **exact** O167 Git HEAD `841c32d435494f6e4d83c44cd00a1a2f8f7ab148` (existing owner PR #504), candidate Reader Git blob `c50522443b88e78ee2cc8361c4ec2bddbb4f0bbb`, Win32 time helper Git blob `70308f454c74fad7b247db6ee36aa8cc7d38c99c`.
- Both packages were independently installed outside source. Raw wheel source bytes matched Git's original Python source **after only recorded CRLF→LF normalization** on the Windows runner. No arbitrary source drift was allowed.

## Native Windows results — exact same 1,935 B archive

| Control | Historical installed O171-derived Reader | Independently installed O167 Reader |
|---|---|---|
| `cmpct verify` | PASS, 8 logical files | PASS, 8 logical files |
| `cmpct extract` | **FAIL / exit 1** | **PASS / exit 0** |
| Immediate historical exception | `NotImplementedError: utime: follow_symlinks unavailable on this platform` | None |
| Installed CLI verification diagnostic wall | 69.892 ms | 68.465 ms |
| Installed CLI extraction diagnostic wall | 72.655 ms, **failed** | 70.964 ms, **successful** |
| Input archive SHA after operation | Exact | Exact |
| Original O171 source-frozen ten-entry physical court | Not reached because baseline extraction rejected | **PASS** |
| Expected entries | — | **5 files, 2 directories, 3 symlinks** |
| Original authenticated hardlink equivalence | — | **PASS** |
| Symlink text and usable link targets | — | **PASS** |
| File lengths and SHA-256 | — | **PASS** |
| Original physical-court recorded failures | — | **[]** |

The current comparison uses two different installed source snapshots **on purpose**. The O171 oracle's `source_identity_ok` binds the producer/test checkout to its unchanged receipt; a separate O176 audit binds the actual O167 installed Reader and helper to their donor Git SHA. Never conflate the two identities or pretend the donor is identical to the historical Reader.

## Decision

**O171 Windows extraction blocker is resolved in the existing O167 product branch for this authentic Linux-sourced r24 tree.** This is a result-bearing positive, not a proposed fix or an inferred correction from code inspection. The historical original O171 red remains valid for the inherited source, and the same runner/archive test reproduced that exact negative before O167 was installed. The candidate also preserves the O171 ten-entry physical topology contract rather than merely returning exit code zero.

This result does **not** attribute the success to a single line of O167: the donor carries O69 xattr/metadata work and O167 Win32 leaf-handle changes. Source-specific actual behavior, not microscopic causal delta, has been proved.

## Unresolved debt and scientific honesty

- Small fixed synthetic ten-entry archive, not arbitrary/hostile filesystem universality or broad NTFS.
- No proof of full mtime precision within this O171 court; O167's own independent native timestamp/reparse court remains separate evidence.
- Win32 ancestor replacement, TOCTOU, malicious reparse/junction paths, alternative data streams, ACL, xattrs, sparse backing, crash-durability, output atomicity and massive-index/resource memory remain **UNMEASURED**.
- Two diagnostic CLI durations use different successful/failing operations and are **NOT** comparable performance data. No output-storage, CPU, RSS, temp-I/O, cold-read, process startup or official same-input r24/ZIP ABBA promotion credit.
- The O507 ZIP/Windows composition has a separate Reader; its O167 helper and changes must not be assumed to inherit this cross-host result without source-specific proof.
- O176 keeps its own historical test/producer sources unchanged and commits only scientific tooling/CI/docs.

## Counterfactual and next executable action

A simple source-inspection disproof anticipated the uncaught exception, and O167 already existed. The only decision-changing missing information was whether an **actual installed** O167 consumer on Windows could materialize the *same* Linux archive with real hardlink/symlink topology; this experiment supplies that answer. Next: notify O167 #504, O171 #508, and O507 #507 owners with this exact source/head/CI evidence; preserve candidate-specific remaining release debt. Reuse the existing O167 implementation; do not build a third timestamp patch. No Discovery Engine policy change or stale `docs/discovery/STATE.json` mirror is warranted.
