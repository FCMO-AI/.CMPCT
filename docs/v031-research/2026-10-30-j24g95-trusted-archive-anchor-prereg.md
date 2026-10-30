# J24G95 — Externally pinned whole-archive SHA as a simpler integrity control (preregistration)

Date: 2026-10-30 UTC. Status: **O0 research only, prospective**. Exact parent PR #856 `f29561c5e2d36a8f47aa35f61191911c0611be6b`; released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, revision 24. Do not modify product Writer, Reader, format, benchmark, comparator, version, release, native ABI, evaluator, or `docs/discovery/STATE.json`.

## Problem and distinct frame

Issue #857 and separate PRs #856/#859/#860/#861 establish that r24's payload SHA does not bind the predecessor pointer; both physically nearest and nearest-rooted heuristics have decisive negative controls. Rather than reimplement lineage guards, test the **different trust/ownership frame**: one separately trusted whole-file digest for a closed archive snapshot. The question is whether it cheaply detects both one- and two-parent edits, what complete physical bytes must be hashed, and where this simple control is unusable for mutable archives.

## Prior/controls

Controls: unchanged original CMPCT files, single-parent rewire, double-parent camouflage, other same-length data mutation, and a **legitimate append by the real public Writer**. A trusted digest is an **external prerequisite**, not a magically authenticated untrusted sidecar. A malicious writer controlling both the archive and its untrusted digest defeats this scheme; a stale *trusted* digest also refuses legitimate committed appends until an authorized update. Distinguish this snapshot identity from an in-format footer SHA and from a signature or MAC.

## Prospective hypotheses and honest kill/narrow conditions

H1 integrity: on real Builder/Writer-produced r24 archives, a previously pinned external SHA-256 accepts the original bytes and rejects every changed-byte variant, including one-pointer and two-pointer rewires. If not, the instrument or representation claim fails. H1 is trivial cryptographically; its value is a **physical control and actual ownership-cost bound**, not a claimed invention.

H2 economics: record complete file length, streamed bytes read, median wall/CPU over at least 31 samples, peak Python-traced allocations and cold-process limits separately, for 16/128/4096 member shapes on Ubuntu and Windows at minimum. Compare *same-host*, *same-file* public Reader cold-open separately with explicit per-sample scope; never subtract measurements from earlier CI. Run fixed chunked SHA (1MiB) and optionally a whole-buffer SHA as an optimistic control, **without calling the latter a bounded-memory implementation**. Preserve raw samples; do not claim a speedup or choose thresholds after results.

H3 boundary: a real valid Writer commit changes the whole-file digest and is refused until separately authorized replacement of the anchor. This is expected functionality, not a regression. If legitimate post-write bytes falsely match the old digest, fail. No full-file hash can be reused after append from a finalized SHA-256 digest without retaining appropriate intermediate state or rereading bytes; do not imply append-O(1) updates.

## Scientific evidence rung and validation

Use genuine Builder+Writer archives and byte mutations under temporary directories, enforce source blob identity, compare candidate bytes and Reader/preflight semantic controls with PR #856. Test archive bytes of different platform provenance, no fixture-specific optimization. Minimal positive and hostile cases; preserve actual complete hashes only in evidence. Independently audit hosted artifacts/JSON if possible. Scientific O0 only: **no product credit** until trusted-anchor transport/custody, update transaction, recovery, cross-platform/native/CLI integration, full size/create/extract/RSS/temp I/O and threat-model boundaries survive.

## Coordination, anti-duplication, decision

Do not duplicate #859 or #860/#861 implementation. They own parent-guard and Writer orphan recovery. This work owns only a **trusted external snapshot anchoring cost/control**, not a new r24 ancestry guard. Notify #857 with exact results and scope. No Discovery state mutation; #574 owns reconciliation. Keep this branch Draft; no merge/release. If whole-file attestation is too expensive for large/mutable archives, preserve that negative and prefer a next-format authenticated commit lineage plus trusted root rather than threshold gardening.
