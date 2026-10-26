# J24F06b — Linux current RSS discriminator, preregistered after first physical A/B

2026-10-26 UTC. **Independent add-on, not a replacement of J24F06 pre-observation preregistration.** The original J24F06 result-bearing source at `32cc6bc25863c1948185460882d797e506187ecb` is frozen. Hosted Linux/macOS #40401295594 both succeeded with correct outputs, but Linux 16/64-MiB `ru_maxrss` medians were bitwise identical between historic J24F04 and bounded-window J24F05 while macOS measured substantial high-water RSS savings. This discrepancy is a valid **negative/ambiguity** of high-water measurement; it does not negate the owned-copy bound.

## Separate falsifiable question

Is Linux process high-water RSS a stale/earlier dominant allocation unrelated to the actual RAW transfer, hiding a **current resident-memory** difference during the transfer? A cheap observational discriminator is the Linux `/proc/self/statm` resident-page count read **inside the already-independent syscall-count control worker** just before extraction and at the first and last actual `os.write`, with the same code sources/archives/sha and no changes to uninstrumented performance workers.

Predictions: J24F04 may show a transfer-point current RSS increase from its owned whole-RAW snapshot; J24F05 may not, even when whole-process `ru_maxrss` is identical. Or both may show indistinguishable current RSS; that would falsify the cheap current-RSS explanation and leave physical-memory economics unresolved. Do not infer memory ownership from noisy current RSS without fully accounting for mmap-resident source pages, baseline importer memory, kernel page cache and OS process accounting.

Do not insert observations into the timed A/B workers; the existing uninstrumented medians and exact-output gates remain unchanged. Preserve first/last/pre-extraction resident-page samples as secondary evidence only, mark unavailable on macOS instead of inventing a portable number. Never treat non-positive or absent samples as product gains. Any output difference, source drift, or uninstrumented timing change is a hard failure. No new release claim, policy edit or changed threshold.
