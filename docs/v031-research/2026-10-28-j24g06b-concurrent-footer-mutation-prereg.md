# J24G06b — Prospectively falsify negative-footer memo correctness under same-inode source mutation

**PREREG BEFORE INSTRUMENT.** Source parent product candidate #650 exact `10a6bc150cfa0ceb8608ee826dc09650ca3f4e3d`, Reader Git blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`. Published original main `80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. This branch is scientific only; no Reader source change, merge/release/version/format authority.

## Falsifiable question

Can a per-open negative ancestry cache incorrectly skip a footer that becomes a valid signed generation **during** one Reader constructor if an actor can modify the same open archive inode between two candidate validations? This matters because J24G06 caches a failed ancestor at one instant and #650 explicitly does not claim a stable immutable source snapshot. Do NOT assume a currently passing static hostile corpus proves source mutation safety.

## Preregistered deterministic adversarial experiment

Create authentic release Builder archive whose tail checkpoint footer position is known. Append TWO locally SHA-committed no-op delta footers: A (older) has `prev=0`; B (newer) has `prev=A`. Both are initially invalid chain heads, so both actual Readers fall back to Builder's checkpoint. At the first actual decoder visit to A *within the candidate B replay*, preserve the original decoder result with `prev=0`, then write a new authentic FTR for A on disk at the SAME OFFSET, with `prev=Builder checkpoint`, keeping payload/hash identical and not changing file size or FMAGIC; the subsequent scan then sees a **different but valid** A header. Observe actual selected generation and delta depth using unchanged original Reader compiled from historical Git blob vs the J24G06 integrated candidate Reader, each on independent identical copies of source archive, with the SAME deterministically scheduled mutation event.

**Prediction:** original Reader revisits A as a candidate and selects the now-valid footer A (generation depth1), while cache candidate regards A as known-invalid and instead selects original Builder footer (generation depth0). Both may read the same member content, so source-generation identity/selection, not only SHA of logical bytes, is mandatory falsifier. If both choose same footer, hypothesis falsified. Include unchanged no-mutation control; signed FTR before/after full SHA and proper header unpack. Do not patch _index_from_footer or affect decoder return; only invoke genuine original decoder and arrange physical mutation immediately after reading A once. The file is opened for Reader as read-only but a separate handle can change same inode, mimicking an independent writer.

## Interpretation and launch gates

If confirmed, a change in supported semantics under same-inode mutation is a **candidate-specific temporal consistency risk**, not automatically a remotely exploitable vulnerability nor necessarily a regression under a documented immutable-source contract. No release until source snapshot/custody or a narrow supported immutability boundary is resolved. If false, preserve negative; doesn't establish all concurrency safety.

This experiment does NOT change a protected benchmark/evaluator, weakening a comparator, or give release credit to either Reader. It establishes one bounded (two-footer) deterministic interleaving only. Hold the original #650 source and scientific negative unchanged. No Discovery STATE update until decision-changing result; link issue #649 on decision. The on-disk FTR header parent pointer is mutable without changing the MessagePack payload SHA, so check full before/after archive SHA to show mutation was real.
