# ONE-G0.2 authenticated Law archive — result

Date: 2026-09-09  
Decision: **ADVANCE_AUTHENTICATED_LAW_ARCHIVE**

## Exact evidence authority

- branch: `research/cmpct1`
- exact evidence source: `171c01df0e5db86c9916132b45c7ec3671d5b27f`
- workflow: `CMPCT1 ONE-G0.2 authenticated Law archive`
- run: `34425312005`
- job: `102709185689`
- artifact: `10132563332`
- artifact digest: `sha256:32ca57d28e169797a84aee6892c03c995dad0fd5a519f9711a89e69c1cd32f74`
- experimental version: `ONE-G0.2`

The hosted lane checked out the exact source, passed the inherited authenticated archive/selective/native/validated-Program semantic surface (`76 passed`), ran the frozen falsifier, and retained the exact-source JSON artifact. No gate threshold was changed after observing the result.

## Mission lock / falsifiable hypothesis

Hypothesis: a two-file temporal object can be stored as one authenticated CMPCT archive in which the current file is ordinary ONE `add8` Law over the previous file, while preserving the same user-visible paths, exact full reconstruction, tamper rejection, authentication-index cost and cone-proportional selective reads as the Surprise-only authenticated comparator.

Disproof: HOLD if productive sizes save less than 25% wire, if the Law archive requires a larger authentication index than the comparator, if a fixed first 4 KiB read reconstructs more than one 4 KiB authenticated leaf, or if inherited exactness/resource/authentication semantics diverge.

## Frozen result

All frozen promotion gates passed.

| file bytes each | logical bytes | Surprise-only authenticated wire | authenticated ONE Law wire | wire saving |
| ---: | ---: | ---: | ---: | ---: |
| 32 KiB | 65,536 | 67,642 B | 34,887 B | **48.4241%** |
| 128 KiB | 262,144 | 268,368 B | 137,310 B | **48.8352%** |
| 512 KiB | 1,048,576 | 1,071,208 B | 546,933 B | **48.9424%** |

At all three scales the authentication index is byte-for-byte the same size between comparator and Law archive:

- 32 KiB/file: `904 B` vs `904 B`;
- 128 KiB/file: `3,976 B` vs `3,976 B`;
- 512 KiB/file: `16,264 B` vs `16,264 B`.

A first 4 KiB selective request remains exactly a **4 KiB reconstruction cone** at every scale. For those rows the Law path reads 4 KiB of source, writes a 4 KiB source plan, reconstructs/authenticates a 4 KiB leaf and uses one plan command. Requests crossing an authentication-leaf boundary expand to the expected 8 KiB cone rather than the whole file. No positive row falls back.

The 512 KiB/file archive therefore avoids **524,275 stored bytes** relative to the authenticated Surprise-only comparator while retaining the comparator's authentication-index footprint and small-range locality.

## Why this matters

This is stronger than the earlier isolated Program/wire microbenchmark. The Law is now composed into an actual authenticated archive surface rather than measured as an abstract candidate payload. The current file remains an ordinary ONE `add8` root; the previous file is its information basis. The archive still exposes two ordinary file paths and reconstructs both exactly.

The result demonstrates, for this temporal Law family, that ONE's density advantage does **not** require giving back CMPCT's authenticated selective-access property. The stored relation and the authentication/index surface coexist in one archive without duplicating the full current file or enlarging the authentication index.

## Hostile review / remaining debt

This result is intentionally narrow and must not be confused with the September 11 Genesis gate.

1. It covers an exact add8 temporal relation, not the full 15-workload corpus or automatic broad Law discovery.
2. Creation CPU/wall and peak RSS are not measured by this falsifier; the already-promoted writer evidence remains the authority for relation discovery/proof economics.
3. A 4 KiB Law cone still packs/writes a 4 KiB source plan. Earlier selective-cone evidence shows this is acceptable on Law-positive rows, but planning/source packing remains a real reader cost owner.
4. The archive composition uses the research ONE envelope. It does not by itself canonicalize the future public `.cmpct` format or claim full production recovery/portability closure.
5. The result proves that authentication overhead does not erase the relation win on this controlled family. It does not prove the same for every future Law topology or Crystal placement.

## Comparator / Genesis truth

Frozen comparator authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No Genesis 15-workload scoring was performed here. This mechanism-level ADVANCE cannot substitute for the same-input, same-semantics gate at or after the first qualifying activation on 2026-09-11.

## Next decisive action

Keep the authenticated Law archive as promoted composition evidence and stop optimizing this exact add8 fixture. Before the gate, prioritize breadth and measurement closure: certify the 15-workload gate substrate/readiness without scoring it, preserve exact comparator authority, and make sure the best ONE candidate can expose complete creation/decode/access/resource evidence on those frozen inputs. If a mature v0.29/v0.30 structure remains stronger on a workload, absorb the predictive structure into ordinary ONE Law rather than adding a permanent archive mode.
