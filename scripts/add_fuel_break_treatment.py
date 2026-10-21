"""Add a fuel-break (FB) treatment to a compiled WS4 dataset (vectorized).

FB is a distinct clearcut **plus full post-harvest fuel disposal** treatment, not
a fourth thinning intensity (see `planning/treatment_design_fb_and_surface.md`).
For every CC destination track it creates a parallel `fb` destination track (a
copy of the CC destination) with:

- a `feature.FuelHazard` curve that is near-null for N years and then recovers;
- a `product.FuelBreakCost` (the disposal cost, per treated hectare);
- the CC destination's yield/area/species features, relabelled to FB;

and, for every CC treatment, an FB treatment on the same source track that
transitions to the FB destination.

This reads/writes the parquet tables directly (the Model API's per-dest coercion
is too slow at ~5M product rows).

Usage::

    python scripts/add_fuel_break_treatment.py \
        --dataset runtime/ws4/compiled_ft_econ \
        --out runtime/ws4/compiled_fb \
        --disposal-cost-per-ha 5000 --near-null-years 8
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

STATE_RE = re.compile(r"SILV_STATE\(([^)]*)\)")


def _fb_track_name(name: str) -> str:
    """Return the track name with its silviculture state replaced by `fb_<state>`."""
    match = STATE_RE.search(str(name))
    if not match:
        return str(name) + "+SILV_STATE(fb)"
    return STATE_RE.sub(f"SILV_STATE(fb_{match.group(1)})", str(name), count=1)


def add_fuel_break(
    *,
    dataset: Path,
    out: Path,
    disposal_cost_per_ha: float,
    near_null_years: int,
) -> Path:
    """Add FB treatments and a per-track hazard feature to a compiled dataset."""
    dataset = Path(dataset)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    tables = {
        name: pd.read_parquet(dataset / f"{name}.parquet")
        for name in (
            "fragments", "blocks", "tracks", "strata", "treatments",
            "curves", "features", "products", "protoaccounts", "accounts",
            "groups", "messages",
        )
    }
    tracks = tables["tracks"]
    strata = tables["strata"]
    treatments = tables["treatments"]
    curves = tables["curves"]
    features = tables["features"]
    products = tables["products"]

    next_track = int(tracks["track_id"].max()) + 1
    next_curve = int(curves["curve_id"].max()) + 1

    # Hazard and disposal-cost curves.
    hazard_curve_id = next_curve
    next_curve += 1
    curves = pd.concat(
        [
            curves,
            pd.DataFrame(
                [
                    {"curve_id": hazard_curve_id, "x": 0.0, "y": 0.05},
                    {"curve_id": hazard_curve_id, "x": float(max(1, near_null_years)), "y": 0.05},
                    {"curve_id": hazard_curve_id, "x": 40.0, "y": 1.0},
                    {"curve_id": hazard_curve_id, "x": 400.0, "y": 1.0},
                ]
            ),
        ],
        ignore_index=True,
    )
    cost_curve_id = next_curve
    curves = pd.concat(
        [
            curves,
            pd.DataFrame(
                [{"curve_id": cost_curve_id, "x": 0.0, "y": float(disposal_cost_per_ha)}]
            ),
        ],
        ignore_index=True,
    )

    cc = treatments[treatments["treatment"] == "CC"]
    dest_ids = np.sort(cc["new_track"].unique())
    dest_to_fb = {int(d): int(next_track + i) for i, d in enumerate(dest_ids)}

    # New track rows.
    dest_tracks = tracks[tracks["track_id"].isin(dest_ids)].copy()
    new_tracks = dest_tracks.copy()
    new_tracks["track_id"] = new_tracks["track_id"].map(dest_to_fb)
    new_tracks["name"] = dest_tracks["name"].map(_fb_track_name)

    # New strata rows.
    new_strata = strata[strata["track_id"].isin(dest_ids)].copy()
    new_strata["track_id"] = new_strata["track_id"].map(dest_to_fb)

    # New features: copy the destination features, retag, add the hazard.
    new_features = features[features["track_id"].isin(dest_ids)].copy()
    new_features["track_id"] = new_features["track_id"].map(dest_to_fb)
    hazard_rows = pd.DataFrame(
        [
            {"track_id": fb, "label": "feature.FuelHazard", "curve_id": hazard_curve_id}
            for fb in dest_to_fb.values()
        ]
    )
    new_features = pd.concat([new_features, hazard_rows], ignore_index=True)

    # New products must live on the SOURCE track, not the destination. WS4 resolves a
    # product by (track the treatment is applied to, treatment label) at apply time; rows
    # written on the destination track make the treatment produce nothing, silently.
    # The yield copied here is the CC harvest product, because an FB is a clearcut.
    source_ids = sorted({int(s) for s in cc["track_id"]})
    new_products = products[
        products["track_id"].isin(source_ids) & (products["treatment"] == "CC")
    ].copy()
    new_products["treatment"] = "FB"
    cost_rows = pd.DataFrame(
        [
            {"track_id": src, "treatment": "FB", "label": "product.FuelBreakCost", "curve_id": cost_curve_id}
            for src in source_ids
        ]
    )
    new_products = pd.concat([new_products, cost_rows], ignore_index=True)
    # Several source tracks can carry the same product under different treatments;
    # retagging them to one treatment collapses those rows onto the same WS4 key.
    # Keep one row per exact key (the builder's rule), but keep different curves,
    # which are the per-AU components and are a sum.
    before = len(new_products)
    new_products = new_products.drop_duplicates(
        ["track_id", "treatment", "label", "curve_id"], keep="first"
    )
    print(f"FB: dropped {before - len(new_products)} duplicated product rows")

    # New treatments: mirror CC, retarget to the FB destination.
    new_treatments = cc.copy()
    new_treatments["treatment"] = "FB"
    new_treatments["new_track"] = new_treatments["new_track"].map(dest_to_fb)

    tables["curves"] = curves
    tables["tracks"] = pd.concat([tracks, new_tracks], ignore_index=True)
    tables["strata"] = pd.concat([strata, new_strata], ignore_index=True)
    tables["features"] = pd.concat([features, new_features], ignore_index=True)
    tables["products"] = pd.concat([products, new_products], ignore_index=True)
    tables["treatments"] = pd.concat([treatments, new_treatments], ignore_index=True)

    for name, frame in tables.items():
        frame.to_parquet(out / f"{name}.parquet", index=False)

    manifest = json.loads((dataset / "manifest.json").read_text())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--disposal-cost-per-ha", type=float, default=5000.0, dest="disposal_cost_per_ha")
    parser.add_argument("--near-null-years", type=int, default=8, dest="near_null_years")
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    out = add_fuel_break(
        dataset=args.dataset,
        out=args.out,
        disposal_cost_per_ha=args.disposal_cost_per_ha,
        near_null_years=args.near_null_years,
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
