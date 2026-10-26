"""Check where a schedule's treatments land, against hazard and burn probability.

A cost-per-hazard ranking is blind to where fire is likely. This compares the chosen blocks
with the landscape on hazard and on the spread model's burn probability, and measures how
clustered the choice is — a human check on a schedule that looks fine as a number.

Usage::

    python scripts/check_treated_map.py \
        --geopackage runtime/ws4/greedy_hazard/schedule.gpkg \
        --dataset runtime/ws4/compiled_sf \
        --burn-probability /tmp/burnprob.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_spread import load_block_hazard  # noqa: E402


def _components(blocks: set[int], adj: dict[int, list[int]]) -> list[int]:
    """Connected-component sizes within ``blocks``."""
    remaining = set(blocks)
    sizes: list[int] = []
    while remaining:
        start = remaining.pop()
        size = 1
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbour in adj.get(node, []):
                if neighbour in remaining:
                    remaining.discard(neighbour)
                    queue.append(neighbour)
                    size += 1
        sizes.append(size)
    return sizes


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geopackage", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_sf"))
    parser.add_argument("--burn-probability", type=Path, required=True, dest="burn_probability")
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    args = parser.parse_args()

    frame = gpd.read_file(args.geopackage, layer="schedule")
    treated = frame[frame["treated"]]
    all_blocks = set(frame["block_id"].astype(int))
    treated_ids = set(treated["block_id"].astype(int))

    hazard = load_block_hazard(args.dataset)
    payload = json.loads(args.burn_probability.read_text())
    probability = {int(k): float(v) for k, v in (payload.get("burn_probability") or payload).items()}

    frame = frame.assign(
        hazard=frame["block_id"].map(hazard),
        burn=frame["block_id"].map(probability),
    )
    frame["hazard"] = frame["hazard"].fillna(1.0)
    frame["burn"] = frame["burn"].fillna(0.0)

    print(f"blocks: {len(frame):,} | treated: {len(treated_ids):,}")
    print()
    print(f"{'metric':28s} {'treated':>10s} {'landscape':>10s} {'ratio':>7s}")
    for column in ("hazard", "burn", "area_ha"):
        t = frame.loc[frame["treated"], column].mean()
        a = frame[column].mean()
        print(f"{column:28s} {t:10.4f} {a:10.4f} {t / a if a else float('nan'):7.2f}")

    # How much of the choice lands in the highest-risk fifth?
    threshold = np.quantile(frame["burn"], 0.8)
    top_share_all = float((frame["burn"] >= threshold).mean())
    top_share_treated = float((frame.loc[frame["treated"], "burn"] >= threshold).mean())
    print()
    print(f"top-quintile burn probability covers {top_share_all:.1%} of blocks")
    print(f"  and {top_share_treated:.1%} of the treated set ({top_share_treated / top_share_all:.2f}x)")

    # Clustering over the topology.
    adj: dict[int, list[int]] = {}
    for src, dst, _distance in pd.read_csv(args.topology).itertuples(index=False):
        adj.setdefault(int(src), []).append(int(dst))
        adj.setdefault(int(dst), []).append(int(src))
    sizes = _components(treated_ids, adj)
    area_by_block = frame.set_index("block_id")["area_ha"].to_dict()
    component_area = []
    remaining = set(treated_ids)
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbour in adj.get(node, []):
                if neighbour in remaining:
                    remaining.discard(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        component_area.append(sum(area_by_block.get(b, 0.0) for b in component))
    component_area.sort(reverse=True)
    print()
    print(f"components: {len(sizes):,} | largest {component_area[0]:,.0f} ha "
          f"({component_area[0] / sum(component_area):.0%} of treated area)")
    print(f"  top 5 components: {[round(a) for a in component_area[:5]]} ha")

    bounds_all = frame.total_bounds
    bounds_treated = treated.total_bounds
    print()
    print(f"extent all:     {bounds_all.round(0).tolist()}")
    print(f"extent treated: {bounds_treated.round(0).tolist()}")


if __name__ == "__main__":
    main()
