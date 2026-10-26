"""Per-block burn probability averaged over the fire-weather ladder.

The risk-weighted schedule depends on where fire is likely, and a single scenario decides
that. This runs the spread model under every scenario in the ladder with **no treatment**
(applying the untreated rate of spread to every block, including stands whose silvicultural
state carries a thinning), and averages the per-block ignition-to-burn probability.

Averaging is over scenarios, not seeds: the point is weather robustness, and the seed is
fixed so the comparison across scenarios is like-for-like.

Usage::

    python scripts/burn_probability_map.py \
        --out runtime/fire/burn_probability_mean.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_spread import (  # noqa: E402
    _adjacency,
    _block_fuel_types,
    simulate_fast,
)


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--fuel-types", type=Path, default=Path("runtime/fire/fbp_stand_curves.csv"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument("--scenarios", default="", help="comma-separated; default is every scenario in the curve file")
    parser.add_argument("--ignitions", type=int, default=200)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--wind-dir", type=float, default=225.0, dest="wind_dir")
    parser.add_argument("--out", type=Path, default=Path("runtime/fire/burn_probability_mean.json"))
    parser.add_argument("--detail", type=Path, default=None, help="optional per-scenario CSV")
    args = parser.parse_args()

    available = sorted(pd.read_csv(args.fuel_types, usecols=["scenario"]).scenario.unique())
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()] or available
    print(f"scenarios: {len(scenarios)} -> {scenarios}")

    adj = _adjacency(args.topology)
    totals: dict[int, float] = {}
    detail_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        frame = _block_fuel_types(args.blocks, args.fuel_types, scenario, 60).copy()
        # Untreated baseline: every block spreads at its own rate. _block_fuel_types marks
        # thinned states as treated, which would seed a treatment effect into a risk map.
        frame["treated"] = False
        frame["ros_eff"] = frame["ros_m_per_min"]
        result = simulate_fast(
            blocks=frame,
            adj=adj,
            ignitions=args.ignitions,
            duration_min=480.0,
            seed=args.seed,
            wind_deg=args.wind_dir,
        )
        per_block = {int(k): float(v) for k, v in result["burn_probability"].items()}
        for block, value in per_block.items():
            totals[block] = totals.get(block, 0.0) + value
        burned = sum(v for v in per_block.values() if v > 0)
        detail_rows.append({
            "scenario": scenario,
            "mean_burned_ha": round(result["mean_area_burned_ha"], 1),
            "p90_burned_ha": round(result["p90_area_burned_ha"], 1),
            "blocks_burned": burned,
            "mean_probability": round(float(np.mean(list(per_block.values()))), 5),
        })
        print(f"  {scenario:8s} mean burned {result['mean_area_burned_ha']:>10.0f} ha  "
              f"mean p {np.mean(list(per_block.values())):.4f}")

    mean_probability = {str(block): value / len(scenarios) for block, value in totals.items()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(
        {
            "scenarios": scenarios,
            "ignitions": args.ignitions,
            "wind_deg": args.wind_dir,
            "treatment": "none",
            "burn_probability": mean_probability,
        },
        indent=1,
    ))
    if args.detail is not None:
        args.detail.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(detail_rows).to_csv(args.detail, index=False)
        print(f"wrote {args.detail}")

    values = np.array(list(mean_probability.values()))
    print(f"\nblocks: {len(values):,} | nonzero: {(values > 0).sum():,} | "
          f"mean {values.mean():.4f} | p95 {np.quantile(values, 0.95):.4f}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
