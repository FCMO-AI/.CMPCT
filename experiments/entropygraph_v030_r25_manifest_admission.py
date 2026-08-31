from __future__ import annotations

"""Content-agnostic admission/decoding seam for canonical r25 filesystem control.

The canonical r25 graph already authenticates regular member path/size/SHA identities.  The implicit-v4
control grammar can therefore omit those duplicated identities and reconstruct exact filesystem-v1 semantics
from the authenticated graph.  This module makes that decision explicit and fail-closed without changing the
shipping canonical reader/writer yet.

Admission law:
* construct implicit-v4 only from a valid filesystem-v1 control;
* prove exact expanded semantics against the original control;
* admit it only when it is strictly smaller; ties retain filesystem-v1;
* never inspect workload names, pack hashes, source paths, or benchmark identity.

The matching decoder accepts exactly the two bounded structural grammars and joins implicit-v4 only with
identities supplied by the authenticated content graph.  This is the productization seam needed before wiring
the compact control into the canonical writer/reader and recovery/native/Android surfaces.
"""

from dataclasses import dataclass

from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS


@dataclass(frozen=True)
class ManifestAdmission:
    raw: bytes
    encoding: str
    filesystem_v1_bytes: int
    selected_bytes: int
    saving_bytes: int


def admit(
    filesystem_v1_raw: bytes,
    *,
    max_path_bytes: int,
    max_entries: int,
) -> ManifestAdmission:
    """Return the strictly smaller exact control, otherwise the original filesystem-v1 bytes."""
    # Decode first so malformed source control can never be normalized into a different grammar.
    FS.decode_manifest(
        filesystem_v1_raw,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    candidate = IFS4.encode_v1(
        filesystem_v1_raw,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    if len(candidate) >= len(filesystem_v1_raw):
        return ManifestAdmission(
            raw=filesystem_v1_raw,
            encoding="filesystem-v1",
            filesystem_v1_bytes=len(filesystem_v1_raw),
            selected_bytes=len(filesystem_v1_raw),
            saving_bytes=0,
        )
    if not IFS4.semantics_equal(
        filesystem_v1_raw,
        candidate,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    ):
        # A compact encoder bug is not a reason to publish changed filesystem semantics.
        return ManifestAdmission(
            raw=filesystem_v1_raw,
            encoding="filesystem-v1",
            filesystem_v1_bytes=len(filesystem_v1_raw),
            selected_bytes=len(filesystem_v1_raw),
            saving_bytes=0,
        )
    return ManifestAdmission(
        raw=candidate,
        encoding="implicit-v4",
        filesystem_v1_bytes=len(filesystem_v1_raw),
        selected_bytes=len(candidate),
        saving_bytes=len(filesystem_v1_raw) - len(candidate),
    )


def decode(
    raw: bytes,
    *,
    regular_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> tuple[dict, str]:
    """Decode either admitted control grammar to exact filesystem-v1 semantics.

    The grammars are structurally disjoint on the wire (filesystem-v1 is a map; implicit-v4 is a four-item
    versioned array).  We still let each bounded decoder validate its own complete grammar rather than using an
    unbounded probe parser.  If neither accepts, the control is hostile/corrupt and the caller must fail closed.
    """
    try:
        return (
            FS.decode_manifest(raw, max_path_bytes=max_path_bytes, max_entries=max_entries),
            "filesystem-v1",
        )
    except RuntimeError as v1_error:
        try:
            return (
                IFS4.decode_to_v1(
                    raw,
                    regular_identities=regular_identities,
                    max_path_bytes=max_path_bytes,
                    max_entries=max_entries,
                ),
                "implicit-v4",
            )
        except RuntimeError as implicit_error:
            raise RuntimeError("unsupported or malformed r25 filesystem control") from implicit_error
