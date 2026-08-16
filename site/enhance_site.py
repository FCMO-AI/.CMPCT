#!/usr/bin/env python3
from __future__ import annotations

"""Apply the non-semantic CMPCT presentation layer to a built static site.

Footnote: this deliberately runs *after* build_site.py. Visual motion and surface-revision labeling are
presentation concerns; keeping them out of the canonical benchmark/data builder reduces the chance that
a cosmetic pass can accidentally alter archive evidence or Browser Lab behavior.
"""

import argparse
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACE_FILE = ROOT / "SURFACE_REVISION"


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return str(tomllib.load(fh)["project"]["version"])


def surface_revision(version: str) -> str:
    value = SURFACE_FILE.read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"(\d+)\.(\d+)\.([a-z]+)", value)
    if not match:
        raise RuntimeError(f"SURFACE_REVISION must use x.x.a lettering, got {value!r}")
    major, minor, _ = match.groups()
    project_major, project_minor, *_ = version.split(".")
    if (major, minor) != (project_major, project_minor):
        raise RuntimeError(
            f"surface revision {value} must remain on project line {project_major}.{project_minor}.x"
        )
    return value


def patch_index(output: Path, version: str, surface: str) -> None:
    path = output / "index.html"
    html = path.read_text(encoding="utf-8")

    if "assets/motion.css" not in html:
        html = html.replace(
            '<link rel="stylesheet" href="assets/styles.css">',
            '<link rel="stylesheet" href="assets/styles.css">\n'
            '  <!-- Footnote: motion.css is optional presentation; styles.css remains the structural baseline. -->\n'
            '  <link rel="stylesheet" href="assets/motion.css">',
        )
    if "assets/motion.js" not in html:
        html = html.replace(
            '<script type="module" src="assets/app.js"></script>',
            '<script type="module" src="assets/app.js"></script>\n'
            '  <script type="module" src="assets/motion.js"></script>',
        )

    html = re.sub(
        r'<span class="release-chip">v[^<]+? · r(\d+)</span>',
        lambda match: f'<span class="release-chip">v{version} · surface {surface} · r{match.group(1)}</span>',
        html,
        count=1,
    )
    html = html.replace(
        f'<span>Project v{version}</span><span>Canonical format',
        f'<span>Project v{version}</span><span>Surface {surface}</span><span>Canonical format',
        1,
    )
    html = html.replace(
        'Every material step<br><em>gets a version and a benchmark.</em>',
        'Core releases must<br><em>earn the number.</em>',
        1,
    )
    html = html.replace(
        'Project versions move whenever substantive work lands. Format revision moves only when readers need new on-disk semantics. The performance gate runs either way.',
        'Numeric project versions move only when CMPCT itself gains a material format/engine capability, performance improvement, reliability gain or interoperability improvement. Site, documentation and repository presentation use the alphabetic surface track (x.x.a, x.x.b, …) and do not consume a core version number.',
        1,
    )

    path.write_text(html, encoding="utf-8")
    (output / "surface-revision.txt").write_text(surface + "\n", encoding="utf-8")


def patch_machine_state(output: Path, surface: str) -> None:
    agent_path = output / "agent.json"
    project_data_path = output / "project-data.json"

    if agent_path.exists():
        agent = json.loads(agent_path.read_text(encoding="utf-8"))
        agent["surface_revision"] = surface
        rules = list(agent.get("non_negotiables") or [])
        old_rule = "Material updates are versioned and benchmarked against their direct base."
        new_rule = (
            "Numeric core versions are reserved for material CMPCT format/engine improvements; "
            "presentation-only work advances the alphabetic surface revision instead."
        )
        rules = [new_rule if rule == old_rule else rule for rule in rules]
        agent["non_negotiables"] = rules
        agent_path.write_text(json.dumps(agent, indent=2) + "\n", encoding="utf-8")

        if project_data_path.exists():
            payload = json.loads(project_data_path.read_text(encoding="utf-8"))
            payload["project"] = agent
            project_data_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    llms_path = output / "llms.txt"
    if llms_path.exists():
        text = llms_path.read_text(encoding="utf-8")
        text = re.sub(
            r"> Project v([^·\n]+) · canonical format r(\d+)\.",
            rf"> Project v\1 · surface {surface} · canonical format r\2.",
            text,
            count=1,
        )
        text = text.replace(
            "Performance is a release contract: material updates are benchmarked against their direct base and deterministic size regressions are rejected.",
            "Performance is a core-release contract: numeric versions are reserved for material CMPCT improvements, while presentation-only work uses the alphabetic surface track. Deterministic size regressions remain rejected for core release candidates.",
            1,
        )
        llms_path.write_text(text, encoding="utf-8")


def enhance(output: Path) -> None:
    version = project_version()
    surface = surface_revision(version)
    patch_index(output, version, surface)
    patch_machine_state(output, surface)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply CMPCT presentation enhancements to a built site")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    enhance(args.output.resolve())
    print(f"Enhanced CMPCT site at {args.output.resolve()}")


if __name__ == "__main__":
    main()
