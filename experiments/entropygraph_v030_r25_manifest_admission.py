from __future__ import annotations

"""Content-agnostic admission/decoding seam for canonical r25 filesystem control.

The canonical r25 graph already authenticates regular member path/size/SHA identities. The implicit-v4
control grammar can therefore omit those duplicated identities and reconstruct exact filesystem-v1 semantics
from the authenticated graph. This module owns the productization seam so writer staging and reader validation
cannot drift into two subtly different policies.

Admission law:
* construct implicit-v4 only from a valid filesystem-v1 control;
* prove exact expanded semantics against the original control;
* admit it only when it is strictly smaller; ties retain filesystem-v1;
* never inspect workload names, pack hashes, source paths, or benchmark identity.

Reader law:
* authenticate the control bytes through the selected content graph before decoding;
* join implicit-v4 only with identities from that same authenticated graph;
* require the reconstructed regular-member set and every size/SHA identity to match the graph exactly;
* fail closed on any mismatch rather than silently falling back to another semantic owner.
"""

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath

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
    # Decode exactly once up front so malformed source control can never be normalized into a different grammar.
    # The validated semantic object is then reused for compact encoding and the independent expansion proof. This
    # removes two redundant full filesystem-v1 parses from the promoted creation path without changing bytes or law.
    original = FS.decode_manifest(
        filesystem_v1_raw,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    candidate = IFS4.encode_decoded_v1(original)
    if len(candidate) >= len(filesystem_v1_raw):
        return ManifestAdmission(
            raw=filesystem_v1_raw,
            encoding="filesystem-v1",
            filesystem_v1_bytes=len(filesystem_v1_raw),
            selected_bytes=len(filesystem_v1_raw),
            saving_bytes=0,
        )
    if not IFS4.semantics_equal_decoded(
        original,
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


def prepare_profile_tree(
    root: Path,
    staging_root: Path,
    *,
    max_path_bytes: int,
    max_profile_files: int,
    max_profile_logical_bytes: int,
    max_entries: int,
) -> dict:
    """Stage graph members once, then select the exact smaller filesystem control in place.

    ``manifest_raw`` intentionally remains the full filesystem-v1 source control because canonical tree identity
    and compatibility accounting are defined from those semantics. ``selected_manifest_raw`` is the authenticated
    member that the r25 graph should actually publish. Keeping both explicit prevents callers from accidentally
    hashing compact wire bytes as though they were the user-visible semantic tree.
    """
    prepared = FS.prepare_profile_tree(
        root,
        staging_root,
        max_path_bytes=max_path_bytes,
        max_profile_files=max_profile_files,
        max_profile_logical_bytes=max_profile_logical_bytes,
        max_entries=max_entries,
    )
    selected = admit(
        prepared["manifest_raw"],
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    manifest_path = Path(staging_root).joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    if manifest_path.read_bytes() != prepared["manifest_raw"]:
        raise RuntimeError("r25 staged filesystem control changed before admission")
    if selected.raw != prepared["manifest_raw"]:
        manifest_path.write_bytes(selected.raw)
    return {
        **prepared,
        "source_manifest_raw": prepared["manifest_raw"],
        "selected_manifest_raw": selected.raw,
        "selected_manifest_encoding": selected.encoding,
        "selected_manifest_bytes": selected.selected_bytes,
        "selected_manifest_sha256": hashlib.sha256(selected.raw).hexdigest(),
        "manifest_control_saving_bytes": selected.saving_bytes,
    }


def decode(
    raw: bytes,
    *,
    regular_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> tuple[dict, str]:
    """Decode either admitted control grammar to exact filesystem-v1 semantics.

    The grammars are structurally disjoint on the wire (filesystem-v1 is a map; implicit-v4 is a four-item
    versioned array). We still let each bounded decoder validate its own complete grammar rather than using an
    unbounded probe parser. If neither accepts, the control is hostile/corrupt and the caller must fail closed.
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


def decode_from_content_identities(
    raw: bytes,
    *,
    content_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> tuple[dict, str]:
    """Authenticate, decode and cross-check one r25 filesystem control against its graph identities."""
    identities = dict(content_identities)
    control_identity = identities.pop(FS.FILESYSTEM_MANIFEST, None)
    expected_control_identity = (len(raw), hashlib.sha256(raw).digest())
    if control_identity != expected_control_identity:
        raise RuntimeError("r25 filesystem control graph identity mismatch")

    try:
        decoded, encoding = decode(
            raw,
            regular_identities=identities,
            max_path_bytes=max_path_bytes,
            max_entries=max_entries,
        )
    except RuntimeError as exc:
        # The low-level dual-grammar decoder intentionally presents malformed inputs through one generic
        # fail-closed boundary. At this graph-bound seam, however, an otherwise valid implicit-v4 control whose
        # authenticated identity set has the wrong cardinality is specifically a logical-member disagreement.
        # Preserve that semantic diagnostic without weakening or bypassing either bounded grammar decoder.
        cause = exc.__cause__
        if (
            str(exc) == "unsupported or malformed r25 filesystem control"
            and isinstance(cause, RuntimeError)
            and str(cause) == "implicit-v4 regular identity count does not match metadata vector"
        ):
            raise RuntimeError("r25 content profile and filesystem control disagree on logical members") from exc
        raise
    if set(decoded["regular"]) != set(identities):
        raise RuntimeError("r25 content profile and filesystem control disagree on logical members")
    for rel, identity in decoded["regular"].items():
        if identities.get(rel) != identity:
            raise RuntimeError(f"r25 filesystem control/content identity mismatch: {rel}")
    return decoded, encoding
