# ONE-G0.2 compact fingerprint ring-view — hostile amendment

Date: 2026-09-06
Experimental line: ONE-G0.2

## Defect found before result authority

The frozen preregistration includes a byte-generated case named `cyclic_local_hits`. Inspection of the immediately preceding local-index result showed that this byte pattern produced **zero local-ring hits**. Repeating source bytes does not guarantee repetition of the accumulated Gear-state key because the Gear state is not reset at motif boundaries.

Therefore the case name cannot be treated as evidence that hit-heavy lookup behavior was timed.

Any result from source `2359dd99efa64477e63d1d55ba9fde356b1cce6c` or earlier is **methodologically incomplete for promotion**, even if its workflow is green. It may be used only as diagnostic evidence.

## Frozen repair

Keep the complete original byte-generated matrix unchanged, including `cyclic_local_hits` as an ordinary structured input. Add one explicitly constructed **native key-stream timing control** that exercises the exact local-index event functions without Gear scanning:

- warm with 64 distinct keys whose 8-bit fingerprints are varied;
- then perform 4,096 lookup events cycling over those same 64 live keys;
- every timed event after warmup is therefore a true hit in both arms;
- use A/B-B/A native timing inside C, not Python per-event timing;
- preserve exact prior-position/hit/checksum parity.

The existing same-fingerprint collision stream remains a separate hostile semantic/work case and is not removed.

## Additional frozen gate

In addition to every preregistered gate:

- hit-rich stream candidate/baseline median elapsed must be `<= 1.03x`;
- hit-rich stream must have exactly identical hit count, prior-position decision checksum and live-entry count;
- candidate full-key checks on the hit-rich stream must not exceed baseline full-key comparisons.

No threshold, fingerprint width, stream length or lookup policy may be changed after observing the repaired result.
