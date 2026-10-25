# O62 — O59 historical custody x O60 product union (preregistered)

Date: 2026-10-25 UTC. Prediction recorded before code composition.

Base: O60 PR #415 at c88a6bc29b9ec8738e23aab788b7c09ab0390e79; historical test source: O59 PR #414 at 93c04cb86734fc91b3ff95a71916ec15056f9540. Released v0.30.0, archive revision 24 unchanged.

Question: Does the O59 original O47-parent Builder comparator run against the real O60 one-buffer VZIP code with full-archive byte equality on tiny/mixed stable sources, both Git-history depths, and POSIX FIFO rejection unchanged?

Proposed test: reuse O59 fixture and test Git blobs exactly. On Ubuntu/macOS/Windows install candidate and execute the three original tests, with full and shallow Git on Ubuntu/Windows. Prove historical O47 blob 6f60dfe63742ff4b777f959a15d6fb828ae29610, test blob 20faf26980693342439c7730f62bd0bab8daca0f, candidate Builder bda9d7f8005e276ba891aac75ae50eabe67bd431 and codec dc3446b0eed82edfba9380e3885a20aa45577899.

Falsifier: any source custody mismatch, improper skip, changed archive bytes, broken installed import, or FIFO acceptance rejects this union. Stronger controls: original O59 5-host and O60 3-host hosted runs, plus inherited CI. Do not soften controls. No code/format/release change; do not update shared discovery STATE. Leave owners #414 and #415 untouched. If failure, preserve it and do not promote.
