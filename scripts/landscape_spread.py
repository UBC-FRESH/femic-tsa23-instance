"""Landscape fire-spread simulation on the TSA23 block topology.

A first-pass stochastic spread model that consumes the stand-scale FBP fire
behaviour and produces landscape outcomes (burn probability, area burned) as a
function of the fuel pattern. It is deliberately simple and auditable:

- nodes are blocks; edges are the block adjacency topology (``distance_m``);
- each block's effective head-fire rate of spread comes from its AU's FBP fuel
  type under a fire-weather scenario;
- fire spreads by minimum travel time (Dijkstra) from an ignition block, and a
  block burns when its arrival time is within a fixed suppression-free duration;
- repeating over many ignition points gives a burn probability per block.

The purpose is the Paper 2 bridge: measure how the fuel *pattern* (which blocks
are treated) changes landscape outcomes, so the response can be compiled into
WS4 patch accounts.

Usage::

    python scripts/landscape_spread.py \
        --blocks output/patchworks_ft/fragments/fragments.shp \
        --fuel-types runtime/fire/fbp_stand_curves.csv \
        --topology runtime/ws4/topology_tsa23.csv \
        --scenario p90 --ignitions 200 --duration-min 480 \
        --out runtime/fire/spread_baseline.json
"""

from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

TREATMENT_ROS_FACTOR = 0.6  # provisional: reduced crown-fire spread on thinned blocks


def _block_fuel_types(blocks: Path, fuel_types: Path, scenario: str, age: int) -> pd.DataFrame:
    """Return per-block fuel type, ROS, area, and treated flag.

    Parameters
    ----------
    blocks : Path
        The fragments/block shapefile (BLOCK, AU, IFM, SILV_STATE).
    fuel_types : Path
        The FBP stand-curve CSV (au_id, fuel_type, scenario, state, age, ros).
    scenario : str
        The fire-weather scenario name.
    age : int
        The stand age at which to read the ROS.

    Returns
    -------
    pandas.DataFrame
        One row per block.
    """
    gdf = gpd.read_file(blocks)
    frame = pd.DataFrame(
        {
            "block_id": gdf["BLOCK"].astype("int64"),
            "au_id": gdf["AU"].astype("int64"),
            "silv_state": gdf["SILV_STATE"].astype("string"),
            "area_ha": pd.to_numeric(gdf["AREA_HA"], errors="coerce").fillna(0.0),
        }
    )
    curves = pd.read_csv(fuel_types)
    ros = (
        curves[(curves["scenario"] == scenario) & (curves["state"] == "untreated") & (curves["age"] == age)]
        .set_index("au_id")["ros_m_per_min"]
    )
    fuel = (
        curves[(curves["scenario"] == scenario) & (curves["age"] == age)]
        .drop_duplicates("au_id")
        .set_index("au_id")["fuel_type"]
    )
    frame["fuel_type"] = frame["au_id"].map(fuel)
    frame["ros_m_per_min"] = frame["au_id"].map(ros).astype(float)
    # A block is treated when its silviculture state is a fuel-treated state.
    frame["treated"] = frame["silv_state"].astype(str).str.contains("_ft", na=False)
    frame["ros_eff"] = np.where(
        frame["treated"], frame["ros_m_per_min"] * TREATMENT_ROS_FACTOR, frame["ros_m_per_min"]
    )
    return frame


def _adjacency(topology: Path) -> dict[int, list[tuple[int, float]]]:
    """Return an undirected adjacency map from the topology CSV."""
    topo = pd.read_csv(topology)
    adj: dict[int, list[tuple[int, float]]] = {}
    for row in topo.itertuples(index=False):
        src, dst, dist = int(row.src_block), int(row.dst_block), float(row.distance_m)
        adj.setdefault(src, []).append((dst, dist))
        adj.setdefault(dst, []).append((src, dist))
    return adj


def _travel_times(
    adj: dict[int, list[tuple[int, float]]],
    traversal_min: dict[int, float],
    source: int,
) -> dict[int, float]:
    """Return minimum fire arrival time (minutes) from a source block.

    Fire crosses from a block to an adjacent block at the target block's
    traversal time (its characteristic length over its rate of spread), so
    touching blocks are not crossed instantaneously.
    """
    times: dict[int, float] = {source: 0.0}
    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        time, node = heapq.heappop(heap)
        if time > times.get(node, float("inf")):
            continue
        for neighbour, _distance in adj.get(node, []):
            step = traversal_min.get(neighbour, float("inf"))
            if not np.isfinite(step):
                continue
            new_time = time + step
            if new_time < times.get(neighbour, float("inf")):
                times[neighbour] = new_time
                heapq.heappush(heap, (new_time, neighbour))
    return times


