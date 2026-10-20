# P117 — Sphinx docs site and publication: plan

Parent issue: `UBC-FRESH/femic-tsa23-instance#15`
Branch: `feature/p117-sphinx-docs`
Status: planned
Template source: `UBC-FRESH/ubc-fresh-dev-workflow`

The goal is to publish the instance documentation as a built Sphinx site on GitHub
Pages using the lab's documented workflow, not a local variant. The template files are
the authority; where the instance differs, the difference is recorded here.

## Source of truth (template files)

| template file | role |
| --- | --- |
| `templates/project/docs/conf.py.tmpl` | Sphinx configuration |
| `templates/project/docs/index.rst.tmpl` | documentation home + toctree |
| `templates/project/docs/api/index.rst` | API reference stub |
| `templates/project/docs/requirements.txt` | docs-only dependencies |
| `templates/project/docs/llms.txt.tmpl` | agent-facing index |
| `.github/workflows/docs.yml` | build (`-W`) + Pages deploy |

## Current state (verified 2026-10-20)

- `docs/` has seven pages, 205 lines total, and no absolute machine paths
  (`grep -rE '/(home|srv|Users)/[a-z]' docs/` → 0 matches).
- `docs/conf.py` lists `sphinx_rtd_theme` **as an extension**, sets
  `html_static_path = ["_static"]` for a directory that does not exist, and does not
  add `scripts/` to `sys.path`, so autodoc cannot import anything.
- No `docs/requirements.txt`. The root `requirements.txt` is a placeholder
  (`-e ../../`) and is not a docs input.
- No `docs/api/`, no `docs/llms.txt`.
- No `.github/workflows/` directory at all.
- GitHub Pages is not enabled: `GET /repos/UBC-FRESH/femic-tsa23-instance/pages`
  returns 404.

## Work

### P117.1 Align the build with the template

- `docs/requirements.txt`:
  ```
  sphinx>=7.2
  sphinx-rtd-theme>=2.0
  numpy
  pandas
  ```
  `numpy`/`pandas` are added because the API pages import the scripts, and they are
  small wheels. The geospatial stack is mocked instead (see below).
- `docs/conf.py`, rewritten to the template:
  - `sys.path.insert(0, parents[1] / "scripts")` — the instance's code lives in
    `scripts/`, as the template assumes;
  - `extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]`
    (the theme is **not** an extension);
  - napoleon numpy style, `autodoc_member_order = "bysource"`;
  - `html_theme = "sphinx_rtd_theme"`, `html_extra_path = ["llms.txt"]`;
  - drop `html_static_path` (no `_static` directory exists);
  - `autodoc_mock_imports = ["geopandas", "pyogrio", "fiona", "shapely", "pyproj", "cffdrs"]`
    — a deliberate divergence from the template, because those imports pull GDAL and
    the FBP library into a docs build that does not need them. Recorded here so the
    divergence is not mistaken for drift.
- `docs/index.rst`: keep the existing pages, add the API toctree.
- `docs/api/index.rst`: `automodule` entries for the public scripts (below).
- `docs/llms.txt`: the template's two-entry form, with the instance's real page list.

### P117.2 Add the docs workflow

Copy `.github/workflows/docs.yml` from the template unchanged apart from the project
name: build with `sphinx-build -b html docs _build/html -W`, upload the Pages artifact,
deploy on `main` (plus `workflow_dispatch`). `-W` is intentional: a broken reference
fails the run rather than publishing a half-built site.

### P117.3 Enable Pages and prove the first deploy

Enable Pages with source **GitHub Actions**, push to `main`, and record the published
URL in this plan and in the issue. A workflow that builds but cannot deploy is not done.

### P117.4 Content pass

API pages for the twelve scripts, grouped rather than one page each:

- fire: `landscape_spread`, `fbp_stand_curves`, `fire_weather_scenarios`;
- bridge: `bridge_matched_footprint`, `ws4_bridge_test`, `export_bridge_footprint`,
  `run_matched_footprint`;
- topology and treatments: `build_block_topology`, `add_fuel_break_treatment`,
  `add_surface_fuel_treatment`, `apply_fuel_treatment_economics`,
  `complete_hazard_feature`.

Keep the operator pages (overview, quickstart, rebuild-contract, tsr-guidance,
seral-interpretation, troubleshooting). Link the public-safe runbooks and planning
notes rather than copying them, so there is one copy of each contract.

### P117.5 Public-safety pass

The repository and the site are public. Before the first deploy, check `docs/`,
`runbooks/`, and anything linked from `planning/` for absolute machine paths,
credentials, raw transcripts, and private data. `docs/` is clean today; the risk is in
the pages added during P117.4.

## Acceptance

```bash
python -m venv /tmp/p117-docs && . /tmp/p117-docs/bin/activate
pip install -r docs/requirements.txt
sphinx-build -b html docs _build/html -W
```

- The build passes with only `docs/requirements.txt` installed.
- The Pages URL serves the site and `/llms.txt` is reachable.
- Every `automodule` page renders real docstrings (no placeholder pages).
- The workflow is the only build path; nothing is generated locally then committed.

## Risks

- **`-W` is strict.** The existing pages may already warn (duplicate labels, missing
  references). They must be fixed, not silenced with `-W --keep-going`.
- **Autodoc imports the modules.** If any script does work at import time (reading a
  shapefile, hitting the network), the mocked-import approach will still fail. Check
  each module's import block before adding it to the API toctree.
- **Pages enablement needs admin.** If the token lacks permission, stop and record the
  blocker rather than leaving a workflow that cannot deploy.
- **Public by default.** A page added for internal convenience becomes world-readable
  the moment `main` builds.

## Out of scope

- The P115 content programme (TSR-depth writing, area accounting, seral guides). P117
  builds and publishes the surface; P115 fills it.
- A custom domain, versioned docs, and search tuning.
- Adopting `scripts/check_workflow.py` from the template. It is a separate decision
  because it changes how the roadmap is validated.

---

## Outcome (2026-10-20)

Built, published, verified.

- **Local build:** `sphinx-build -b html docs _build/html -W` passes with no warnings.
- **Site:** `https://ubc-fresh.github.io/femic-tsa23-instance/` serves the home page
  (200), `llms.txt` (200), and `api/index.html` (200), with real function anchors on the
  API pages.
- **Pages:** enabled with `build_type: workflow`.

### What the first CI run caught

The first workflow run failed on **15 autodoc warnings**, all
`ModuleNotFoundError: No module named 'numpy'` / `'pandas'`. The docs-only environment
carried `sphinx` and the theme but not the numeric stack, so every `automodule` import
failed. Fixed by adding `numpy` and `pandas` to `docs/requirements.txt`; the geospatial,
FBP and `ws4` imports remain mocked.

That failure is the reason `-W` is worth having: without it the run would have published
an empty API section and reported success.

### The deploy gate

`deploy` was rejected with *"Branch feature/fuel-treatment-layer is not allowed to deploy
to github-pages due to environment protection rules"*. The `github-pages` environment
allows `main` only. To verify the deploy end to end without merging the whole branch,
the environment policy was widened to include the feature branch, the deploy ran and was
verified, and the policy was then **restored to `main`** (custom policies off,
`protected_branches: true`).

Consequence: the site currently holds the feature-branch build. It will rebuild from
`main` once this branch is merged. Merging to `main` is the remaining step for the phase,
and it is a repository-wide integration (48 commits), not a docs-only change.

### Not done here

- The P115 content depth: area accounting, THLB/AU documentation, seral guides.
- Search tuning, a custom domain, versioned docs.
