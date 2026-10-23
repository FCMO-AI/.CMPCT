"""POSIX capability-root boundary microcourt (research-only, no product credit).

All names are temporary synthetic paths. This distinguishes physical inode
identity from containment by the current destination pathname under renames.
The original Reader is not executed. A fixed directory descriptor is useful,
but not by itself a proof that a writable ancestor cannot move out of root.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory


def court() -> dict[str, bool]:
    assert os.name == "posix"
    o_dir = getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    assert o_dir and nofollow and os.open in os.supports_dir_fd
    result = {}
    with TemporaryDirectory(prefix="cmpct-destination-inode-court-") as td:
        base = Path(td)
        root = base / "destination"
        outside = base / "outside"
        root.mkdir()
        outside.mkdir()

        # A symlink ancestor is rejected with fd-relative no-follow traversal.
        (root / "pivot").symlink_to(outside, target_is_directory=True)
        root_fd = os.open(root, os.O_RDONLY | o_dir | nofollow)
        try:
            refused = False
            try:
                pivot_fd = os.open("pivot", os.O_RDONLY | o_dir | nofollow, dir_fd=root_fd)
            except OSError:
                refused = True
            else:
                os.close(pivot_fd)
            result["symlink_component_rejected"] = refused
        finally:
            os.close(root_fd)

        # No-follow on a regular leaf does not stop alias writes through a
        # hardlink to an external file; replacing with a new inode does.
        nested = root / "nested"
        nested.mkdir()
        victim = outside / "victim"
        victim.write_bytes(b"ORIGINAL")
        os.link(victim, nested / "member")
        nested_fd = os.open(nested, os.O_RDONLY | o_dir | nofollow)
        try:
            fd = os.open("member", os.O_WRONLY | os.O_TRUNC | nofollow, dir_fd=nested_fd)
            os.write(fd, b"ALTERED")
            os.close(fd)
            result["nofollow_truncate_writes_external_hardlink"] = victim.read_bytes() == b"ALTERED"

            fd = os.open(
                ".new-member", os.O_CREAT | os.O_EXCL | os.O_WRONLY | nofollow,
                0o600, dir_fd=nested_fd,
            )
            os.write(fd, b"NEW-PRIVATE-INODE")
            os.close(fd)
            os.rename(".new-member", "member", src_dir_fd=nested_fd, dst_dir_fd=nested_fd)
            result["atomic_new_inode_preserves_external_hardlink"] = (
                victim.read_bytes() == b"ALTERED"
                and (nested / "member").read_bytes() == b"NEW-PRIVATE-INODE"
                and victim.stat().st_ino != (nested / "member").stat().st_ino
            )
            # A prospective lstat(nlink==1) is stale the instant another
            # writable actor replaces that leaf with a hardlink to the
            # outside inode. No symlink is introduced. The subsequent
            # no-follow truncate still modifies the outside inode.
            late_leaf = nested / "late-leaf"
            late_leaf.write_bytes(b"INITIALLY-ONE-LINK")
            before = os.lstat(late_leaf)
            late_alias = outside / "late-alias"
            os.link(victim, late_alias)
            os.replace(late_alias, late_leaf)
            changed = b"POST-CHECK-OUTSIDE-MUTATION"
            fd = os.open("late-leaf", os.O_WRONLY | os.O_TRUNC | nofollow, dir_fd=nested_fd)
            os.write(fd, changed)
            os.close(fd)
            result["lstat_one_link_then_leaf_swap_bypasses_static_guard"] = (
                before.st_nlink == 1
                and os.lstat(late_leaf).st_nlink > 1
                and os.lstat(late_leaf).st_ino == os.lstat(victim).st_ino
                and victim.read_bytes() == changed
            )
        finally:
            os.close(nested_fd)

        # A renamed directory remains addressable by an already-held FD.
        # This is correct inode-capability behavior, but invalidates claims of
        # confinement to the *current pathname* of a concurrently mutable root.
        mobile = root / "mobile"
        mobile.mkdir()
        mobile_fd = os.open(mobile, os.O_RDONLY | o_dir | nofollow)
        try:
            moved = outside / "moved-root-child"
            os.rename(mobile, moved)
            fd = os.open(
                "late-file", os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
                0o600, dir_fd=mobile_fd,
            )
            os.write(fd, b"FD-STILL-NAMES-MOVED-INODE")
            os.close(fd)
            result["dirfd_can_publish_under_moved_directory_outside_current_path_root"] = (
                (moved / "late-file").read_bytes() == b"FD-STILL-NAMES-MOVED-INODE"
                and not mobile.exists()
            )
        finally:
            os.close(mobile_fd)

    assert all(result.values()), result
    return result


if __name__ == "__main__":
    print(json.dumps({
        "evidence_class": "isolated_posix_microcourt_not_cmpct_product",
        "observations": court(),
        "scope": "Linux POSIX, deterministic path-operation ordering, no adversarial concurrent thread",
        "boundary": "inode-capability identity is not equivalent to current-pathname containment under writable ancestor renames",
    }, sort_keys=True, indent=2))
