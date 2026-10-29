# J24I33a preregistration addendum — complete Builder serialization invalidates initial prediction

**2026-10-29 UTC; committed before any J24I33 hosted execution.** Do not rewrite the original preregistration `2026-10-29-j24i33-native-directory-sentinel-prereg.md`.

## Prospective source-audit counterevidence

An additional read of unchanged Builder source blob `663ef0922992b1fbb8f19e6eea88d55c10a56044` exposed an overlooked second transformation. `scan()` indeed writes intermediate `[path,K_DIR,...,b'',None]` at line 91, **but** `build()` maps every row to the final index at lines 284–302 using `keep_hash=h if (storage and storage[0] in (S_CHUNKS,S_CDC,S_SPARSE)) else None`, then emits `files.append([...,keep_hash,storage])`. Directory storage is `None`; its temporary `b''` is replaced by `None` **before physical serialization**.

Therefore the original J24I33 **product-severity hypothesis** (ordinary current-Builder directory trees necessarily fail native `Archive::open`) is **falsified at the deterministic source-transform level** before any hosted court, not validated. It was a source-interpretation mistake, not an OS-specific failure. This does not erase J24I30's actual native `b''` difference on independently re-signed files.

## Narrowed question and stronger controls (before executing)

1. **Authentic Builder control:** nested real directories and nested file emit `row[5] is None`; native and Python both **accept** and verify the regular file. Failure here is a new independent defect, not proof of original `b''` claim.
2. **Derived optional-absence compatibility:** reconstruct the authentic directory archive by replacing only the final `None` in two directory rows with `b''` and correctly re-signing both index copies. Python preflight/verify **accept**, native source parser **rejects** with `invalid logical SHA-256 length`. This is an *artificial* but Python-valid r24 representation; it is not claimed as current Builder output or historical shipped wire.
3. **Stronger simpler control:** flat real Builder file with identical content is accepted by both readers.
4. **Hostile control:** one-byte `b'X'` directory SHA must be rejected on both sides, preserving invalid-length boundaries.

A native acceptance of the derived `b''` case falsifies the parser-disparity prediction. Unexpected rejection of authentic or flat controls establishes a separate defect. This lower rung determines whether native `b''` work should be a **historical compatibility question** rather than an urgent current-Builder regression. No native product edit is authorized from this science-only experiment. #754 historical negatives remain unchanged.

## Discovery counterfactual

Following the complete encoder dataflow to the final MessagePack write would have caught the false positive earlier than an installed court. This is an evidence-backed *local* process lesson: reason from **serialized bytes**, not intermediate row objects, before claiming an interoperability blocker. No policy or evaluator change.
