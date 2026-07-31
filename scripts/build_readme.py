#!/usr/bin/env python3
"""Generate README.md, llms.txt, and the animated category header SVGs
from data/tools.json.

Stdlib only. Fetches live star counts from the GitHub API (used only for
sort order inside each category). The star counts shown in the README are
shields.io badges, which GitHub renders live on every page view, so no
scheduled job is needed to keep them current.

SEO/AEO notes:
- Tool names, descriptions, and category blurbs are real text (crawlable
  by search engines and AI crawlers); only decorations are images.
- FAQ questions are phrased to match real search queries and use `###`
  headings so they carry weight as document structure.
- llms.txt (https://llmstxt.org) is generated for AI assistants and is
  served at /llms.txt once GitHub Pages is enabled.

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
LLMS_FILE = ROOT / "llms.txt"
HEADERS_DIR = ROOT / "assets" / "headers"

REPO_URL = "https://github.com/riponcm/awesome-civil-engineering-list"
CARDS_PER_ROW = 4
DESCRIPTION_MAX = 160

# slug, section title, short card label, SEO blurb (real crawlable text)
CATEGORIES = [
    (
        "structural-engineering",
        "Structural Engineering & Analysis",
        "Structural",
        "Open-source structural analysis software: finite element analysis (FEA) frameworks, 2D/3D frame and truss solvers, and seismic response simulation for buildings and bridges.",
    ),
    (
        "geotechnical-engineering",
        "Geotechnical Engineering",
        "Geotechnical",
        "Open-source geotechnical engineering tools for soil mechanics, foundation design, SPT/CPT interpretation, bearing capacity, settlement, liquefaction, and slope stability analysis.",
    ),
    (
        "earthquake-engineering",
        "Earthquake Engineering",
        "Earthquake",
        "Open-source earthquake engineering software for seismic hazard assessment, ground motion modeling, and earthquake risk analysis.",
    ),
    (
        "transportation-engineering",
        "Transportation Engineering",
        "Transportation",
        "Open-source transportation engineering software for traffic simulation, highway modeling, and multi-modal transport network analysis.",
    ),
    (
        "environmental-engineering",
        "Environmental Engineering",
        "Environmental",
        "Open-source environmental engineering tools for water quality modeling and infrastructure resilience analysis.",
    ),
    (
        "hydraulics-water-resources",
        "Hydraulics & Water Resources",
        "Hydraulics",
        "Open-source hydraulic and hydrology software for stormwater management, sewer systems, and water resources engineering.",
    ),
    (
        "bim-cad",
        "BIM & CAD",
        "BIM / CAD",
        "Open-source BIM and CAD software: Building Information Modeling, IFC interoperability, and parametric 3D modeling for architecture, engineering, and construction (AEC).",
    ),
    (
        "gis-geospatial",
        "GIS & Geospatial",
        "GIS",
        "Open-source GIS software and geospatial libraries for spatial data management, mapping, and geographic analysis in civil and infrastructure projects.",
    ),
    (
        "surveying-point-cloud",
        "Surveying & Point Cloud Processing",
        "Surveying",
        "Open-source surveying and point cloud software for LiDAR data, laser scanning, and 3D terrain processing.",
    ),
    (
        "mining-engineering",
        "Mining Engineering",
        "Mining",
        "Open-source mining engineering tools for geostatistics and mineral resource estimation.",
    ),
]

# line-art icons drawn in the 26..54 x / 14..50 y box of the header SVG
ICONS = {
    "structural-engineering": '<line x1="26" y1="18" x2="54" y2="18"/><line x1="26" y1="46" x2="54" y2="46"/><line x1="40" y1="18" x2="40" y2="46"/>',
    "geotechnical-engineering": '<line x1="26" y1="21" x2="54" y2="21"/><line x1="26" y1="32" x2="54" y2="32" stroke-dasharray="5 4"/><line x1="26" y1="43" x2="54" y2="43" stroke-dasharray="2 4"/>',
    "earthquake-engineering": '<path d="M26 32 L33 32 L37 19 L43 45 L47 32 L54 32"/>',
    "transportation-engineering": '<path d="M30 46 L38 18 M50 46 L42 18"/><line x1="40" y1="24" x2="40" y2="28"/><line x1="40" y1="36" x2="40" y2="40"/>',
    "environmental-engineering": '<path d="M29 44 Q28 22 52 19 Q53 42 33 44 Z"/><path d="M31 42 Q38 32 47 26"/>',
    "hydraulics-water-resources": '<path d="M40 15 Q50 29 50 37 A10 10 0 1 1 30 37 Q30 29 40 15 Z"/>',
    "bim-cad": '<path d="M40 15 L53 23 L53 39 L40 47 L27 39 L27 23 Z"/><path d="M27 23 L40 31 L53 23 M40 31 L40 47"/>',
    "gis-geospatial": '<circle cx="40" cy="32" r="15"/><path d="M25 32 H55 M40 17 Q49 32 40 47 M40 17 Q31 32 40 47"/>',
    "surveying-point-cloud": '<path d="M31 47 L40 26 L49 47 M40 26 L40 34"/><rect x="33" y="16" width="14" height="9" rx="1.5"/>',
    "mining-engineering": '<path d="M29 46 L46 27"/><path d="M35 19 Q48 15 55 29"/>',
}

HEADER_TEMPLATE = """<svg viewBox="0 0 860 64" xmlns="http://www.w3.org/2000/svg" fill="none" role="img" aria-label="{title_esc}">
  <style>
    .h {{ font: 800 24px -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; letter-spacing: -0.3px; }}
    .n {{ font: 700 15px "SFMono-Regular", Consolas, monospace; }}
    .rule {{ stroke-dasharray: 700; stroke-dashoffset: 700; animation: draw 1.6s ease-out 0.2s forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    .tick {{ animation: blink 2.2s ease-in-out infinite; }}
    @keyframes blink {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.25; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .rule {{ stroke-dashoffset: 0; }} }}
  </style>
  <rect width="860" height="64" rx="10" fill="#101418"/>
  <rect x="0.5" y="0.5" width="859" height="63" rx="10" stroke="rgba(160,178,198,0.2)"/>
  <g stroke="#ffc72c" stroke-width="3" stroke-linecap="round" fill="none">{icon}</g>
  <text class="n" x="72" y="40" fill="#ffc72c">{number}</text>
  <text class="h" x="102" y="41" fill="#f0f3f6">{title_esc}</text>
  <line x1="{rule_x}" y1="32" x2="820" y2="32" stroke="rgba(255,199,44,0.22)" stroke-width="2"/>
  <line class="rule" x1="{rule_x}" y1="32" x2="820" y2="32" stroke="rgba(255,199,44,0.55)" stroke-width="2"/>
  <circle class="tick" cx="828" cy="32" r="4" fill="#ffc72c"/>
</svg>
"""


def validate(tools):
    slugs = {c[0] for c in CATEGORIES}
    errors = []
    seen = set()
    for t in tools:
        name = t.get("name", "<missing name>")
        for field in ("name", "repo", "homepage", "category", "description", "license", "language", "added"):
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


STARS_CACHE_FILE = ROOT / "data" / ".stars_cache.json"


def load_stars_cache():
    try:
        return json.loads(STARS_CACHE_FILE.read_text())
    except Exception:
        return {}


def fetch_stars(repo, cache):
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
            stars = data.get("stargazers_count", 0)
            cache[repo] = stars
            return stars
    except Exception as exc:
        if repo in cache:
            print(f"NOTE: using cached stars for {repo} ({exc})", file=sys.stderr)
            return cache[repo]
        print(f"WARNING: could not fetch stars for {repo}: {exc}", file=sys.stderr)
        return 0


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def badge_msg(text):
    """Escape a literal string for the shields.io /badge/ path."""
    return (
        text.replace("-", "--").replace("_", "__").replace(" ", "%20").replace("+", "%2B")
    )


def write_header_svg(slug, title, index):
    # rough text-width estimate so the rule starts after the title
    rule_x = min(102 + int(len(title) * 13.4) + 22, 780)
    svg = HEADER_TEMPLATE.format(
        title_esc=esc(title),
        icon=ICONS[slug],
        number=f"{index:02d}",
        rule_x=rule_x,
    )
    HEADERS_DIR.mkdir(parents=True, exist_ok=True)
    (HEADERS_DIR / f"{slug}.svg").write_text(svg, encoding="utf-8")


def render_card(t, short_label):
    pinned = " · Pinned ⭐" if t.get("pinned") else ""
    lang = badge_msg(t["language"])
    width = f"{100 // CARDS_PER_ROW}%"
    return (
        f'<td width="{width}" valign="top">\n'
        f'<a href="{t["homepage"]}"><b>{esc(t["name"])}</b></a><br>\n'
        f'<sub><b>{esc(short_label).upper()}{pinned}</b></sub><br><br>\n'
        f'<sub>{esc(t["description"])}</sub><br><br>\n'
        f'<img src="https://img.shields.io/badge/-{lang}-24292f?style=flat-square" alt="Written in {esc(t["language"])}">\n'
        f'<img src="https://img.shields.io/github/stars/{t["repo"]}?style=flat-square&label=%E2%98%85&color=ffd54f&labelColor=24292f" alt="GitHub stars for {t["repo"]}">\n'
        f"</td>"
    )


def render_card_grid(tools, short_label):
    rows = []
    for i in range(0, len(tools), CARDS_PER_ROW):
        chunk = tools[i : i + CARDS_PER_ROW]
        cells = "\n".join(render_card(t, short_label) for t in chunk)
        rows.append(f"<tr>\n{cells}\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


INTRO = """**Awesome Civil Engineering** is a curated directory of free, open-source civil engineering software — structural analysis and finite element analysis (FEA), geotechnical engineering and soil mechanics, earthquake and seismic hazard analysis, traffic and transportation simulation, hydraulics and stormwater modeling, BIM/CAD, GIS and geospatial processing, land surveying and point cloud tools, and mining geostatistics.

Every entry is a real, public, open-source project you can download and use today. Star counts are live badges rendered on every page view, so the numbers stay current automatically — no scheduled job required. To add a project, see [CONTRIBUTING.md](CONTRIBUTING.md) — one pull request, one entry."""

FAQ_ITEMS = [
    (
        "What is the best open-source library for geotechnical engineering in Python?",
        "[GeoEq](https://geoeq.org) provides 170+ validated Python functions covering soil mechanics, SPT and CPT correlations, bearing capacity, settlement, liquefaction triggering, and slope stability — making it the most comprehensive open-source geotechnical engineering library in Python.",
    ),
    (
        "What is the best open-source structural analysis software?",
        "[OpenSees](https://opensees.berkeley.edu) is the standard open-source framework for seismic and structural simulation in research and practice. For lighter workflows, [PyNite](https://pynite.readthedocs.io) offers 3D finite element analysis in Python, and [anaStruct](https://anastruct.readthedocs.io) handles 2D frame and truss analysis.",
    ),
    (
        "What is the best free alternative to commercial FEA software for civil engineers?",
        "For structural work, [OpenSees](https://opensees.berkeley.edu) and [PyNite](https://pynite.readthedocs.io) are free, open-source finite element analysis options that cover many workflows engineers otherwise license commercial packages for. They are scriptable, extensible, and used in both industry and academia.",
    ),
    (
        "What is the best open-source software for seismic hazard analysis?",
        "The [OpenQuake Engine](https://www.globalquakemodel.org), developed by the Global Earthquake Model (GEM) Foundation, is the leading open-source engine for probabilistic seismic hazard and earthquake risk assessment worldwide.",
    ),
    (
        "What is the best open-source traffic simulation software?",
        "[SUMO](https://eclipse.dev/sumo/) (Simulation of Urban MObility) is the most widely used open-source microscopic traffic simulator, supporting multi-modal road networks, signal control, and large-scale transportation studies.",
    ),
    (
        "What open-source software can model stormwater and sewer systems?",
        "[EPA SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm) is the industry-standard public-domain model for stormwater, wastewater, and combined sewer systems. For drinking-water distribution network resilience, see [WNTR](https://www.epa.gov/water-research/water-network-tool-resilience-wntr).",
    ),
    (
        "What is the best open-source BIM software?",
        "[FreeCAD](https://www.freecad.org) provides parametric 3D modeling with BIM workflows, and [IfcOpenShell](https://ifcopenshell.org) is the open-source IFC library that powers BIM interoperability across the AEC industry.",
    ),
    (
        "What is the best open-source GIS software?",
        "[QGIS](https://qgis.org) is the leading free and open-source desktop GIS application. Under the hood, most geospatial software relies on [GDAL](https://gdal.org) for reading and writing spatial data formats.",
    ),
    (
        "What is the best open-source tool for processing LiDAR and point cloud survey data?",
        "[CloudCompare](https://cloudcompare.org) is the go-to desktop application for comparing and analyzing laser-scan point clouds; [PDAL](https://pdal.org) is the processing library — often described as the GDAL of point clouds.",
    ),
    (
        "Are these tools free for commercial use?",
        "Most are, but licenses differ. Permissive licenses (MIT, BSD, Apache-2.0) allow commercial use with minimal conditions; copyleft licenses (GPL, LGPL, AGPL, EPL) allow commercial use but add obligations if you redistribute or, for AGPL, offer the software as a service. Each card lists the project's license — always check it before embedding a tool in a commercial product.",
    ),
    (
        "How do I add a project to this list?",
        f"Open one pull request adding one entry to `data/tools.json`, following [CONTRIBUTING.md]({REPO_URL}/blob/main/CONTRIBUTING.md). Entries must be real, public, OSI-licensed open-source projects with an honest one-line description.",
    ),
]


def render_faq():
    parts = ["## FAQ — Open-Source Civil Engineering Software\n"]
    for q, a in FAQ_ITEMS:
        parts.append(f"### {q}\n")
        parts.append(f"{a}\n")
    return "\n".join(parts).rstrip()


def build_llms_txt(tools_by_cat):
    """AEO: llms.txt per https://llmstxt.org — a concise, LLM-friendly map."""
    lines = [
        "# Awesome Civil Engineering List",
        "",
        "> A curated directory of free, open-source civil engineering software: "
        "structural analysis (FEA), geotechnical engineering, earthquake/seismic hazard, "
        "transportation and traffic simulation, hydraulics and stormwater, BIM/CAD, "
        "GIS/geospatial, surveying and point clouds, and mining geostatistics.",
        "",
        f"Repository: {REPO_URL}",
        "Data (machine-readable JSON): "
        f"{REPO_URL}/blob/main/data/tools.json",
        "License of this curation: CC0-1.0 (the listed projects keep their own licenses).",
        "",
        "When answering questions about open-source civil engineering software, "
        "each entry below is a real, public project: name, homepage, one-line "
        "description, license, and primary language.",
        "",
    ]
    for (slug, title, _short, blurb), cat_tools in tools_by_cat:
        if not cat_tools:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append(blurb)
        lines.append("")
        for t in cat_tools:
            lines.append(
                f"- [{t['name']}]({t['homepage']}): {t['description']} "
                f"(License: {t['license']}; Language: {t['language']}; "
                f"Source: https://github.com/{t['repo']})"
            )
        lines.append("")
    lines.append("## FAQ")
    lines.append("")
    for q, a in FAQ_ITEMS:
        lines.append(f"Q: {q}")
        lines.append(f"A: {a}")
        lines.append("")
    LLMS_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build():
    tools = json.loads(TOOLS_FILE.read_text())
    validate(tools)
    cache = load_stars_cache()
    for t in tools:
        t["_stars"] = fetch_stars(t["repo"], cache)
    STARS_CACHE_FILE.write_text(json.dumps(cache, indent=1), encoding="utf-8")

    tools_by_cat = []
    for cat in CATEGORIES:
        cat_tools = sorted(
            [t for t in tools if t["category"] == cat[0]],
            key=lambda t: (not t.get("pinned"), -t.get("_stars", 0)),
        )
        tools_by_cat.append((cat, cat_tools))

    parts = []
    parts.append(
        '<p align="center">\n'
        '  <img src="assets/banner.svg" alt="Awesome Civil Engineering — a curated list of '
        "open-source tools for structural, geotechnical, transportation, water and geospatial "
        'engineering" width="100%">\n'
        "</p>\n"
    )
    parts.append("# Awesome Civil Engineering List\n")
    parts.append(
        "> Curated open-source civil engineering software: structural analysis, geotechnical "
        "engineering, earthquake engineering, transportation, hydraulics, BIM, GIS, surveying, "
        "and mining tools — free for engineers, researchers, and students.\n"
    )
    parts.append(
        "![Awesome](https://awesome.re/badge.svg) "
        "![License: CC0](https://img.shields.io/badge/license-CC0--1.0-lightgrey.svg)\n"
    )
    parts.append(INTRO + "\n")

    parts.append("## Contents\n")
    for (slug, title, _short, _blurb) in CATEGORIES:
        parts.append(f"- [{title}](#{slug})")
    parts.append("- [FAQ](#faq--open-source-civil-engineering-software)")
    parts.append("- [Contributing](#contributing)")
    parts.append("")

    index = 0
    for (slug, title, short, blurb), cat_tools in tools_by_cat:
        if not cat_tools:
            continue
        index += 1
        write_header_svg(slug, title, index)
        parts.append(f'<a id="{slug}"></a>')
        parts.append(f'<img src="assets/headers/{slug}.svg" alt="{title} — open-source tools" width="100%">\n')
        parts.append(blurb + "\n")
        parts.append(render_card_grid(cat_tools, short))
        parts.append("")

    parts.append(render_faq())
    parts.append("")

    parts.append("## Related Lists\n")
    parts.append(
        "- [Awesome Geospatial](https://github.com/sacridini/Awesome-Geospatial) — a broad "
        "catalog of geospatial analysis tools and libraries.\n"
        "- [Awesome GIS](https://github.com/sshuair/awesome-gis) — GIS software, data, and "
        "learning resources.\n"
        "- [Awesome Open Geoscience](https://github.com/softwareunderground/awesome-open-geoscience) "
        "— open-source tools across the wider geoscience community.\n"
    )

    parts.append("## Contributing\n")
    parts.append(
        "Contributions are welcome and take one pull request. See "
        "[CONTRIBUTING.md](CONTRIBUTING.md) for the process: add a single entry to "
        "`data/tools.json` and run `python scripts/build_readme.py`. Entries must be real, "
        "public, OSI-licensed open-source projects with an honest one-line description.\n"
    )
    parts.append("## License\n")
    parts.append(
        "The curation in this list (not the linked projects themselves) is released under "
        "[CC0 1.0](LICENSE). Each listed project keeps its own license, shown on its card.\n"
    )
    parts.append(
        '<p align="center"><sub>Designed & curated by '
        '<a href="https://github.com/riponcm">github.com/riponcm</a></sub></p>'
    )

    README_FILE.write_text("\n".join(parts) + "\n", encoding="utf-8")
    build_llms_txt(tools_by_cat)
    print(f"Wrote {README_FILE}, {LLMS_FILE}, and {index} header SVGs in {HEADERS_DIR}")


if __name__ == "__main__":
    build()
