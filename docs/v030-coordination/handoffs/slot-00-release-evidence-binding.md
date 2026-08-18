# Slot-00 release-evidence binding update

Final T02 evidence/receipts must use the strict release front door now present on slot-00:

```bash
python -m experiments.entropygraph_v030_release_lock_strict --print-fingerprint
```

After T01/T03 implementation is integrated and the final release/public source is frozen, every durable **final** JSON artifact intended to source a release receipt must embed that exact fingerprint in a stable field, preferably top-level:

```json
{"candidate_fingerprint":"<64 hex>", ...}
```

The strict receipt template contains `candidate_fingerprint_source` and the lock verifies that the hashed evidence JSON itself records the current fingerprint. An old green artifact plus a newly typed receipt fingerprint is rejected.

Intermediate causal/diagnostic artifacts may retain their historical provenance. Only final authority artifacts need the release-fingerprint binding. Do not mint final receipts from the current specialist branch before the canonical product/native integration source is frozen; wire the harnesses so the final integrated rerun can populate the field deterministically.
