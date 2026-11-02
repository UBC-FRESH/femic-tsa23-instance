#!/usr/bin/env python3
"""Run the TSA 23 BA-only inventory consumer test.

The test maps the published 25 m BA pilot to the compiled TSA 23 WS4 fragment
grid, adds report-only fields to a copy of the compiled dataset, validates the
copy, and runs one bounded simulation. It does not change the production dataset
or any model, curve, THLB, AAC, target, or schedule value.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--ba-table", type=Path, required=True)
    parser.add_argument("--ba-raster", type=Path, required=True)
    parser.add_argument("--fragments", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--years", type=int, default=1)
    return parser.parse_args()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process.

    Parameters
    ----------
    command : list[str]
        Command and arguments.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process.
    """
    print("+ " + " ".join(command))
    return subprocess.run(command, check=True, capture_output=True, text=True)


def cell_rows_cols(ids: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Return the raster row and column encoded in a cell id.

    Parameters
    ----------
    ids : pandas.Series
        Cell ids such as ``cell_02006_02548``.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Row and column arrays.
    """
    parts = ids.str.extract(r"^cell_(\d+)_(\d+)$")
    if parts.isna().any().any():
        raise ValueError("a cell id does not match cell_<row>_<col>")
    return parts[0].to_numpy(dtype=np.int64), parts[1].to_numpy(dtype=np.int64)


def weighted_block_mean(
    fragments: pd.DataFrame, values: pd.Series, area: pd.Series
) -> pd.DataFrame:
    """Aggregate fragment values to blocks by area-weighted mean.

    Parameters
    ----------
    fragments : pandas.DataFrame
        Fragment table with ``block_id``.
    values : pandas.Series
        Fragment values; NaN means unavailable.
    area : pandas.Series
        Fragment areas in hectares.

    Returns
    -------
    pandas.DataFrame
        Columns ``block_id``, ``inventory_ba_m2_ha``, ``inventory_ba_available``.
    """
    frame = pd.DataFrame({"block_id": fragments["block_id"], "value": values, "area": area})
    valid = frame.dropna(subset=["value"])
    if valid.empty:
        return pd.DataFrame(columns=["block_id", "inventory_ba_m2_ha", "inventory_ba_available"])
    grouped = valid.groupby("block_id").apply(
        lambda group: np.average(group["value"], weights=group["area"]),
        include_groups=False,
    )
    result = grouped.rename("inventory_ba_m2_ha").reset_index()
    result["inventory_ba_available"] = True
    return result


def main() -> None:
    """Run the consumer test and write the summary."""
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    table = pd.read_parquet(args.ba_table)
    rows, cols = cell_rows_cols(table["fragment_id"].astype(str))
    with rasterio.open(args.ba_raster) as raster:
        array = raster.read(1)
        nodata = raster.nodata
        valid = array != nodata
        valid_count = int(valid.sum())
        table_values = table["value"].to_numpy(dtype=float)
        raster_values = array[rows, cols].astype(float)
        max_abs_diff = float(np.max(np.abs(raster_values - table_values)))
        transform = raster.transform
        crs = raster.crs

    fragments = gpd.read_file(args.fragments).rename(columns={"FRAGMENT_I": "fragment_id"})
    fragments = fragments.to_crs(crs)
    fragment_grid = rasterize(
        (
            (geometry, int(fragment_id))
            for fragment_id, geometry in zip(
                fragments["fragment_id"], fragments.geometry, strict=True
            )
        ),
        out_shape=array.shape,
        transform=transform,
        fill=0,
        dtype=np.int32,
    )
    cell_fragment = fragment_grid[rows, cols]
    matched = cell_fragment > 0
    matched_cells = int(matched.sum())
    unmatched_cells = int((~matched).sum())

    joined = pd.DataFrame(
        {
            "fragment_id": cell_fragment[matched],
            "value": table_values[matched],
        }
    )
    fragment_means = (
        joined.groupby("fragment_id")
        .agg(inventory_ba_m2_ha=("value", "mean"), inventory_ba_cells=("value", "size"))
        .reset_index()
    )
    fragments = fragments.merge(fragment_means, on="fragment_id", how="left")
    fragments["inventory_ba_available"] = fragments["inventory_ba_m2_ha"].notna()
    fragments["inventory_ba_cells"] = fragments["inventory_ba_cells"].fillna(0).astype(int)

    fragments_table = pd.read_parquet(args.dataset / "fragments.parquet")
    fragment_fields = fragments_table.merge(
        fragments[
            ["fragment_id", "inventory_ba_m2_ha", "inventory_ba_available", "inventory_ba_cells"]
        ],
        on="fragment_id",
        how="left",
    )
    block_means = weighted_block_mean(
        fragment_fields,
        fragment_fields["inventory_ba_m2_ha"],
        fragment_fields["area_ha"],
    )
    blocks_table = pd.read_parquet(args.dataset / "blocks.parquet")
    blocks = blocks_table.merge(block_means, on="block_id", how="left")
    blocks["inventory_ba_available"] = blocks["inventory_ba_available"].fillna(False).astype(bool)

    copy_dir = args.output_dir / "compiled_ft_econ_ba"
    if copy_dir.exists():
        shutil.rmtree(copy_dir)
    shutil.copytree(args.dataset, copy_dir)
    fragment_fields.to_parquet(copy_dir / "fragments.parquet", index=False)
    blocks.to_parquet(copy_dir / "blocks.parquet", index=False)

    schedule = pd.read_csv(args.schedule)
    if "period" in schedule.columns and "offset" not in schedule.columns:
        schedule = schedule.rename(columns={"period": "offset"})
    schedule_path = args.output_dir / "schedule_offset.csv"
    schedule.to_csv(schedule_path, index=False)

    validate = run([sys.executable, "-m", "ws4.cli", "validate", "--dataset", str(copy_dir)])
    run_dir = args.output_dir / "simulate"
    simulate = run(
        [
            sys.executable,
            "-m",
            "ws4.cli",
            "simulate",
            "--dataset",
            str(copy_dir),
            "--schedule",
            str(schedule_path),
            "--out",
            str(run_dir),
            "--years",
            str(args.years),
        ]
    )
    from ws4.sim.engine import Simulator

    simulator = Simulator.from_dataset(copy_dir)
    simulator_fragments = set(simulator.fragments.columns)
    simulator_blocks = set(pd.read_parquet(copy_dir / "blocks.parquet").columns)

    matched_area_ha = float(
        fragments_table.loc[
            fragments_table["fragment_id"].isin(fragment_means["fragment_id"]), "area_ha"
        ].sum()
    )
    summary: dict[str, Any] = {
        "table_rows": len(table),
        "raster_valid_pixels": valid_count,
        "table_raster_max_abs_diff": max_abs_diff,
        "matched_cells": matched_cells,
        "unmatched_cells": unmatched_cells,
        "matched_fragments": len(fragment_means),
        "matched_blocks": int(block_means["block_id"].nunique()),
        "matched_area_ha": matched_area_ha,
        "matched_cell_area_ha": matched_cells * 625.0 / 10000.0,
        "fragment_fields_present": sorted(
            field
            for field in ("inventory_ba_m2_ha", "inventory_ba_available", "inventory_ba_cells")
            if field in simulator_fragments
        ),
        "block_fields_present": sorted(
            field
            for field in ("inventory_ba_m2_ha", "inventory_ba_available")
            if field in simulator_blocks
        ),
        "validate_passed": validate.returncode == 0,
        "simulator_reads_fragment_fields": {
            "inventory_ba_m2_ha",
            "inventory_ba_available",
            "inventory_ba_cells",
        }.issubset(simulator_fragments),
        "simulate_passed": simulate.returncode == 0,
        "simulate_completed": "Simulation complete" in simulate.stdout,
        "years": args.years,
        "ba_mean_matched": float(joined["value"].mean()),
        "ba_min_matched": float(joined["value"].min()),
        "ba_max_matched": float(joined["value"].max()),
    }
    (args.output_dir / "ba_consumer_test.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
