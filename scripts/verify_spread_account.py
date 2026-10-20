"""Verify WS4's spread-connectivity account against the measured oracle (#13).

Applies each bridge pattern's schedule at period 0 to the deduplicated TSA23 FT
dataset, then computes WS4's spread account on the resulting treated set with the
published settings (bearing 225, tolerance 60, no search-distance limit).

The expected values are the ones recorded by the WS4 side after the product-table
fix (`femic-tsa23-instance#13`):

=================  ==============  ==========  =================  ====================
pattern            treated blocks  treated ha  largest (ha)       percolation (ha)
=================  ==============  ==========  =================  ====================
barrier            3,483           54,368      82,874.4           25,696.8
clumped            3,557           55,837      105,020.4          32,250.4
random             3,366           53,697      196,766.6          50,280.8
=================  ==============  ==========  =================  ====================

Usage::

    python scripts/verify_spread_account.py \
        --dataset runtime/ws4/compiled_ft_econ \
        --masks /srv/shared-data/gep/ws4/ws4/tmp/bridge-masks-dedup
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from ws4.sim.engine import Simulator
from ws4.spread.accounts import SpreadAccount

PATTERNS = ("barrier", "clumped", "random")
EXPECTED = {
    "barrier": {"blocks": 3483, "ha": 54368.0, "largest": 82874.4, "percolation": 25696.8},
    "clumped": {"blocks": 3557, "ha": 55837.0, "largest": 105020.4, "percolation": 32250.4},
    "random": {"blocks": 3366, "ha": 53697.0, "largest": 196766.6, "percolation": 50280.8},
}


def block_coordinates(fragments: Path, out: Path) -> Path:
    """Dissolve the fragment inventory by block and write its representative points."""
    import geopandas as gpd

    frame = gpd.read_file(fragments)
    blocks = frame[["BLOCK", "geometry"]].dissolve(by="BLOCK", as_index=False)
    # The WS4 side used the dissolved block centroid, not a representative point.
    points = blocks.geometry.centroid
    pd.DataFrame(
        {
            "block": blocks["BLOCK"].astype("int64"),
            "x": points.x.to_numpy(),
            "y": points.y.to_numpy(),
        }
    ).to_csv(out, index=False)
    return out


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_ft_econ"))
    parser.add_argument("--fragments", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument(
        "--schedules",
        type=Path,
        default=Path("runtime/fire"),
        help="directory holding bridge_{pattern}_sched.csv (the pattern's own schedule)",
    )
    parser.add_argument("--out", type=Path, default=Path("runtime/ws4/spread_verify"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    coordinates = block_coordinates(args.fragments, args.out / "block_centroids.csv")
    blocks = pd.read_parquet(args.dataset / "blocks.parquet")
    account = SpreadAccount(
        name="spread.ft",
        criteria="product.Treated.managed.FT",
        bearing=225.0,
        tolerance=60.0,
        search_distance=None,
    )

    rows: list[dict[str, object]] = []
    for pattern in PATTERNS:
        # The mask in bridge-masks-dedup is the *result* of applying this schedule, not an
        # input: re-applying the result treats an already-treated block and drops it.
        schedule = args.schedules / f"bridge_{pattern}_sched.csv"
        run_dir = args.out / pattern
        # A fresh simulator per pattern: run() mutates the treatment state, so reusing one
        # would make each pattern inherit the previous pattern's treatments.
        sim = Simulator.from_dataset(args.dataset)
        sim.run(
            schedule,
            1,
            run_dir,
            topology_csv=args.topology,
            spread_accounts=(account,),
            block_coordinates=coordinates,
        )
        metrics = (
            pd.read_csv(run_dir / "spread_metrics.csv")
            .query("year == 0")
            .set_index("account")["value"]
        )
        total_blocks = int(blocks["block_id"].nunique())
        total_area = float(blocks["area_ha"].sum())
        rows.append(
            {
                "pattern": pattern,
                "blocks": int(total_blocks - metrics["spread.ft.TOTAL.blocks"]),
                "treated_ha": float(total_area - metrics["spread.ft.TOTAL.area"]),
                "largest_ha": float(metrics["spread.ft.largest_component"]),
                "percolation_ha": float(metrics["spread.ft.percolation_reach"]),
            }
        )

    frame = pd.DataFrame(rows).set_index("pattern")
    frame.to_csv(args.out / "spread_account_verify.csv")

    failures: list[str] = []
    print(f"{'pattern':8s} {'blocks':>7s} {'treated ha':>11s} {'largest ha':>11s} {'percolation':>12s}")
    for pattern in PATTERNS:
        got = frame.loc[pattern]
        want = EXPECTED[pattern]
        print(
            f"{pattern:8s} {int(got.blocks):7d} {got.treated_ha:11.1f} "
            f"{got.largest_ha:11.1f} {got.percolation_ha:12.1f}"
        )
        if int(got.blocks) != want["blocks"]:
            failures.append(f"{pattern}: {int(got.blocks)} blocks, expected {want['blocks']}")
        for key, column in (("ha", "treated_ha"), ("largest", "largest_ha"), ("percolation", "percolation_ha")):
            delta = abs(got[column] - want[key]) / want[key] * 100
            if delta > 1.0:
                failures.append(f"{pattern} {column}: {got[column]:.1f} vs {want[key]:.1f} ({delta:.2f}%)")

    if failures:
        print("\nDISAGREEMENT")
        for line in failures:
            print(f"  {line}")
        sys.exit(1)
    print("\nAGREES with the recorded oracle (blocks exact, areas within 1%)")


if __name__ == "__main__":
    main()
