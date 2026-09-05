# ONE-G0.2 direct generic-control streaming — terminal negative

Date: 2026-09-05
Experimental line: ONE-G0.2

## Frozen question

Could the promoted one-pass +1 Ref/Surprise segmenter emit an identical generic control stream directly, avoiding the transient `Segment[]` write/read, and earn a separate writer implementation on speed as well as memory traffic?

Frozen authority: `docs/one/evidence/ONE_G02_DIRECT_GENERIC_CONTROL_STREAM_PREREG_2026-09-05.md`.

## Exact CI receipt

- branch source: `9facbfface10c69717e8ea4576e3bf6f7925a6e6`
- PR merge SHA executed by Actions: `737c6a17428985df7c142398bf52df2c538f99f6`
- workflow run: `33981789429`
- job: `101348190244`
- artifact: `9973993563`
- artifact ZIP SHA-256: `a1cafc89d3da3ad02a89823bbed1cdb1cc7b1e7015795fe699a31bcefa6c8196`
- ONE semantic/hostile tests: **83 passed**
- frozen experiment conclusion: **failure / hold**

All 14 rows were byte-exact against baseline and the independent Python oracle. Accounting was exact. Candidate and baseline each scanned the target once. Candidate transient segment-plan bytes were zero on every row while baseline reached **65,568 B** on 256 KiB `fragmented_every96`.

The frozen timing claim failed. Median candidate/baseline elapsed across all 14 rows was **0.9757155x**, above the preregistered <=0.95x gate. The >=16 KiB fragmented rows also failed the required <=0.90x gate:

- 16 KiB: 0.94259x
- 32 KiB: 0.97849x
- 64 KiB: 0.96144x
- 128 KiB: 0.95963x
- 256 KiB: 0.97387x

The dense quarter-damage rows became neutral or slightly slower as size grew, culminating in **1.03183x at 256 KiB**, which also exceeded the per-row <=1.03x cap.

## Causal interpretation

The transient plan is real memory traffic, but it is not the dominant elapsed-time owner in this kernel. Once both paths already use one target scan, run classification plus identical control/payload emission dominates enough that deleting the plan array only buys a few percent. A second writer implementation is therefore not justified as a general speed path.

This is a useful negative result, not a request to retune the 0.90/0.95 gates. The direct emitter may remain discovery evidence for a future explicitly memory-constrained implementation, but it is **retired as the general speed optimization tested here**.

## Hostile reviewer / next owner

Moving upward into the actual ONE wire exposed a more material blocker: the temporal-adjacency integration can generate a flat `concat` with more references than the reader's hard `max_nodes`-derived per-node cap. The current workflow also masked that Python exception behind `tee` because it lacked `set -o pipefail`; a green run was therefore not valid scientific evidence.

Next work should repair evidence plumbing, preserve that overflow as a real bounded-reader failure, and test whether the same generic concat relation can be hierarchically compiled under existing limits with measured wire and reconstruction overhead. Do not add a shift opcode and do not simply raise the hard cap.
