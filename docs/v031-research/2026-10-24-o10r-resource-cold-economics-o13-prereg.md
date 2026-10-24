# O13 preregistration — price signed-generation ceilings against installed O9 Reader economics

**Date:** 2026-10-24 UTC. **Status:** PREREGISTERED before instrument or result.
**Parent O10R SHA:** `54c998200b1908b696ade049fe94df71a736c284` (resource ceilings); **control O9 SHA:** `1d8701588bdb8ece69749149a60d4b70a643e12f` (indexed replay, no ordinary Reader generation caps).
**Released product:** v0.30.0, physical revision 24. This O13 is research-only; no release, comparator/format mutation.

## Primary question
Does O10R's new eager `ParserLimits` import at ordinary Reader footer admission materially erase O9's verified cold journal speedup or export a meaningful penalty into checkpoint-only opens? Source inspection predicts checkpoint import debt because O9 avoids validation import on a checkpoint, while O10R imports validation even before checking signed footer type. O9 already lazily imports validation for signed deltas; 4096-journal penalty should be much smaller but remains to be measured.

## Prediction and cheap falsifier
Create authentic signed Builder-backed r24 journal files with 512 and 4096 renames, plus logically identical fully signed checkpoint controls. Under unchanged default resource settings, compare O9 original Reader *exact source* vs O10R installed Reader using fresh independent subprocesses, same O10R non-Reader dependency closure, alternating historical/candidate order and identical archive SHA/input semantics. Record raw import+constructor/CPU, whole Python subprocess wall, Linux VmHWM/ru_maxrss, exact reconstructed index SHA, physical payload SHA, and all archive bytes. Use five ABBA/BAAB repeat blocks (10 per cell).

**Prospective decision:** If O10R checkpoint cold-open exceeds O9 by BOTH >5% and >3ms in controlled medians, declare meaningful exported checkpoint debt; if 4096-journal import+constructor is worse by BOTH >5% and >3ms, declare journal replay debt. Independently report any >10MiB and >10% VmHWM increase. Do not relax the official parity comparator or treat its PASS as proof about cold Reader open. A larger source-only Reader regression must be preserved even when all official gates pass. If negligible, O10R passes this economic filter and next work is stronger whole-wheel A/B or broader hostile caps only if warranted.

## Controls, alternatives and limits
Simpler static import inspection predicts risk but is not product measurement. Import-time micro alone omits actual signed Reader/index work; a full CI release matrix cannot measure startup latency with adequate precision. Reuse O11's proven fresh-subprocess experiment architecture rather than invent a new benchmark method. Historical O9 Reader dynamically loaded into O10R *installed* package's non-Reader dependency closure: not a full independent O9 wheel. O9 historical source hash `bd1df6091c952e74c8690cf2ba0764747e6db815`; O10R installed Reader Git blob `2402721258531a56cfa2a53dcbd81874fd6c1f76`. These identities must be checked before data collection.

## Kill / safety / coordination
Any drift in source blobs, editable candidate module, archive/source hash mismatch, final index discrepancy, payload mismatch, or unaccounted omitted repetition invalidates the measurement. O10R's 3-host authenticated limit court already passed; this O13 **does not reimplement the limits**, mutate Reader, change policy, touch shared Discovery STATE or claim source-independent causal proof. This separate branch is scoped to measurable exported cold/CPU/RSS cost; owner PR #365 remains intact. Preserve negative results and raw receipts even if O13 finds debt.
