# J24K11c — Signed owner-type adversarial transfer and corrected bridge result

Date: 2026-10-28 UTC
Status: **HOSTILE BOOL-INDEX ADAPTER COUNTEREXAMPLE CLOSED IN SCIENCE; STRICT PROJECTION TEST PASS; NO PRODUCT PROMOTION**.
Source: [Draft PR #660](https://github.com/FCMO-AI/.CMPCT/pull/660), exact-hosted scientific HEAD `a175bc42a52e4da2f9b0e4682ea703eb8053d951`.
[Three-stage Ubuntu CI #40655650597](https://github.com/FCMO-AI/.CMPCT/actions/runs/40655650597) **SUCCESS**, original hosted raw [artifact #12802001156](https://github.com/FCMO-AI/.CMPCT/actions/runs/40655650597/artifacts/12802001156), ZIP SHA-256 `0f6c19ed7381c4a83708220d3399b04a30a1b243e6ad933131ba635962aa6680`.
The new falsification and remedy were preregistered as a distinct addendum `7cc965e3f36bf036ecd083d02bba97bc81b82f26` before the source fix.

## Negative discovered after J24K11b — preserved, not rewritten
The previously favorable science-only adapter materialized a 7-field native row using `blobs[rawref]` before proving `type(rawref) is int`. Python's `True==1` index alias permitted a signed `rawref=True` to select owner 1 and then pass the fast native physical header check, whereas the current J24K09 production Reader's `_vzip_physical_stream_size` explicitly rejects non-exact integers.

A local original-source witness proved: `type(True) is int` is false, `blobs[True]` selects descriptor 1, and `native.scan` accepted the projected bytes. **This is an experimentally falsified adapter equivalence claim, not a demonstrated flaw in published CMPCT or the guarded Reader**; the adapter is not installed in either.

## Remedial source and exact hosted test
The modeled Python projection now verifies exact signed index type, nonnegative in-bounds owner, exact integer `csize`, and supported physical mode before constructing the tuples. The strong direct Python control now rejects unsupported modes consistently. The C scanner remains unchanged and does not convert malformed source input into approval; the adapter rejects before the C boundary.

All original **54 hostile signed-length/physical-header cases** still reject and all **108 new reference/type cases** reject across 18 cells: boolean owners, integer subclasses, negative/out-of-range refs, unsupported methods/modes, and boolean signed sizes. The scientific source court passed all 648 raw timed observations, 324 repeated original J24K11 samples, both separate receipt auditors and **9/9 forged receipt rejections** for the new strict-reference audit (the original court retained its own 8/8 forged receipt rejections).

## Retested, freshly charged strict adapter economics
The held-out 4,096-stream mode/layout cells retained a valid-input advantage over the strong direct Python loop. All CPU and wall ratios are within **2.787x–2.995x** on this Ubuntu CPython 3.11 run; the **worst frozen 1.5x discriminator remains satisfied**.

| Representation modeled | Physical owner order | Direct Python wall | Strict projection + native wall | Wall speedup |
|---|---|---:|---:|---:|
| STORED | Sequential | 2.514 ms | 0.840 ms | **2.995x** |
| STORED | Permuted | 2.391 ms | 0.853 ms | **2.804x** |
| Canonical Deflate mode0 | Sequential | 2.470 ms | 0.850 ms | **2.907x** |
| Canonical Deflate mode0 | Permuted | 2.584 ms | 0.901 ms | **2.867x** |
| Retained Deflate mode1, opaque owner | Sequential | 2.491 ms | 0.863 ms | **2.887x** |
| Retained Deflate mode1, opaque owner | Permuted | 2.516 ms | 0.903 ms | **2.787x** |

The row projection allocates approximately **426,264 B of transient Python list and tuple object overhead** per 4,096-stream call, with all construction included in measured wall/CPU. Separate process RSS and true future memory-traffic under actual Reader are unmeasured.

**Do not infer the change from 3.87x in the earlier run to 2.787x now was itself the incremental cost of type guards.** These are different hosted runs with different absolute baseline/candidate times, without a same-runner direct A/B of the original insecure projection versus corrected projection. It would be scientifically invalid to attribute that ratio difference causally to the fix.

## Authority and product boundaries
These are only r24-compatible **synthetic physical BHDR component geometries** and modeled signed recipes, not independently authenticated CMPCT archives. No real installed `read_range`, full verification, mode2 regenerated streams, true source ownership under mutation, source FD vs mmap safety, release parity, wheels on three systems, or peak RSS was established. A 2.787x component ratio is **research/oracle credit, not a product improvement**. On native negative, an actual Reader must preserve original Python fallback/error semantics. No changes to `src/`, `native/`, frozen tests, CI evaluators, format, version or release occurred. Parent J24K09 #653 remains the only product owner.

The transferable prospective lesson is **never allow a fast adapter to normalize a hostile signed reference before applying the original exact-type/bounds validator**. This originated from a specific counterexample, not enough evidence to rewrite the Discovery Engine policy.

The next highest-leverage unclaimed action is a genuine signed r24 installed Reader A/B including whole-Reader CPU/wall/RSS, reference projection allocation under multi-query use, failed native fallback on all hostile modes, and fd/mmap same-inode mutation behavior. If the current corrected adapter loses there, retire productization despite micro headroom. Published product still **v0.30.0 / revision 24**.
