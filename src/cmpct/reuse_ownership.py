from __future__ import annotations

"""Fixed-point ownership for optional reuse-backed representations.

A tentative owner may earn reuse only from streams that still have at least two
*realized* owners. Hidden owners below the economic floor are peeled; when an
identity drops from two owners to one, the survivor loses that stream's credit.
Each owner/identity edge is removed at most once.
"""

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping

Identity = tuple[int, int, bytes]


def realized_reuse_fixed_point(
    owner_identities: Mapping[str, Iterable[Identity]],
    *,
    hidden_owners: Iterable[str],
    fixed_owners: Iterable[str] = (),
    min_verified_reuse: int,
) -> tuple[frozenset[str], dict[str, int]]:
    """Return stable realized owners and their final reusable-byte credit.

    ``fixed_owners`` are already-realized product owners (for example explicit
    VZIP owners) and are never peeled. ``hidden_owners`` are optional owners;
    they survive only while their reuse credit meets ``min_verified_reuse``.
    Identity byte cost is identity[1] (compressed size).
    """
    hidden = set(hidden_owners)
    fixed = set(fixed_owners)
    if hidden & fixed:
        raise ValueError("an owner cannot be both hidden and fixed")
    active = hidden | fixed
    normalized: dict[str, set[Identity]] = {
        owner: set(owner_identities.get(owner, ())) for owner in active
    }
    identity_owners: dict[Identity, set[str]] = defaultdict(set)
    for owner, identities in normalized.items():
        for identity in identities:
            identity_owners[identity].add(owner)

    credit = {owner: 0 for owner in active}
    for identity, owners in identity_owners.items():
        if len(owners) >= 2:
            size = int(identity[1])
            for owner in owners:
                credit[owner] += size

    queue = deque(owner for owner in hidden if credit[owner] < int(min_verified_reuse))
    queued = set(queue)
    while queue:
        owner = queue.popleft()
        queued.discard(owner)
        if owner not in active or owner in fixed or credit[owner] >= int(min_verified_reuse):
            continue
        active.remove(owner)
        for identity in normalized[owner]:
            owners = identity_owners[identity]
            if owner not in owners:
                continue
            before = len(owners)
            owners.remove(owner)
            # Only 2 -> 1 changes remaining reuse credit. Higher cardinalities
            # remain reusable; 1 -> 0 has no survivor to debit.
            if before == 2:
                survivor = next(iter(owners))
                credit[survivor] -= int(identity[1])
                if survivor in hidden and survivor in active and credit[survivor] < int(min_verified_reuse) and survivor not in queued:
                    queue.append(survivor)
                    queued.add(survivor)
        credit[owner] = 0

    return frozenset(active), {owner: int(credit[owner]) for owner in active}
