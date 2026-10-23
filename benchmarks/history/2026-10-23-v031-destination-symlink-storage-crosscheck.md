# v0.31 destination symlink — independently preregistered storage-kind crosscheck (2026-10-23)

This is an **append-only second experiment**, proposed after the first court's source-pinned result. Its purpose is not to relabel previous evidence, but to isolate whether an atomic file staging primitive solves the observed boundary in isolation.

## Predictions
1. Authentic `S_CDC` (ordinary 1 MiB+ source with no symlinks) whose **ancestor directory** is a preexisting symlink to an outside sibling will still publish the correct verified bytes **outside** the requested destination, because `mkstemp(dir=parent)` and `os.replace(tmp,full)` use path resolution through the parent symlink. `safe_symlinks=True` cannot reject a link absent from the archive index.
2. Authentic `S_CDC` whose **leaf** is a preexisting symlink to an outside file will **not** modify the outside file; atomic `os.replace` should replace the link inode itself.
3. Authentic archive **symlink entry** extraction, for a safe relative target, should unlink a preexisting destination symlink leaf and recreate the intended safe symlink, without modifying the outside victim.

These three outcomes distinguish parent traversal, direct leaf truncation and atomic publication, rather than assuming any symlink is always dangerous.

## Disproof / limits
Failure of source archive verification, unexpected storage kinds, a CDC ancestor not changing its outside victim, CDC leaf changing victim, or symlink-row replacement changing victim invalidates the prospective classification. Isolated deterministic local temporary trees only: not a concurrent adversarial race, format change, product fix, or proof of portable filesystem semantics. Preserve JSON raw outcomes from hosted exact-source run.

## Consequence if confirmed
The safety boundary cannot be repaired solely by changing `S_BLOB` leaf `O_TRUNC` to atomic replacement, since `S_CDC` already uses atomic replacement and remains susceptible to a preexisting parent pivot. A shared directory-capability resolution layer is the more general mechanism to investigate, with Windows/macOS/Android and r24 compatibility explicitly still open.
