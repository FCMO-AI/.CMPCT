# O4 outcome — verifier-fed compressed wire identity can bind a later bounded copy

Date: 2026-10-23
**Class:** positive *detached mechanism* oracle; not a full ZIP writer and **not a product fix**.
Predicted preregistration: `benchmarks/history/2026-10-23-v031-deflate-wire-identity-o4-prereg.md` committed `9473a61e5eb382229214aa0618126e1144418d5d`, before executable `e1672fe8ba09531bd92accc031268c1eafd34dd2`.
GitHub hosted exact-head [run 40021926321](https://github.com/FCMO-AI/.CMPCT/actions/runs/40021926321), job `120648354300`, source `5f95955af28fde180b5289936cc806b506df2e99`, **SUCCESS**; steps O2, O3, O4 all passed. Artifact `12531420806`, ZIP SHA-256 `8f67210ba2d88a09803f1fd4c02d09b77d96d573cbf5ed13ccf348c588e40078`, containing all three original JSON receipts, exact source SHA, Reader and instrument Git object identities.

## Observations (r24 actual source, raw-Deflate private-stage research, Linux/Python3.11)

| Condition | Preflight | Wire comparison/publication | Existing output |
|---|---|---|---|
| Valid immutable physical source | genuine CRC32/SHA256/length verified; compressed wire SHA captured from **the same immutable byte chunks fed inflater** | exact compressed stream SHA matches bounded copied bytes; published | replaced with correct Deflate |
| Corrupt before proof | strict original logical proof rejected | not published | preserved |
| In-place mutation **after proof** | original stream verified | copied wire SHA differs; private stage rejected/deleted | preserved |
| Mutation **mid-copy** at a future payload byte | original stream verified | immutable chunks actually written hash differently; rejected | preserved |
| Source altered and subsequently **restored to identical source file SHA** | original stream verified | copied wire SHA still differs despite final source SHA equaling initial SHA | preserved |

CI output: `VERIFIER_FED_WIRE_IDENTITY_REJECTS_POSTCHECK_AND_MIDCOPY_SOURCE_MUTATION`.
All three O2/O3/O4 experimental suites passed on the exact HEAD; O4 had **5/5 outcome regimes as preregistered**, all existing-target integrity and staging-cleanup assertions green. The copy uses <=256-byte chunks; verifier input <=65,536 bytes, decoder output <=65,536 bytes. These are **per-buffer experimental** ceilings, not product RSS measurements.

## Important distinction from O3

O3 independently tested a *complete real ZIP* output: verifies staged ZIP member logical CRC+SHA on actual emitted data then publishes. O4 tests only detached **raw Deflate compressed stream** staging. Its smaller cost potential comes from hashing each compressed chunk twice rather than decoding every alias again after copy. O4 does not prove all ZIP metadata, repeated logical aliases, archive-level publication, end-of-stream CRC in actual ZIP, directory records, ZIP64/count/offset, resource-exhaustion behavior, cross-platform guarantees, or atomic crash durability.

A new production implementation could compute wire SHA as part of existing unique-blob logical verifier and **hash the exact immutable bytes buffer passed to every real ZIP output write**. Re-reading an unlocked source to compute the preflight wire SHA in another pass would reintroduce the TOCTOU hole. In an output-staged implementation, compare the wire commitment of all copied members, check all other non-Deflate members and metadata under existing semantics, then atomically publish only after all pass. Charging output temp bytes and multi-member hash traffic remains mandatory.

**Disproof of overclaim:** This evidence does not establish arbitrary concurrent mutation resistance when metadata commitments themselves are mutable, nor does it prove safe pathname publication under hostile destination changes. The mere presence of a SHA-256 hash anywhere in the path does not ensure its input is the data actually published. PR #284 owns implementation and release decisions.

## Counterfactual

An exact-before/after immutable-buffer equivalence assertion would have exposed the PR #284 preflight/copy trust boundary without random race timing. The more precise rule is prospective: whenever a pipeline independently verifies and consumes the same mutable backing store, prove which **exact immutable bytes** were verified and ultimately published. No single scientific episode modifies global discovery policy.
