# Agent slot claims

`slot-00.json` is occupied by the authoritative integrator.

The three resumed agents atomically claim slots 01–03 by attempting to create the lowest missing `slot-NN.json` on `agent/v030-authoritative-integration`. A Git create conflict means another agent won that slot; fetch and try the next missing slot.

Required claim shape:

```json
{
  "schema": "cmpct-v030-agent-claim-v1",
  "slot": "slot-01",
  "role": "native-portability",
  "status": "ACTIVE",
  "branch": "agent/v030-coop-native-portability",
  "claim_owner": "agent-chosen-stable-name",
  "base_integration_sha_observed": "<sha>",
  "task_ids": ["T01"],
  "notes": "<optional concise blocker/context>"
}
```

Use these fixed mappings:

- slot-01 -> T01 -> `agent/v030-coop-native-portability`
- slot-02 -> T02 -> `agent/v030-coop-evidence-performance`
- slot-03 -> T03 -> `agent/v030-coop-graph-productization`

A claim is coordination metadata, not permission to modify another slot's implementation paths.
