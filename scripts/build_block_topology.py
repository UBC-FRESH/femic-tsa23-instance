"""Build a block adjacency topology for the TSA23 model.

WS4 patch metrics and spatial constraints need a block topology: an undirected
edgelist ``src_block,dst_block,distance_m``. This script derives it from the
FEMIC Patchworks fragments shapefile (one polygon per BLOCK): blocks that touch
get distance 0, and blocks whose polygons are within ``--search-distance`` metres
get their shortest inter-polygon distance.

Usage::

    python scripts/build_block_topology.py \
        --fragments output/patchworks_ft/fragments/fragments.shp \
        --out runtime/ws4/topology_tsa23.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.strtree import STRtree


def build_topology(
    *,
    fragments: Path,
    out: Path,
    search_distance_m: float,
    block_column: str = "BLOCK",
) -> Path:
    """Write a block adjacency edgelist derived from fragment/block polygons.

    Parameters
    ----------
    fragments : Path
        The fragments/block polygon shapefile.
    out : Path
        The output topology CSV.
    search_distance_m : float
        Blocks whose polygons are within this distance get an edge.
    block_column : str
        The block id column.

    Returns
    -------
    Path
        The written CSV.
    """
    gdf = gpd.read_file(fragments)
    if block_column not in gdf.columns:
        raise ValueError(f"missing block column {block_column!r} in {fragments}")
    gdf = gdf[[block_column, "geometry"]].copy()
    gdf[block_column] = gdf[block_column].astype("int64")
    # One polygon per block (dissolve in case of multiple fragment rows).
    blocks = gdf.dissolve(by=block_column, as_index=True)
    ids = np.asarray(blocks.index, dtype="int64")
    geoms = np.asarray(blocks.geometry.values, dtype=object)
    tree = STRtree(geoms)

    pairs: dict[tuple[int, int], float] = {}
    for i, geom in enumerate(geoms):
        if search_distance_m > 0.0:
            probe = geom.buffer(search_distance_m)
        else:
            probe = geom
        for j in tree.query(probe, predicate="intersects"):
            j = int(j)
            if j <= i:
                continue
            distance = float(geom.distance(geoms[j]))
            if distance <= search_distance_m:
                pairs[(int(ids[i]), int(ids[j]))] = distance

    out.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        [
            {"src_block": src, "dst_block": dst, "distance_m": dist}
            for (src, dst), dist in sorted(pairs.items())
        ]
    )
    frame.to_csv(out, index=False)
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--search-distance", type=float, default=100.0, dest="search_distance_m")
    parser.add_argument("--block-column", default="BLOCK")
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    out = build_topology(
        fragments=args.fragments,
        out=args.out,
        search_distance_m=args.search_distance_m,
        block_column=args.block_column,
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
