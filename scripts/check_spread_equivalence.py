"""Check that the sparse spread solver reproduces the reference solver.

Compares :func:`landscape_spread.simulate_fast` against
:func:`landscape_spread.simulate` on explicit treated-block masks, and reports the
runtime of each. The equivalence check is the gate for making the fast path the
default.

Usage::

    python scripts/check_spread_equivalence.py \
        --cases runtime/fire/bridge_barrier_blocks.csv \
        --cases /srv/shared-data/gep/ws4/ws4/tmp/bridge-masks-dedup/treated_barrier.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_spread import (  # noqa: E402
    _adjacency,
    _block_fuel_types,
    simulate,
    simulate_fast,
)

SCALARS = ("mean_area_burned_ha", "p90_area_burned_ha", "total_area_ha", "treated_area_ha")


def _frame(mask_path: Path, blocks_path: Path, fuel_types: Path, factor: float) -> pd.DataFrame:
    """Return the block table with the mask applied as the treated set."""
    frame = _block_fuel_types(blocks_path, fuel_types, "p90", 60).copy()
    mask = set(pd.read_csv(mask_path)["block_id"].astype(int))
    frame["treated"] = frame["block_id"].isin(mask)
    frame["ros_eff"] = frame["ros_m_per_min"] * frame["treated"].map(
        {True: factor, False: 1.0}
    )
    return frame


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, action="append", required=True)
    parser.add_argument("--blocks", type=Path, default=Path("output/patchworks_ft/fragments/fragments.shp"))
    parser.add_argument("--fuel-types", type=Path, default=Path("runtime/fire/fbp_stand_curves.csv"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument("--treat-ros-factor", type=float, default=0.3, dest="treat_ros_factor")
    parser.add_argument("--ignitions", type=int, default=50)
    parser.add_argument("--duration-min", type=float, default=480.0, dest="duration_min")
    parser.add_argument("--wind-dir", type=float, default=225.0, dest="wind_dir")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    adj = _adjacency(args.topology)
    failures = 0
    for mask_path in args.cases:
        frame = _frame(mask_path, args.blocks, args.fuel_types, args.treat_ros_factor)
        start = time.perf_counter()
        reference = simulate(
            blocks=frame,
            adj=adj,
            ignitions=args.ignitions,
            duration_min=args.duration_min,
            seed=args.seed,
            wind_deg=args.wind_dir,
        )
        t_ref = time.perf_counter() - start
        start = time.perf_counter()
        fast = simulate_fast(
            blocks=frame,
            adj=adj,
            ignitions=args.ignitions,
            duration_min=args.duration_min,
            seed=args.seed,
            wind_deg=args.wind_dir,
        )
        t_fast = time.perf_counter() - start

        deltas = {k: abs(fast[k] - reference[k]) for k in SCALARS}
        ref_prob = reference["burn_probability"]
        fast_prob = fast["burn_probability"]
        prob_delta = max(
            abs(fast_prob[b] - ref_prob[b]) for b in ref_prob if b in fast_prob
        )
        worst = max(deltas.values())
        ok = worst < 1e-6 and prob_delta < 1e-12
        failures += 0 if ok else 1
        print(
            f"{mask_path.name:28s} ref {t_ref:7.1f}s  fast {t_fast:6.1f}s  "
            f"speedup {t_ref / t_fast:5.1f}x  max_delta {worst:.3e}  "
            f"prob_delta {prob_delta:.1e}  {'OK' if ok else 'MISMATCH'}"
        )
        if not ok:
            for key, value in deltas.items():
                print(f"    {key}: ref {reference[key]:.6f} fast {fast[key]:.6f} delta {value:.3e}")
    print(f"\n{'PASS' if failures == 0 else 'FAIL'} ({failures} mismatch(es))")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
