# O228b prospective transfer falsifier — Builder-produced CDC run structure

**Frozen before implementation and any O228b outcome:** 2026-10-27 UTC. Research-only continuation of O228 #600, whose original hosted oracle was successful at merge ref `389f3283...` and source blob `59916588...`. Released CMPCT remains v0.30.0 / revision 24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`. This file introduces no product/format claims or authority.

## Question and the cheaper discriminator

O228's 262,144-reference synthetic index showed bounded wins, but an actual Builder emits **CDC chunks only for files over 4×256 KiB** (source `src/cmpct/builder.py:107-114`) and its CDC minimum is **128 KiB** (`src/cmpct/codec.py`). A 262,144-reference authentic Builder file would therefore require **at least 32 GiB** of logical CDC data. The original O228 64–88-byte chunks are not directly Builder-generated. Also, current `Builder.scan()` creates S_CDC, S_BLOB, S_SPARSE and S_PACK, but does not appear to create S_CHUNKS for ordinary current inputs; S_CHUNKS is a reader/legacy representation. These are source-grounded observations, not yet an empirical corpus transfer result.

**Primary hypothesis (transfer):** At least two distinct reproducible dense file families built with the actual released Builder produce adjacent identical CDC (length, physical-owner) runs long enough to yield a >=2× index-unpack heap saving *without increasing full dual compressed-index bytes*, and one family saves >=1% of complete archive bytes after all unchanged physical records and duplicated index are charged.

**Strong simpler control:** the released Builder's literal CDC index compressed by its existing Zstd12 path, plus full physical blob records. Do not compare an uncompressed list with a compressed grammar. A post-hoc choose-smaller complete-index portfolio is a gifted *oracle* only, not a valid generic admission rule.

## Protocol, observable and kill

- Deterministic self-generated 16 MiB dense single-file sources, never fixture identity as encoder policy: repeated all-zero (best case), periodic 1 MiB high-entropy blocks, alternating two independent high-entropy blocks, a shift/perturbed repeat, structured repeated records, and independently generated high-entropy bytes (hostile).
- Use the **actual v0.30.0 Builder**, with `workers=1,reproducible=True`, and read its genuine complete r24 archive via ordinary `CMPCT`. Record exact Builder and Reader source hashes, logical SHA, archive SHA/size, physical owner count, storage tag, CDC reference count, full run-length histogram/max, and preserved read/verify results.
- Modify **only a cloned in-memory decoded index** to prospective storage tag 105 and `[count,length,physical-owner]` runs. Charge full MessagePack/Zstd12 index bytes twice, new tag, unchanged physical record bytes, unchanged framing and metadata; do not claim such a hypothetical archive is readable by present Reader. Measure candidate encode CPU/wall, full archive byte delta, decoder-only heap via isolated child processes when feasible.
- Do not customize the Builder's chunker, its minimum size, dedup policy, compressors, or per-file format. Do not bypass `Builder` to insert synthetic logical references.
- If no two nontrivial distinct Builder families meet the stated joint heap/no-byte-debt criterion **and** none achieves >=1% complete-archive savings, classify `NO_BUILDER_TRANSFER_AT_THIS_SCALE`; retain O228's synthetic large-N result as a separate oracle, not a contradiction. If the criteria pass, classify `BOUNDED_BUILDER_TRANSFER_SEED` with all negative rows and mandatory format/Reader/portability/update debt. If the workload generator/CI cannot produce meaningful CDC cases, mark `INSTRUMENT_INVALID`, not a product negative.

## Anti-confirmation and decision

The experiment can show no material product leverage because CDC's >=128 KiB minimum makes these reference lists tiny even when repetition exists, or because ordinary Zstd already compresses the index. If that happens, retire further threshold gardening on short run-length patterns and focus on structurally different information/ownership. Never grant product credit from this oracle, never rewrite O228's frozen protocol, and never alter current release gates or `docs/discovery/STATE.json` (state reconciliation #574 ownership).