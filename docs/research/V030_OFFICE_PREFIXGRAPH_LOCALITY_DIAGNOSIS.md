# v0.30 Office PrefixGraph locality diagnosis

Status: **research/oracle evidence; zero release credit**.

Exact source: `9bbfa24f2f08f91e0c7aeb54920c6b198100bd85`, Actions run `35306582238`, accepted repair-v6 Office tree `aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57` (20 files / 16,063,798 logical bytes).

The canonical-r25-only oracle selected G04 at 11,633,013 B because the much smaller PrefixGraph candidate failed the existing <=8x locality contract.

## PrefixGraph candidate

- bytes: **7,605,401 B**;
- Zstd-19 control: **8,312,879 B** -> PrefixGraph is **707,478 B smaller**;
- 7z control: **7,455,748 B** -> PrefixGraph is **149,653 B larger**;
- worst decoded-context amplification: **10.970673x** -> **FAIL** against <=8x;
- PrefixGraph records: 12;
- locality preflight used authenticated metadata only and materialized 0 payload bytes.

The failing prefix-record amplifications were:

- record 6: 10.970673x;
- record 7: 9.557916x;
- record 8: 8.596012x;
- record 10: 10.878271x;
- record 11: 9.663485x;
- record 12: 8.571310x.

Records 9 and 13 are already just inside the contract at 7.913565x and 7.907915x. Later prefix records 17-20 are comfortably bounded at 3.48-3.77x. Direct records are 1.0x.

## Causal conclusion

The earlier ~7.6 MB PrefixGraph observation is real on the accepted substrate, but it is **not a hidden publishable winner**. Its disqualifier is now isolated: six prefix records exceed the locality ceiling, with the worst only ~1.37x beyond the allowed 8x bound. The outer selector is correct to reject it and publish G04; this is not a selector bug.

This sharply narrows the Office representation problem. Before porting the older v0.25 stream-graph family, test whether PrefixGraph can be resegmented/rebased so those six dependency cones fall <=8x while keeping the fully charged archive below Zstd-19 and preserving exact semantics. The current 707,478 B advantage over Zstd-19 is the byte budget available for locality rehabilitation. Any fix must be generic, structure-derived, and charged for all added bases/metadata; no Office identity or workload labels may enter policy.

If a bounded PrefixGraph variant cannot fit inside that 707,478 B budget, preserve the negative and return to the v0.25 compact-floor legality/materialization lane.
