# v0.30 Office v0.25 compact-floor locality result

Status: **research/oracle evidence; zero release credit**.

Exact source: `4082c08f4d98f3e4bd8af4becf9e0ceb38eb4762`, Actions run `35306897195`, job `105480828060`, artifact `10531781945`, artifact ZIP SHA-256 `fdb8d7c73991aeceae4e5121a9cc23cb5656b88a78afa3e3733d56f8d477231b`.

Accepted repair-v6 Office tree: `aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57` (20 files / 16,063,798 logical bytes).

## Result

The current checked-in v0.25-style EntropyGraph engine built the exact Office tree to **5,954,026 B** and strong verification reproduced the accepted tree identity.

This equals the immutable historical v0.28 Office floor recorded by the oracle and is **200 B smaller** than the current nested-floor observation (`5,954,226 B`). The distinction is provenance only: this experiment tests the current checked-in v0.25-style engine directly and does not re-label it as canonical v0.30 product evidence.

The selective-read falsifier passed the current `<=8x` locality law:

- maximum member amplification: **4.001128526645768x**;
- members over 8x: **0**;
- weighted member amplification: **1.0258147543936995x**;
- worst member: `assets/dashboard_3.png` at **4.001128526645768x**;
- exact-tree strong verification: **PASS**.

The measured build itself took **0.463597182 s** on the GitHub-hosted oracle runner. That single research timing is not a release/runtime comparison and receives no speed credit.

Terminal oracle decision: **`COMPACT_FLOOR_SURVIVES_LOCALITY_FALSIFIER`**.

## Causal consequence

The old ~5.95 MB Office floor is **not** cheap because it violates the current selected-member locality contract. That alternative explanation is falsified on the accepted repair-v6 tree. The representation is both dramatically smaller than the current canonical-r25 G04 Office contender and comfortably inside the 8x selective-read ceiling in this oracle.

This changes the next question. PrefixGraph locality rehabilitation remains interesting, but even a successful repair only starts from its measured **7,605,401 B** complete artifact. The v0.25-style floor is another **1,651,375 B smaller**. Therefore the higher-leverage representation problem is now to determine which exact v0.25 ownership/reconstruction mechanisms produce that compact floor and whether those mechanisms can be expressed inside the current bounded r25 product contract without importing obsolete grammar, parser debt, or unbounded work.

Do **not** port the historical engine wholesale. Treat it as an oracle. Decompose its byte advantage by mechanism and test the smallest semantically compatible materialization against the current r25 G04/PrefixGraph tournament. Charge all metadata, recovery, native-reader, filesystem and locality costs. A candidate that only reproduces the old research grammar earns no product credit.

## Strongest negative / remaining uncertainty

This result establishes only exact reconstruction + archive bytes + per-member physical-pack locality for one accepted Office tree. It does **not** establish current r25 legality, native parity, hostile-input safety, two-way recovery, current filesystem semantics, create/extract parity, strict external competitor creation-time dominance, or transfer beyond Office. Those are precisely the debts a productizable compact-floor mechanism would have to pay.

The next decisive lane is a mechanism attribution oracle: identify the byte contribution of stream pooling / ZIP-stream reconstruction / micro-packing / derived recipes versus a strong current r25 control, then materialize only the dominant transferable mechanism behind current semantic boundaries. If no bounded current-semantic subset can retain material advantage, preserve that negative rather than reviving the historical format by sentiment.