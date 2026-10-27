"""Epsilon-constraint abatement curve for TSA23 fuel treatments.

For each fuel-treatment subsidy budget, deploy the most cost-effective treatments
on the blocks where they become operable within a 20-year horizon, simulate the
result, and report the fire-risk reduction against the treated area. The result is
an approximate marginal-abatement-cost curve over the deployment domain.

Method (heuristic, stated as such): blocks are ranked by risk-weighted hazard
reduction per dollar - the same ranking the greedy hazard schedule uses - and taken
until the budget is spent. Each candidate is scheduled at the first year its
treatment window is open (treatments are age-windowed at 30-60 for FT and 50+ for
CC/FB), so the deployment spreads across the horizon rather than piling onto year 0.

This is not the optimal epsilon-constrained solve. WS4's annealer converts only a
handful of blocks per hundred iterations at this scale, and the seeded constructor
either ignores the harvest schedule or replaces it (see
planning/abatement_curve_pilot.md). The curve below is the ranking frontier, and is
labelled that way wherever it is reported.

Usage::

    python scripts/abatement_curve.py \
        --dataset runtime/ws4/compiled_sf_bc \
        --burn-probability runtime/fire/burn_probability_mean_wind.json \
        --budgets 0,25000000,50000000,100000000,200000000,400000000,800000000,1600000000 \
        --out-dir runtime/ws4/abatement_bc
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

COST_LABELS = {
    "FT": "product.FuelTreatmentCost",
    "FB": "product.FuelBreakCost",
    "SF": "product.SurfaceFuelCost",
}
COST_PER_HA = {"FT": 10000.0, "FB": 7500.0, "SF": 3750.0}
HAZARD_AFTER = {"FT": 0.4, "FB": 0.05}
YEARS = 20


def _curve_values(curves: pd.DataFrame) -> dict[tuple[int, float], float]:
    return {(int(c), float(x)): float(y) for c, x, y in zip(curves.curve_id, curves.x, curves.y)}


def _hazard_at(by_track, table, track, age):
    c = by_track.get(track)
    if c is None:
        return None
    v = table.get((c, age))
    return table.get((c, 0.0)) if v is None else v


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_sf_bc"))
    parser.add_argument("--burn-probability", type=Path, default=None)
    parser.add_argument("--budgets", default="0,25000000,50000000,100000000,200000000,400000000")
    parser.add_argument("--years", type=int, default=YEARS)
    parser.add_argument("--out-dir", type=Path, default=Path("runtime/ws4/abatement_bc"))
    args = parser.parse_args()

    ds = args.dataset
    blocks = pd.read_parquet(ds / "blocks.parquet")
    treatments = pd.read_parquet(ds / "treatments.parquet")
    features = pd.read_parquet(ds / "features.parquet")
    curves = pd.read_parquet(ds / "curves.parquet")
    products = pd.read_parquet(ds / "products.parquet")
    table = _curve_values(curves)

    hazard = features[features["label"] == "feature.FuelHazard"]
    by_track = dict(zip(hazard.track_id.astype(int), hazard.curve_id.astype(int)))
    cost_curves = {}
    for tr, label in COST_LABELS.items():
        rows = products[products["label"] == label]
        if not rows.empty:
            cost_curves[tr] = int(rows["curve_id"].iloc[0])

    treat_by_key = {}
    for row in treatments.itertuples(index=False):
        key = (int(row.track_id), str(row.treatment))
        if key not in treat_by_key:
            treat_by_key[key] = (float(row.begin), float(row.end), int(row.new_track))

    probability = {}
    if args.burn_probability is not None:
        payload = json.loads(args.burn_probability.read_text())
        probability = {int(k): float(v) for k, v in (payload.get("burn_probability") or payload).items()}

    candidates = []
    for row in blocks.itertuples(index=False):
        track = int(row.track_id)
        age = float(row.offset)
        area = float(row.area_ha)
        before = _hazard_at(by_track, table, track, age)
        if before is None:
            continue
        for tr in ("FB", "FT"):
            if (track, tr) not in treat_by_key:
                continue
            begin, end, new_track = treat_by_key[(track, tr)]
            year = max(0.0, begin - age)
            if year > args.years - 1 or age + year > end:
                continue  # window opens beyond the horizon, or the stand is past it
            after = _hazard_at(by_track, table, new_track, min(age + year, args.years - 1))
            if after is None:
                continue
            reduction = max(before - after, 0.0) * area
            if reduction <= 0:
                continue
            curve = cost_curves.get(tr)
            per_ha = table.get((curve, 0.0), COST_PER_HA[tr]) if curve is not None else COST_PER_HA[tr]
            cand = {
                "block_id": int(row.block_id),
                "treatment": tr,
                "year": int(round(year)),
                "area_ha": area,
                "hazard_reduction": reduction,
                "cost": per_ha * area,
            }
            cand["risk"] = probability.get(int(row.block_id), 0.0)
            cand["expected_reduction"] = reduction * cand["risk"]
            candidates.append(cand)

    frame = pd.DataFrame(candidates)
    if probability:
        frame = frame[frame.expected_reduction > 0].copy()
        frame["sort_key"] = frame["cost"] / frame["expected_reduction"]
        frame = frame.sort_values(["sort_key", "area_ha"], ascending=[True, False])
    else:
        frame["sort_key"] = frame["cost"] / frame["hazard_reduction"]
        frame = frame.sort_values(["sort_key", "area_ha"], ascending=[True, False])

    args.out_dir.mkdir(parents=True, exist_ok=True)
    budgets = [float(b) for b in args.budgets.split(",") if b.strip()]
    rows = []
    for budget in budgets:
        chosen, spent = [], 0.0
        for cand in frame.itertuples(index=False):
            if spent + cand.cost > budget:
                continue
            chosen.append(cand)
            spent += cand.cost
        sched = pd.DataFrame(
            [{"block_id": c.block_id, "treatment": c.treatment, "offset": c.year} for c in chosen]
        )
        path = args.out_dir / f"sched_{int(budget)}.csv"
        sched.to_csv(path, index=False)
        rows.append(
            {
                "budget": budget,
                "planned_spend": spent,
                "blocks": len(sched),
                "planned_area_ha": float(sum(c.area_ha for c in chosen)),
                "risk_weighted_reduction": float(sum(c.expected_reduction for c in chosen)),
            }
        )
        print(f"budget ${budget:,.0f}: {len(sched)} blocks, {rows[-1]['planned_area_ha']:,.0f} ha, "
              f"spend ${spent:,.0f}")
    out = pd.DataFrame(rows)
    out.to_csv(args.out_dir / "frontier_planned.csv", index=False)
    print(f"wrote {args.out_dir / 'frontier_planned.csv'} ({len(frame)} candidates)")


if __name__ == "__main__":
    main()
