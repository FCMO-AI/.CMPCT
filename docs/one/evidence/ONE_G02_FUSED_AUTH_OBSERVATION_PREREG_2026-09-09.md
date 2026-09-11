# ONE-G0.2 fused authentication observation — preregistration

Date: 2026-09-09  
Experimental version: ONE-G0.2  
Status: frozen before candidate implementation/result inspection

## Mission lock / referee

The promoted authenticated complete-archive seam proves that ONE0 can persist authentication state and reopen for authenticated, cone-proportional selective reads. Its writer currently rereads every regular-file payload in full solely to construct the generic AuthTree after the Surprise archive builder already read the same bytes.

The frozen question is whether authentication leaf construction can consume the same file bytes already required by ordinary archive ingestion, eliminating the authentication-only reread without changing ONE representation, archive bytes, authentication semantics, selective-read geometry, or hostile-input behavior.

This is a writer/dataflow experiment only. It adds no reader-visible opcode, codec, integrity mode, or format revision.

## Baseline

Baseline: `build_authenticated_archive()` at the preregistration parent on `research/cmpct1`.

Observed promoted debt on the system-seam fixture:

- logical regular-file bytes: 1,327,314 B;
- authentication-only source reread: 1,327,314 B (1.0x logical bytes);
- authenticated archive wire: 1,356,848 B;
- authenticated selective semantics: already promoted separately.

The baseline therefore performs two complete payload reads at the Python/source boundary: one to construct ordinary ONE file nodes and roots, then another solely to build per-file authentication trees.

## Hypothesis

A single ingest loop can derive both ordinary ONE file representation and AuthTree leaves from the same immutable bytes object. If the second read is accidental staging rather than a fundamental integrity requirement, the candidate should produce byte-identical authenticated archives while reducing physical source payload traffic from 2.0x logical bytes to 1.0x.

The important causal claim is elimination, not acceleration: authentication should consume already-read bytes instead of requiring another filesystem/source pass.

## Disproof / HOLD rule

HOLD or invalidate if any of the following occurs:

1. candidate wire differs from the baseline for identical source trees;
2. reopened file bytes, path semantics, authentication roots, or frozen selective request results differ;
3. candidate performs any authentication-only filesystem reread of regular-file payload bytes;
4. candidate source payload reads exceed exactly 1.0x logical regular-file bytes in the instrumented builder contract;
5. candidate median build CPU exceeds 1.05x baseline or any frozen row exceeds 1.15x baseline;
6. candidate peak retained payload state exceeds the baseline's one-file-at-a-time bytes contract merely to avoid rereading;
7. hostile source-change/path/resource behavior is weakened;
8. the result requires a new reader-visible representation or changes persisted authentication semantics.

Advance requires exact semantics plus the source-traffic elimination. CPU improvement is desirable but not required beyond the no-material-regression gates because the primary mechanism removes a complete source pass and should remain valuable on slower/remote storage even when the synthetic fixture is memory/cache dominated.

## Frozen matrix

Use deterministic temporary source trees with the same complete archive semantics and at least these payload shapes:

- one 32 KiB file;
- one 256 KiB file;
- one >1 MiB file crossing ONE chunk boundaries;
- mixed tree containing empty/tiny/medium/>1 MiB files, directories, and a safe symlink;
- multiple medium files so reuse of one giant aggregate buffer cannot masquerade as fusion.

For each row compare baseline and candidate on exactly the same source tree and record:

- logical regular-file bytes;
- baseline and candidate wire bytes plus SHA-256;
- exact wire equality;
- build CPU and wall time across repeated runs;
- baseline authentication-only reread bytes;
- candidate payload-source-read bytes and authentication-only reread bytes;
- regular-file count;
- reopened full-file equality;
- a deterministic set of authenticated selective reads covering prefix, middle, auth-leaf crossing, ONE-chunk crossing where applicable, tail, and zero length;
- persisted authentication metadata bytes;
- candidate peak per-file source-buffer bytes (modeled from the largest simultaneously retained payload in the builder contract).

## Invariants

- ordinary file payloads remain ONE roots;
- AuthTree remains generic Crystallization metadata in the canonical manifest;
- manifest/root commitments remain authenticated and exact;
- reader performs no discovery;
- selective requests reconstruct/authenticate only their existing aligned dependency cones;
- resource/path/symlink checks remain fail closed;
- no comparator, Genesis corpus, or September 11 scoring is touched by this experiment.

## Builder direction

Prefer one shared archive-ingest traversal that reads each regular file once, immediately derives its digest, ONE nodes/root and AuthTree from that immutable payload, then releases the file buffer before advancing. Do not cache the whole archive merely to claim one-pass I/O.

## Hostile-review target

The strongest likely failure is a fake fusion that removes an explicit `Path.read_bytes()` call but keeps a second complete memory scan and then reports it as zero cost. The benchmark must distinguish **filesystem/source reads** from **in-memory authentication hashing work**. This experiment claims removal of source reread traffic, not zero hashing/memory traffic.

A second concern is source mutation between metadata enumeration and read. The candidate has only one content snapshot; root digest and AuthTree must derive from exactly that same snapshot. This is stronger consistency than the baseline's two-read equality check, but it does not by itself provide filesystem transaction isolation. Do not claim snapshot semantics beyond the bytes actually read.

## Promotion scope

An ADVANCE promotes the fused ingest/dataflow principle for the research archive writer. It does not establish full mature-CMPCT recovery/filesystem parity, does not compact the JSON/base64 authentication index, and does not substitute for the September 11 Genesis matrix.