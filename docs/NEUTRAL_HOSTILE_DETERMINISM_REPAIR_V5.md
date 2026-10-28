# Neutral/hostile media determinism repair v5

Status: **preregistered benchmark-substrate experiment / no baseline migration until cross-run equality**.

## Failure being repaired

Repair-v4 added FFmpeg bitexact mode, one encoder thread and stripped metadata. It passed two differently
nested regenerations on each individual runner, but failed when repeated on a fresh GitHub host:

- round A media: tree `4751714e55227cec997d00a53039656bea9671a432f9214dee213c1710fef543`,
  **28,844,501 logical B**, exact v0.28 **28,722,245 B**;
- round B media: tree `2eb3279c5a7abd85100d0c04cd8afb7bace157abb9430ed04b87dc3aaf7f377e`,
  **28,845,891 logical B**, exact v0.28 **28,723,474 B**.

Office, logs and backup rows reproduced exactly across those fresh runners. Therefore v4 is preserved as
REJECT and the historical/repair-v3 baseline is not rewritten.

## v5 hypothesis

The remaining source of variation is plausibly host CPU feature dispatch inside FFmpeg/native encoders.
V5 forces a common software CPU surface (`cpuflags=0`, `cpucount=1`), one filter/encoder thread, bitexact
mode and stripped metadata. For the libx264 fixture it additionally enables x264's cross-CPU
`cpu-independent` policy and disables assembly dispatch (`asm=0`).

These controls change only benchmark generation. CMPCT and every comparator must consume the exact same
resulting files after an identity is accepted.

## Frozen acceptance contract

The workflow launches **two independent hosted-runner jobs**. Each job first regenerates the four affected
workloads under two different directory shapes and must prove byte-identical file manifests internally.
Then a third job compares the two independent-runner JSON records.

Repair-v5 is accepted only if, for all four rows, both runners match exactly on:

- tree SHA-256;
- file count and logical bytes;
- every relative file path, byte length and SHA-256;
- exact v0.28 selected archive bytes;
- v0.28 raw graph/inherited bytes and selected strategy.

The evidence retains every per-file manifest. If v5 fails, the record must identify which exact media
file/codec still changes rather than collapsing the mismatch into one opaque tree hash.

## Non-goals

- Do not replace H.264/AAC, FLAC or MP3 with raw/easier benchmark material just to obtain determinism.
- Do not patch finished media bytes after encoding.
- Do not update preserved baseline hashes or thresholds from a one-run success.
- Do not treat a within-run pass as acceptance; v4 already disproved that standard.

A cross-run pass earns a **new explicit benchmark identity**, not permission to rewrite historical v0.28
evidence. Dependent generalization evidence must be regenerated against that new identity in a later,
separately visible commit.
