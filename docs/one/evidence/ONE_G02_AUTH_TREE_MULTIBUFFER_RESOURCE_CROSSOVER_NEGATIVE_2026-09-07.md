# ONE-G0.2 auth-tree multi-buffer resource crossover — negative

## Mission lock / Referee

Question: can exact current ONE AuthTree SHA-256 construction use Intel Multi-Buffer behind a content-independent node-count threshold while improving writer wall time and CPU, with bounded explicit workspace and unchanged authenticated bytes?

Frozen authority: `docs/one/prereg/ONE_G02_AUTH_TREE_MULTIBUFFER_RESOURCE_CROSSOVER_PREREG_2026-09-07.md`.

Result-bearing source head: `502e2e75a0d78ab4d164c3b73188ab804caf17f3`.
Hosted run: `34109668113`.
Pinned external research oracle: Intel Multi-Buffer `4f808234a91e87147a4f26167df40f3fd7c7f0c6`.
Artifact: `one-g02-auth-tree-multibuffer-resource-502e2e75a0d78ab4d164c3b73188ab804caf17f3` (artifact id `10013995558`).

## Result

**Decision: `reject_node_count_multibuffer_dispatch_principle`.**

All baseline and candidate roots were byte-identical and the accounting checker reported no root/accounting mismatches. The scientific gate failed because no discovery suffix satisfied the frozen elapsed+CPU criteria, so no node threshold was learned and no holdout was dispatched.

Discovery rows, candidate / baseline:

| root bytes | nodes | wall | CPU | staged/source |
|---:|---:|---:|---:|---:|
| 1,024 | 22 | 2.3209x | 2.1036x | 2.0586x |
| 2,048 | 41 | 1.8311x | 1.7551x | 1.9873x |
| 4,096 | 78 | 1.4827x | 1.4586x | 1.9336x |
| 8,192 | 152 | 1.3218x | 1.3141x | 1.9004x |
| 16,384 | 299 | 1.1954x | 1.1934x | 1.8824x |
| 32,768 | 592 | 1.1507x | 1.1497x | 1.8712x |
| 65,536 | 1,178 | 1.1002x | 1.1001x | 1.8648x |
| 131,072 | 2,349 | 1.1071x | 1.1068x | 1.8614x |
| 262,144 | 4,690 | 1.0880x | 1.0880x | 1.8595x |

Independent holdouts were likewise raw losses: 6,144 B 1.3039x wall / 1.2960x CPU; 12,288 B 1.1912x / 1.1889x; 24,576 B 1.1322x / 1.1314x; 49,152 B 1.1094x / 1.1089x; 98,304 B 1.0989x / 1.0987x; 196,608 B 1.0782x / 1.0780x. Because there was no learned threshold, the frozen dispatcher correctly retained baseline on every holdout.

Candidate fixed extra explicit workspace was 56,064 bytes, in addition to baseline tree storage. Candidate total explicit workspace therefore ranged from 56,544 B at the 1 KiB discovery root to 168,448 B at 256 KiB.

## Builder interpretation

The previous elapsed-only multi-buffer seed does not transfer to the resource-accounted frozen experiment. The candidate's curve improves with width but asymptotes above baseline over the measured range. The strongest visible cost owner is staging: the candidate copies roughly 1.86 source-equivalents even at large roots, before hashing work is complete. A node-count selector cannot cure an implementation shape whose raw candidate remains slower throughout both discovery and generator-distinct holdouts.

Do **not** rescue this result by raising the minimum root size, weakening the CPU gate, excluding small rows, or dispatching based on the same failed node-count coordinate.

## Hostile Reviewer

This negative is limited to the tested multi-buffer implementation shape and node-count dispatch principle. It does not prove all parallel SHA scheduling is bad. In particular, a future candidate that removes or amortizes message staging, reuses already-materialized writer buffers, or changes the authenticated-tree construction work while preserving exactly the same authenticated bytes is causally distinct and may be tested under a new preregistration.

The 56,064-byte figure is the benchmark's explicit candidate workspace. Persistent implementation-internal manager allocation is outside that explicit accounting, so this result should not be used to claim a complete library-memory footprint. That omission cannot rescue the candidate because it already loses on wall and CPU before any additional manager memory is charged.

## Campaign consequence

Retire automatic node-count multi-buffer dispatch for this candidate. The shared authenticated-family path remains independently promising: native shared-family transfer at the same source head showed roughly 0.112x persisted bytes and 0.112-0.115x build time versus nine independently authenticated roots, with about 1.065-1.069x read time and exact/corruption gates clean. Authentication-tree creation remains optimization debt inside that broader structural win, not a reason to abandon the shared Law+Surprise family.
