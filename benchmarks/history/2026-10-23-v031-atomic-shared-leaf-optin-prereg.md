# v0.31 — conditional shared-destination-leaf atomic materialization: prospective O1

Date: 2026-10-23
Status: PREDICTION FROZEN BEFORE IMPLEMENTATION / MEASUREMENT
Source owner: [PR #294](https://github.com/FCMO-AI/.CMPCT/pull/294) at `700fa74df7d9101b3d00322ab5b3606ee64faf88`, stacked on symlink-preflight [PR #269](https://github.com/FCMO-AI/.CMPCT/pull/269) at `0273c628872dce672936aa0ddd555ed10a900bf7`. Independent branch, no write to either owner. Parent static negative and nine focused tests remain mandatory; no release change.

## Decision question
Can CMPCT **optionally** replace a pre-existing regular destination leaf with multiple hardlink names by staging a *new inode* on the same filesystem and publishing via `os.replace`, without touching any other alias, while keeping default strict refusal and ordinary/atomic no-alias behavior unchanged? This is **static-only**: a preread `lstat` and pathname-based `os.replace` cannot ensure race safety or confinement under concurrent directory moves.

## Baseline
Parent safe extraction fails closed on `st_nlink > 1` for every direct-truncate leaf; a benign in-root sibling therefore cannot be extracted. Parent CDC/CHUNKS publish a fresh inode already. Parent full Tests on exact `700fa74...` = **799 passed, four inherited release-custody failures** ([run 40032511249](https://github.com/FCMO-AI/.CMPCT/actions/runs/40032511249)); historical gate comparison also blocked on the same inherited Tests before benchmark evidence ([run 40032511225](https://github.com/FCMO-AI/.CMPCT/actions/runs/40032511225)). Do not modify/waive those tests or classify the performance gate as passing.

## Mechanism and prediction
Add one explicit opt-in to extraction, defaulting to parent fail-closed. When chosen and a direct-truncate regular leaf is preobserved with `st_nlink > 1`, stage a new inode using a constant-length basename in the same parent filesystem; write the chosen representation through existing Reader pathways, publish only after successful reconstruction and close, then apply metadata to the new path. Preserve sparse extents by writing only their bytes plus `ftruncate`, not a full zero stream. Treat the extra disk/inode/I/O and divergence of an old shared inode as real compatibility costs, not invisible optimizations.

Expected outcomes:
1. authentic `S_BLOB`, `S_SPARSE`, `S_PACK` and `S_VZIP` aliases whose other name is *outside* destination: opt-in completes and outside inode/size/SHA remain unchanged; output SHA matches `CMPCT.read()`, new destination inode differs;
2. benign aliases *inside* destination: opt-in completes, untouched sibling retains old bytes/inode (an observable, deliberate alias-breaking semantic); archive-listed hardlinks may reconstruct their own identities separately;
3. default safe mode still rejects before any prior entry is written, preserving parent tests unmodified; explicit `safe_symlinks=False` still retains legacy behavior;
4. length-255 POSIX filename works with short staging prefix; staging cleanup happens on read/decode errors, leaving pre-existing aliases unchanged; metadata-off mode should not silently become mode `0600`;
5. workflow runs real Builder + Reader with native installation, an independent outside-sentinel check, and a bounded same-host overhead comparison with the no-alias control. The overhead is research economics, not complete product performance or equal inode semantics.

## Strong simpler controls and alternatives
- Parent conservative refusal: strongest safety-minimal control; remains default.
- Existing CDC/CHUNKS atomic path: no duplicate implementation if already safe.
- Always-atomic every file: broad changes to inode ownership, metadata and temp I/O, rejected for this narrow experiment.
- Merely using `O_NOFOLLOW`, or a postwrite copy: does not prevent shared-inode changes and cannot pass the outside sentinel.
- Preflight-only with no fresh inode: preserves existing parent false positives.
- FD-rooted directory traversal and no-follow **for all publication and metadata operations**: stronger race-safe architectural lane reserved for separate work; this opt-in explicitly does not claim it.

## Kill/narrow conditions
Any altered outsider SHA, inode, size or mode; failure to preserve correct logical bytes/sparse holes; default refusal weakened; temp file leaked on decode failure; a 255-byte valid basename broken; any unintended change to parent tests; unexpected memory proportional to logical sparse holes; or serious resource/performance debt without a bounded admission policy blocks productization. Any concurrent path pivot refutes race-safe claims even if every static test passes.

## Evidence classification
The initial commit is **prospective hypothesis only**. Later test/CI evidence must name exact source SHA, full artifact receipt and directly observed outcomes. Preserve negatives and complete inherited CI failures. No format r24, version, comparator, frozen benchmark or threshold change. No policy self-modification is earned by one experiment.