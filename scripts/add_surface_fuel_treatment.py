"""Add a surface-fuel reduction (SF) treatment to a compiled WS4 dataset.

SF is a distinct treatment the scheduler applies **after** thinning, within a
short post-treatment window (the activity fuels are fresh). For every FT
destination track it creates a parallel `sf_*` destination track (a copy of the FT
destination) with:

- a `feature.FuelHazard` curve reduced for the SF window and then recovering;
- a `product.SurfaceFuelCost` (the SF cost, per treated hectare);
- the FT destination's features/products relabelled to SF;

and an SF treatment on the FT destination track with an age window `0..window`
(years since thinning; the simulator resets the offset to 0 on thinning).

Usage::

    python scripts/add_surface_fuel_treatment.py \
        --dataset runtime/ws4/compiled_fb_haz --out runtime/ws4/compiled_sf \
        --cost-per-ha 3000 --window-years 10
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

STATE_RE = re.compile(r"SILV_STATE\(([^)]*)\)")


def _sf_track_name(name: str) -> str:
    """Return the track name with its silviculture state prefixed by `sf_`."""
    match = STATE_RE.search(str(name))
    if not match:
        return str(name) + "+SILV_STATE(sf)"
    return STATE_RE.sub(f"SILV_STATE(sf_{match.group(1)})", str(name), count=1)


def add_surface_fuel(
    *,
    dataset: Path,
    out: Path,
    cost_per_ha: float,
    window_years: int,
) -> Path:
    """Add SF treatments and their hazard/cost curves."""
    dataset = Path(dataset)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    tracks = pd.read_parquet(dataset / "tracks.parquet")
    strata = pd.read_parquet(dataset / "strata.parquet")
    treatments = pd.read_parquet(dataset / "treatments.parquet")
    curves = pd.read_parquet(dataset / "curves.parquet")
    features = pd.read_parquet(dataset / "features.parquet")
    products = pd.read_parquet(dataset / "products.parquet")

    next_track = int(tracks["track_id"].max()) + 1
    next_curve = int(curves["curve_id"].max()) + 1

    hazard_curve_id = next_curve
    next_curve += 1
    curves = pd.concat(
        [
            curves,
            pd.DataFrame(
                [
                    {"curve_id": hazard_curve_id, "x": 0.0, "y": 0.2},
                    {"curve_id": hazard_curve_id, "x": float(max(1, window_years)), "y": 0.2},
                    {"curve_id": hazard_curve_id, "x": 20.0, "y": 0.6},
                    {"curve_id": hazard_curve_id, "x": 40.0, "y": 1.0},
                    {"curve_id": hazard_curve_id, "x": 400.0, "y": 1.0},
                ]
            ),
        ],
        ignore_index=True,
    )
    cost_curve_id = next_curve
    curves = pd.concat(
        [curves, pd.DataFrame([{"curve_id": cost_curve_id, "x": 0.0, "y": float(cost_per_ha)}])],
        ignore_index=True,
    )

    ft = treatments[treatments["treatment"] == "FT"]
    dest_ids = np.sort(ft["new_track"].unique())
    dest_to_sf = {int(d): int(next_track + i) for i, d in enumerate(dest_ids)}

    dest_tracks = tracks[tracks["track_id"].isin(dest_ids)].copy()
    new_tracks = dest_tracks.copy()
    new_tracks["track_id"] = new_tracks["track_id"].map(dest_to_sf)
    new_tracks["name"] = dest_tracks["name"].map(_sf_track_name)

    new_strata = strata[strata["track_id"].isin(dest_ids)].copy()
    new_strata["track_id"] = new_strata["track_id"].map(dest_to_sf)

    new_features = features[features["track_id"].isin(dest_ids)].copy()
    new_features = new_features[new_features["label"] != "feature.FuelHazard"]
    new_features["track_id"] = new_features["track_id"].map(dest_to_sf)
    hazard_rows = pd.DataFrame(
        {
            "track_id": list(dest_to_sf.values()),
            "label": "feature.FuelHazard",
            "curve_id": hazard_curve_id,
        }
    )
    new_features = pd.concat([new_features, hazard_rows], ignore_index=True)

    # Products must live on the track the treatment is applied to (the FT destination),
    # not the SF destination: WS4 resolves a product by (source track, treatment) at
    # apply time. Surface-fuel work yields no timber, so only the cost is produced;
    # copying the FT yields here would double-count the thinning.
    cost_rows = pd.DataFrame(
        {
            "track_id": [int(d) for d in dest_ids],
            "treatment": "SF",
            "label": "product.SurfaceFuelCost",
            "curve_id": cost_curve_id,
        }
    )
    new_products = cost_rows
    new_products = pd.concat([new_products, cost_rows], ignore_index=True)
    # Several source tracks can carry the same product under different treatments;
    # retagging them to one treatment collapses those rows onto the same WS4 key.
    # Keep one row per exact key (the builder's rule), but keep different curves,
    # which are the per-AU components and are a sum.
    before = len(new_products)
    new_products = new_products.drop_duplicates(
        ["track_id", "treatment", "label", "curve_id"], keep="first"
    )
    print(f"SF: dropped {before - len(new_products)} duplicated product rows")

    # SF follows thinning: operable on the FT destination for `window_years`.
    new_treatments = ft.copy()
    new_treatments["treatment"] = "SF"
    new_treatments["new_track"] = new_treatments["new_track"].map(dest_to_sf)
    new_treatments["begin"] = 0
    new_treatments["end"] = int(window_years)
    new_treatments["track_id"] = ft["new_track"].to_numpy()

    for name, frame in (
        ("tracks", pd.concat([tracks, new_tracks], ignore_index=True)),
        ("strata", pd.concat([strata, new_strata], ignore_index=True)),
        ("features", pd.concat([features, new_features], ignore_index=True)),
        ("products", pd.concat([products, new_products], ignore_index=True)),
        ("treatments", pd.concat([treatments, new_treatments], ignore_index=True)),
        ("curves", curves),
    ):
        frame.to_parquet(out / f"{name}.parquet", index=False)
    for name in ("fragments", "blocks", "protoaccounts", "accounts", "groups", "messages"):
        pd.read_parquet(dataset / f"{name}.parquet").to_parquet(out / f"{name}.parquet", index=False)
    manifest = json.loads((dataset / "manifest.json").read_text())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cost-per-ha", type=float, default=3750.0, dest="cost_per_ha")
    parser.add_argument("--window-years", type=int, default=10, dest="window_years")
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    out = add_surface_fuel(
        dataset=args.dataset,
        out=args.out,
        cost_per_ha=args.cost_per_ha,
        window_years=args.window_years,
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
