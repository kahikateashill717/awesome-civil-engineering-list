#!/usr/bin/env python3
"""Generate README.md from data/tools.json.

Stdlib only. Fetches live star counts from the GitHub API (used only for
sort order), then renders one table per category: Tool | What it is |
License | Stars. The star/license values shown in the README itself are
shields.io badges, which GitHub renders live every time the page is
viewed -- so the numbers stay current without any scheduled job.

Run: python scripts/build_readme.py
Optional: set GITHUB_TOKEN to raise the API rate limit.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS_FILE = ROOT / "data" / "tools.json"
README_FILE = ROOT / "README.md"

CATEGORIES = [
    ("structural-engineering", "Structural Engineering & Analysis"),
    ("geotechnical-engineering", "Geotechnical Engineering"),
    ("earthquake-engineering", "Earthquake Engineering"),
    ("transportation-engineering", "Transportation Engineering"),
    ("environmental-engineering", "Environmental Engineering"),
    ("hydraulics-water-resources", "Hydraulics & Water Resources"),
    ("bim-cad", "BIM & CAD"),
    ("gis-geospatial", "GIS & Geospatial"),
    ("surveying-point-cloud", "Surveying & Point Cloud Processing"),
    ("mining-engineering", "Mining Engineering"),
]

DESCRIPTION_MAX = 160


def validate(tools):
    slugs = {c[0] for c in CATEGORIES}
    errors = []
    seen = set()
    for t in tools:
        name = t.get("name", "<missing name>")
        for field in ("name", "repo", "homepage", "category", "description", "license", "added"):
            if not t.get(field):
                errors.append(f"{name}: missing required field '{field}'")
        if t.get("category") and t["category"] not in slugs:
            errors.append(f"{name}: unknown category slug '{t['category']}'")
        if len(t.get("description", "")) > DESCRIPTION_MAX:
            errors.append(f"{name}: description too long")
        if t.get("repo") in seen:
            errors.append(f"{name}: duplicate repo '{t['repo']}'")
        seen.add(t.get("repo"))
    if errors:
        sys.exit("tools.json validation failed:\n  " + "\n  ".join(errors))


def fetch_stars(repo):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"User-Agent": "awesome-civil-engineering-list", "Accept": "application/vnd.github+json"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
            return data.get("stargazers_count", 0)
    except Exception as exc:
        print(f"WARNING: could not fetch stars for {repo}: {exc}", file=sys.stderr)
        return 0


def star_badge(repo):
    return f"![stars](https://img.shields.io/github/stars/{repo}?style=flat-square&label=%E2%98%85)"


def render_table(tools):
    lines = ["| Tool | What it is | License | Stars |", "|---|---|---|---|"]
    for t in tools:
        name_link = f"[{t['name']}]({t['homepage']})"
        lines.append(f"| {name_link} | {t['description']} | {t['license']} | {star_badge(t['repo'])} |")
    return "\n".join(lines)


def build():
    tools = json.loads(TOOLS_FILE.read_text())
    validate(tools)
    for t in tools:
        t["_stars"] = fetch_stars(t["repo"])

    parts = []
    parts.append("# Awesome Civil Engineering List\n")
    parts.append(
        "> A curated list of open-source tools, libraries, and resources for "
        "civil, structural, geotechnical, and geospatial engineering.\n"
    )
    parts.append(
        "![Awesome](https://awesome.re/badge.svg) "
        "![License: CC0](https://img.shields.io/badge/license-CC0--1.0-lightgrey.svg)\n"
    )

    parts.append("## Contents\n")
    for slug, title in CATEGORIES:
        anchor = title.lower().replace(" & ", "--").replace(" ", "-")
        parts.append(f"- [{title}](#{anchor})")
    parts.append("")

    for slug, title in CATEGORIES:
        cat_tools = sorted(
            [t for t in tools if t["category"] == slug],
            key=lambda t: (-t.get("_stars", 0)),
        )
        if not cat_tools:
            continue
        parts.append(f"## {title}\n")
        parts.append(render_table(cat_tools))
        parts.append("")

    parts.append("## Contributing\n")
    parts.append(
        "See [CONTRIBUTING.md](CONTRIBUTING.md) for the one-PR process to add a project.\n"
    )

    README_FILE.write_text("\n".join(parts) + "\n")
    print(f"Wrote {README_FILE}")


if __name__ == "__main__":
    build()
