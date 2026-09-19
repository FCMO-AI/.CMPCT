# G04 delimiter-inverse negative raw receipt

This directory preserves the exact raw JSON emitted by workflow run `35034826327`, artifact `10422747226` (`v030-g04-delimiter-inverse-ab-bf1cba9106568e3dfa22db62a6072aa670cf980f`). The Actions artifact digest is `sha256:8c4b8577f1b9ac759b96e0fe5dbf3c1e6d50993c4193763a34e6efe1e2854ee3`.

The original JSON was `v030-g04-delimiter-inverse-ab.json`, 27,114 bytes, with SHA-256:

`af20f5e67a4a029f8f097ae2ee802c1b298ba06edab1f4eeb9095fb917aada26`

Because GitHub's text contents API is used for repository custody, the exact JSON is stored reversibly as deterministic gzip (`gzip -n -9`) followed by base64 in `v030-g04-delimiter-inverse-ab.json.gz.b64`. Recover and verify with:

```bash
base64 -d v030-g04-delimiter-inverse-ab.json.gz.b64 | gzip -dc > /tmp/v030-g04-delimiter-inverse-ab.json
printf '%s  %s\n' af20f5e67a4a029f8f097ae2ee802c1b298ba06edab1f4eeb9095fb917aada26 /tmp/v030-g04-delimiter-inverse-ab.json | sha256sum -c -
```

Decision boundary is unchanged: this is research/mechanism evidence only, `release_credit=false`. Nine control and nine candidate samples produced control median `0.16170011799999884 s`, candidate median `0.2428096749999895 s`, candidate/control `1.5016048102079385x`, i.e. the candidate was about 50.16% slower. The inherited promotion floor was +15%; `promotion_signal=false`. Product source, archive bytes, and release thresholds were unchanged. Preserve the negative; do not reopen or productize this delimiter-inverse route without genuinely new evidence.