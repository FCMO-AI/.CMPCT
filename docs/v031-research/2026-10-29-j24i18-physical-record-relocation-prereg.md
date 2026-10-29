# J24I18 — Physical r24 archive-record relocation oracle (pre-result preregistration)

Date: 2026-10-29 UTC. Status: **PREDICTION FROZEN BEFORE RUN**. Research only; no product promotion, no release claim.

## Owner / independence

This is an independent **representation/ownership** experiment. Base is released main `80c358f8824ec1b20d349c92ed94c898090969b0`. It does not edit `Builder`, `Reader`, `transactions`, format, CI gates, or frozen comparators and does not compete with #723/#735/#738 compaction implementation, #726/#740 staging custody, or #620 sparse verification. Scientific evidence will use independently generated revision-24 artifacts originally attached to #723/J24I06; exact bytes and identities must be recorded. `docs/discovery/STATE.json` is stale and not a lock.

## Baseline / problem

`compact_archive()` reconstructs the logical archive into an on-disk filesystem tree, then invokes `Builder(root)`. That exports cost and authority into untrusted filesystem path materialization, re-encoding and large sparse/hardlink logical reads. Existing #726 reports a stage-name substitution risk; #737 measures >254 MiB RSS alias amplification for a 128 MiB sparse source on a specific stacked candidate. Those are independent measured controls and are **not** proof this oracle works.

## Primary falsifiable question

Can a fresh revision-24 checkpoint be formed by copying the *exact authenticated physical blob records*, rewriting only blob offsets in the latest authenticated logical index, and emitting an ordinary full primary/tail index and footer, without ever reconstructing filesystem entries or decoding logical payloads? This is a new architecture frame, not a threshold adjustment.

The cheap first variant retains **all** indexed blobs (including dead records) in original index order. It must preserve every logical index entry, filesystem metadata, blob SHA/CRC/codec/meta/compressed bytes and exact logical reconstruction under an independent parser. It may remove obsolete journal framing but earns **no dead-blob reclamation** credit. The later sparse/ref-closure variant may prune only when every descriptor/dependency is exhaustively accounted for; unsupported kinds must fail closed.

## Predicted outcome / control / kill

H1: on at least six distinct physical r24 inputs spanning regular data, symlink literals, true hardlinks, sparse extents, metadata and a committed delta, the unoptimized all-blob oracle produces a readable checksum-valid single-checkpoint archive, exact latest logical metadata, and identical blob-record bytes in indexed order.

H2: on the genuine delta input, it eliminates obsolete *journal framing* while retaining unused physical records; no claim of archive-size superiority to the extract+rebuild baseline. A small or negative size result is scientifically acceptable.

Strong simpler control: existing installed #723 compaction artifact when available, independently parsed for semantics and byte size. Alternative explanation: existing Builder recompression/dedup may make its output smaller despite the oracle's lower logical work. Distinguish encoding time, source parsing time, pure relocation time and verification time; do not time local Python in lieu of hosted platform performance.

Kill/narrow: any mismatch in full logical index (except blob offsets), blob integrity, fsmeta, bytes or hash; inability to verify a complete r24 archive without trusting the same algorithm; or unsafe handling of unsupported formats. If metadata/physical correctness holds but size worsens, preserve as an execution/ownership seed with explicit size debt, not product credit. If a cheap proof shows raw-relocation cannot remain safe under verified source identity or update concurrency, retire/no promotion pending source-fd/root-binding design.

## Evidence rung and adversarial checks

Use the cheapest independently parsable physical archive corpus already available. Parse header/footer, replay committed delta, authenticate indexes, copy exact blob records using bounded file-slice reads, re-encode primary/tail indexes using standard libzstd, recompute canonical SHA. Independently parse output, compare latest rows, all storage descriptions (including sparse and hardlink), fsmeta, original blob bytes/hashes, and footers. Include explicit corruption mutations (truncated record, forged record size, altered record hash, journal corruption); fail closed or explicitly classify unsupported. Record raw archive bytes and full SHA256.

No actual secure publication claim: output is written into an isolated local working directory. No installed CMPCT candidate on all three operating systems, adversarial concurrent source write, atomic fsync/durability test, official performance gate, large-scale memory/RSS test, or full arbitrary-codec/virtual-recipe closure is inferred from this oracle.

## Competing research actions, PARETOBONK

- Exploit sparse alias owner #738/#620: owned; avoid duplicate.
- Patch staging #740/#726: owned; avoid duplicate.
- Repeat Win32 leaf HANDLE #739: owned; avoid duplicate.
- Physical-record relay oracle: different ownership model, cheap ability to falsify filesystem-staging necessity. Chosen.
- Universal production direct compactor: rejected before micro evidence due large correctness/safety burden.

The result must be recorded append-only with actual checks, negatives, and cheapest next decision. The Discovery Engine policy and release law must remain unchanged.
