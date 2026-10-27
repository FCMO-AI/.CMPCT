# J24Z02 preregistration: pooled Zstd streaming buffers

Parent: J24Z01 PR #550, commit 7e1d52b3badec55e0fb5556028a19b231e94fb31. Research only, no product or release edits.

Question: Does repeated Python buffer allocation and copying explain a meaningful part of the measured streaming-decode CPU and wall-time debt, while preserving its large memory saving?

Control A: authentic CMPCT Reader on the unchanged 64 MiB Zstd physical frame.
Control B: existing J24Z01 full CRC32/SHA256 64 KiB streaming implementation.
Candidate C: keep 64 KiB input/output windows but reuse the output allocation, feed CRC32 and SHA256 the live bounded buffer synchronously, and avoid materializing a new decoded Python bytes object for every 64 KiB window. Reuse bounded input storage.

Use the same authentic archive and exact 1 MiB requested range for every arm. Five alternating fresh processes per arm on Linux. Record original CPU and wall times, VmHWM, full decoded work, archive and source identity. Require independent selected-byte SHA256, complete physical CRC32/SHA256 and rejection of corrupt, truncated and trailing Zstd frames for both streaming arms.

Prediction: candidate C improves CPU and wall each at least 15% relative to B, with median VmHWM increase no greater than 4 MiB. Any missing integrity check or unsuccessful hostile case rejects C. If timing improvement does not meet both conditions, retire Python buffer reuse as a product priority.

Alternative explanation: inherent Zstd streaming cost or mandatory full-frame integrity dominates. Larger buffers already lost in J24Z01b; this experiment keeps 64 KiB output and changes ownership/copies only.

No product success or release credit follows from this oracle. Parent code, frozen evaluation, format and benchmarks remain untouched. Honest negatives and source custody must be retained.
