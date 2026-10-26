"""Add per-block burn probability and a risk-weighted hazard feature to a compiled dataset.

Mirrors the two risk representations in Bhusal et al. (2026, *Forests* 17(8):886): a
simulation-derived spread probability used to weight where treatment matters. WS4 can only
target additive accounts, so the product of hazard and probability is materialized as its
own feature rather than multiplied at read time.

- ``feature.BurnProbability`` — the block's burn probability under an untreated landscape,
  constant over age.
- ``feature.RiskWeightedHazard`` — the track's ``feature.FuelHazard`` curve scaled by the
  block's probability. Because the hazard curve already carries the treatment states, the
  weighted feature falls when a treatment lowers hazard *and* weights blocks a fire is likely
  to reach.

Usage::

    python scripts/add_burn_probability_feature.py \
        --dataset runtime/ws4/compiled_sf \
        --burn-probability /tmp/burnprob.json \
        --out runtime/ws4/compiled_sf_risk
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_sf"))
    parser.add_argument("--burn-probability", type=Path, required=True, dest="burn_probability")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.burn_probability.read_text())
    per_block = payload.get("burn_probability") or payload
    per_block = {int(k): float(v) for k, v in per_block.items()}

    blocks = pd.read_parquet(args.dataset / "blocks.parquet")
    features = pd.read_parquet(args.dataset / "features.parquet")
    curves = pd.read_parquet(args.dataset / "curves.parquet")

    hazard = features[features["label"] == "feature.FuelHazard"][["track_id", "curve_id"]]
    hazard_by_track = dict(zip(hazard.track_id.astype(int), hazard.curve_id.astype(int)))

    # A treatment moves a block's fragment to a *destination* track. If a feature exists only
    # on the current tracks, a treated block drops out of the account entirely and the account
    # "improves" by deleting area. Build a track -> block map that follows the treatments.
    treatments = pd.read_parquet(args.dataset / "treatments.parquet")
    track_block = {int(t): int(b) for t, b in zip(blocks["track_id"], blocks["block_id"])}
    for row in treatments.itertuples(index=False):
        source_block = track_block.get(int(row.track_id))
        if source_block is not None:
            track_block.setdefault(int(row.new_track), source_block)
    all_tracks = pd.read_parquet(args.dataset / "tracks.parquet")["track_id"].astype(int).tolist()
    points = (
        curves.groupby("curve_id")[["x", "y"]]
        .apply(lambda g: list(zip(g.x.astype(float), g.y.astype(float))))
        .to_dict()
    )

    next_curve = int(curves["curve_id"].max()) + 1
    new_rows: list[dict[str, object]] = []
    new_points: list[dict[str, float]] = []
    probability_curve: dict[float, int] = {}

    for track in all_tracks:
        block = track_block.get(track)
        if block is None:
            continue
        p = per_block.get(block, 0.0)
        rounded = round(p, 4)
        if rounded not in probability_curve:
            probability_curve[rounded] = next_curve
            new_points.append({"curve_id": next_curve, "x": 0.0, "y": rounded})
            next_curve += 1
        new_rows.append(
            {"track_id": track, "label": "feature.BurnProbability",
             "curve_id": probability_curve[rounded]}
        )

        hazard_curve = hazard_by_track.get(track)
        if hazard_curve is None or rounded <= 0.0:
            continue
        scaled = next_curve
        next_curve += 1
        for x, y in points.get(hazard_curve, [(0.0, 1.0)]):
            new_points.append({"curve_id": scaled, "x": x, "y": y * rounded})
        new_rows.append(
            {"track_id": track, "label": "feature.RiskWeightedHazard", "curve_id": scaled}
        )

    features = pd.concat([features, pd.DataFrame(new_rows)], ignore_index=True)
    curves = pd.concat([curves, pd.DataFrame(new_points)], ignore_index=True)

    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("fragments", "blocks", "tracks", "strata", "treatments", "products",
                 "protoaccounts", "accounts", "groups", "messages"):
        source = args.dataset / f"{name}.parquet"
        if source.exists():
            pd.read_parquet(source).to_parquet(args.out / f"{name}.parquet", index=False)
    features.to_parquet(args.out / "features.parquet", index=False)
    curves.to_parquet(args.out / "curves.parquet", index=False)
    manifest = json.loads((args.dataset / "manifest.json").read_text())
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1))

    blocks_with_probability = sum(1 for v in per_block.values() if v > 0)
    print(f"blocks with p > 0: {blocks_with_probability} of {len(per_block)}")
    print(f"distinct probability curves: {len(probability_curve)}")
    print(f"feature rows added: {len(new_rows)}; curve rows added: {len(new_points)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
