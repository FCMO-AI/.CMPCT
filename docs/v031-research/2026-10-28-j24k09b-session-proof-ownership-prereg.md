# J24K09b — Charge the per-session physical proof owner (preregistration)

Date: 2026-10-28 UTC. Preregistered before this oracle's source.
Primary product hypothesis/branch: #653 J24K09. **Research oracle only**, no change to released format or Reader guarantees.

## Observation prompting this fork
The first actual macOS 14 J24K09 same-source component court observed, at 4,096 earlier STORED streams, a 4.496 ms median single suffix-range call with the same-mmap BHDR size witness, versus 0.822 ms using an *optimistic predecoded* size callback and 0.526 ms with the known unsafe unguarded control. These do not share all integrity semantics; the result is a bottleneck/falsification prompt, not a release regression claim. The original wrong-byte bug is addressed by per-call physical proof, but its O(number of prior streams) cost matters.

## New question
Does one complete proof of physical geometry per immutable in-memory Reader snapshot, then using a local cached-size vector for successive suffix reads, lower total *session* CPU/wall versus proving every prior size for every suffix read? A sound product implementation would require a validated snapshot/invalidity boundary under same-inode mutation, so this oracle makes no production claim.

## Strong controls
- Per-read physical BHDR parsing through unchanged `_vzip_physical_stream_size`, no upfront work (current safe candidate).
- Prevalidate **every stream's physical header** upfront through the SAME actual BHDR function (no gifted lengths), store a compact owner-size array, then read suffix using those proven lengths.
- Unsafe no-size-witness control only as a lower bound; not a product competitor.
Run same synthetic physical bytes and recipes, same host/process, at 64 / 512 / 4096 streams and 1 / 8 / 64 suffix reads. Charge full upfront validation into total session cost; all replies must equal independently expected bytes. Repeat ABBA source-exact sessions and record raw CPU/wall measurements.

## Prediction / kill condition
The one-shot session must be slower or tied at Q=1 (extra setup and allocation), but should amortize at Q=64 for larger recipes. If it does not, retire a per-recipe cache as a low-value complexity increase. If it wins, this only proves headroom; a product design needs source snapshot/invalidity guarantees, RSS/allocation bounds, exact installed-Reader semantics and adversarial same-inode mutation tests. Missing those veto promotion.

## Adversarial limits
Cache trust is **not** allowed to survive a mutable source change without a proven invalidation/snapshot protocol. Do not conflate logical stream geometry with SHA authentication of arbitrary partial content (#646). Preserve negative outcomes and do not tweak the prior J24K09 test gates.
