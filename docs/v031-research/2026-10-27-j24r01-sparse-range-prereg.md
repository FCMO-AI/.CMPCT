# J24R01 Sparse range lookup — preregistration

Base: PR #569 exact c5e13bb3fbb4cdade8b64246658ce7c7818de41f, format r24 unchanged.

Hypothesis: the strict monotone and nonoverlap properties validated at Reader open allow binary search over extent ends in Python 3.10+ with O(log E + overlapped extents) time and no auxiliary index. Control: exact old linear scan. Alternative: cached offset array, with O(E) additional memory and construction cost.

Prediction: same bytes for Builder-independent sparse range vectors, holes, zero-length, multiple chunks and adversarial geometry rejection. >10x selective-read hot speedup at 65,536 extents while preserving cold-open behavior; small E may be slower. Kill: any wrong byte, weakened invalid admission, or material >10% regression on small sparse requests. Measure complete stored bytes, open CPU/wall, repeated range wall/CPU, peak RSS, and raw repeated ABBA source-exact runs; no release credit from microbenchmarks.

Claim surface is S_SPARSE read_range only; no edit to S_CHUNKS validation, ZIP64, extractall, frozen benchmarks or parent PR. Outcome to be appended after evidence, not retroactively in this preregistration.
