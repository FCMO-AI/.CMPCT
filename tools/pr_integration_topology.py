#!/usr/bin/env python3
"""Live, stateless CMPCT PR topology and shared-mutation-surface witness.

GitHub PR metadata is volatile: this instrument does NOT prove conflict-free
merges, source correctness, CI parity or release readiness. It makes no writes.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


CODE_PREFIXES = ("src/", "native/", "tools/", "research/")
DEFAULT_API = "https://api.github.com"


def _get_json(path: str, token: str | None) -> object:
    req = urllib.request.Request(
        DEFAULT_API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "CMPCT-pr-topology-readonly/1",
            **({"Authorization": "Bearer " + token} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def _api_repo(repo: str) -> str:
    bits = repo.split("/")
    if len(bits) != 2 or not all(bits):
        raise ValueError("repository must be owner/name")
    return "/repos/" + "/".join(urllib.parse.quote(x, safe="") for x in bits)


def _pages(base: str, token: str | None, max_pages: int) -> list:
    result: list = []
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in base else "?"
        values = _get_json(f"{base}{sep}per_page=100&page={page}", token)
        if not isinstance(values, list):
            raise ValueError("GitHub collection response must be an array")
        result.extend(values)
        if len(values) < 100:
            return result
    # Never represent an incomplete file listing as complete.
    raise ValueError(f"GitHub collection exceeds {max_pages * 100} entries; increase explicit bound")


def live_snapshot(repo: str, numbers: list[int], limit: int, workers: int = 6) -> list[dict]:
    """Read live PR heads and file paths; never write, cache, or claim locks."""
    base = _api_repo(repo)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if numbers:
        selected = [_get_json(f"{base}/pulls/{n}", token) for n in sorted(set(numbers))]
    else:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be 1..100")
        # Select only the bounded most recently UPDATED open PRs.
        selected = _get_json(
            f"{base}/pulls?state=open&sort=updated&direction=desc&per_page={limit}", token
        )
    if not isinstance(selected, list):
        raise ValueError("GitHub PR response must be a list")
    if len(selected) > 100:
        raise ValueError("more than 100 PRs requires an explicit scoped run")

    def read_one(pr: dict) -> dict:
        n = int(pr["number"])
        files = _pages(f"{base}/pulls/{n}/files", token, 5)
        return {
            "number": n,
            "title": str(pr.get("title", "")),
            "url": str(pr.get("html_url", "")),
            "state": str(pr.get("state", "")),
            "draft": bool(pr.get("draft", False)),
            "head_ref": str(pr["head"]["ref"]),
            "head_sha": str(pr["head"]["sha"]),
            "head_repo": str((pr["head"].get("repo") or {}).get("full_name") or ""),
            "base_ref": str(pr["base"]["ref"]),
            "base_sha": str(pr["base"]["sha"]),
            "base_repo": str((pr["base"].get("repo") or {}).get("full_name") or ""),
            "files": sorted({f["filename"] for f in files}),
        }

    with ThreadPoolExecutor(max_workers=max(1, min(8, workers))) as pool:
        return sorted(pool.map(read_one, selected), key=lambda p: p["number"])


def analyze(prs: list[dict], *, canonical_branches: tuple[str, ...] = ("main",)) -> dict:
    """Pure projection. Filename intersection is a risk signal, NOT git conflict."""
    by_number = {}
    by_head = {}
    for p in prs:
        n = int(p["number"])
        if n in by_number:
            raise ValueError(f"duplicate PR number: {n}")
        if len(p["head_sha"]) != 40 or len(p["base_sha"]) != 40:
            raise ValueError(f"missing exact Git SHA for PR {n}")
        by_number[n] = p
        key = (p.get("head_repo", ""), p["head_ref"])
        if key in by_head:
            raise ValueError(f"ambiguous head branch {key}")
        by_head[key] = n

    parents: dict[int, int | None] = {}
    external = []
    for n, p in sorted(by_number.items()):
        ref = (p.get("base_repo", ""), p["base_ref"])
        parent = by_head.get(ref)
        parents[n] = parent
        if parent == n:
            raise ValueError(f"PR #{n} self-based branch")
        if parent is None and p["base_ref"] not in canonical_branches:
            external.append({"number": n, "base_ref": p["base_ref"], "base_sha": p["base_sha"]})

    def ancestor(a: int, b: int) -> bool:
        """True when a is a known parent of b. Fail on cycles."""
        visited = set()
        current = b
        while current in parents and parents[current] is not None:
            if current in visited:
                raise ValueError(f"cycle among PR base/head references at #{current}")
            visited.add(current)
            current = parents[current]
            if current == a:
                return True
        return False

    # Diagnose graph cycles even when pairwise shared code paths are absent.
    for n in parents:
        ancestor(-1, n)

    stacks = [{"parent": parent, "child": n} for n, parent in sorted(parents.items())
              if parent is not None]
    overlaps = []
    ns = sorted(by_number)
    unknown = {e["number"] for e in external}
    for i, a in enumerate(ns):
        for b in ns[i + 1:]:
            shared = sorted(set(by_number[a]["files"]) & set(by_number[b]["files"]))
            if not shared:
                continue
            code = [f for f in shared if f.startswith(CODE_PREFIXES)]
            if not code:
                continue
            if ancestor(a, b) or ancestor(b, a):
                relation = "known_stacked_shared_code"
            elif a in unknown or b in unknown:
                relation = "shared_code_ancestry_incomplete"
            else:
                relation = "parallel_shared_code_surface"
            overlaps.append({
                "a": a, "b": b, "relation": relation,
                "code_paths": code,
                "note": "File overlap alone does not establish a merge conflict or code regression",
            })

    return {
        "schema": "cmpct-live-pr-topology-v1",
        "scope": "read-only snapshot, no lock, no merge or release decision",
        "pr_count": len(prs),
        "heads": [
            {
                "number": n, "url": p.get("url", ""), "head": p["head_sha"],
                "head_ref": p["head_ref"], "base_ref": p["base_ref"],
                "base_sha": p["base_sha"], "state": p.get("state", ""),
                "draft": p.get("draft", False),
            }
            for n, p in sorted(by_number.items())
        ],
        "known_stacks": stacks,
        "external_bases_not_in_sample": external,
        "shared_mutation_surfaces": overlaps,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="FCMO-AI/.CMPCT")
    ap.add_argument("--numbers", help="comma-separated live PR numbers; otherwise most recently updated")
    ap.add_argument("--limit", type=int, default=25, help="bounded latest open PR count (max 100)")
    ap.add_argument("--input", type=Path, help="offline JSON list of normalized PR records")
    ap.add_argument("--output", type=Path, help="optional JSON receipt path")
    args = ap.parse_args(argv)
    numbers = []
    if args.numbers:
        numbers = [int(v) for v in args.numbers.split(",") if v.strip()]
        if len(numbers) > 100 or any(n < 1 for n in numbers):
            ap.error("numbers must contain 1..100 positive PR numbers")
    try:
        prs = json.loads(args.input.read_text()) if args.input else live_snapshot(
            args.repo, numbers, args.limit
        )
        report = analyze(prs)
        report["repository"] = args.repo
        report["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
        report["data_source"] = "offline fixture" if args.input else "live GitHub REST"
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded)
        else:
            sys.stdout.write(encoded)
        return 0
    except (ValueError, KeyError, urllib.error.URLError, OSError) as exc:
        # Never leak the bearer token, raw request headers or secret-bearing env.
        print(f"PR topology unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
