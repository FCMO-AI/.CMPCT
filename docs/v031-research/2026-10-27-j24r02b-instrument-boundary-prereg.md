# J24R02b — instrument admission repair, prospective before mutation

Date: 2026-10-27
Parent experimental failure: J24R02 run 40480971958 / job 122110887272, HEAD 01cb6378a11f773f3fbc642d33525020a99c1e46
J24R01 original instrument: frozen in PR #584 at 70336307312b5b277f0885c0057d2cddab0aefc1
Classification: **EVIDENCE INFRASTRUCTURE FAILURE**, not a Reader red; leave all failed receipts available.

## Root cause established before intervention

On the independently framed one-extent r24 profile, `len(truth)==4`. The original test probes `read_range(pos=8,n=0)` because it puts a hardcoded position 8 in a generic seven-position sample. The ordinary *baseline* Reader correctly raises `ValueError('range outside member')`. The original `subprocess.run(...,check=True,stderr=PIPE)` erases useful child stderr from the parent log and aborts before any measurable ABBA. The same failure would occur regardless of bisect optimization. Source-exact three-host safety tests already PASS.

## Narrow repair hypothesis, control, disproof

Change only the **untimed, post-measurement** secondary correctness oracle to clamp literal probe 8 to the file's logical boundary; count *actually executed* correctness checks instead of claiming all nominal checks happened. Preserve all existing warm and timed 256 range requests, exact fixture construction, three ABBA rounds, metric boundaries, source packages, comparator, full safety checks and invalid-range Reader contract. Keep zero-length boundary probes; skip out-of-range positive-length ones rather than suppressing Reader failures. No missing/incorrect in-bounds bytes allowed.

New independent referee must use 531 expected checks for E=1 and 533 for E>1, confirm exact source hashes, 48 sample observations and ABBA order. No unconditional PASS, no dropped samples, no weaker validation. Failure to obtain full receipts after this change invalidates the experiment, not the product. If a new Reader discrepancy is exposed, disclose it unmodified.

This child lane intentionally alters the *research-only instrument* while the parent implementation/owner remains unchanged. The child amendment must be audited as a deviation from the first frozen J24R02 setup, not silently substituted into historical evidence. Owner informed at PR #584 comment 6438319067. Three-host semantic tests and official product/release requirements remain independent.
