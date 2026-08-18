# Four-agent branch bootstrap snapshot

All non-integrator cooperation branches start from the same coordination-complete authoritative integration snapshot.

Bootstrap integration SHA: `767ef73157e028443d6f51bf52b514b89a006b54`

Branches:

- slot-00: `agent/v030-authoritative-integration`
- slot-01: `agent/v030-coop-native-portability`
- slot-02: `agent/v030-coop-evidence-performance`
- slot-03: `agent/v030-coop-graph-productization`

The three non-integrator branches above were created from exactly that SHA.

Before final evidence, each branch must re-resolve the current slot-00 integration SHA because T00 main reconciliation may advance it. This bootstrap SHA is a common starting state, not permanent release authority.
