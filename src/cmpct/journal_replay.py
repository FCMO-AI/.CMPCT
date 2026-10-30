from __future__ import annotations

"""Shared revision-24 journal replay, independent of Reader and preflight imports.

Footnote: signed filesystem metadata uses file-row ordinals, but archive identity
survives inserts/deletes/renames by logical path. Reader, transactions/checkpoint
and bounded preflight must replay one identical identity transformation.
"""

class JournalReplayLimitError(ValueError):
    """A journal insertion would exceed the caller's file-count budget."""

class JournalReplayAdmissionError(ValueError):
    """A checksum-consistent journal contains an unsupported/malformed operation."""


def _validate_journal_ops(ops: list) -> None:
    """One fail-closed r24 opcode grammar shared by Reader, writer and preflight.

    A digest-valid but semantically unknown opcode must not be silently ignored,
    nor can a known mutation execute before an invalid later operation is found.
    MessagePack arrays decode to lists; accepting a new Python shape here would
    create a different on-disk interpretation from bounded preflight.
    """
    if not isinstance(ops, list):
        raise JournalReplayAdmissionError("transaction operations must be an array")
    for op in ops:
        if not isinstance(op, list) or not op:
            raise JournalReplayAdmissionError("malformed transaction operation")
        tag = op[0]
        if tag == 'put' and len(op) == 2:
            row = op[1]
            if not isinstance(row, list) or not row or not isinstance(row[0], str):
                raise JournalReplayAdmissionError("malformed put operation")
        elif tag == 'del' and len(op) == 2 and isinstance(op[1], str):
            continue
        elif tag == 'ren' and len(op) == 3 and all(isinstance(x, str) for x in op[1:]):
            continue
        elif tag == 'put':
            raise JournalReplayAdmissionError("malformed put operation")
        else:
            raise JournalReplayAdmissionError(f"unsupported transaction operation {tag!r}")



def _try_indexed_row_mutations(rows: list, ops: list, lineage: dict,
                               max_files: int | None) -> bool:
    """Use a name index only when a dry-run proves simple unambiguous semantics.

    The general fallback below deliberately retains historical first-match rename,
    all-match deletion and transient duplicate handling. This bounded fast path is
    for large unique-name histories; a collision or limit violation falls back
    *before* changing a row. Tombstones avoid repeated O(N) delete compaction.
    """
    if len(rows) < 64 or len(ops) < 16:
        return False
    try:
        present = {row[0] for row in rows}
    except (TypeError, IndexError):
        return False
    if len(present) != len(rows):
        return False
    active = len(rows)
    for op in ops:
        kind = op[0]
        if kind == 'put':
            name = op[1][0]
            if name not in present:
                present.add(name)
                active += 1
                if max_files is not None and active > max_files:
                    return False
        elif kind == 'del':
            name = op[1]
            if name in present:
                present.remove(name)
                active -= 1
        else:  # 'ren' — grammar already admitted the complete operation list.
            old, new = op[1], op[2]
            if old not in present:
                continue
            if new != old and new in present:
                return False
            present.remove(old)
            present.add(new)

    positions = {row[0]: i for i, row in enumerate(rows)}
    deleted = False
    for op in ops:
        kind = op[0]
        if kind == 'put':
            row = op[1]
            position = positions.get(row[0])
            if position is None:
                positions[row[0]] = len(rows)
                rows.append(row)
            else:
                rows[position] = row
        elif kind == 'del':
            path = op[1]
            position = positions.pop(path, None)
            if position is not None:
                rows[position] = None
                deleted = True
            lineage.pop(path, None)
        else:
            old, new = op[1], op[2]
            position = positions.pop(old, None)
            if position is not None:
                rows[position][0] = new
                positions[new] = position
                if old in lineage:
                    lineage[new] = lineage.pop(old)
    if deleted:
        rows[:] = [row for row in rows if row is not None]
    return True


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
    # Validate the *entire* operation list before mutating any index state.
    _validate_journal_ops(ops)
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
    if not _try_indexed_row_mutations(rows, ops, lineage, max_files):
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
            else:
                # Defensive if the list ever changes after grammar admission.
                raise JournalReplayAdmissionError(f"unsupported transaction operation {kind!r}")
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
