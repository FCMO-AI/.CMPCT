# J24G84 — A08/A07 exact path-name adjacency: charged metadata O0

Date: 2026-10-30. Status: **preregistered before instrument or measurements**. Research only; no product, format, ABI, compression result, release, comparator or benchmark promotion.

## Authority and original opportunity
Published v0.30.0 is revision 24; v0.31 is unmerged development. Use the exact immutable development base `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Main Discovery STATE is staleable and #574 owns state reconciliation; no edits to STATE or constitutional/release files. Parallel #833 owns the fast-Reader-vs-Writer-session full-product question; #820/#829 own replay and Writer state lifetime. This experiment changes a DIFFERENT information/representation boundary only: checkpoint/index path names. No other implementation claims.

A08 asks if update history and checkpoint state admit better exact representation. A07 asks whether explicit navigation metadata duplicates structure. Filename sequences have long prefixes; conventional front coding removes repeated prefix bytes but also costs a prefix integer, length integer and decoding. Mature Zstd already captures much of the same redundancy. The point of this O0 is to **kill** that classical family quickly if full Zstd-compressed metadata does not materially improve.

## Primary question, baseline, alternative, falsifier
On actual revision-24 Builder-produced index objects representing four deterministic, structurally distinct trees, does a fully reversible **adjacent-name prefix transform** improve the Zstd-19-compressed **complete authenticated index payload**, after charging every decoder-visible prefix/suffix byte, framing, unchanged blobs, recipes and filesystem metadata, relative to the SAME index untransformed and compressed with SAME Zstd-19 engine/settings?

A = `Zstd19(msgpack.packb(original_index, use_bin_type=True))`. B = `Zstd19(msgpack.packb(index_with_all_original_names_removed_and_encoded_frontcoding_field, use_bin_type=True))`. Original row ordering must be retained; no free sort/permutation and no invented external dictionary. Candidate decoder must restore the byte-exact original MessagePack stream and every original name before any size result is credited. The compressed actual index is a **research oracle** only; not a valid revision-24 on-disk archive.

Deterministic held-out structural families (no benchmark fixture identity): sorted-flat-numbered; deep multi-level folder hierarchies; low-prefix random/hash-like basename; mixed Unicode and variable-depth. Each builds a real CMPCT archive via unchanged Builder/Reader in reproducible mode. Additional hostile standalone lists include shuffled names, duplicate names, empty name, and Unicode distinct-codepoint sequences to prove exact order and byte semantics; they do not assert valid filesystem admission.

**Prospective H1 materiality:** B must reduce total compressed index bytes by both >=5% and >=256 bytes in at least TWO of the four independent structural families, and must not increase bytes by >1% in any family. Otherwise **NO_GENERAL_METADATA_HEADROOM**; retain positives as narrow observations only, do not tune thresholds or declare product win. This is a deliberately high bar for imposing an extra decoder and on-disk representation. If H1 passes, future work still requires full archive files/reads, CPU+RSS, archival/ZIP/native parity and an economic/admission argument before any productization.

## Predeclared alternatives and BONK
- Simpler control A is modern Zstd-19 over the original MsgPack index, not raw uncompressed strings.
- Rename/path trie alternatives are strictly *more* complex and deferred until a cheap frontcode bound demonstrates missing headroom.
- A gifted name-only oracle is weaker than the whole-index charge; cannot earn credit.
- Hash-like names and shuffled order are direct hostile falsifiers.
- No name-specific threshold, generated-fixture hash, downstream dictionary, side-channel or external work may be gifted.
- Other product owners already address the measured Writer CPU bottleneck; this O0 must stay limited and cannot claim to supersede their work.

## Evidence contract
Commit research-only Python instrument and focused Ubuntu workflow separately after this immutable prereg. Attest exact base/ancestry, installed package source, dependency versions, deterministic generator seeds, file tree, original MessagePack SHA, recovered MessagePack SHA, exact compressed byte counts and encode/decode CPU/wall, host, and source HEAD. Preserve all four results including losses. Reference the original artifact/run. At minimum use independent output-byte comparison and adversarial decoder tampering/invalid framing rejection; refuse fallback masquerading as the candidate.

A source-level experiment without hosted exact-HEAD results remains PENDING. One-host O0 cannot claim cross-platform portability, product acceptance, complete archive savings, create/extract speed or release credit. If H1 fails, retire generic frontcoded names as an independent index-format direction absent a **new** causal mechanism or real-data regime.

## Safety/public surface
No shipping src/native file edits, official benchmarks, format, version, policies, evaluator, frozen thresholds or v0.30 release evidence. Synthetic fixtures only, no private filenames/credentials/client material. No general path-mangling assumptions. Do not update Discovery STATE (current owner #574).