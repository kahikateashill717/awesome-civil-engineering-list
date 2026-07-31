# Contributing

Thanks for considering adding a project to this list! To keep it useful, entries must meet a few basic criteria:

- The project must be public, open-source, and have an OSI-approved (or public-domain) license.
- The project must be actively maintained (a commit or release within the last ~12 months) unless it's a stable, widely-used reference implementation.
- The description must be a single, honest sentence describing what the tool does -- no marketing language.
- One project per pull request, please.

## How to add an entry

1. Fork this repository.
2. Add an object to `data/tools.json` with these fields: `name`, `repo` (in `owner/repo` form), `homepage`, `category` (must match one of the existing category slugs), `description` (140 characters or fewer), `license`, and `added` (today's date, YYYY-MM-DD).
3. Add a matching row to the relevant category table in `README.md` so the two files stay in sync.
4. Open a pull request describing the project and, if it's your own project, say so -- full disclosure is welcome and won't count against you.

## Categories

- `structural-engineering` -- Structural Engineering & Analysis
- `geotechnical-engineering` -- Geotechnical Engineering
- `bim-cad` -- BIM & CAD
- `gis-geospatial` -- GIS & Geospatial
- `hydraulics-water-resources` -- Hydraulics & Water Resources

If your project doesn't fit an existing category, propose a new one in your pull request description.
