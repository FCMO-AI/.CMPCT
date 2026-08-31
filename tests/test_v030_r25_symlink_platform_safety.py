from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_product_fs as FS


def _decoded_symlink(target: str) -> dict:
    return {
        "manifest": {
            "entries": [
                ["link", "l", 0o777, 0, 0, 0, [], target],
            ]
        }
    }


@pytest.mark.parametrize(
    "link_target",
    [
        "/absolute/posix",
        "../escape",
        r"..\escape",
        r"C:\absolute\windows",
        r"C:drive-relative",
        r"\\server\share\escape",
    ],
)
def test_safe_symlink_restore_rejects_cross_platform_escape_spellings(
    tmp_path: Path,
    link_target: str,
) -> None:
    with pytest.raises(RuntimeError, match="unsafe r25 symlink target"):
        FS.restore_manifest_tree(tmp_path, _decoded_symlink(link_target), safe_symlinks=True)
    assert not (tmp_path / "link").is_symlink()


@pytest.mark.parametrize(
    "link_target",
    [
        "sibling",
        "subdir/target",
        "name-with-colon-not-drive",
    ],
)
def test_cross_platform_symlink_guard_keeps_bounded_relative_targets(link_target: str) -> None:
    assert FS._unsafe_symlink_target(link_target) is False
