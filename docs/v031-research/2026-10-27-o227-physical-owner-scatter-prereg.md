# O227 — physical-owner scatter / operation-local decode oracle (prospective)

Date: 2026-10-27 UTC. **FROZEN BEFORE instrument, workflow and result-bearing execution.**

## Authority, inherited evidence, concurrency
Canonical shipped CMPCT stays v0.30.0 with wire revision 24; `main@80c358f8824ec1b20d349c92ed94c898090969b0`. This research-only branch starts from O226 #594 `12a8b08a661746653a4af1801dfe89c00a39dd85`, which carries the exact J24C02 #569 Reader source blob `dbd4ac576a05a47eae97e1e40de89cf1de440516` (source parent `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`). Do not modify Reader, O226, cache policy (#506/#510), #569 or discovery STATE (#574 owner). No simultaneous PR known claiming physical-owner scatter full-read. This is a materially different execution/ownership frame from O223/O225/O226 repeated serial-versus-futures scheduling; no further scheduler threshold gardening.

### Primary question
Can a bounded **per-full-read physical-owner scatter pass** avoid duplicate *uncached* (>2 MiB) decoder work when chunk IDs recur at non-adjacent offsets, while preserving exact revision-24 reconstruction and not exporting unacceptable output-copy/RSS cost?

This mechanism traverses the authenticated effective logical references, builds physical-owner postings of logical destination offsets, decodes each physical owner once via unchanged `Reader._blob`, scatters into one preallocated logical output and returns bytes. It may save repeated decode but incurs O(number of references) transient postings and a complete additional output-copy boundary. No format, cache, validator, historical test, or codec changes; experiment only.

### Competing actions and BONK
- Strongest simpler control: same installed Reader with simple serial `b''.join(reader._blob(i) for i in ids)` (O226 showed it generally dominates eager).
- Inherited product control: original eager `Reader.read(name)` including its thread-pool shutdown.
- Candidate: per-operation unique-owner scatter with bounded decoder-live retention; decode one owner at a time; no persistent decoded cache, no cross-request cache.
- Excluded: unconditional global owner cache (unbounded RSS), r24 format/new index, renamed scheduling thresholds, and editing #569's Reader.

### Frozen workload and evidence rung
Use O226's **actual independent Builder-free authenticated two-index r24** fixture writer, original Reader install and O226 frozen `Reader` blob. Four reused families and two once-only controls: `zstd_entropy_twice`, `deflate_entropy_twice`, `zstd_pattern_twice`, `deflate_pattern_twice`, `zstd_entropy_once`, `deflate_entropy_once`; both `S_CHUNKS` and `S_CDC`. Twelve **distinct physical** 3 MiB owners, twice family 24 non-adjacent logical references in order [0..11,0..11], once family 12 refs. Exact same archive bytes within each triple comparison. Three fresh child processes per arm, randomized/counterbalanced arm order, 6x2x3x3=108 observations. Charge `Reader.__init__`, per-read construction/scatter/output conversion, Reader.close, CPU and wall, and own-process Linux VmHWM (not inherited `ru_maxrss`), plus archive and logical bytes, decoder calls and transitory index/posting accounting. Separate process-launch wall.

Independent output SHA256 and byte count **every sample**. Held-out nonuniform tiny RAW/Zstd/Deflate mixed-owner + non-monotone refs and 1,000 randomized range-read controls; deliberately corrupted referenced physical CRC must reject under each arm, not merely verify later. Validate true r24 with `preflight_archive(verify_blob_headers=True)`, ordinary `Reader.verify()`, installed-source path and exact original blob SHA. Use stock Ubuntu/Python3.12 only, no full release credit.

### Decision gates (precommitted)
1. `SCATTER_SEED` if candidate is **>=1.20x faster in full-session wall AND CPU** than **both** eager and serial (compare candidate with faster of those) on at least **two** of eight reused cells; original and independent byte/SHA/corruption controls pass. Report all twelve cells and RSS deltas.
2. `NO_COST_BOUND_PROMOTION` if any once-only cell is >1.10x slower in session wall or candidate VmHWM exceeds the lower of eager/serial by >8 MiB in **any** cell; a seed can coexist with this debt but is **not promotable**, and no threshold changes.
3. `NO_MATERIAL_HEADROOM` when criterion (1) fails, even if candidate beats only eager; retire this scatter family absent genuinely new information/model.
4. `INVALID_EVIDENCE` for different input, byte mismatch, accepted referenced CRC corruption, missing/nonfinite sample, source drift, false fresh-process accounting or auditor failure. Invalid scientific evidence never counts as winning or losing.
Interpret a winner only as O0/O1 architectural research, never a product patch or v0.31 promotion. Profiling/complexity/memory adversarial counterexamples must be preserved.

### Disproof and cost accounting
If decoding each owner once cannot beat a simple serial stream after charging offset postings, allocation and output copy, the mechanism does not justify global reader complexity. RSS/posting O(refs) and loss of streaming locality are major potential reasons to reject even a wall-time win. Held-out adversarial metadata and 3-host ABI/native/ZIP64/security/recovery parity remain necessary before any integration. Contradictory results remain intact; don't change the target.

### Counterfactual / later handoff
If owner-scatter wins, test an output-ownership API that can elide one complete copy without forcing extra decoded-unit lifetime; otherwise retire and ask #569 to productize only the simpler serial evidence if full Reader parity supports it. If source verification prevents hosted execution, preserve the blocker identity and pursue an independent safe lane. There is no automatic version, merge, or release from this experiment.
