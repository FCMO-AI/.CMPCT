# J24P09b — Real pip root .pth executes before whole-package attestation

Date: 2026-10-30 UTC. **New negative evidence discovered after the original J24P09 preregistration and before integration.** This is a benign real-pip experiment; no malicious action or genuine CMPCT package compromise claimed.

## Primary scientific contradiction

The original J24P09 composition ran the strict #864 no-`.data` profile before install and then compared every `cmpct/` byte to the wheel after install. However #864 deliberately allowed unrelated top-level wheel members, including an executable Python interpreter startup `.pth` file. A postinstall check of only `cmpct/` cannot prove that no additional wheel-supplied code ran **before** the CMPCT import, when the validation interpreter itself starts.

## Physically executed falsifier

Started from an authentic sdist-first Linux CMPCT wheel containing 23 ZIP members. Added `cmpct_inert_hook.pth` at the wheel root with the deliberately inert startup statement `import builtins; builtins.CMPCT_INERT_PTH_EXECUTED=True`. Recomputed coherent SHA-256 `RECORD` fields, without altering original `cmpct/` Python/native files.

- Original wheel SHA-256: `07f2ebd657fd887570b953eaa8c5fa52073dc4d0e0d3e4ec0c8ffaf9d26761dd`.
- Altered self-consistent wheel SHA-256: `9e75b4eea56b138a2257cd292749fbaef31c463da8ebeb5bcb40b63bbc37ef27`.
- Fresh isolated CPython venv, real `pip install --no-compile`: **SUCCESS**.
- Fresh independent Python process **before CMPCT import**: `getattr(builtins, 'CMPCT_INERT_PTH_EXECUTED', False)` printed **True**.
- Earlier no-`.data` validator: **PASS** for changed wheel.
- Earlier installed `cmpct/` SHA-byte attestor: **PASS**, despite already executed wheel-supplied startup code.
- All original native/Python module bytes remained unchanged.

This falsifies the claim that a no-`.data` gate plus postinstall package-file equality fully bounds wheel-supplied executable code. It does **not** falsify the weaker explicitly stated attestor scope: equality of the installed `cmpct/` files.

## Decision and cheapest safety boundary

**Proposed scope-specific repair:** refuse any final CMPCT wheel ZIP member outside `cmpct/` and one and only one consistent `cmpct-<package-version>.dist-info/` root, before `pip install`. All three previously observed genuine official-style 23-member Linux, macOS and Windows wheels have only these two roots. The strict rule is CMPCT-specific; it must not be presented as a validator of general PEP 427 wheels.

Keep the complete original #864 path, no-`.data`, Unicode, device name, collision/ancestor checks; keep #854 Mach-O/RECORD contract; keep the J24P09a cached-bytecode rejection and `pip --no-compile`. New rejection controls for top-level `.pth`, `sitecustomize.py`, extra unrelated roots and distinct metadata roots; new positive legitimate content under `cmpct/assets/`.

The earlier #864 acceptance of disjoint `other/data.bin` and `pkg/` roots is **honest historical evidence that was valid under its narrower policy but incompatible with this newly proven publisher-execution guarantee**. Reclassifying them requires updating prospective tests explicitly, not silently erasing earlier positives.

No source-identity claim against a malicious publisher, arbitrary pip, concurrent filesystem mutation, compromised host or installer. This negative doesn't authorize a change to Discovery Engine policy. Counterfactual: inventory *all* executable post-install surfaces (including import startup .pth) before treating package-only SHA as end-to-end execution integrity.
