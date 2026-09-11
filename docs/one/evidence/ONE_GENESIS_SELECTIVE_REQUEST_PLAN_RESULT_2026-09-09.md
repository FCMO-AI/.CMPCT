# CMPCT1 / ONE Genesis selective-request plan — result

Date: 2026-09-09 America/Mexico_City  
Experimental state: **ONE-G0.2**  
Decision: **READY_SELECTIVE_REQUEST_PLAN**  
Claim boundary: **source-derived query geometry only; no contender archive encoding, layout inspection or scoring occurred.**

## Exact hosted authority

- branch: `research/cmpct1`
- exact evidence source: `1820521b402dc94470835daa81a7adcb028d8738`
- workflow: `CMPCT1 ONE Genesis selective request plan`
- run: `34420547435`
- job: `102694780002`
- artifact: `10130802805`
- artifact name: `one-genesis-selective-request-plan-1820521b402dc94470835daa81a7adcb028d8738`
- artifact digest: `sha256:ba4257ca1297db34619f46653bacacebad04dc8c9bf682fc4eafd5946125fcdf`

## Frozen result

The hosted lane regenerated the accepted repair-v6 15-workload substrate twice and independently rebuilt the logical selective-request plan twice. Both builds were byte-identical at the request-record level and emitted the same canonical plan digest.

- workloads: **15**
- target files: **27**
- frozen logical requests: **133**
- all workload identities exact: **true**
- request-plan SHA-256: `9a74f57befcf0510d3229c31ba1086c259dbfe4307abe7a1559db3acd20453c8`
- errors: `[]`
- scoring executed: **false**
- CMPCT1 encoding executed: **false**
- comparator encoding executed: **false**
- contender archive layout inspected: **false**

Every request is bound to the source workload tree, target path, full logical-file length and SHA-256, logical `(offset,length)`, and SHA-256 of the exact expected returned bytes before any contender archive exists.

## Bias-control interpretation

This closes a subtle degree of freedom in the September 11 gate. Selective requests cannot be hand-selected after seeing where CMPCT1, v0.29 or v0.30 places chunks, reconstruction cones or authentication boundaries.

For each workload the plan chooses, at most, the largest non-empty regular file and the smallest distinct regular file of at least 4096 bytes using deterministic source-tree ordering. Prefix, middle, logical-4096-crossing and suffix ranges are derived only from logical file geometry. Duplicate `(offset,length)` queries caused by small files are removed before the plan is frozen.

## Hostile review / strongest caveat

The plan samples at most two files per workload. It is therefore a deterministic locality probe, not exhaustive archive-access coverage. Filesystem semantics, recovery behavior, hostile corruption and integrity/resource behavior still require their own evidence under the Genesis measurement contract.

The logical 4096 crossing can coincidentally align with a contender's physical boundary. That does not make the plan adaptive: the offset was fixed before any archive layout was inspected, and every contender receives the identical logical query.

## Next use

On or after the first qualifying September 11 activation, the exact plan digest above should be consumed by all three contenders. Any change to source-tree identity or request-plan digest must fail closed rather than silently regenerate a new scored query set.
