"""Join a schedule to block geometry and write GeoPackage.

The web map already joins a run to ``--geometry`` for the browser; this is the static
counterpart a student can open in QGIS. One feature per block, carrying the treatment
assigned to it and the offset it was applied at, plus area and the block's hazard at the
start of the horizon where a compiled dataset is supplied.

Usage::

    python scripts/schedule_to_geopackage.py \
        --schedule runtime/ws4/greedy_hazard/schedule.csv \
        --fragments output/patchworks_ft/fragments/fragments.shp \
        --out runtime/ws4/greedy_hazard/schedule.gpkg
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--fragments", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--dataset", type=Path, default=None,
                        help="optional compiled dataset, to carry the block's hazard")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--layer", default="schedule")
    args = parser.parse_args()

    schedule = pd.read_csv(args.schedule)
    treated = schedule.groupby("block_id").agg(
        treatment=("treatment", "first"),
        offset=("offset", "min"),
    )

    fragments = gpd.read_file(args.fragments)
    blocks = fragments.dissolve(by="BLOCK", as_index=False)[["BLOCK", "geometry"]]
    blocks = blocks.rename(columns={"BLOCK": "block_id"})
    blocks["block_id"] = blocks["block_id"].astype(int)
    blocks["area_ha"] = blocks.geometry.area / 10000.0

    out = blocks.merge(treated, on="block_id", how="left")
    out["treated"] = out["treatment"].notna()
    out["treatment"] = out["treatment"].fillna("")

    if args.dataset is not None:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from landscape_spread import load_block_hazard

        hazard = load_block_hazard(args.dataset)
        out["hazard"] = out["block_id"].map(hazard).fillna(1.0)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(args.out, layer=args.layer, driver="GPKG")
    print(f"blocks in geometry: {len(blocks)}")
    print(f"treated in schedule: {int(out['treated'].sum())}")
    if "treatment" in out:
        print("by treatment:", out.loc[out['treated'], 'treatment'].value_counts().to_dict())
    print(f"wrote {args.out} (layer {args.layer})")


if __name__ == "__main__":
    main()
