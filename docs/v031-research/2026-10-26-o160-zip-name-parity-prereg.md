# O160 — Canonical ZIP member namespace (preregistered before product mutation)

**Exact stack:** O149 product candidate PR #492 at `ca01d885fedc8ffc343b9c3c624eddd134158452`; released v0.30.0, physical format revision 24. Original independent O156 negative witness is PR #498 at `a8e01869c0e7c8674c59ac94b8e9c55b391f2393`, original instrument blob `c08cd28fe0fb984c873d0efb13d6924862e9bb18`, and hosted two-POSIX run `40278444729`. Do not alter its experiment, expected negative, or evidence.

## Primary question
Can the public Python ZIP exporter serialize the same **canonical slash-separated logical names** as ordinary CMPCT extraction, for authenticated revision-24 index rows containing backslashes, while preserving exact payloads and the clean ZIP byte identity for names already canonical?

## Prediction / falsifiers (before code)
1. Replace exported member *names*, not stored index keys, physical bytes, reads, or ZIP compression. Use the already normative `canonical_logical_path` policy and its canonical duplicate refusal. Predict O156's three backslash rows will extract through ordinary ZIP into exactly `nested/leaf.bin`, matching ordinary CMPCT extraction, for RAW/Zstd/Deflate on Ubuntu and macOS, and preferably Windows when hosted.
2. Original/slash controls must remain byte-for-byte identical to the inherited O149 ZIP exports on identical inputs/settings. A changed ZIP byte, a changed logical SHA-256, a new collision, an incorrect symlink/directory member name, an O149/O140 destination-admission regression, or a CI source-custody red that cannot be explained is a **block**, never a reason to weaken the old court.
3. Pathological source paths that normalize to identical ZIP member keys must fail closed **before opening any output**. Inherited CMPCT ordinary open already rejects duplicate canonical keys; independently test or preserve that condition.
4. High-cardinality names/ZIP64 fallback must follow the same naming rule as the normal direct-Deflate writer. Reconcile encoded name lengths in ZIP32/64 boundary calculations.

## Simpler alternatives
Documentation-only compatibility disclaimer leaves reproducible file-layout divergence. Literal string replacement in the ZIP serializer can repair backslashes, but must be checked against the shared canonical validator to avoid silently creating aliases. Rewriting the canonical index or changing format revision 24 is unnecessary and forbidden here.

## Boundaries / negative evidence
This **does not** repair O157's concurrent stage-file identity vulnerability, inherited ZIP output symlink/mode semantics, Unicode normalization/case aliasing, unsafe arbitrary names admitted by other writers, ZIP extended attributes, or power-loss durability. No compression improvement or release credit is claimed. The strongest current product risk remains O157; this narrow implementation is safe as an independent ZIP member-namespace lane and must not overwrite the O149 stage-publication owner.

## Evidence plan
Implement a minimal source change in `src/cmpct/reader.py` on a **stacked, isolated branch**, add a positive *Builder-independent* revision-24 conformance/namespace court adapted from but separate from immutable negative O156, compare exact control ZIP SHA against original Reader where feasible, run on multiple hosts with exact-source identity, and leave performance/size credit unearned until actually measured.

**Owner coordination:** O149 #492 retains publication/inode ownership; O156 #498 retains negative source-exact experiment. This branch owns only serialization of ZIP entry names.