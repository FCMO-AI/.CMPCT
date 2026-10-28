# J24B06 — measured published-Reader extraction-budget undercount

**2026-10-28 UTC · SCIENTIFIC RESULT: CONFIRMED / TWO UBUNTU HOSTS.**
No product release, merge, version, format, benchmark promotion, Reader source edit or generalized hostile-input guarantee. Original frozen prediction committed at `391885a50b0b37103f2acf294a72939bb8d637a5` **before code**.

## Baseline source, real installed execution and material result

- Exact source: published v0.30.0/r24 `main@80c358f8824ec1b20d349c92ed94c898090969b0` (Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`, raw SHA-256 `83be3f08f7fafb1fd638fda6140bbe1af6676c261be10acc9ea8f8b633beefff`).
- Frozen research code HEAD: `4831d0f7a3d15d2a0b7e9d4d863076527f3214ed`, [GitHub Actions run 40732802978](https://github.com/FCMO-AI/.CMPCT/actions/runs/40732802978) **SUCCESS two of two** Ubuntu 22.04 and Ubuntu 24.04. Installed Reader source matched exact Git blob and actual checkout in both. Both used Python3.11.17.
- Real first-party Builder produced a valid r24 8192-byte regular member and 11-byte relative symlink member; ordinary `CMPCT.verify()==2`.
- The experiment changed **only symlink logical size row[4] to −8192**, recompressed MessagePack with original package-owned Zstd, recomputed **both primary and tail unkeyed SHA-256 index checksums**, and preserved the complete physical record span byte-for-byte. The index SHA-256 is not a digital signature or keyed MAC; no cryptographic forgery claim.
- After mutation, ordinary published `CMPCT.verify()==2` still succeeded. **`extractall(max_bytes=4096)` wrote an entire 8192-byte regular file**, SHA-256 `99fdb93482cfa4faaf7e77857f46d4eb1ecabc7ee17a696e0ed7b0ab3cf15ee5`, and a relative in-root symlink without error.
- Honest Builder original with symlink declared size 11: correctly refused at declared total **8203 B > cap 4096 B**, no regular file published. Zero-size symlink metadata: correctly refused at **8192 B > 4096 B**. Negative budget `-1`: correctly refused even under the cancelled zero total.

## Independent wire referee and original artifacts

| Host | Job ID | Artifact ID | SHA-256 of GitHub artifact ZIP | Result |
|---|---:|---:|---|---|
| Ubuntu 24.04 | 122973320042 | [12835089011](https://github.com/FCMO-AI/.CMPCT/actions/runs/40732802978/artifacts/12835089011) | `8b32c207fc04c1b19b63c2c9a11658c94c5382ff0f2504580e8e8e545747ac40` | CONFIRMED |
| Ubuntu 22.04 | 122973320504 | [12835437802](https://github.com/FCMO-AI/.CMPCT/actions/runs/40732802978/artifacts/12835437802) | `51a4c3cac4823942e7172fcef31663ce4c3aa183c189a015d971bd4c25bd0e09` | CONFIRMED |

Second referee did **not** import either the candidate experiment or CMPCT. Using Python standard library/msgpack, standalone `zstd` and struct, it authenticated both index copies, all source/physical identities and exact index semantic diffs. Physical span SHA-256 was **`fe1e24b5331204645e840b557c9a8c8928edf0de49ff602fe16e9795c2efd5ca`** for original, negative and zero variants. The second implementation rejected five independent forged receipt/physical cases per host, **10/10** total, with no observed legitimate-byte discrepancy.

Unkeyed SHA consistency is not trusted-producer authentication. This is a *malformed, self-consistent, hostile* archive, not normal Builder output. Source trust cannot substitute for semantic geometry checks.

## Causal mechanism and counterfactual

Published Reader `src/cmpct/reader.py` computes `sum(x[4] for x in self.files if x[1]!=K_DIR)` then checks `total>max_bytes`, with no `size>=0` validation. The Reader's symlink `read` ignores the signed logical size and returns actual physical blob; `verify` checks actual bytes/hash but not the declared symlink length. Therefore **−8192 + 8192 = 0** passes a cap of **4096** although 8192 real output bytes are written.

The cheapest prospective discriminator is exactly the negative-size signed metadata case; merely measuring unsigned archive correctness would miss it. Static source analysis predicted the counterexample, but **only the actual hosted signed-wire and output tests earned the observed exploit claim**. This is a transferable methodological lesson for any signed/checksummed metadata semantics; it does not justify altering Discovery policy from one activation.

## Scope, severity, limitations and ownership

This confirms resource-limit correctness for the exact published Reader on two Linux distributions. It does **not** prove a general filesystem escape, remote execution, crash-only DoS, absence of other related bugs, universal portability or a bound on the size of possible malformed archives. Valid original passes `verify`; mutant passes `verify` but is semantically invalid under the intended length contract. Directory creation before budget preflight on the original Reader is another limited side effect; the candidate moves the guard before mkdir.

Focused issue [#689](https://github.com/FCMO-AI/.CMPCT/issues/689) records the result, and independent isolated **draft** product candidate [#690](https://github.com/FCMO-AI/.CMPCT/pull/690) adds per-row nonnegative exact-type admission to `extractall` without changing the format, Builder, Decoder/Reader open, or native code. The candidate is **not merged or released**. Its first CI run was blocked by unrelated historical `tests/conftest.py` imports; a workflow-only fix isolates the targeted suite, while unchanged main suite still runs. It has measured component CPU overhead and all product gates remain open.

## Discovery & coordination

Compared dominant production Reader #662/#676 owner, sparse publication #255/#270/#573, MessagePack #684/#686 and A16 #683/#685. No duplicate exact max_bytes issue was found before registration. Research commits only new scripts, docs and isolated CI; shared `docs/discovery/STATE.json` remains owned by #574 and was not mutated. **Primary question answered: YES**, decision-changing correctness regression confirmed. No concurrency collision, no policy modification.

**Highest-leverage next:** validate #690 exact-head all hosts and additional signed generation/metadata cases; close observed accounting-loop overhead before any promotion, integrate semantic owner-length admission with neighboring product owners; full existing general tests and release parity must pass. This dossier is scientific evidence, not permission to merge or bump version.
