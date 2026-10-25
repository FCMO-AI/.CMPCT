# O79b held-out multistream result — SHA fail-closed versus unselected corruption

Date: 2026-10-25. Status: **SCIENTIFIC POSITIVE, NO PRODUCT PROMOTION**.

This is a new prospectively preregistered test *after* original O79 (not a replacement of the first experiment or its negative). Preregistration commit `0e8197658c7857ffdc2b7a7aabc13984c87c5f6f`; real source-exact run [40191456187](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191456187) at `1af0261b605311ac0597a108cbab732af3fade5e`, **SUCCESS**, original [artifact 12598162304](https://github.com/FCMO-AI/.CMPCT/actions/runs/40191456187/artifacts/12598162304), archive SHA-256 `85c74574d1863cc344b39a9724ec8d1fde425fd9eafd8d7da465aa27299283d1`. Original JSON independently parsed.

Real installed unchanged r24 Builder/Reader/Codec, held-out authentic three-member ZIP with a 2MiB first Deflate, STORED member, second independently structured 1MiB Deflate; VZIP recipe 3 members with modes [0,0,0], complete original ZIP 9,474B, selected 64B from first Deflate. The research oracle hashes 9,474 **original compressed ZIP bytes**, not 3MiB expanded bytes, checks original recipe SHA and reconstructs exactly. All clean read/verify and selected range checks pass. The oracle is not production code.

Two distinct physical one-byte hostile mutations were made on **unselected** members (second Deflate and STORED): **2/2 SHA-authenticated range rejects**. Existing ordinary `read_range()` **returned selected bytes** without detecting either remote corruption; full `verify()` rejected both. Thus whole-recipe authenticated selective range genuinely detects corruption outside the requested range, a stronger guarantee than local-only CRC. It does **not** prove all crashes/hostile filesystem races or authentication across mutable storage; the experiment keeps hashes and returned bytes coupled through copied Python segments.

**Negative/cost:** full SHA scans all 9,474 nested ZIP bytes; large random ZIP incurs significant cost, as original O79 random-negative demonstrated. No new timing eligibility gate or product performance claim is inferred from this structural held-out test. Other complex ZIP layouts, multiple encoded stream versions, multi-GB input memory, source mutation during open, and Windows/macOS remain untested.

**CI truth:** O79b specialized actual hosted job SUCCESS; latest-head CI topology **FAIL** due to missing latest-head commit gate in the new deep workflow. This is an evidence-infrastructure red, not an experimental failure. No official r24 benchmark effectively executed on this HEAD. Fix topology before any later integration; do not waive the check.

**Decision:** multistream/unselected physical corruption generality **SURVIVES tested scope**. The simplest next useful step is a bounded proof-cost and source-lifetime review with the VZIP product owner. No canonical merge, format change or release.
