from __future__ import annotations

"""Hostile extension of the shared-dictionary R4 through baseline/high effort.

The cheap dictionary receipt (levels 3/5/9) was negative.  Before retiring the family, remove the strongest
alternative explanation: that the dictionary lost only because its backend effort was below the level-15
fixed-representation baseline.  This wrapper reuses the exact charged oracle and expands only the dictionary
compression levels to 15 and 19.  Level 19 is intentionally included as an upper-bound hostile control;
its work still has to fit the same charged external-time budget to count.
"""

from benchmarks import v030_r4_shared_dictionary_oracle as ORACLE

ORACLE.DICT_LEVELS = (3, 5, 9, 15, 19)


if __name__ == "__main__":
    ORACLE.main()
