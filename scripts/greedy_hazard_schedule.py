"""Greedy hazard-reduction schedule: rank treatments by cost per hazard-hectare.

The optimizer cannot cross the scale a hazard target needs (ws4#165), so this builds the
schedule directly: for every operable block and treatment, compute the hazard reduction the
treatment buys by year 4 and its cost, rank by cost per hazard-hectare, and take candidates
until the target is met or the budget is spent.

It answers the treatment-mix question empirically, and doubles as the baseline a seeded
optimizer would need.

Usage::

    python scripts/greedy_hazard_schedule.py --target 970000 --budget 100000000
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Cost curve per treatment label, as built by the instance scripts.
COST_LABELS = {
    "FT": "product.FuelTreatmentCost",
    "FB": "product.FuelBreakCost",
    "SF": "product.SurfaceFuelCost",
}
COST_PER_HA = {"FT": 20000.0, "FB": 5000.0, "SF": 3000.0}


def _curve_values(curves: pd.DataFrame) -> dict[tuple[int, float], float]:
    return {(int(c), float(x)): float(y) for c, x, y in zip(curves.curve_id, curves.x, curves.y)}


def _hazard_at(
    hazard_by_track: dict[int, int], table: dict[tuple[int, float], float], track: int, age: float
) -> float | None:
    curve = hazard_by_track.get(track)
    if curve is None:
        return None
    value = table.get((curve, age))
    if value is None:
        value = table.get((curve, 0.0))
    return value


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_sf"))
    parser.add_argument("--target", type=float, default=970000.0)
    parser.add_argument("--baseline", type=float, default=992334.0)
    parser.add_argument("--budget", type=float, default=100_000_000.0)
    parser.add_argument("--year", type=int, default=4)
    parser.add_argument("--out", type=Path, default=Path("runtime/ws4/greedy_hazard/schedule.csv"))
    args = parser.parse_args()

    blocks = pd.read_parquet(args.dataset / "blocks.parquet")
    treatments = pd.read_parquet(args.dataset / "treatments.parquet")
    features = pd.read_parquet(args.dataset / "features.parquet")
    curves = pd.read_parquet(args.dataset / "curves.parquet")
    table = _curve_values(curves)

    hazard = features[features["label"] == "feature.FuelHazard"]
    hazard_by_track = dict(zip(hazard.track_id.astype(int), hazard.curve_id.astype(int)))
    # The cost curves are identified by their product label, one curve per treatment.
    cost_curves: dict[str, int] = {}
    products = pd.read_parquet(args.dataset / "products.parquet")
    for tr, label in COST_LABELS.items():
        rows = products[products["label"] == label]
        if rows.empty:
            continue
        cost_curves[tr] = int(rows["curve_id"].iloc[0])

    # (track, treatment) -> (begin, end, new_track); a dict keeps this linear. A per-row
    # pandas filter over 168k fragments is O(n^2) and never finishes.
    treat_by_key: dict[tuple[int, str], tuple[float, float, int]] = {}
    for row in treatments.itertuples(index=False):
        key = (int(row.track_id), str(row.treatment))
        if key not in treat_by_key:
            treat_by_key[key] = (float(row.begin), float(row.end), int(row.new_track))

    candidates: list[dict[str, object]] = []
    for row in blocks.itertuples(index=False):
        track = int(row.track_id)
        offset = float(row.offset)
        area = float(row.area_ha)
        before = _hazard_at(hazard_by_track, table, track, offset)
        if before is None:
            continue
        for tr in ("FB", "FT"):
            treat = treat_by_key.get((track, tr))
            if treat is None:
                continue
            begin, end, new_track = treat
            if not (begin <= offset <= end):
                continue
            after = _hazard_at(hazard_by_track, table, new_track, float(args.year))
            if after is None:
                continue
            reduction = max(before - after, 0.0) * area
            if reduction <= 0:
                continue
            curve = cost_curves.get(tr)
            per_ha = table.get((curve, 0.0), COST_PER_HA[tr]) if curve is not None else COST_PER_HA[tr]
            cost = per_ha * area
            candidates.append(
                {"block_id": int(row.block_id), "treatment": tr, "area_ha": area,
                 "hazard_reduction": reduction, "cost": cost,
                 "cost_per_hazard": cost / reduction}
            )

    frame = pd.DataFrame(candidates).sort_values("cost_per_hazard")
    gap = args.baseline - args.target
    chosen: list[dict[str, object]] = []
    spent = 0.0
    reduced = 0.0
    for row in frame.itertuples(index=False):
        if reduced >= gap:
            break
        if spent + row.cost > args.budget:
            continue
        chosen.append({"block_id": row.block_id, "treatment": row.treatment, "offset": 0,
                       "cost": row.cost, "reduction": row.hazard_reduction})
        spent += row.cost
        reduced += row.hazard_reduction

    out = pd.DataFrame(chosen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out[["block_id", "treatment", "offset"]].to_csv(args.out, index=False)
    print(f"candidates: {len(frame)}")
    print(f"chosen: {len(out)} blocks")
    print(out.groupby("treatment").agg(blocks=("block_id", "size"), cost=("cost", "sum"),
                                       reduction=("reduction", "sum")).round(0).to_string())
    print(f"\nspend: ${spent:,.0f} of ${args.budget:,.0f}")
    print(f"hazard reduction: {reduced:,.0f} hazard-ha of the {gap:,.0f} needed")
    print(f"projected hazard: {args.baseline - reduced:,.0f} (target {args.target:,.0f})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
