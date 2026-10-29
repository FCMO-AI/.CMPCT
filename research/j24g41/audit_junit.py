"""Fail-closed admission of true physical native-xattr tests, not a green pytest shell."""
import json
import platform
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

junit = Path(sys.argv[1])
output = Path(sys.argv[2])
root = ET.parse(junit).getroot()
cases = root.findall(".//testcase")
by_name = {case.attrib["name"]: case for case in cases}
required = [
    "test_provider_capability_matches_native_platform",
    "test_bounded_native_two_pass_never_silently_truncates",
    "test_native_name_is_lossless_or_rejected",
]
if sys.platform in ("darwin", "linux"):
    required.append("test_native_xattr_roundtrip_through_authentic_r24_archive")
if sys.platform == "darwin":
    required.append("test_darwin_nofollow_does_not_inherit_target_xattr")
observed = {name: {
    "present": name in by_name,
    "skipped": name in by_name and by_name[name].find("skipped") is not None,
    "failed": name in by_name and (by_name[name].find("failure") is not None or by_name[name].find("error") is not None),
} for name in required}
all_failures = [case.attrib["name"] for case in cases if case.find("failure") is not None or case.find("error") is not None]
decision = all(v["present"] and not v["skipped"] and not v["failed"] for v in observed.values()) and not all_failures
receipt = {
    "platform": sys.platform,
    "uname": platform.platform(),
    "python": sys.version,
    "tests_executed": len(cases),
    "required": observed,
    "failures": all_failures,
    "physical_mac_os_test_executed": sys.platform == "darwin" and observed["test_native_xattr_roundtrip_through_authentic_r24_archive"]["present"] and not observed["test_native_xattr_roundtrip_through_authentic_r24_archive"]["skipped"],
    "decision": "ADMITTED" if decision else "REJECTED",
}
output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
if not decision:
    raise SystemExit("J24G41 court did not satisfy physical test requirements")
