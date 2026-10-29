# J24I21 — Sparse hardlink proof-reuse custody discriminator (PRE-RESULT)

**Preregistered 2026-10-29 UTC before code or measurement. SCIENCE ONLY, not Reader patch, release or security certification.**

## Source/ownership
Canonical shipped main is v0.30.0/r24 at `80c358f8824ec1b20d349c92ed94c898090969b0`. Exact research base is #620 HEAD `7ca3951d48b4ebabf07f740b551b009ce78a3e34`, whose Reader source Git blob is `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`. #620 and #738 retain Reader/product-composition ownership; #741 retains stage custody. This branch adds **only** a detached test/oracle, CI and receipts; no Reader, Builder, format, benchmark, thresholds or shared Discovery STATE edits.

## Primary question and falsifiable prediction
The #620 `verify()` intentionally repeats streamed SHA-256 for every sparse hardlink alias, even after memoizing terminal-owner **resolution**, to avoid losing observation frequency against a concurrently mutable archive. Test a **tempting simpler optimization**: a private, research-only monkeypatch that reuses one successful terminal-owner digest proof for all aliases within a verify call. Is it semantically interchangeable with unmodified #620 under a controlled mutation that happens after the owner's first successful proof and before the next alias?

**Predicted decisive disproof:** for an authentic Builder-created revision-24 16MiB logical sparse file with >=16 true filesystem hardlink aliases, unmodified Reader detects an in-place physical blob-byte mutation between verification calls, while a proof-cache oracle skips the next physical read and accepts. This would retire *naive* per-owner proof caching without immutable-archive custody, even if it saves CPU. The mutation must occur after the first owner proof, not before; the same source bytes must be used for baseline/oracle within each paired test before interposition. Verify physical framing, source SHA, and installed Reader Git blob.

## Controls and evidence ladder
1. Confirm source/install equality to #620 (not working-directory imports). Generate real S_SPARSE and K_HARDLINK entries from actual `Builder`, verify archive bytes and physical sparse admission.
2. Compare original `verify()` and a scoped proof-cached oracle on identical physical source, in fresh processes and A/B/B/A order, recording actual streamed proof calls, process wall/CPU, RSS, full logical and stored byte counts, archive SHA and output verification count. Also use a small 1-alias control and a larger >=16 alias case. This establishes *research/oracle* headroom only.
3. Inject exactly one in-place record-payload byte change between owner and alias verification (on independently copied source files, same pre-mutation SHA). Compare normal Reader and oracle outcomes. Preserve original file bytes; never alter the standard project tests or their expectations.
4. Run inherited #620 signed hostile-graph suite unchanged. An external/simple record-geometry audit plus per-file SHA/source fingerprint should check that the adversarial byte was within a physical blob rather than corrupting only the footer/index.
5. Preserve raw receipts even on failure. CI actual status and source fingerprints are mandatory; setup/runner failure is not product loss.

## Decision/kill, alternate causes, debt
If both methods reject, the predicted safety discriminator is falsified; inspect cache behavior and mutator offset, never weaken the baseline or forge a win. If the oracle accepts but baseline rejects, **naive proof cache is scientifically retired for mutable archives**, regardless of speed. If both accept, test has not shown equivalence; record ambiguity. If caching is slower, retire economic claim independently. Stronger options require an immutable physical snapshot, copy-on-write/FD custody or a proof whose physical consistency is certified, **fully charging** snapshot I/O, memory, source races and reader complexity. No product promotion from this court.

Concurrency caveat: a controlled actor with write access to the underlying archive is assumed. This proves only a bounded observation window, not remote exploitability, full TOCTOU defense, or archive authenticity against a signer who controls index SHA. Published Reader and all release checks stay unchanged.

## Value selection
This is a separate proof-ownership frame, not another #737/#738 compaction-RSS measurement. A cheap deterministic race discriminator can kill an entire unsafe CPU shortcut before expensive productization; ongoing compaction source, private stage and historical comparison owners are untouched. No evidence-backed Discovery policy change is proposed.
