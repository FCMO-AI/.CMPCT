# v0.30 r25 membership complete-artifact integration negative — 2026-09-12

Status: **construction falsified by current physical S_PACK geometry; no product/release credit**.

Source head: `fb3227f7c4f8c21d53358e612df1abf744ecbc06`  
Hosted run: `34732590827`  
Hosted job: `103658030176`

## What failed

The complete-artifact mission required the candidate to start from the current locality-bounded canonical r24 physical artifact, preserve its entire physical data span byte-identical, and compare against C25CC01 before any compact-membership format discussion.

The run never reached the membership candidate. C25CC01 correctly rejected the source physical artifact during its pre-existing locality audit:

```text
ProfileNotEligible: compact control source S_PACK exceeds release locality:
path='src/module_0000.ts' decoded=215448 logical=1253 amp=171.945730
```

This is **not** a missing dependency, timeout, source leak or comparator loss. It is a real incompatibility between the current r24 micro-pack geometry and the r25 <=8x selective-read contract.

## Diagnosis

The current release-r24 policy derives `builder.micro_pack_target` as:

```text
min(2 MiB, 8 * largest_regular_member)
```

That limits a pack relative to the largest regular source member, while an S_PACK selective read decodes the complete owning pack for *each* packed member. A pack containing a 1,253-byte member therefore needs a decoded size <=10,024 B to satisfy 8x for that member; the observed 215,448-byte pack cannot qualify.

The canonical Builder already sorts micro-pack candidates by size before grouping. Therefore a locality-safe group has a direct mechanism-level bound that does not require a threshold sweep:

```text
sum(group raw bytes) <= 8 * min(member raw bytes in group)
```

For size-sorted members, `min(member)` is the first member in the group. An independent member is always the 1x fallback.

## Verdict

The exact hypothesis **“reuse the current r24 physical S_PACK layout unchanged and only compact membership metadata” is retired**.

The positive `membership-v1` wire result remains valid as a metadata mechanism. This negative does not weaken or reinterpret it; it says the current physical grouping cannot be carried into an r25 product artifact under the frozen locality law.

## Next admissible Builder

Construct a locality-derived micro-pack policy whose group ceiling is `8 * smallest_member`, compare it with independent-file fallback and the current r24/C25CC01 economics, then apply compact membership only to groups that are both locality-valid and complete-artifact byte-positive. The experiment must preserve mature r24 semantics, exact strong verification, authenticated two-copy control, recovery and direct member reads.

Do **not** raise the 8x budget, hide the rejected tiny members, or call this CI red a benchmark loss for the compact-membership mechanism itself.
