# J24C07b — signed VZIP preflight economics, prospective control (before instrument)

Status: **research performance question, not product/release credit**. Parent candidate #638 composed exact #630 guarded Reader with existing #624 VZIP guard. This addendum preregisters an *additional* performance court before its instrument and workflow changes.

## Question and baseline
Does the bounded physical-projection validation cost materially more than unchanged #630 preflight when many valid recipes exist? Compare identical authenticated archive bytes, same Python and host and module source, not separate historical benchmarks or distinct corpora. Baseline is parent #630 commit `0a128ff55c7ae0f14c6bdf019a81b40f0d894eff`; candidate is #638 post-transfer source. Both must accept every valid file and preserve identical effective index semantics.

## Mechanism and prediction
For each recipe the candidate scans literals and payloads one more time and compares fixed authenticated blob sizes. Preflight already traverses the recipe and the complete file table. Predict candidate/baseline median wall and CPU ratio <=1.25 on two independent valid recipe regimes at 4,096 files/recipes, with no extra physical blob reconstruction. This is an *economic screen*, not an official promotion threshold. A ratio above 1.25 (or a semantic mismatch) is a preserved negative and mandates cost attribution before product integration.

## Input, controls and falsifier
Construct wholly authenticated revision-24 archives from frozen positive STORED and retained-Deflate golden wires. Retain the original physical blob bytes, vary only index copies consistently, create 32/512/4096 distinct file names, each with its own copy of the valid recipe referencing existing blob IDs. Both original and candidate receive the same archive path, bytes and source SHA recorded. Do not read archive identity into optimized code. Because the original archive's source geometry is independently valid, false invalidity at higher counts is a functional negative.

Two ABBA cycles per size and mode, in fresh Python subprocess workers, 10 preflight repetitions within each worker. Separate process startup wall from timed calls, record raw wall/CPU samples, source identities, complete archive size/SHA and status; Linux VmHWM optional as diagnostic. Independently recompute medians from raw JSON, disallow silently dropped workers or swapped source/archives; do not count benchmark output unless source/semantic custody passes. Strong control: #630 exact source, with package installed into an isolated target directory; candidate into a different isolated target directory. Import outside checkout to exclude accidental source-folder leakage.

## Kill conditions and scope
Any valid golden rejected, source mismatch, raw-result loss, invalid ABBA order, changed file/byte identity or ratio above the prereg screen falsifies the corresponding claim. Never move the 1.25 screen, comparator or structure to rescue the result. No cold-OS-cache claim, no native ABI, no official release/full Reader economic credit, no separate archive-size/create/extract performance claim. Focus solely on the preflight additional cost while inherited #569 reference-heavy opening remains known red.

## Decision
If the focused three-host correctness court passes and this source-exact screen is acceptable, hand off as a bounded integration candidate to #630/#569 owners. If negative, preserve the measured cost; repair only if it changes the product decision. No change to Discovery STATE (#574 owns), frozen benchmarks or version.
