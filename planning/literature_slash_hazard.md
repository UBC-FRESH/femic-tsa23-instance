# Literature notes: the clearcut slash hazard spike, and mapping the literature

Two things are recorded here: what the literature says about the post-clearcut slash
hazard spike (and the parameters chosen for the model), and the plan for building a
citation graph around the thesis bibliography.

## Part 1 — The CC slash spike

### The question

`feature.FuelHazard` had baseline 1.0, FT 0.4, FB 0.05 and SF 0.2, but `cc_pl` (fresh
clearcut, no treatment) read baseline 1.0. That says a newly harvested block burns no
worse than an old forest, which biases every treatment comparison: it makes the untreated
baseline look safer than it is.

### Magnitude: derived from FBP, not guessed

The Canadian FBP System already represents slash as fuel types **S-1 (light), S-2
(moderate), S-3 (heavy)**. Running our own FBP implementation at the three fire-weather
scenarios gives head-fire rate of spread (m/min):

| fuel | median | p90 | extreme |
| --- | ---: | ---: | ---: |
| C-3 (standing pine) | 1.92 | 26.87 | 62.47 |
| C-7 (standing Douglas-fir) | 1.48 | 10.00 | 19.91 |
| S-1 (light slash) | 9.35 | 35.35 | 57.10 |
| S-2 (moderate slash) | 3.90 | 18.53 | 30.57 |
| S-3 (heavy slash) | 4.62 | 41.24 | 67.17 |

Ratio to the mean standing-timber rate:

| slash | median | p90 | extreme |
| --- | ---: | ---: | ---: |
| S-1 | **5.50** | 1.92 | 1.39 |
| S-2 | 2.29 | 1.00 | 0.74 |
| S-3 | 2.71 | 2.24 | 1.63 |

Two implications:

1. The spike is **weather-dependent** and collapses at extreme weather, because a
   standing C-3 already spreads at 62 m/min. A constant multiplier — which is what
   `TREATMENT_HAZARD` uses everywhere — cannot represent that. This is a recorded model
   limitation, not a solved problem.
2. A central value of **2.0×** is inside the S-2/S-3 range at median-to-p90 weather,
   which is where the treatment ranking actually moves (E9/E10).

Method: `cffdrs.fbp.FBPInput` at the FFMC/BUI/WS of `runtime/fire/fwi_scenarios.csv`,
elevation 1000 m, cc/cbh/cfl at the values used by `scripts/fbp_stand_curves.py`.

### Duration: the weak evidence

- **BC regulatory frame:** hazard assessment and abatement on 6- and 12-month cycles
  under the Wildfire Regulation. This is an obligation schedule, not a decay curve.
- **Post-fire salvage logging:** fine fuel loadings **+160% to +237%**, persisting about
  **22 years**; slash-loading differences dissipate after about **13 years** (USDA
  synthesis of postfire-logging studies). Salvage logging is a related but distinct
  disturbance — do not transfer the number to green-tree harvest without saying so.
- **Green harvest:** genuinely unsettled. This is the honest gap.

### Counter-evidence, which must not be buried

A national quasi-experimental study finds harvested stands carry a **~28% lower
first-fire hazard** than matched unharvested neighbours (hazard ratio 0.72), persistent to
about 29 years. At the stand scale, "harvest creates slash hazard" is contested: harvest
removes crown fuel and the stand regenerates, and abatement is applied.

Consequence for the thesis: the slash spike is a **scenario**, not a fact. The defensible
move is to parameterize it and test whether the treatment ranking changes.

### Parameters chosen

| parameter | value | why |
| --- | ---: | --- |
| multiplier | **2.0×** | inside the S-2/S-3 FBP range at median-p90 weather |
| full-intensity window | **3 years** | long enough to matter, short enough to sit inside the BC abatement cycle |
| decay to baseline | **10 years** | between the 1-2 year regulatory cycle and the ~13 year loading evidence |

Curve: `(0, 2.0) (3, 2.0) (10, 1.0) (400, 1.0)`, applied to state `cc_pl` only — the
`*_ft` and `sf_*` variants already carry their own treatment hazard, and `fb_cc_pl` is a
fuel break, not slash.

Implemented in `scripts/complete_hazard_feature.py` (`CC_SLASH_MULTIPLIER`,
`CC_SLASH_FULL_YEARS`, `CC_SLASH_DECAY_YEARS`), and the code comment points here.

### What this changes, and what it does not

- 20,530 `cc_pl` tracks now carry the 2.0 → 1.0 curve.
- **The bridge oracle is unchanged**: 471 / 765 / 913 blocks, verified by re-running
  `export_bridge_footprint.py` after the rebuild. The account uses hazard only for
  membership (`> 0.5`), and the spike only raises a value that was already above the
  threshold.
