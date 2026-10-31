# J24G97 — prospective O0 fault cut: archive generation and trusted head durability

**Freeze:** 2026-10-31 UTC. Separate follow-on question after J24G96/J24G96b O0, and **before** J24G97 script/measurement. Research-only under the same Draft PR #869; no new active product lane, release, format, benchmark, state or shared-file edit. Base currently `FCMO-AI/.CMPCT` v0.30.0 / r24 `main@80c358f8`. Original input artifacts are the same four provider-SHA-pinned J24G92/J24G91 ZIPs; compare only authentic adjacent footer roots.

## Primary question

Is the intended *externally trusted append head* enough for automatic crash-safe visibility if archive append and trusted-head publication are **separate durable transactions**? Preregistered answer: **no**. Either publication order has a crash cut where latest archive bytes and trusted root disagree. This need not mean archive corruption: those are separately valid states. Only an explicit persistent commit/rollback/recovery protocol can reconcile.

## Cheapest decisive control

For each of the eight authentic archive histories, select the physically genuine penultimate footer as committed prior state and last footer as next valid append. Build original `Cprev` as the exact file prefix through penultimate footer, and `Ccurrent` as complete original file. Verify both independently through unchanged detached r24 footer parser and compute prospective chain roots `Pprev`, `Pcurrent`. Test the *four actual archival/pin pairings*:

1. prior archive / prior independently trusted head: PASS.
2. current archive / current independently trusted head: PASS.
3. current archive / prior independently trusted head (append survived, trust-head commit lost): REJECT latest, optionally recover trusted prior prefix.
4. prior archive / current independently trusted head (head committed first, archive append lost): REJECT; no matching file generation for newest pin.

A fully attacker-controlled head can authorize the old archive and is the mandatory rollback negative. Matching a trusted ancestor is **not** proof that a legitimate append was or was not committed.

## Disproof and scope

Falsify if original Cprev/Ccurrent files are structurally invalid r24, Pprev/Pcurrent collide, either inconsistent cross-pair is accepted, or no historical prefix can be reconstructed. Require 8/8 authentic histories × four pairings = 32 observed O0 state checks. Charge original archive prefix bytes, appended suffix bytes, two optional external records (2×32B) and number of footer checks. Do not claim actual filesystem crash, atomicity, Windows execution, IPC, distributed trust, Reader/Writer correctness, author identity, source immutability, CPU/RSS or product improvement. No external trust-state machinery is implemented.

## Decision

If the predicted matrix survives, treat atomic **archive generation ↔ trusted head** commit as a productization veto to both J24G96 schemes; prioritize an authority-owned compare-and-swap/transaction protocol plus ancestor recovery compatibility before any format changes. It is not permission to change r24 or weaken release gates. A two-phase/rollback scheme is only a design hypothesis until physically crash-tested.
