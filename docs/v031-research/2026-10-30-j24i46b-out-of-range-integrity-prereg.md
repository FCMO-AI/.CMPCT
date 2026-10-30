# J24I46b — out-of-range corruption discriminator (prospective)
Date: 2026-10-30 UTC. Research-only extension to #796, recorded **before** introducing a corrupted FLAC source.

## Mechanism discovered from current source audit
The native r24 `decode_wav_flac_blob` in #788 (exact source `2a6dbd5407731c5660faf71d04a4ef5de2d431bd`) reconstructs **all** codec-2 bytes and checks SHA-256 against CMA4 **before** exposing even a partial `Archive::read_range`. The newly preregistered libsndfile seek oracle checks only the requested PCM region. Identical requested bytes do not imply equivalent full-member authentication, regardless of a successful seek performance result.

## Bounded falsifier
Take one valid independently fully-decoded FLAC from J24I46; flip exactly one bit in a late compressed audio-frame region (>70% of physical payload, excluding all metadata), target a 4KiB PCM range around 25% of the logical file. Preserve source FLAC SHA and mutation offset. Compare (a) full sequential decode and whole logical SHA/CRC versus original, (b) single-range seek bytes to original WAV. A sought range may pass while full stream is invalid/changed; if so, **seek-only is not a drop-in optimization** for native full-digest read semantics. If the seek refuses due global validation, record it; do not rescue by altering corruption position until a clear preregistered bounded second attempt. An invalid FLAC may be decoder-rejected rather than expose a different PCM hash; either is sufficient for whole-stream negative. Do not construct a fake revision-24 archive or claim a shipping vulnerability.

## Consequence
Even if fast libsndfile seek is measured on clean inputs, productization requires a separate authenticated locality proof (e.g., durable per-frame/segment digests under a trusted root, verified source cache with strict snapshot policy, or full pre-verification) **or** a deliberately reviewed change of integrity semantics. Each route has exported index bytes, CPU, RAM, recovery, dependency and portability costs. Baseline complete decode is allowed to win on contract equivalence.
