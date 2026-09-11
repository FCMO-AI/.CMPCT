# ONE-G0.2 — fused phase-witness native cost-owner decomposition preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Parent evidence: exact source `df083da415fb8aa426c3f6a1ed84cd6d25f5e32d`, workflow `33973449301`, job `101325924360`, artifact `9971607895` (`sha256:d98b9c280c557b19b8c523bff5daccbca3e8d8965e10fa7840beba44a2b5bf80`).

## Mission Lock / Referee

The frozen unconditional fused phase witness is structurally exact but economically rejected. Native witness tuples matched the independent Python reference on every control, all pre-existing ONE semantic/hostile tests passed, and retained state stayed at 248 B; nevertheless the five-large-control median fused/baseline elapsed ratio was **2.7600x**. Random and compressed-like were 2.7044x and 2.9138x, and the 4 KiB / 64 B controls were 3.2088x / 3.0203x.

The failed gate already forbids changing phases, bottom-4 witness count, hash, stride, or thresholds as a rescue on those controls. The parent preregistration instead requires profiling the owner among per-byte raw-window maintenance, phase hashing, and bottom-K admission.

This experiment does exactly that. It does not attempt promotion.

## Frozen variants

Compile four native loops from the same source and compiler flags:

1. **baseline** — promoted observer control: run observation + Gear update/anchor test only;
2. **word** — baseline plus the 8-byte rolling raw-word register, but no phase test, hash, or witness structure;
3. **hash** — word plus the frozen phase schedule `{0,1,2,30,31} mod 32` and the frozen `_mix64(word ^ 0x9E3779B97F4A7C15)` at every sampled phase, but no bottom-K witness admission; hashes are accumulated into an escaping checksum so the compiler cannot delete them;
4. **full** — the exact rejected fused witness path, including bottom-4 maintenance for all five phases.

The full variant must remain witness-identical to the frozen Python phase-certificate reference. The intermediate variants are diagnostic only and cannot nominate a Law.

## Frozen controls and timing

Reuse the exact parent controls and repetition policy so the decomposition explains the rejected result rather than creating a new cohort:

- random 1 MiB;
- zlib-compressed random ~1 MiB;
- repeated-basis 1 MiB;
- shifted/versioned 1 MiB;
- zero 1 MiB;
- alternating-byte hostile 1 MiB;
- random 4 KiB;
- random 64 B.

Use seven outer repetitions and the same internal repetition scaling as the parent. Report median elapsed for all four variants and incremental nanoseconds per input byte for:

- `word - baseline` => raw-window carrying cost;
- `hash - word` => phase test + frozen hash cost;
- `full - hash` => bottom-K witness maintenance cost.

Negative incremental values caused by timer/code-layout noise remain visible and are not clamped when choosing the owner.

## Falsifiable hypothesis

The dominant exported cost is expected to be **phase hashing**, not the rolling word itself or the rare bottom-K replacements. This is falsified if phase hashing is not the largest positive incremental median cost on at least four of the five large gate controls.

## Frozen interpretation law

- If one component is the largest positive increment on at least 4/5 large gate controls, name it the stable first cost owner.
- If no component wins at least 4/5, record a co-dominant cluster; do not pick the largest aggregate after seeing the data.
- Full witness/reference mismatch invalidates timing interpretation and must be fixed before any optimization.
- This experiment cannot revive the unconditional fused path. It only selects the next causal Builder.

## Next move by outcome

- **raw-window owner:** derive phase words from already-required observer state or sparse snapshots instead of maintaining an independent byte window;
- **phase-hash owner:** test a mechanism-level reuse of already-computed Gear state / a cheaper certificate algebra whose collision/exact-window contract is independently preserved; do not merely reduce phase count on this cohort;
- **bottom-K owner:** replace heap-style online admission with a branch-light fixed-size selection network or buffered/block selection, preserving exact bottom-4 tuples;
- **co-dominant:** fuse the owning stages together or opportunity-gate certificate construction from independent cheap evidence rather than micro-tune one layer.

No density, reader-speed, format, v0.29, deferred-v0.30, or product promotion claim follows from any outcome.