from __future__ import annotations

"""Shared revision-24 journal replay, independent of Reader and preflight imports.

Footnote: signed filesystem metadata uses file-row ordinals, but archive identity
survives inserts/deletes/renames by logical path. Reader, transactions/checkpoint
and bounded preflight must replay one identical identity transformation.
"""

class JournalReplayLimitError(ValueError):
    """A journal insertion would exceed the caller's file-count budget."""


def _apply_journal_ops(index: dict, ops: list, *, max_files: int | None = None) -> dict:
    """Apply r24 journal ops while binding positional fsmeta to logical path identity.

    The signed r24 base index stores xattrs and owner overrides by sorted file-row ordinal.
    Journal operations may change those ordinals; retaining the old numbers would silently
    attach verified metadata to the wrong file. Both replay and checkpoint creation must
    use this same transformation, or the 64-delta checkpoint resurrects the defect.

    New journal members carry no xattr/owner override fields, so they inherit the
    original archive's common owner but never another member's sparse overrides.
    A same-path put retains preexisting metadata; rename transfers it; delete removes it.
    """
    rows = index['files']
    # The frequent replace-in-place journal op never changes row ordinals. Avoid
    # allocating a per-file lineage map or sorting a large index for that case.
    if len(ops) == 1 and ops[0][0] == 'put':
        replacement = ops[0][1]
        for i, prior in enumerate(rows):
            if prior[0] == replacement[0]:
                rows[i] = replacement
                return index
    old_names = [row[0] for row in rows]
    # Lineage maps a current path to its original file-row identity. An inserted name
    # has no preexisting metadata, even if an earlier op deleted a homonymous path.
    lineage = {name: name for name in old_names}
    for op in ops:
        kind = op[0]
        if kind == 'put':
            row = op[1]
            for i, prior in enumerate(rows):
                if prior[0] == row[0]:
                    rows[i] = row
                    break
            else:
                rows.append(row)
                if max_files is not None and len(rows) > max_files:
                    raise JournalReplayLimitError("journal file count exceeds parser limit")
        elif kind == 'del':
            path = op[1]
            rows[:] = [row for row in rows if row[0] != path]
            lineage.pop(path, None)
        elif kind == 'ren':
            old, new = op[1], op[2]
            for row in rows:
                if row[0] == old:
                    row[0] = new
                    if old in lineage:
                        lineage[new] = lineage.pop(old)
                    break
    rows.sort(key=lambda row: row[0])
    new_names = [row[0] for row in rows]
    fsmeta = index.get('fsmeta')
    # A delete followed by a fresh put of the same name may leave the sorted
    # filenames unchanged while replacing the underlying file identity. Dropping
    # that lineage must remove the deleted file's authenticated metadata too.
    needs_rekey = (new_names != old_names or len(lineage) != len(new_names)
                   or any(lineage.get(name) != name for name in new_names))
    if fsmeta and needs_rekey:
        old_positions = {name: i for i, name in enumerate(old_names)}
        for field in ('owner_overrides', 'xattrs'):
            if field not in fsmeta:
                continue
            by_old_ordinal = {}
            for record in fsmeta[field]:
                ordinal = record[0]
                # Never transfer an ambiguous or out-of-range authenticated ordinal.
                if (type(ordinal) is not int or ordinal < 0
                        or ordinal >= len(old_names) or ordinal in by_old_ordinal):
                    raise ValueError(f'invalid signed fsmeta {field} ordinal: {ordinal!r}')
                by_old_ordinal[ordinal] = record[1:]
            fsmeta[field] = [
                [new_ordinal, *by_old_ordinal[old_positions[lineage[path]]]]
                for new_ordinal, path in enumerate(new_names)
                if path in lineage
                and old_positions[lineage[path]] in by_old_ordinal
            ]
    return index
