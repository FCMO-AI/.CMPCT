# ONE-G0.2 authenticated Law archive seam — preregistration

Date: 2026-09-09  
Experimental version: ONE-G0.2  
Status: frozen before candidate implementation/result inspection

## Mission lock / referee

The complete authenticated research archive seam currently proves filesystem Manifest + AuthTree + selective read behavior using Surprise-only regular-file roots. Separately, generic ONE relation Programs have proved large density gains, exact reconstruction, native whole-root execution, and authenticated native selective Law cones.

The frozen question is whether those already-proven pieces compose inside **one actual archive artifact**: can a regular-file root be an ordinary ONE Law over another file root, while the same Manifest and generic AuthTree preserve exact full-file and authenticated selective access without a reader-visible relation codec or archive-specific Law mode?

This experiment is deliberately about composition, not discovery quality. The fixture supplies the relation family/value so that a failure cannot be blamed on heuristic nomination. Automatic admission remains separately governed by the promoted writer evidence.

## Hypothesis

For two equal-length regular files where `current[i] = (previous[i] + 37) mod 256`, the authenticated archive can store `previous` as Surprise and `current` as an ordinary `add8(previous, Fill(37))` Law root, plus ordinary Manifest/AuthTree metadata. The existing authenticated archive reader should then reconstruct both files exactly and answer selective authenticated reads from `current` with cone-proportional work rather than reconstructing the whole root.

If archive and relation components are genuinely unified by ONE rather than merely adjacent demos, no new reader-visible opcode, container mode, integrity exception or second archive type should be needed.

## Disproof / gates

Invalidate or HOLD if any of the following occurs:

1. full-file bytes differ after canonical wire encode/decode/reopen;
2. file/root SHA-256 or AuthTree root differs from the logical bytes;
3. authenticated selective requests differ from exact requested bytes or fail root verification;
4. a fixed 4 KiB request into `current` reconstructs/touches work proportional to the full current file as the root grows;
5. the reader performs relation discovery;
6. implementation introduces an archive-specific relation opcode, opaque legacy codec, or special integrity format;
7. resource/path/manifest validation is weakened;
8. productive relation archive fails to save at least 25% wire versus an otherwise-equivalent authenticated Surprise-only two-file archive at 128 KiB and 512 KiB per file;
9. authentication metadata is omitted from either logical file merely to improve wire.

Advance requires exact semantics, authentication, selective locality and >=25% complete-artifact wire saving on the productive 128 KiB and 512 KiB rows. This threshold intentionally charges Manifest and AuthTree overhead rather than comparing bare relation Programs.

## Frozen matrix

Use deterministic synthetic pairs at 32 KiB, 128 KiB and 512 KiB per file:

- `previous.bin`: deterministic high-entropy-like bytes;
- `current.bin`: exact ADD8(+37) transform of previous;
- both represented as ordinary archive entries with their own logical digest and generic AuthTree;
- comparator: same files and same authentication metadata under the current Surprise-only authenticated archive builder.

For each row record:

- comparator and Law-archive wire bytes;
- complete-artifact wire saving fraction;
- exact full-file parity after wire reopen;
- Manifest path/root identity;
- per-file authentication roots/index bytes;
- authenticated selective requests: first 64 B, first 4 KiB, middle 4 KiB, auth-leaf crossing, ONE-chunk crossing where applicable, tail 257 B, zero-length;
- requested bytes, reconstructed cone bytes, source-read bytes, source-plan writes, proof payload/hash bytes, plan commands, fallback/reason;
- fixed 4 KiB cone geometry as root size grows.

## Invariants

- ONE representation remains Law + Surprise;
- `add8` and `fill` are existing generic primitives, not file-format modes;
- Manifest remains the user-visible filesystem mapping;
- AuthTree remains generic Crystallization metadata;
- reader discovers nothing;
- source and current roots retain independent exact hashes;
- no September 11 corpus or comparator scoring is executed here.

## Hostile reviewer

A bare-Program win is insufficient. The complete archive must still carry both files' Manifest and authentication metadata, and the comparison must charge those bytes. Likewise, a selective read that silently falls back to whole-root reconstruction is a failure even if returned bytes are correct.

The strongest likely integration bug is root-reference mismatch: the archive reader was first exercised with Surprise-only roots, while a Law root can depend on another file's node. Tests must prove canonical encode/decode preserves that cross-file graph and that authenticated reads verify the logical `current` bytes, not the stored Surprise basis.

## Promotion scope

An ADVANCE proves composition of an already-supported generic Law with the authenticated complete-archive seam. It does not prove automatic discovery breadth, full mature-CMPCT recovery parity, or the September 11 supersession decision.