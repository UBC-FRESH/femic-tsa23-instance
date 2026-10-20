"""Run the landscape spread model on an explicit treated-block mask.

Used for the matched-footprint bridge check (UBC-FRESH/femic-tsa23-instance#11):
the treated set comes from a CSV produced by WS4, not from a pattern generator.

The published bridge runs used ``--treat-ros-factor 0.3`` (confirmed by reproducing
``bridge_barrier.json`` exactly: mean 19640.448328143004, p90 37637.13355349601).

Usage::

    python scripts/run_matched_footprint.py \
        --treated-blocks runtime/fire/bridge_barrier_blocks.csv \
        --seed 1 --treat-ros-factor 0.3 --ignitions 50 --duration-min 480 \
        --wind-dir 225 --out runtime/fire/matched_barrier_seed1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_spread import _adjacency, _block_fuel_types, simulate  # noqa: E402


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--fuel-types", type=Path, default=Path("runtime/fire/fbp_stand_curves.csv"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument("--treated-blocks", type=Path, required=True, dest="treated_blocks")
    parser.add_argument("--scenario", default="p90")
    parser.add_argument("--age", type=int, default=60)
    parser.add_argument("--ignitions", type=int, default=50)
    parser.add_argument("--duration-min", type=float, default=480.0, dest="duration_min")
    parser.add_argument("--wind-dir", type=float, default=225.0, dest="wind_dir")
    parser.add_argument("--treat-ros-factor", type=float, default=0.3, dest="treat_ros_factor")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    frame = _block_fuel_types(args.blocks, args.fuel_types, args.scenario, args.age)
    mask = set(pd.read_csv(args.treated_blocks)["block_id"].astype(int))
    missing = mask - set(frame["block_id"])
    if missing:
        raise SystemExit(f"{len(missing)} treated blocks are not in the block table")

    frame = frame.copy()
    frame["treated"] = frame["block_id"].isin(mask)
    frame["ros_eff"] = frame["ros_m_per_min"] * frame["treated"].map(
        {True: args.treat_ros_factor, False: 1.0}
    )

    adj = _adjacency(args.topology)
    result = simulate(
        blocks=frame,
        adj=adj,
        ignitions=args.ignitions,
        duration_min=args.duration_min,
        seed=args.seed,
        wind_deg=args.wind_dir,
    )
    result.update(
        {
            "treated_blocks": len(mask),
            "treat_ros_factor": args.treat_ros_factor,
            "seed": args.seed,
            "scenario": args.scenario,
            "wind_deg": args.wind_dir,
            "treated_source": str(args.treated_blocks),
        }
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(
        f"{args.treated_blocks.name} seed {args.seed}: "
        f"treated {result['treated_area_ha']:.1f} ha, "
        f"mean burned {result['mean_area_burned_ha']:.4f} ha, "
        f"p90 {result['p90_area_burned_ha']:.4f} ha"
    )


if __name__ == "__main__":
    main()
