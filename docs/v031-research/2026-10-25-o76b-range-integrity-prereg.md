# O76b prospective hostile semantic-equivalence test — mode-0 range integrity

**Scope:** independent adversarial follow-up to the already-run O76 installed range-economics oracle at `632ec5b81260602b774fcf62a382443ba28a8764`. That original result and thresholds are immutable. **Preregistered before hostile instrument implementation.**

## Mechanism / concern

O76 compared regenerated Deflate (`stream_mode=2`) versus retained raw Deflate (`stream_mode=0`) on authentic unchanged revision-24 archives and observed a major selective-read wall benefit. An equal-bytes, equal-Reader trial is not necessarily an **equal-integrity-tier** trial: in `reader.py` mode 2 uses `_blob()` (per-blob CRC32 check), while mode 0 obtains physical compressed-stream bytes directly from `mmap` through `_stream()` without per-blob verification during `read_range()`. The original full-file `read()` / `verify()` still checks reconstruction. This matters because a performance optimization that delivers unchecked bytes under corruption cannot be credited as equivalent to a verified path.

## Falsifiable experiment

Build one deterministic valid high-ratio Deflate ZIP under both original Builder policies, require S_VZIP mode2 and mode0 respectively; verify full original archives and exact selected physical 64-byte range. Use the authenticated index to locate the physical mode0 `CODEC_DEFLATE` compressed stream record. In an independent copy of the CMPCT archive, flip one byte **inside that selected physical range** but outside index/footer, preserving lengths. Open corrupted CMPCT and call `read_range()` on that exact selected 64-byte range; check whether it returns bytes silently differing from the source. On the same corrupted archive, independently invoke `verify()` in a new Reader and require it to reject; this proves the mutation is detected at full-authentication boundary. Apply a symmetric physical corruption to mode2 raw-content blob and test `read_range()` in a fresh Reader; record whether it rejects via `_blob` CRC rather than silently returning bytes. Repeat on two different deterministic high-ratio streams; exact offsets/hashes, exceptions and raw byte differences must be recorded. No global fuzzing or blind-byte searching.

## Prospective decisions

**If mode0 silently returns corrupt bytes while full verify rejects and mode2 range rejects**, O76's large speed ratio is an **integrity-tier mismatch** in corrupted-source conditions and can receive no verified-range product credit. It remains truthful micro-level range-economics research on valid immutable archives. **If both ranges enforce equal integrity or both silently allow corruption**, narrow the criticism accordingly and record which guarantees actually hold. A legitimate performance product path must explicitly choose an API integrity tier or add authentication/proofs for mode0 without hiding the cost. Never weaken `verify`, `read_range` or synthetic mutations to rescue speed.

## Authority/coordination/cost

Canonical v0.31 development Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, Codec `29526db4203723d83523fc95d074c346b63d7587`; official format remains r24 and v0.30 released. No product or evaluator change; only scientific attack in PR #433. No production mitigation or release credit. Candidate compaction is measured with full-archive byte economics, but checking authenticated range semantics has priority over claiming an unchecked speedup.
