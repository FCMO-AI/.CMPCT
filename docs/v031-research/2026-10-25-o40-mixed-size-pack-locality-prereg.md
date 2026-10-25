# O40 prospective research: selected-member versus largest-member micro-PACK locality

Date: 2026-10-25
Status: **PREREGISTERED / NO RESULT AT THIS COMMIT**
Owner: independent Phase2 scientific falsifier; NOT the O34b/O34c packaging owner (PR #391).
Source: canonical `agent/v031-development`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`, Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, release product-base blob `b6b87b5c2b2f50fe53114ad3b5d228cd1e887367`.

## Decision question (new invariant dimension, not another size-threshold variant)

The shipping r24-fallback pack policy calculates `target=min(2 MiB,8*largest_regular_member_bytes)`. O34c [#391](https://github.com/FCMO-AI/.CMPCT/pull/391) established this is sufficient to explain the 5,000-tiny-file byte cost. But the public Python Reader decodes the **entire physical S_PACK** even when a caller asks for one tiny member. Does `8*largest_member` bound **per-selected-member cold decoded work**, or only a largest-member-derived pack budget? This asks about the meaning of the locality guarantee, not whether to change a threshold.

### Evidence hierarchy and source control
1. Freeze the **three product Git blobs above**, exact SHA of the executing HEAD, and unchanged r24 format/reader/release harness.
2. Build authentic revision-24 CMPCT outputs through shipping `_locality_bounded_r24_build` on four deterministic all-`.txt` pairs, lengths (1,753), (32,768), (128,512), (512,512), distinct contents, no fixtures used for tuning. Normalize input file mode and nanosecond timestamps; retain input and archive SHA-256.
3. Read the **smaller full member first with a fresh Reader** (cold cache) and verify exact returned bytes. Inspect its authenticated `S_PACK` mapping, physical owner uncompressed size and compression codec. Separately, a fresh Reader must pass explicit strong SHA verification for both members; ensure no preprocessing/strong-verify warmed the timed Reader.
4. Compute (a) full cold-owner uncompressed bytes / smaller member bytes, (b) compressed owner bytes / smaller member bytes, (c) owner uncompressed bytes / largest member bytes, and (d) total archive bytes. The model charges the entire decoded physical owner even though only one member is returned; this is a deterministic **decoded-work** accounting, not an RSS/cpu/wall benchmark. Record owner codec; RAW owners prove full buffer access, not Zstd decompression.
5. Adversarial simpler control: an independent genuine r24 Builder with singleton target on the **same source tree** should have no shared two-member owner; count its full archive bytes and exact reconstruction. Keep nonidentical encoder knob caveat explicit; it cannot earn release-parity credit.

### Prospective hypotheses / falsifiers

H1: for a mixed-size pair (1,753) the shipping Reader maps the one-byte member into the same compressed S_PACK as the 753-byte member and must decode >=754 bytes on its first full-file read; hence >8x per-small-member amplification even though packed owner <=8x the *largest* member. Replicate qualitatively for (32,768) and test (128,512) as a near/below-limit control. (512,512) is the homogeneous negative control.

KILL / NARROW H1 if shipping does not select revision 24, either member is not S_PACK, both map to different owners, the physical owner has <=8x the small member's length, strong verification fails, or any structural/correctness test is invalid. Do **not** invent a number from a source-level derivation if product code emits a different layout.

H2: a one-file-per-pack control eliminates cross-member decode amplification but may increase complete archive bytes; quantify rather than assume superiority. The control is a diagnostic, NOT a proposed shipping policy.

## Competing routes / PARETOBONK

- Immediate micro-PACK threshold increase/rollback: rejected; O34c already proved size savings and read-work debt.
- 256-KiB physical shared context with no extra seek structure: cannot give cheap per-member cold decoding; a single compressed owner must be processed to extract an arbitrary slice.
- New seekable shared-context representation: high-upside but must first prove this *particular* locality contract matters; dictionary bytes, random-access metadata and any repeated decode work must be fully charged.
- Existing product/CI integration: generally high priority; this independent bounded falsifier does not touch active O31/O38/O39 Reader ownership or O34 packaging source.

## Decision / limits

If H1 holds, narrow the asserted 8x guarantee to a *largest-member proxy* in existing policy and hand off a product-level decision: enforce true per-member locality with bounded admission/physical splitting (and fully measure byte debt), or explicitly define and prove another useful locality objective. **Do not silently weaken any frozen 8x promotion gate.** If H1 fails, preserve that negative and retire this route. No new version, format, release, merge, benchmark promotion or performance claim from this science-only experiment. Linux/Python research host first; future product decision requires stronger portable conformance plus measured bytes/CPU/RSS/selective physical I/O.

Independent jobs must retain source HEAD, GitHub run ID and uploaded JSON/logs; a failing setup is infrastructure, not a product falsification. Preserve this preregistration verbatim; append a separate decision receipt after result.
