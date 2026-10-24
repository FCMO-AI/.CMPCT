# O16 preregistration — charge a genuine r24 envelope around frozen coordered BDC

Date: 2026-10-24
Status: PREREGISTERED BEFORE INSTRUMENT/WORKFLOW
Scope: independent bounded research oracle; no format or product implementation change.

## Authority and baseline
- Frozen coordered BDC owner: `agent/v031-bounded-drift-coordered-court@a34b050933b2f946fcf5fb1a4a7d02f58f777c0f`.
- Exact benchmark blob `2fd04bacd64c14b45678b8575ba8ae7c692aa2df`, prereg blob `f8e53f058a1c123ea4665b730c45f5619eb93d5f`. Imported primitives and Builder/Reader are pinned to the unchanged nine Git blob SHAs already enforced by PR #239's hosted court.
- Frozen research receipt: PR #236 / run 39925132930 / artifact 12489775120. Complete noncanonical sibling: Shifted 1,687,989 B (SHA-256 6f15c582a4c448524f112e5a74d832401004895c30a3e53723684d3d921b2b30), Boundary 72,841 B (SHA-256 da20e529c5acd391e1ea26ab3101e1d6a1960c8216f5438e998cbc27489c78ae).
- Fixed Zstd-19 comparator bytes from independently authenticated frozen court: Shifted 1,694,674 B; Boundary 73,097 B. These are scientific fingerprints, not a new same-run comparator benchmark.
- Stronger actual canonical r24 incumbent: PR #239 / run 39929731385, same source trees, 30,275,353 B Shifted / 902,960 B Boundary, with exact filesystem reconstruction under its recorded semantics. A single diagnostic run reported noncanonical sibling create-cost debt.

## Primary falsifiable question
Can the *simplest* r24-compatible encapsulation — taking unchanged, source-identity-verified BDC bytes as one opaque regular payload and building a real canonical r24 archive — retain BOTH frozen strict external byte wins after **all physical envelope bytes** are charged?

This is a deliberately generous oracle for the opaque-container route, **NOT** a CMPCT archive that natively exposes the original underlying filesystem. A future BDC-aware decoder and generic admission would add nonnegative implementation/work costs; the oracle cannot earn product or release credit even if it wins.

## Predictions and controls
- Boundary is close to the hard external threshold: its frozen 256 B slack may be eliminated by a complete r24 envelope. Shifted has 6,685 B slack and may survive.
- Independently re-generate frozen trees and sibling bytes, rejecting any exact SHA/tree drift before measuring the envelope.
- Build r24 through the actual unchanged `cmpct.builder.Builder` on a directory with **one named binary file containing the exact frozen sibling bytes**; no mock framing or estimated index overhead.
- Open with unchanged `cmpct.reader.CMPCT`, run `verify`, extract to a fresh root and compare the nested member bytes bitwise/SHA-256 to the frozen sibling. Also decode the original sibling using frozen parser and require the unchanged original canonical manifest. This checks envelope and sibling composition, **not** automatic extraction of original files from an r24 archive.
- Charge full r24 stored bytes, wall/CPU of nested envelope construction, source read and archive construction in the diagnostic boundary; report raw number of stored bytes and total net carry cost. CPU/wall have no release timing credit and are not matched ABBA.
- Result is a positive scoped oracle only if both envelope archives are STRICTLY smaller than the relevant pinned Zstd-19 complete-byte controls and all content/provenance checks pass. If Boundary fails, retire/narrow the **opaque r24 encapsulation as an external strict-win productization route**, NOT BDC itself or alternative direct representation grammars.
- Corruption/integrity/metadata claims about arbitrary nested and original filesystem archives remain outside the oracle. Do not weaken the existing stronger controls.

## Opposing hypotheses / alternatives
1. A direct new admissible representation in the r24 product may avoid double framing; this stronger alternate remains open regardless of opaque-wrapper loss and requires actual Reader/Builder integration plus safety/economics.
2. Compressing the already compressed BDC payload inside r24 may happen opportunistically; its measured full physical effect, not an assumed constant header cost, decides this question.
3. The historical Zstd bytes could differ under another compressor runtime; this oracle binds the original comparator receipt and explicitly **does not** re-run an external comparison or claim one.

## Evidence / coordination
Work exclusively on isolated child branch of PR #239 (`df6920b5a2e72df3d4cae81c6d17d6f457ce6e63`), preserving nine inherited exact blob identities and no changes to the frozen scientific owner, shared discovery state, format, product, benchmark matrix or release thresholds. Record HEAD, Git blobs, run/artifact identity, exact source tree SHA and both size verdicts. Keep an explicit one-question frontier and promote no version.
