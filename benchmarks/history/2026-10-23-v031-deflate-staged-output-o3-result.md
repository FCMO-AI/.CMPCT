# O3 outcome — staged-output verification protects the user-visible ZIP

Date: 2026-10-23
Class: **positive research-level architecture oracle**, NOT an implemented CMPCT product fix.
Prediction frozen at `b929852e0b4daf0784bd79ecc0adfc37b69f150b`, before O3 executable `6d7294e5a6975c83d8ca44439cb209e3a37dcf01`.
Exact-head hosted court: [run 40021504766](https://github.com/FCMO-AI/.CMPCT/actions/runs/40021504766), job `120646927643`, source HEAD `c73b8b1a6176bb09aea4c4778b201289fa01c0b3`, **SUCCESS**.
Artifact: `12530472902`, ZIP `sha256:21244e09d7d68f22fd3cbae10cdf1bc62e176417bafb7e3e4df0b2422c709355` — both O2 and O3 JSON, source identity and Git blobs.

## Exact observations

| Test | Ordinary preflight/export from PR #284 | Research stage/authenticate/publish wrapper | Existing destination |
|---|---|---|---|
| Valid immutable source | correct raw Deflate stream reused | ZIP exact physical SHA equal to ordinary exporter | replaced only after authenticated |
| Corrupt-before-preflight | rejected | rejected; temporary deleted | **original bytes retained** |
| Mutate-after-original-preflight, one member | ordinary method creates corrupt temp ZIP; independent member read fails | refuses publication after independently reading/crosschecking the **written** ZIP | **original bytes retained** |
| Same mutation, three aliases | all three emitted ZIP members fail independent CRC | refuses publication; temporary deleted | **original bytes retained** |

Output court: `OUTPUT_STAGE_VERIFICATION_PROTECTS_PUBLICATION_IN_TESTED_REGIME`.
The pristine ZIP was byte-identical to the owner's ordinary exporter and valid under `zipfile`. No stage leak was observed in any of the four conditions. In both after-preflight cases, the source mmap saw the deliberate later write; the original exporter still returned success when called with a private temporary output, but the research wrapper independently rejected its actual emitted bytes.

## Why this changes the engineering fork

O2 alone showed the current source-epoch TOCTOU gap. O3 establishes a **constructive product path**: verify the bytes actually published, not a potentially stale earlier view. Same-filesystem private output staging plus full committed logical SHA-256/CRC/length validation removes the observed postcheck race in this limited regime and avoids modifying a pre-existing destination on error.

Alternative: an enforced immutable-source lifetime/snapshot contract would avoid staging/reverification, but must be real. Rechecking source stat or mmap a second time is a weak control and does not bind output bytes.

## Important debt

The wrapper is *not* an accepted general exporter. It double-checks members via streaming ZIP reads after writing, which adds another full archive read, CRC/SHA computation and potentially duplicate decompression for aliases. It stages output-sized temporary disk bytes, and its target-parent security, symlink policies, disk-full handling and process crash durability are not tested. It only operates on physical direct Deflate members, and only on a Linux/Python 3.11 source where the mmap mutation is visible. Source commitment metadata is frozen before deliberate payload mutation; an attacker who can also rewrite it is outside the tested contract. Full cross-platform, native, ZIP64 and performance gates remain unmeasured.

A potentially lower-cost follow-up is to compute a wire SHA-256 **on the exact immutable compressed chunks supplied to the original logical validator**, then compare against a wire SHA-256 computed **on the exact bytes copied to staging** in bounded chunks. This may avoid duplicate logical decompression per alias, but requires an independent non-TOCTOU implementation and cost comparison; calculating the wire digest by re-reading the live source after validation would reintroduce the original race.

No core source, test threshold, format, site, history lock, or other PR owner's implementation was changed by this experiment. Keep PR #284 responsible for the product decision; O3 is decision-changing architecture evidence only.