def simulate(
    *,
    blocks: pd.DataFrame,
    adj: dict[int, list[tuple[int, float]]],
    ignitions: int,
    duration_min: float,
    seed: int,
) -> dict[str, object]:
    """Run the Monte Carlo spread and return landscape outcome statistics."""
    rng = np.random.default_rng(seed)
    block_ids = blocks["block_id"].to_numpy()
    area = blocks.set_index("block_id")["area_ha"].to_dict()
    ros = blocks.set_index("block_id")["ros_eff"].to_dict()
    # Traversal time: characteristic block length (m) over rate of spread (m/min).
    traversal_min = {
        int(b): (np.sqrt(max(a, 0.0) * 10000.0) / r) if r > 0.0 else float("inf")
        for b, a, r in zip(block_ids, blocks["area_ha"], blocks["ros_eff"])
    }
    ignited = rng.choice(block_ids, size=min(ignitions, len(block_ids)), replace=False)

    burn_count = {int(b): 0 for b in block_ids}
    area_burned: list[float] = []
    for source in ignited:
        times = _travel_times(adj, traversal_min, int(source))
        reached = [b for b, t in times.items() if t <= duration_min]
        for b in reached:
            burn_count[int(b)] = burn_count.get(int(b), 0) + 1
        area_burned.append(float(sum(area.get(b, 0.0) for b in reached)))

    total_area = float(blocks["area_ha"].sum())
    burn_prob = {str(b): c / len(ignited) for b, c in burn_count.items()}
    return {
        "ignitions": int(len(ignited)),
        "duration_min": duration_min,
        "total_area_ha": total_area,
        "mean_area_burned_ha": float(np.mean(area_burned)),
        "p90_area_burned_ha": float(np.quantile(area_burned, 0.9)),
        "treated_area_ha": float(blocks.loc[blocks["treated"], "area_ha"].sum()),
        "mean_burn_probability": float(np.mean(list(burn_prob.values()))),
        "burn_probability": burn_prob,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, required=True)
    parser.add_argument("--fuel-types", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--scenario", default="p90")
    parser.add_argument("--age", type=int, default=60)
    parser.add_argument("--treat-fraction", type=float, default=0.0, dest="treat_fraction")
    parser.add_argument(
        "--treat-pattern", default="random", choices=["random", "clumped"], dest="treat_pattern"
    )
    parser.add_argument("--clusters", type=int, default=20)
    parser.add_argument("--ignitions", type=int, default=200)
    parser.add_argument("--duration-min", type=float, default=480.0, dest="duration_min")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    blocks = _block_fuel_types(args.blocks, args.fuel_types, args.scenario, args.age)
    adj = _adjacency(args.topology)
    if args.treat_fraction > 0.0:
        rng = np.random.default_rng(args.seed)
        eligible_ids = set(
            blocks.loc[
                (~blocks["treated"]) & blocks["fuel_type"].isin(["C2", "C3", "C7"]), "block_id"
            ].to_numpy()
        )
        area_by_block = blocks.set_index("block_id")["area_ha"].to_dict()
        eligible_area = sum(area_by_block.get(b, 0.0) for b in eligible_ids)
        target_area = min(1.0, args.treat_fraction) * eligible_area
        chosen: set[int] = set()
        treated_area = 0.0
        if args.treat_pattern == "clumped":
            seeds = rng.choice(list(eligible_ids), size=args.clusters, replace=False)
            for seed in seeds:
                queue = [int(seed)]
                cluster: set[int] = set()
                while queue:
                    node = queue.pop(0)
                    if node in cluster or node not in eligible_ids:
                        continue
                    cluster.add(node)
                    for neighbour, _d in adj.get(node, []):
                        if neighbour in eligible_ids and neighbour not in cluster:
                            queue.append(neighbour)
                for node in sorted(cluster):
                    if treated_area >= target_area:
                        break
                    if node not in chosen:
                        chosen.add(node)
                        treated_area += area_by_block.get(node, 0.0)
                if treated_area >= target_area:
                    break
        else:
            ids = list(eligible_ids)
            rng.shuffle(ids)
            for node in ids:
                if treated_area >= target_area:
                    break
                chosen.add(int(node))
                treated_area += area_by_block.get(node, 0.0)
        blocks.loc[blocks["block_id"].isin(chosen), "treated"] = True
        blocks["ros_eff"] = np.where(
            blocks["treated"],
            blocks["ros_m_per_min"] * TREATMENT_ROS_FACTOR,
            blocks["ros_m_per_min"],
        )
        print(f"treated pattern={args.treat_pattern} blocks={len(chosen)}")
    result = simulate(
        blocks=blocks,
        adj=adj,
        ignitions=args.ignitions,
        duration_min=args.duration_min,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary = {k: v for k, v in result.items() if k != "burn_probability"}
    args.out.write_text(json.dumps(result))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
