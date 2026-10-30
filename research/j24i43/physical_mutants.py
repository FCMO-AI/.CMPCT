#!/usr/bin/env python3
"""J24I43 negative physical controls. No cmpct imports; one bit per mutation."""
import argparse, hashlib, json, struct
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    a = p.parse_args()
    root = a.case_dir
    m = json.loads((root / "bounded-container-manifest.json").read_text())
    assert m["schema"] == "j24i42-audited-original-container-ranges-v1"
    out = {"schema":"j24i43-source-exact-physical-mutants-v1","records":{}}
    for mib in (8,32):
        item = m["records"][str(mib)]
        raw = (root / item["archive_path"]).read_bytes()
        assert sha(raw) == item["archive_sha256"]
        meta = (root / item["metadata_path"]).read_bytes()
        off = item["encoded_offset"]
        encoded = item["encoded_bytes"]
        blob_start = off - len(meta) - 64
        assert raw[blob_start:blob_start+4] == b"CMA4"
        assert raw[off:off+4] == b"fLaC"
        assert struct.unpack_from("<Q",raw,blob_start+16)[0] == encoded
        crc_at = blob_start + 28
        frame_at = off + encoded//2
        assert frame_at < off + encoded - 64
        rows={}
        for name,pos in (("crc-only",crc_at),("flac-mid",frame_at)):
            mutated=bytearray(raw)
            mutated[pos] ^= 1
            path=root / f"j24i43-{name}-{mib}m.cmpct"
            path.write_bytes(mutated)
            assert len(mutated) == len(raw)
            assert all(mutated[i] == raw[i] for i in (0,68,len(raw)-1))
            assert sum(x!=y for x,y in zip(raw,mutated)) == 1
            rows[name] = {"path":path.name,"byte_offset":pos,"xor":1,
                          "original_sha256":sha(raw),"modified_sha256":sha(mutated)}
        out["records"][str(mib)] = rows
    (root/"j24i43-mutants.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":"PASS","cases":4,"manifest":out},sort_keys=True))

if __name__ == "__main__": main()