- **The spread model can now read it.** `load_block_hazard` plus
  `run_matched_footprint.py --hazard-dataset` replaces the flat multiplier with the
  per-block feature. The equivalence gate reproduces the published barrier run exactly
  (19,640.448328143004) when the dataset is the pre-slash one.
- **With the slash state active the ranking is unchanged** — barrier < clumped < random on
  mean and p90 — but burned area rises ~59% and the arrangement effect grows from 3.2% to
  4.2%. Details in E15. The hazard-fed path is opt-in; the default is still the constants,
  so the recorded E2/E7/E9/E10 numbers stand as they were.

### Sensitivity: run, and the answer is reassuring

`scripts/slash_sensitivity.py` varies the multiplier {1.5, 2.0, 3.0, 5.0} and the decay
{5, 10, 20} years across the three patterns. **The ranking holds in all 12 combinations**
(barrier < clumped < random), with the pattern spread between 3.6% and 4.7% — against 3.2%
with no slash state. A 3.3x range in the contested parameter moves the effect by about one
percentage point. E16.

The first run of that script produced the opposite ranking with a 40% spread, which was a
harness bug (the treated override leaked between patterns), not a result. It is recorded
because the wrong answer looked plausible.

What remains a limitation: `TREATMENT_HAZARD` is constant while FBP's slash-to-timber
ratio is weather-dependent (5.5x at median, 1.4x at extreme). A weather-conditioned hazard
is the honest next step if that matters; the sensitivity above says the arrangement
conclusion does not depend on it.

## Part 2 — Mapping the literature space

### What exists off the shelf

**`litstudy`** (Apache-2.0, PyPI 1.0.6, 2023) is the closest Python package: reads BibTeX,
CrossRef, Semantic Scholar and Scopus, builds bibliographic networks, and does NLP topic
discovery. Alternatives: `pybliometrics` (Scopus, needs a key), `metaknowledge`,
`ScientoPy`, and VOSviewer (GUI).

We did not use it because the seed here is a **local bibliography**, and litstudy is built
around notebook-driven source queries. A versioned script with a fixed seed is the better
artifact for a thesis.

### What we built

`scripts/literature_graph.py`:

1. Collects every `.bib` entry from the four writing repos — **257 unique keys** across
   Proposal, Thesis, Paper-1 and Paper-2.
2. Resolves each against OpenAlex (DOI first, then title), recording the match confidence.
3. Pulls each work's `referenced_works`, so the graph covers what the thesis cites and
   what *that* literature cites.
4. Writes `runtime/literature/{seeds,nodes,edges}.csv`, `graph.json`, and `summary.md`
   (top works by in-degree, OpenAlex topic mix, publication years).

### Status and the design change

The first design resolved titles through OpenAlex directly and died on **HTTP 429**: the
free-text search endpoint rate-limits hard from a shared host. The resolver now goes
**Crossref first** (`query.bibliographic`, generous limits, no key) and then fetches
`referenced_works` from OpenAlex **by DOI**, one cheap lookup per work.

### What the smoke test revealed, and it matters

Eight entries, two resolved. The six failures are not a matching bug:

| entry | why it fails |
| --- | --- |
| 100 Mile House TSA TSR Data Package | BC government data package |
| FireSmart: Protecting your Community from Wildfire | programme guide |
| 2022 Fuel Management Prescription Guidance | BC guidance |
| 2024 Fuel Management Practices Guide | BC guidance |
| Forest Inventory | textbook/reference |
| Wildland Urban Interface Risk Class Maps | provincial mapping product |

Crossref and OpenAlex index journal literature. **A large share of this thesis's evidence
base is grey literature** — provincial guides, data packages, mapping products — and a
citation graph built on those sources will systematically miss it. That grey literature
is arguably the operative evidence for a policy thesis, so it needs its own track rather
than being treated as a gap to fill with more searching.

Resolution rate on the full set is therefore expected to be modest (35 entries carry
DOIs outright; a further share will match through Crossref). The graph maps the
peer-reviewed core; it does not map the grey literature, and should not be presented as
if it does.

To run:

```bash
python scripts/literature_graph.py --repos-root /path/to/workspace --out runtime/literature
```

### What the graph is for

- Find which works the thesis leans on repeatedly (in-degree inside the seed set).
- See which topic clusters the citation neighbourhood actually contains, so a literature
  review can be aimed rather than exhaustive.
- Answer questions like this one faster: "who has measured post-harvest slash hazard and
  how" becomes a lookup in `nodes.csv` rather than a fresh search.

It is a map, not evidence. Any claim still has to be read in the source.
