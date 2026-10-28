# J24G26 — ZIP export symlink output semantics (preregistration)

Date: 2026-10-28 UTC  
Status: PREREGISTERED / RESEARCH ONLY / NO PRODUCT SOURCE MUTATION

## Authority and ownership
Canonical released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, CMPCT v0.30.0, revision 24. Experimental staged-output source: PR #492 `ca01d885fedc8ffc343b9c3c624eddd134158452`. PR #492 owns ZIP export publication, PRs #284/#707 own physical Deflate verification, #260 owns ZIP64. This new court touches none of those implementations and does not change format, version, benchmarks, thresholds, or `docs/discovery/STATE.json` (stale, reconciliation owned by #574). No `docs/discovery/CONCURRENCY_PROTOCOL.md` exists on main.

## Question
Does staging a ZIP to a temporary sibling and then `os.replace(stage, out)` introduce a **change to existing output-symlink semantics** relative to the published `open(out,'wb')` writer, even when the output symlink points to a legitimate unrelated regular file or is dangling? Is that change an intended security boundary or a compatibility debt that must be made explicit before promotion?

This is a different abstraction from the already-complete J24G25 Deflate trailing-byte acceptance court: pathname topology and file identity, not compressed stream framing. The candidate may rationally choose one contract; the comparison must **not silently label either behavior secure or insecure** without an explicit product policy.

## Frozen predictions and controls
1. Same frozen independent r24 source bytes, same output symlink names, same output referent names, same host, installed source `main` vs candidate #492 in separate interpreter processes.
2. With an existing symlink to an unrelated valid ZIP, published `main` follows the symlink and rewrites the referent, keeping the symlink. Candidate #492 replaces the symlink itself with the newly published ZIP, preserving the old referent. Both exported archives decode to the fixed known member bytes.
3. With a dangling symlink to an absent referent, published `main` creates the referent while preserving the symlink; candidate #492 replaces the symlink and leaves the absent referent absent.
4. Candidate #492 must reject output symlinks to the *source CMPCT inode* before publication, preserving the source bytes and link. Never run published main on this dangerous control.
5. An ordinary non-symlink output must export successfully on both engines and yield the same member bytes. Repeat on POSIX Ubuntu and macOS; Windows symlink privileges are excluded, not silently assumed.
6. Use independent `zipfile` to validate output bytes, record old/new inode and symlink state, source/target hashes, and all original observations. No benchmark or performance credit follows.

## Kill/narrow
If the two engine versions behave identically on verified same-input outputs, retire the hypothesis. If either archive cannot open or the fixed member does not round-trip, classify an instrument failure and do not claim a semantic mismatch. A observed difference is **compatibility evidence, not an automatic defect verdict**: forward to #492 so the owner can choose an explicit symlink output policy, possibly rejecting rather than following/replacing links. This test does not prove concurrency/TOCTOU defenses, namespace sandboxing, power-loss durability, or general ZIP release safety.

## Alternatives and expected value
The simplest old writer control uses `open('wb')`; the staged writer uses `os.replace`. A direct filesystem-only simulation would predict the behavior cheaply, but exact CMPCT-endpoint execution is necessary to rule out the code's existing admission checks. Avoid implementing a third exporter or patching the owner. This narrow test can prevent an unannounced behavioral change and inform a single release-policy decision with negligible CI compute.
