"""Joint invariant court: Win32 and macOS destination policies coexist on one Reader source.

This file is additive: original owner tests are imported unchanged and executed
in the same hosted matrix. Both helpers remain destination-specific, not wire grammar.
"""
from __future__ import annotations

import pytest

from cmpct.path_policy import (
    canonical_logical_path,
    canonical_windows_extraction_key,
    macos_comparison_component,
)


def test_both_destination_name_policy_helpers_exist_without_rewriting_wire_names() -> None:
    # A portable r24 path parser must not silently outlaw valid Linux names.
    for path in ("a:stream", "NUL.txt", "caf\u00e9", "cafe\u0301"):
        assert canonical_logical_path(path)[0] == path
    assert canonical_logical_path("caf\u00e9")[0] != canonical_logical_path("cafe\u0301")[0]

    # These are destination-specific admission decisions; a successful import
    # of one implementation must not remove the other.
    with pytest.raises(ValueError, match="Windows"):
        canonical_windows_extraction_key(("NUL.txt",))
    assert canonical_windows_extraction_key(("ordinary", "file.txt")) == "ordinary/file.txt"
    assert macos_comparison_component("caf\u00e9") == macos_comparison_component("cafe\u0301")
    assert macos_comparison_component("Alpha") == macos_comparison_component("alpha")


def test_platform_policies_reject_different_ambiguity_classes() -> None:
    # On Win32, ADS syntax needs refusal even when legal in POSIX. On APFS,
    # different UTF-8 normalization spellings need a shared collision key.
    with pytest.raises(ValueError, match="Windows"):
        canonical_windows_extraction_key(("a:stream",))
    assert macos_comparison_component("a:stream") == "a:stream"

    # Normal UTF-8 byte spelling remains expressible in portable archive grammar.
    assert canonical_logical_path("Dir/cafe\u0301")[1] == ("Dir", "cafe\u0301")
