"""Bridge test: can WS4 patch accounts reproduce the fire-spread ranking?

For three equal-area fuel-treatment patterns (random, clumped, and a
wind-perpendicular barrier), this compares:

- the landscape fire-spread outcome (mean area burned) from
  ``landscape_spread.py``, and
- WS4's patch-size accounts for the same treated blocks.

The question is whether a WS4 patch account (size classes, search distance)
ranks the patterns the way the fire model does. If it does not, the missing
account is the extension WS4 needs.

Usage::

    python scripts/ws4_bridge_test.py --dataset runtime/ws4/compiled_ft_econ \
        --topology runtime/ws4/topology_tsa23.csv --fire-dir runtime/fire
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from ws4.patch.accounts import PatchAccount
from ws4.sim.engine import Simulator

PATTERNS = ("random", "clumped", "barrier")


def run(*, dataset: Path, topology: Path, fire_dir: Path, out_dir: Path) -> pd.DataFrame:
    """Compute fire outcomes and WS4 patch accounts for each pattern."""
    sim = Simulator.from_dataset(dataset)
    rows: list[dict[str, object]] = []
    for pattern in PATTERNS:
        fire = json.loads((fire_dir / f"bridge_{pattern}.json").read_text())
        blocks = pd.read_csv(fire_dir / f"bridge_{pattern}_blocks.csv")
        schedule = fire_dir / f"bridge_{pattern}_sched.csv"
        blocks.assign(treatment="FT", period=0).to_csv(schedule, index=False)
        account = PatchAccount(
            name="patch.ft",
            criteria="product.Treated.managed.FT",
            threshold=0.5,
            size_classes=(10.0, 50.0, 150.0, 400.0, float("inf")),
            search_distance=0.0,
        )
        sim.run(
            schedule,
            1,
            out_dir / f"bridge_{pattern}",
            topology_csv=topology,
            patch_accounts=(account,),
        )
        pa = pd.read_csv(out_dir / f"bridge_{pattern}" / "patch_accounts.csv").iloc[0]
        rows.append(
            {
                "pattern": pattern,
                "mean_burned_ha": fire["mean_area_burned_ha"],
                "ws4_total_ha": float(pa["patch.ft.TOTAL.area"]),
                "ws4_patches": float(pa["patch.ft.TOTAL.frequency"]),
                "ws4_pct_400plus": float(pa.get("patch.ft.400_9999999.size", float("nan"))),
            }
        )
    return pd.DataFrame(rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--fire-dir", type=Path, required=True, dest="fire_dir")
    parser.add_argument("--out-dir", type=Path, default=Path("runtime/ws4"), dest="out_dir")
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    frame = run(
        dataset=args.dataset,
        topology=args.topology,
        fire_dir=args.fire_dir,
        out_dir=args.out_dir,
    )
    frame = frame.sort_values("mean_burned_ha")
    print(frame.to_string(index=False))
    fire_rank = list(frame["pattern"])
    size_rank = list(frame.sort_values("ws4_pct_400plus", ascending=False)["pattern"])
    print("\nfire rank (best first):", fire_rank)
    print("size rank (largest 400+ share first):", size_rank)
    print("agree:", fire_rank == size_rank)


if __name__ == "__main__":
    main()
