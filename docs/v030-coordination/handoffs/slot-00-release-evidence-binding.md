# Slot-00 release-evidence binding update

Final T03 architecture evidence/receipt must use the strict release front door now present on slot-00:

```bash
python -m experiments.entropygraph_v030_release_lock_strict --print-fingerprint
```

After the canonical r25/r24 product semantics are integrated and the final release/public source is frozen, the durable **final** JSON architecture/conformance artifact intended to source the `canonical-architecture` receipt must embed that exact fingerprint in a stable field, preferably top-level:

```json
{"candidate_fingerprint":"<64 hex>", ...}
```

The strict receipt template contains `candidate_fingerprint_source` and the lock verifies that the hashed evidence JSON itself records the current fingerprint. An old green artifact plus a newly typed receipt fingerprint is rejected.

Do not mint the final architecture receipt while the r24 product floor, user/internal tree identity, signed timestamp, cross-platform safe-symlink, or global-profile-mutation review items remain open. Intermediate architecture notes/tests remain useful without retroactive fingerprinting.
