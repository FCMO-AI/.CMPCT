# J24G56b — footer flag admission parity, second prospective independent discriminator

Date: 2026-10-29 UTC. Separate question observed **after** J24G56's outcome; do not rewrite original prereg/result.
Parent remains unmerged #789 exact 83e9f2eb277f023186b646f667cd443b7108f268; test source child head before this prereg 447142f4b5de045fa34bb408e1a19ea3ea5bfa0e. Own research-only #791; existing #789 product implementation is not modified.

## New question and source-only baseline
An independently visible structural inconsistency exists between `reader._decode_generation_payload` and `validation._decode_footer`: both unpack revision-24 footer `<8sBBBBQQQ32s>`, but Reader checks only magic/size and SHA of decoded payload; validator **also** requires `flags==0` and `reserved==0`. These footer header bytes are not included in the payload SHA field, so a one-byte nonzero-flags/reserved mutation of a known valid committed update might remain accepted by Reader but be ignored by preflight's recovery search.

## Prediction and cheap physical control
Use actual Builder archive and append ordinary valid `del a.bin` via the existing Writer helper; mutate **one byte** in the committed footer's flags field, separately the reserved field, leaving everything else including the delta SHA physically unchanged. Independent external wire parser should verify identical decoded payload and SHA but a known *invalid* footer header. Reader expected to select the modified latest generation and report one surviving file. Preflight expected to recover the prior footer and report both original files.

Controls: unchanged valid `del` accepted by both; altered footer digest recovered by both; unknown-op J24G56 original observation remains frozen. If Reader rejects/recover latest rather than selecting it, or if preflight accepts nonzero header fields, the predicted divergence is disproved. Preserve exact original samples and SHA.

## BONK, semantics and limits
This is a different admission boundary from unsupported logical opcodes: a **physically malformed footer header**, not an unknown versioned operation. It is a cheap one-byte O0 falsifier with high possible payoff for recovery trust. Do not say SHA-256 makes an invalid footer authoritative. If positive, the legitimate Reader owner should align the footer decoder's permitted kind/codec/flags/reserved and predecessor geometry with structural preflight, while preserving backward compatible r24 and recovery for incomplete/corrupt tails. Not a published-wheel claim, not a digital signature, not a physical security attack, and no product credit until owner repair.
