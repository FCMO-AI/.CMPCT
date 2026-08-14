from pathlib import Path
import plistlib
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MIME = "application/vnd.fcmo.cmpct"
MIME_ALIAS = "application/x-cmpct"
EXTENSION = "cmpct"
APPLE_UTI = "com.fcmo.cmpct.archive"
WINDOWS_PROGID = "FCMO.CMPCT.Archive"


def test_linux_mime_registration_keeps_canonical_identity():
    path = ROOT / "integrations/linux/application-vnd.fcmo.cmpct.xml"
    text = path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    mime_nodes = [node for node in root.iter() if node.tag.endswith("mime-type")]
    assert len(mime_nodes) == 1
    assert mime_nodes[0].attrib["type"] == MIME
    assert any(node.attrib.get("pattern") == f"*.{EXTENSION}" for node in root.iter() if node.tag.endswith("glob"))
    assert "CMPCT24" in text


def test_windows_association_targets_packaged_native_browser_without_hijacking_default():
    text = (ROOT / "integrations/windows/cmpct-file-association.reg").read_text(encoding="utf-8")
    assert f"\\Software\\Classes\\.{EXTENSION}]" in text
    assert f"\\Software\\Classes\\.{EXTENSION}\\OpenWithProgids]" in text
    assert WINDOWS_PROGID in text
    assert f'"Content Type"="{MIME}"' in text
    assert "RegisteredApplications" in text
    assert "Capabilities\\FileAssociations" in text
    assert "@CMPCT_BROWSER_EXE@" in text
    assert "python" not in text.lower()
    # .reg string values escape embedded command-line quotes with backslashes;
    # assert the serialized form rather than the post-registry command spelling.
    assert '\\"%1\\"' in text
    extension_block = text.split(f"[HKEY_CURRENT_USER\\Software\\Classes\\.{EXTENSION}]", 1)[1].split("\n\n", 1)[0]
    assert '\n@="' not in extension_block


def test_apple_document_type_exports_cmpct_uti_and_both_mime_names():
    path = ROOT / "integrations/apple/CMPCTDocumentTypes.plist"
    with path.open("rb") as handle:
        plist = plistlib.load(handle)
    decl = plist["UTExportedTypeDeclarations"][0]
    assert decl["UTTypeIdentifier"] == APPLE_UTI
    tags = decl["UTTypeTagSpecification"]
    assert EXTENSION in tags["public.filename-extension"]
    assert MIME in tags["public.mime-type"]
    assert MIME_ALIAS in tags["public.mime-type"]
    assert "public.archive" in decl["UTTypeConformsTo"]
    doc = plist["CFBundleDocumentTypes"][0]
    assert APPLE_UTI in doc["LSItemContentTypes"]


def test_android_view_contract_routes_known_mimes_and_requires_magic_validation_comment():
    path = ROOT / "integrations/android/AndroidManifest-cmpct.xml"
    text = path.read_text(encoding="utf-8")
    ET.fromstring(text)
    assert MIME in text
    assert MIME_ALIAS in text
    assert "application/octet-stream" in text
    assert re.search(r"cmpct", text, re.IGNORECASE)
    # Association metadata is intentionally not a trust boundary; keep the
    # nearby invariant explicit so future packaging work does not regress it.
    assert "verify CMPCT24" in text
