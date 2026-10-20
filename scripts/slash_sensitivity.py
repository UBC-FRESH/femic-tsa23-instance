"""Sensitivity of the arrangement ranking to the clearcut slash parameters.

The hazard feature gives `cc_pl` a slash spike (`CC_SLASH_*` in
`complete_hazard_feature.py`), chosen inside the FBP S-1/S-3 range with a decay window
that the literature does not pin down. This script varies both and asks the only question
that matters for the thesis: does the arrangement ranking move?

Each combination rebuilds the per-block hazard in memory (no dataset rebuild), then runs
the three published landscape patterns on their own treated masks.

Output: ``runtime/fire/slash_sensitivity.csv`` plus a printed ranking table.

Usage::

    python scripts/slash_sensitivity.py --ignitions 50
"""

from __future__ import annotations

import argparse
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

PATTERNS = ("barrier", "clumped", "random")
RE_STATE = r"SILV_STATE\(([^)]*)\)"


def _state_map(dataset: Path) -> dict[int, str]:
    """Return block id -> the state of its row with the largest offset (the current one)."""
    import re

    blocks = pd.read_parquet(dataset / "blocks.parquet")
    tracks = pd.read_parquet(dataset / "tracks.parquet").set_index("track_id")["name"]
    blocks = blocks.assign(
        state=blocks["track_id"].map(tracks).map(
            lambda name: (re.search(RE_STATE, str(name)).group(1) if re.search(RE_STATE, str(name)) else "")
        )
    )
    current = blocks.sort_values("offset").groupby("block_id").tail(1)
    return dict(zip(current["block_id"].astype(int), current["state"]))


def _hazard(dataset: Path, multiplier: float, decay_years: float, full_years: float) -> dict[int, float]:
    """Per-block hazard with a parameterized slash spike on `cc_pl` blocks."""
    blocks = pd.read_parquet(dataset / "blocks.parquet")
    features = pd.read_parquet(dataset / "features.parquet")
    curves = pd.read_parquet(dataset / "curves.parquet")
    states = _state_map(dataset)
    hazard_rows = features[features["label"] == "feature.FuelHazard"][["track_id", "curve_id"]]
    merged = blocks.merge(hazard_rows, on="track_id", how="left")
    table = curves.set_index(["curve_id", "x"])["y"].to_dict()

    records = []
    for row in merged.itertuples(index=False):
        curve_id = getattr(row, "curve_id", None)
        value = 1.0 if pd.isna(curve_id) else table.get((curve_id, float(row.offset)),
                                                        table.get((curve_id, 0.0), 1.0))
        state = states.get(int(row.block_id), "")
        if state == "cc_pl":
            age = float(row.offset)
            if age <= full_years:
                value = multiplier
            elif age >= decay_years:
                value = 1.0
            else:
                span = max(decay_years - full_years, 1e-9)
                value = multiplier + (1.0 - multiplier) * (age - full_years) / span
        records.append((int(row.block_id), float(row.area_ha), float(value)))

    frame = pd.DataFrame(records, columns=["block_id", "area_ha", "hazard"])
    weighted = frame.groupby("block_id").apply(
        lambda g: float((g.hazard * g.area_ha).sum() / g.area_ha.sum())
        if g.area_ha.sum() > 0 else float(g.hazard.mean()),
        include_groups=False,
    )
    return {int(b): float(v) for b, v in weighted.items()}


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--fuel-types", type=Path, default=Path("runtime/fire/fbp_stand_curves.csv"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_fb_haz"))
    parser.add_argument("--schedules", type=Path, default=Path("runtime/fire"))
    parser.add_argument("--ignitions", type=int, default=50)
    parser.add_argument("--out", type=Path, default=Path("runtime/fire/slash_sensitivity.csv"))
    args = parser.parse_args()

    frame = _block_fuel_types(args.blocks, args.fuel_types, "p90", 60).copy()
    adj = _adjacency(args.topology)
    multipliers = (1.5, 2.0, 3.0, 5.0)
    decays = (5.0, 10.0, 20.0)
    rows = []
    for multiplier in multipliers:
        for decay in decays:
            hazard = _hazard(args.dataset, multiplier, decay, 3.0)
            base = frame["ros_m_per_min"] * frame["block_id"].map(hazard).fillna(1.0)
            for pattern in PATTERNS:
                mask = set(pd.read_csv(args.schedules / f"bridge_{pattern}_blocks.csv")["block_id"].astype(int))
                treated = frame["block_id"].isin(mask)
                # Reset from the untreated baseline for every pattern: leaving the previous
                # pattern's 0.3 in place would stack all three treated sets on the last run.
                frame["ros_eff"] = base.where(~treated, frame["ros_m_per_min"] * 0.3)
                result = simulate_fast(blocks=frame, adj=adj, ignitions=args.ignitions,
                                       duration_min=480.0, seed=1, wind_deg=225.0)
                rows.append({"multiplier": multiplier, "decay_years": decay, "pattern": pattern,
                             "mean_burned_ha": round(result["mean_area_burned_ha"], 1),
                             "p90_burned_ha": round(result["p90_area_burned_ha"], 1)})
            print(f"multiplier {multiplier} decay {decay:.0f} done")

    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)
    print("\n=== mean burned (ha) ===")
    print(out.pivot_table(index=["multiplier", "decay_years"], columns="pattern",
                          values="mean_burned_ha").round(0).to_string())
    print("\n=== ranking by mean burned (best first) ===")
    for (multiplier, decay), group in out.groupby(["multiplier", "decay_years"]):
        order = list(group.sort_values("mean_burned_ha")["pattern"])
        spread = (group["mean_burned_ha"].max() - group["mean_burned_ha"].min()) / group["mean_burned_ha"].mean() * 100
        print(f"mult {multiplier:>4} decay {decay:>4.0f}: {' < '.join(order)}   (spread {spread:.1f}%)")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
