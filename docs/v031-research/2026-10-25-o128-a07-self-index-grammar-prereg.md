# O128 — A07 self-indexed grammar as physical navigation (prospective, frozen)

**Recorded before outcome-bearing implementation or measurement (2026-10-25 UTC).** Scope: Foundry Assumption A07; unclaimed family at orientation (no A07-specific open PR in current search). Base: canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Research only; no change to published revision 24, Reader, Builder, benchmarks, gates or historical results.

## Question

Can exact repeated **sequences of physical block identities** support a binary grammar in which the grammar itself is the traversal/index structure (production child links + logical lengths), avoiding redundant explicit per-member block-pointer runs, while beating an equally charged **strong compressed flat member-block-ID catalog**? Unlike content compression, the proposed win is physical navigation/control storage and its selective-access economics; a larger entropy-encoded payload cannot be called a win.

## Pre-result mechanism, alternatives and predicted failure modes

Invented frame: reusable pair productions over exact block IDs; a member's compressed root stream links to productions; decode uses stored/derived subtree lengths for range navigation. All payload blocks are immutable, self-contained, exactly decoded, separately Zstd-19 compressed with immutable hashes, physical offsets, and declared bytes. RePair-like global pair selection is gifted to the oracle. The strongest simpler control receives **the exact same physical block dictionary**, but per-member sequences are encoded directly with the minimum of raw varints and Zstd-19 frames. Also report a **single solid Zstd-19 stream** of full logical files as a size-only control, and per-member direct Zstd-19 with full semantics/independent decode. No unfair omission of grammar descriptors, codec flags, lengths, path/member indexes, integrity metadata, block records, or source/reference bytes.

Prediction: a grammar may save index bytes on highly repeated motif sequences, but codec-compressed direct IDs may already subsume the pattern, and whole-container savings likely vanish under independently compressed payload and fixed decoder/metadata costs. The oracle could justifiably **falsify** production investment.

## Fixed test family / held-outs

Deterministic seeds `31, 101, 2026, 4096`; 16 files per case; 64 fixed-size 256-byte logical blocks/member. Families: repeated motifs with controlled mutation; rotated subsequences with controlled mutation; independent reference sequences; wholly independent opaque blocks. Inputs and variation are generated without inspecting outcomes; no path/extension identity-driven admission. Every member and physical block is reconstructed and SHA-256 checked. No fixed public release corpus or private data is modified.

## Honest evidence rung and decision

Run only the cheapest **charged local/reproducible oracle**. Search up to 96 global binary pair rules with deterministic non-overlapping substitution. Meter whole stored bytes, exact reconstruction, creator oracle wall, compressed metadata and grammar size, shared payload cost, per-member cold metadata work and selective physical/logical/decode bytes for 256-byte seeks. Preserve raw per-case losses; an oracle is not a valid r24 archive or product benchmark.

The family earns stronger-product consideration only if at least **two structurally different families** achieve >=1% *complete stored-byte* improvement over the best equally selective flat-ID control, with no logical reconstruction failure, with <=8x logical selective decode amplification and without violating the stronger solid/per-member size comparison disclosure. Failing this retires **this binary block-reference grammar frame**, not A07 or self-indexes universally. An oracle-specific positive cannot earn product credit until real format/Reader, generic admission, cold-open RSS/latency, updates, portable decoder and release parity.

Disproof: any generated member mismatch; descriptor omission; single baseline invalid; winner depending on a corpus/seed identity; selective work hidden; positive under only one family; or full archive byte savings <1% means no further implementation investment under this model.

## Concurrency and handoff

No product/CI owner source will be modified. Current Builder/Reader integration (#336/#442/#468/#472), source custody (#431/#473), and historical comparator (#306/#318) remain independently owned. An open research draft may retain decisive negative evidence; no merge/release implied. `docs/discovery/STATE.json` is managed under #440; do not overwrite it.