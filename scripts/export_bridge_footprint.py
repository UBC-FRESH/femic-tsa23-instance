"""Export the matched-footprint oracle bundle for the WS4 directed-connectivity account.

Reproduces the exact footprint used by ``bridge_matched_footprint.py`` (seed 1,
20,000 ha), then writes everything the WS4 account needs to recompute the
directed reach without any access to this instance:

- ``topology_footprint.csv``  : ``src_block,dst_block,distance_m,bearing_deg``
  restricted to the footprint (bearing is the absolute compass bearing src->dst).
- ``block_points.csv``        : ``block_id,x,y`` representative points.
- ``footprint_blocks.csv``    : ``block_id,area_ha,base_hazard`` at period 0.
- ``oracle.json``             : measured directed metrics under the WS4 semantics.

The WS4 semantics are: a block is *flammable* when its criterion value
(``feature.FuelHazard``) is >= ``threshold``; reach is computed only through
flammable blocks. Blocks treated by the schedule (FB) read 0.05 and therefore
act as barriers. This script asserts that every footprint block is flammable at
period 0 (base hazard 1.0), so the oracle is exactly the pattern-treated set.

Usage::

    python scripts/export_bridge_footprint.py \
        --blocks output/patchworks_ft/fragments/fragments.shp \
        --fuel-types runtime/fire/fbp_stand_curves.csv \
        --topology runtime/ws4/topology_tsa23.csv \
        --dataset runtime/ws4/compiled_fb_haz \
        --schedules runtime/fire/footprint_bridge_fb_schedules \
        --out /srv/shared-data/gep/ws4/tmp/ft-bridge-oracle
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge_matched_footprint import _footprint  # noqa: E402
from landscape_spread import _adjacency, _bearing_deg, _block_fuel_types  # noqa: E402

THRESHOLD = 0.5
WIND_DEG = 225.0


def _block_hazard(dataset: Path) -> pd.Series:
    """Return the period-0 ``feature.FuelHazard`` value per block."""
    blocks = pd.read_parquet(dataset / "blocks.parquet")
    features = pd.read_parquet(dataset / "features.parquet")
    curves = pd.read_parquet(dataset / "curves.parquet")
    hazard = features[features["label"] == "feature.FuelHazard"][["track_id", "curve_id"]]
    merged = blocks.merge(hazard, on="track_id", how="left")
    # Read the curve at the block's current age (offset).
    curve = curves.set_index(["curve_id", "x"])["y"].to_dict()
    values = []
    for row in merged.itertuples(index=False):
        y = curve.get((row.curve_id, float(row.offset)))
        if y is None:
            y = curve.get((row.curve_id, 0.0))
        values.append(y if y is not None else np.nan)
    merged["hazard"] = values
    return merged.groupby("block_id")["hazard"].max()


def _reach(
    nodes: set[int],
    flammable: set[int],
    adj: dict[int, list[tuple[int, float]]],
    centroids: dict[int, tuple[float, float]],
    wind_deg: float,
) -> dict[str, float]:
    """Directed reach through flammable blocks only."""
    sizes: list[int] = []
    for start in flammable:
        seen = {start}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbour, _d in adj.get(node, []):
                if neighbour in flammable and neighbour not in seen:
                    x0, y0 = centroids[node]
                    x1, y1 = centroids[neighbour]
                    bearing = _bearing_deg(x0, y0, x1, y1)
                    delta = abs(((bearing - wind_deg + 180.0) % 360.0) - 180.0)
                    if delta <= 90.0:
                        seen.add(neighbour)
                        queue.append(neighbour)
        sizes.append(len(seen))
    cut = 0
    for node in flammable:
        for neighbour, _d in adj.get(node, []):
            if neighbour in nodes and neighbour not in flammable:
                x0, y0 = centroids[node]
                x1, y1 = centroids[neighbour]
                bearing = _bearing_deg(x0, y0, x1, y1)
                delta = abs(((bearing - wind_deg + 180.0) % 360.0) - 180.0)
                if delta <= 90.0:
                    cut += 1
    return {
        "flammable_blocks": len(flammable),
        "directed_largest_reach": float(max(sizes) if sizes else 0),
        "directed_mean_reach": float(np.mean(sizes)) if sizes else 0.0,
        "directed_edge_cut": float(cut),
    }


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, required=True)
    parser.add_argument("--fuel-types", type=Path, required=True, dest="fuel_types")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--schedules", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--footprint-ha", type=float, default=20000.0, dest="footprint_ha")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    blocks = _block_fuel_types(args.blocks, args.fuel_types, "p90", 60)
    adj = _adjacency(args.topology)
    area = blocks.set_index("block_id")["area_ha"].to_dict()
    centroids = {
        int(b): (float(x), float(y))
        for b, x, y in zip(blocks["block_id"], blocks["x"], blocks["y"])
    }
    eligible = set(
        blocks.loc[
            (~blocks["treated"]) & blocks["fuel_type"].isin(["C2", "C3", "C7"]), "block_id"
        ].to_numpy()
    )
    rng = np.random.default_rng(args.seed)
    seed_block = int(rng.choice(sorted(eligible)))
    footprint = _footprint(adj, area, eligible, seed_block, args.footprint_ha)
    print(f"footprint: {len(footprint)} blocks, {sum(area[b] for b in footprint):.1f} ha")

    hazard = _block_hazard(args.dataset)
    missing = [b for b in footprint if b not in hazard.index or pd.isna(hazard.get(b))]
    if missing:
        raise SystemExit(f"{len(missing)} footprint blocks have no hazard value")
    base = {b: float(hazard[b]) for b in footprint}
    flammable_base = {b for b in footprint if base[b] >= THRESHOLD}
    print(f"base flammable: {len(flammable_base)} / {len(footprint)}")
    if len(flammable_base) != len(footprint):
        bad = sorted(set(footprint) - flammable_base)[:10]
        raise SystemExit(f"footprint contains pre-treated blocks (hazard < {THRESHOLD}): {bad}")

    args.out.mkdir(parents=True, exist_ok=True)
    topo = pd.read_csv(args.topology)
    topo = topo[topo["src_block"].isin(footprint) & topo["dst_block"].isin(footprint)].copy()
    topo["bearing_deg"] = [
        _bearing_deg(centroids[int(s)][0], centroids[int(s)][1], centroids[int(d)][0], centroids[int(d)][1])
        for s, d in zip(topo["src_block"], topo["dst_block"])
    ]
    topo.to_csv(args.out / "topology_footprint.csv", index=False)
    pd.DataFrame(
        {"block_id": sorted(footprint), "x": [centroids[b][0] for b in sorted(footprint)],
         "y": [centroids[b][1] for b in sorted(footprint)]}
    ).to_csv(args.out / "block_points.csv", index=False)
    pd.DataFrame(
        {"block_id": sorted(footprint), "area_ha": [area[b] for b in sorted(footprint)],
         "base_hazard": [base[b] for b in sorted(footprint)]}
    ).to_csv(args.out / "footprint_blocks.csv", index=False)

    result: dict[str, object] = {
        "footprint_blocks": len(footprint),
        "footprint_ha": float(sum(area[b] for b in footprint)),
        "threshold": THRESHOLD,
        "wind_direction_deg": WIND_DEG,
        "patterns": {},
    }
    for sched in sorted(args.schedules.glob("*_sched.csv")):
        pattern = sched.name.replace("_sched.csv", "")
        treated = set(pd.read_csv(sched)["block_id"].astype(int))
        treated &= footprint
        flammable = footprint - treated
        metrics = _reach(footprint, flammable, adj, centroids, WIND_DEG)
        result["patterns"][pattern] = {
            "treated_blocks": len(treated),
            "treated_ha": float(sum(area[b] for b in treated)),
            **metrics,
        }
        print(f"{pattern:8s} treated={len(treated):4d} largest={metrics['directed_largest_reach']:.0f} "
              f"mean={metrics['directed_mean_reach']:.1f} cut={metrics['directed_edge_cut']:.0f}")
    (args.out / "oracle.json").write_text(json.dumps(result, indent=2))
    ranked = sorted(result["patterns"], key=lambda p: result["patterns"][p]["directed_largest_reach"])
    print("directed_largest_reach ranking:", ranked)


if __name__ == "__main__":
    main()
