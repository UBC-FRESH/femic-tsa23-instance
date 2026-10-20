"""Sensitivity screen for the matched-footprint bridge experiment.

Recon, not a claim: sweeps the knobs that could flip the arrangement result so the
student can see where the cliffs are before choosing a direction. Every cell is the
same fixed footprint and the same shared ignition set, so only the swept knobs move.

Knobs:

- treated fraction inside the footprint: 0.05, 0.10, 0.15, 0.20
- fire weather: median, p90, extreme
- treated ROS multiplier: 0.05 (FB hazard), 0.30 (published bridge), 1.00 (control)
- seed: 1-3

Usage::

    python scripts/sensitivity_screen.py --out runtime/fire/sensitivity_screen.csv
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_matched_footprint import run  # noqa: E402

DENSITIES = (0.05, 0.10, 0.15, 0.20)
SCENARIOS = ("median", "p90", "extreme")
FACTORS = (0.05, 0.30, 1.00)
SEEDS = (1, 2, 3)
PATTERNS = ("barrier", "clumped", "random")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--fuel-types", type=Path, default=Path("runtime/fire/fbp_stand_curves.csv"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument("--out", type=Path, default=Path("runtime/fire/sensitivity_screen.csv"))
    parser.add_argument("--footprint-ha", type=float, default=20000.0)
    parser.add_argument("--ignitions", type=int, default=40)
    parser.add_argument("--densities", default="0.05,0.10,0.15,0.20")
    parser.add_argument("--scenarios", default="median,p90,extreme")
    parser.add_argument("--factors", default="0.05,0.30,1.00")
    parser.add_argument("--seeds", default="1,2,3")
    args = parser.parse_args()

    densities = tuple(float(x) for x in args.densities.split(",") if x.strip())
    scenarios = tuple(x.strip() for x in args.scenarios.split(",") if x.strip())
    factors = tuple(float(x) for x in args.factors.split(",") if x.strip())
    seeds = tuple(int(x) for x in args.seeds.split(",") if x.strip())
    rows: list[dict[str, object]] = []
    cells = list(itertools.product(densities, scenarios, factors, seeds))
    for i, (density, scenario, factor, seed) in enumerate(cells, 1):
        result = run(
            blocks_path=args.blocks,
            fuel_types=args.fuel_types,
            topology=args.topology,
            footprint_ha=args.footprint_ha,
            treat_fraction=density,
            treatment="fb",
            scenario=scenario,
            ignitions=args.ignitions,
            duration_min=480.0,
            wind_deg=225.0,
            seed=seed,
            footprint_seed=1,
            treat_factor=factor,
        )
        for pattern, payload in result["patterns"].items():
            rows.append(
                {
                    "density": density,
                    "scenario": scenario,
                    "factor": factor,
                    "seed": seed,
                    "pattern": pattern,
                    "treated_ha": round(payload["treated_ha"], 1),
                    "mean_burned_ha": round(payload["mean_burned_ha"], 1),
                    "p90_burned_ha": round(payload["p90_burned_ha"], 1),
                    "dir_largest": payload["directed_largest_reach"],
                    "cone60_largest_ha": round(payload["cone60_largest_component_ha"], 0),
                }
            )
        print(f"[{i}/{len(cells)}] density {density:.2f} {scenario:8s} factor {factor:.2f} seed {seed}")

    frame = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)

    def order(group: pd.DataFrame, metric: str) -> tuple[str, ...]:
        return tuple(group.sort_values(metric)["pattern"])

    summary = []
    for (density, scenario, factor, seed), group in frame.groupby(
        ["density", "scenario", "factor", "seed"]
    ):
        mean_order = order(group, "mean_burned_ha")
        p90_order = order(group, "p90_burned_ha")
        means = group.set_index("pattern")["mean_burned_ha"]
        p90s = group.set_index("pattern")["p90_burned_ha"]
        summary.append(
            {
                "density": density,
                "scenario": scenario,
                "factor": factor,
                "seed": seed,
                "mean_order": "/".join(p[0] for p in mean_order),
                "p90_order": "/".join(p[0] for p in p90_order),
                "mean_gap_pct": round((means.max() - means.min()) / means.mean() * 100, 2),
                "p90_gap_pct": round((p90s.max() - p90s.min()) / p90s.mean() * 100, 2),
            }
        )
    summary_frame = pd.DataFrame(summary)
    summary_frame.to_csv(args.out.with_name(args.out.stem + "_orders.csv"), index=False)

    print("\n=== p90: barrier best, share of cells ===")
    pivot = summary_frame.assign(barrier_best=lambda d: d["p90_order"].str.startswith("b"))
    pivot = pivot.pivot_table(
        index=["density", "factor"], columns="scenario", values="barrier_best", aggfunc="mean"
    )
    print((pivot * 100).round(0).to_string())

    print("\n=== p90 effect size, % (mean over scenarios and seeds) ===")
    size = summary_frame.pivot_table(
        index="density", columns="factor", values="p90_gap_pct", aggfunc="mean"
    )
    print(size.round(1).to_string())

    print("\n=== mean effect size, % (mean over scenarios and seeds) ===")
    size = summary_frame.pivot_table(
        index="density", columns="factor", values="mean_gap_pct", aggfunc="mean"
    )
    print(size.round(1).to_string())

    print(f"\nwrote {args.out} and {args.out.with_name(args.out.stem + '_orders.csv')}")


if __name__ == "__main__":
    main()
