from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path


path = Path("tests/conformance/v24-chunk-maps.json")
payload = json.loads(path.read_text())
for record in payload["vectors"]:
    # Footnote: archive bytes are the independent conformance oracle. Length/SHA are derived from
    # those frozen bytes rather than manually duplicated, so transcription mistakes cannot redefine
    # or obscure which exact revision-24 object future readers must consume.
    raw = base64.b64decode(record["archive_base64"], validate=True)
    record["archive_bytes"] = len(raw)
    record["archive_sha256"] = hashlib.sha256(raw).hexdigest()
path.write_text(json.dumps(payload, indent=2) + "\n")
