# O162 — Actual r24 POSIX tree roundtrip, observed 2026-10-26

Status: **hosted narrow positive; cross-host semantic boundary identified**. Research/evidence only. No product/format change or release credit.

## Hypothesis, code and provenance

Predicted before the experiment in commit `6b6b74b670e5862a42dd56e808c06a2817a5f563`: a stable source containing hardlinks, file/directory symlinks, nested and empty directories, Unicode filenames, nondefault modes and binary payloads should roundtrip through installed Builder/Reader while preserving the independent O155 static POSIX tree witness. Destroying an actual restored hardlink without changing bytes should elude historical `tree_digest` but not O155.

Frozen source blobs: Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, original comparator `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`, O155 `0bef46e8d1944ff327063c66edc9bbc29fa58481`.

## Results

[Run 40282300911](https://github.com/FCMO-AI/.CMPCT/actions/runs/40282300911), original result-bearing HEAD `e82db7664c0940c9611985ac5aa5aa2167bc7166`: Ubuntu **SUCCESS**, macOS **SUCCESS**, independent per-job log examination. Both reconstructed manifests equaled their corresponding source manifest, original hardlink remained the same physical inode, all 3 symlink targets/modes and payload were preserved. After replacing the restored hardlink with a same-byte/mode copy, the legacy digest stayed equal while O155 digest changed on both hosts. Complete archive: Ubuntu **1,937 B**, macOS **1,965 B**; archives were generated on separate host source trees and are not fair same-input size comparators. Artifacts: [Ubuntu 12633230822](https://github.com/FCMO-AI/.CMPCT/actions/runs/40282300911/artifacts/12633230822); [macOS 12632352332](https://github.com/FCMO-AI/.CMPCT/actions/runs/40282300911/artifacts/12632352332).

Follow-up diagnostic-only instrument HEAD `5d8dfc4a08434851cfcbf71a544d7efc042c4cfb`, [run 40282568552](https://github.com/FCMO-AI/.CMPCT/actions/runs/40282568552): **2/2 SUCCESS** again. It records raw 10-entry source/extracted manifests with no changed assertions. Artifacts: [Ubuntu 12633105764](https://github.com/FCMO-AI/.CMPCT/actions/runs/40282568552/artifacts/12633105764); [macOS 12632358026](https://github.com/FCMO-AI/.CMPCT/actions/runs/40282568552/artifacts/12632358026).

Independent manifest comparison isolated **exactly three host differences**, all at symlink permissions: `ln-dir`, `ln-file`, `nested/ln-nested` have Linux physical `0777` and macOS physical `0755`. All other relative path/type/content/target/mode records, root mode and hardlink group match. Consequently different cross-host source strict digests are expected and are **not** CMPCT reconstruction failures. The O155 witness is physically strict; a portable semantic projection must be separately defined rather than quietly normalizing its historical evidence.

## Scope / decision

Evidence: genuine installed same-host r24 source→archive→extract topology preservation for the tested supported stable fixture; historical comparator blind to actual restored hardlink topology loss. Not evidence of portable cross-host archive reconstruction, ACL/xattr/uid/gid, timestamp, raw filename, sparse extent, special entry (already O48-owned), concurrency safety, crash recovery, performance or overall filesystem equivalence. Synthetic small-tree wall timings are noncomparative. No normative discovery-policy change.

Next cheapest decisive experiment: exchange the **same** archived bytes between Linux/macOS, compare receiver physical tree against the source witness, and explicitly distinguish symlink-mode host constraints from any CMPCT bug. Preserve current O155 witness unchanged.
