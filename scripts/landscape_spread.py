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

TREATMENT_ROS_FACTOR = 0.6  # provisional fallback spread multiplier on treated blocks
# Spread multipliers from the model's fuel-hazard curves (feature.FuelHazard):
# 1.0 baseline, 0.4 thinning (FT), 0.2 surface fuel (SF), 0.05 fuel break (FB).
TREATMENT_HAZARD = {"ft": 0.4, "sf": 0.2, "fb": 0.05}


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
    centroid = gdf.geometry.representative_point()
    frame = pd.DataFrame(
        {
            "block_id": gdf["BLOCK"].astype("int64"),
            "au_id": gdf["AU"].astype("int64"),
            "silv_state": gdf["SILV_STATE"].astype("string"),
            "area_ha": pd.to_numeric(gdf["AREA_HA"], errors="coerce").fillna(0.0),
            "x": centroid.x.to_numpy(),
            "y": centroid.y.to_numpy(),
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


def load_block_hazard(dataset: Path, block_ids: set[int] | None = None) -> dict[int, float]:
    """Return the per-block ``feature.FuelHazard`` value at the block's current age.

    This is the dataset-fed counterpart to the flat ``TREATMENT_HAZARD`` constants. The
    value is the area-weighted mean over the block's fragment rows, matching how WS4's
    ``Simulator.block_criteria`` treats a product or feature criterion.

    Parameters
    ----------
    dataset : Path
        A compiled WS4 dataset directory.
    block_ids : set of int, optional
        Restrict the result to these blocks.

    Returns
    -------
    dict of int to float
        Block id to hazard multiplier. Blocks without a hazard feature fall back to 1.0.
    """
    blocks = pd.read_parquet(dataset / "blocks.parquet")
    features = pd.read_parquet(dataset / "features.parquet")
    curves = pd.read_parquet(dataset / "curves.parquet")
    hazard = features[features["label"] == "feature.FuelHazard"][["track_id", "curve_id"]]
    merged = blocks.merge(hazard, on="track_id", how="left")
    if block_ids is not None:
        merged = merged[merged["block_id"].isin(block_ids)]
    values = curves.set_index(["curve_id", "x"])["y"].to_dict()
    rows: list[dict[str, float]] = []
    for row in merged.itertuples(index=False):
        curve_id = getattr(row, "curve_id", None)
        if pd.isna(curve_id):
            value = 1.0
        else:
            value = values.get((curve_id, float(row.offset)))
            if value is None:
                value = values.get((curve_id, 0.0), 1.0)
        rows.append({"block_id": int(row.block_id), "area_ha": float(row.area_ha), "hazard": float(value)})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {}
    weighted = frame.groupby("block_id").apply(
        lambda g: float((g["hazard"] * g["area_ha"]).sum() / g["area_ha"].sum())
        if g["area_ha"].sum() > 0
        else float(g["hazard"].mean()),
        include_groups=False,
    )
    return {int(block): float(value) for block, value in weighted.items()}


def _adjacency(topology: Path) -> dict[int, list[tuple[int, float]]]:
    """Return an undirected adjacency map from the topology CSV."""
    topo = pd.read_csv(topology)
    adj: dict[int, list[tuple[int, float]]] = {}
    for row in topo.itertuples(index=False):
        src, dst, dist = int(row.src_block), int(row.dst_block), float(row.distance_m)
        adj.setdefault(src, []).append((dst, dist))
        adj.setdefault(dst, []).append((src, dist))
    return adj


def _directional_factor(bearing_deg: float, wind_deg: float) -> float:
    """Return a spread-rate factor from a bearing relative to the wind.

    Head fire (bearing aligned with the wind) spreads fastest; back fire
    slowest. A simple ellipse approximation: 1.0 head, ~0.6 flank, 0.2 back.
    """
    angle = np.radians(bearing_deg - wind_deg)
    return 0.2 + 0.8 * ((1.0 + np.cos(angle)) / 2.0)


def _bearing_deg(x0: float, y0: float, x1: float, y1: float) -> float:
    """Return the compass bearing (degrees) from (x0,y0) to (x1,y1)."""
    return float(np.degrees(np.arctan2(x1 - x0, y1 - y0)) % 360.0)


def _travel_times(
    adj: dict[int, list[tuple[int, float]]],
    traversal_min: dict[int, float],
    centroids: dict[int, tuple[float, float]],
    wind_deg: float,
    source: int,
) -> dict[int, float]:
    """Return minimum fire arrival time (minutes) from a source block.

    Fire crosses to an adjacent block at that block's traversal time (its
    characteristic length over its rate of spread), scaled by a directional
    factor from the spread bearing relative to the wind.
    """
    times: dict[int, float] = {source: 0.0}
    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        time, node = heapq.heappop(heap)
        if time > times.get(node, float("inf")):
            continue
        x0, y0 = centroids.get(node, (0.0, 0.0))
        for neighbour, _distance in adj.get(node, []):
            step = traversal_min.get(neighbour, float("inf"))
            if not np.isfinite(step):
                continue
            x1, y1 = centroids.get(neighbour, (x0, y0))
            factor = _directional_factor(_bearing_deg(x0, y0, x1, y1), wind_deg)
            new_time = time + step / max(factor, 1e-6)
            if new_time < times.get(neighbour, float("inf")):
                times[neighbour] = new_time
                heapq.heappush(heap, (new_time, neighbour))
    return times


def simulate_fast(
    *,
    blocks: pd.DataFrame,
    adj: dict[int, list[tuple[int, float]]],
    ignitions: int,
    duration_min: float,
    seed: int,
    wind_deg: float,
) -> dict[str, object]:
    """Run the Monte Carlo spread with a sparse multi-source Dijkstra.

    Same model as :func:`simulate`, evaluated as one shortest-path call over a
    directed weighted graph: the weight of ``u -> v`` is ``v``'s traversal time
    divided by the directional factor of the ``u -> v`` bearing. All ignitions are
    solved together, which is what makes a sweep cheap enough to explore.

    The reference implementation stays in :func:`simulate` for equivalence checks.
    """
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra

    rng = np.random.default_rng(seed)
    block_ids = blocks["block_id"].to_numpy()
    index = {int(b): i for i, b in enumerate(block_ids)}
    area = blocks["area_ha"].to_numpy(dtype=float)
    ros = blocks["ros_eff"].to_numpy(dtype=float)
    centroids = {
        int(b): (float(x), float(y))
        for b, x, y in zip(block_ids, blocks["x"], blocks["y"])
    }
    traversal = np.where(
        ros > 0.0,
        np.sqrt(np.maximum(area, 0.0) * 10000.0) / np.where(ros > 0.0, ros, 1.0),
        np.inf,
    )

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for src, neighbours in adj.items():
        i = index.get(int(src))
        if i is None:
            continue
        x0, y0 = centroids[int(src)]
        for dst, _distance in neighbours:
            j = index.get(int(dst))
            if j is None or not np.isfinite(traversal[j]):
                continue
            x1, y1 = centroids[int(dst)]
            factor = _directional_factor(_bearing_deg(x0, y0, x1, y1), wind_deg)
            rows.append(i)
            cols.append(j)
            data.append(float(traversal[j] / max(factor, 1e-6)))

    graph = csr_matrix((data, (rows, cols)), shape=(len(block_ids), len(block_ids)))
    ignited = rng.choice(block_ids, size=min(ignitions, len(block_ids)), replace=False)
    sources = np.array([index[int(b)] for b in ignited], dtype=int)
    times = dijkstra(graph, directed=True, indices=sources)
    if times.ndim == 1:
        times = times.reshape(1, -1)
    reached = times <= duration_min
    area_burned = reached.astype(float) @ area
    burn_count = reached.sum(axis=0)
    burn_prob = burn_count / max(len(sources), 1)

    return {
        "ignitions": int(len(sources)),
        "duration_min": duration_min,
        "total_area_ha": float(area.sum()),
        "mean_area_burned_ha": float(np.mean(area_burned)),
        "p90_area_burned_ha": float(np.quantile(area_burned, 0.9)),
        "treated_area_ha": float(area[blocks["treated"].to_numpy(dtype=bool)].sum()),
        "mean_burn_probability": float(np.mean(burn_prob)),
        "burn_probability": {str(int(b)): float(c) for b, c in zip(block_ids, burn_prob)},
    }


def simulate(
    *,
    blocks: pd.DataFrame,
    adj: dict[int, list[tuple[int, float]]],
    ignitions: int,
    duration_min: float,
    seed: int,
    wind_deg: float,
) -> dict[str, object]:
    """Run the Monte Carlo spread and return landscape outcome statistics."""
    rng = np.random.default_rng(seed)
    block_ids = blocks["block_id"].to_numpy()
    area = blocks.set_index("block_id")["area_ha"].to_dict()
    ros = blocks.set_index("block_id")["ros_eff"].to_dict()
    centroids = {
        int(b): (float(x), float(y))
        for b, x, y in zip(block_ids, blocks["x"], blocks["y"])
    }
    # Traversal time: characteristic block length (m) over rate of spread (m/min).
    traversal_min = {
        int(b): (np.sqrt(max(a, 0.0) * 10000.0) / r) if r > 0.0 else float("inf")
        for b, a, r in zip(block_ids, blocks["area_ha"], blocks["ros_eff"])
    }
    ignited = rng.choice(block_ids, size=min(ignitions, len(block_ids)), replace=False)

    burn_count = {int(b): 0 for b in block_ids}
    area_burned: list[float] = []
    for source in ignited:
        times = _travel_times(adj, traversal_min, centroids, wind_deg, int(source))
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
        "--treat-pattern",
        default="random",
        choices=["random", "clumped", "barrier", "band"],
        dest="treat_pattern",
    )
    parser.add_argument("--clusters", type=int, default=20)
    parser.add_argument("--stripes", type=int, default=10)
    parser.add_argument("--ignitions", type=int, default=200)
    parser.add_argument("--duration-min", type=float, default=480.0, dest="duration_min")
    parser.add_argument("--wind-dir", type=float, default=225.0, dest="wind_dir")
    parser.add_argument("--treat-ros-factor", type=float, default=0.6, dest="treat_ros_factor")
    parser.add_argument(
        "--treatment", choices=sorted(TREATMENT_HAZARD), default=None,
        help="Use the model's hazard multiplier for this treatment (ft/sf/fb).",
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--method",
        choices=("fast", "reference"),
        default="fast",
        help="fast uses a sparse multi-source Dijkstra; reference is the per-ignition loop",
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    blocks = _block_fuel_types(args.blocks, args.fuel_types, args.scenario, args.age)
    treat_factor = (
        TREATMENT_HAZARD[args.treatment] if args.treatment else args.treat_ros_factor
    )
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
        if args.treat_pattern == "band":
            # A single continuous band perpendicular to the wind (no gaps).
            wx = np.sin(np.radians(args.wind_dir))
            wy = np.cos(np.radians(args.wind_dir))
            coords = blocks.set_index("block_id")[["x", "y"]]
            proj = coords["x"] * wx + coords["y"] * wy
            eligible_frame = blocks.loc[blocks["block_id"].isin(eligible_ids), ["block_id"]]
            proj_eligible = proj.reindex(eligible_frame["block_id"]).dropna()
            centre = float(proj_eligible.median())
            ordered = [
                int(b)
                for b in (proj_eligible - centre).abs().sort_values().index
            ]
            for node in ordered:
                if treated_area >= target_area:
                    break
                chosen.add(node)
                treated_area += area_by_block.get(node, 0.0)
        elif args.treat_pattern == "barrier":
            # Stripes perpendicular to the wind: treat alternate stripes.
            wx = np.sin(np.radians(args.wind_dir))
            wy = np.cos(np.radians(args.wind_dir))
            coords = blocks.set_index("block_id")[["x", "y"]]
            proj = coords["x"] * wx + coords["y"] * wy
            lo, hi = float(proj.min()), float(proj.max())
            stripe = ((proj - lo) / max(hi - lo, 1e-9) * args.stripes).astype(int)
            ordered = [
                int(b)
                for b in blocks.loc[blocks["block_id"].isin(eligible_ids), "block_id"]
                if int(stripe.get(b, 0)) % 2 == 0
            ]
            for node in ordered:
                if treated_area >= target_area:
                    break
                chosen.add(node)
                treated_area += area_by_block.get(node, 0.0)
        elif args.treat_pattern == "clumped":
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
            blocks["ros_m_per_min"] * treat_factor,
            blocks["ros_m_per_min"],
        )
        print(f"treated pattern={args.treat_pattern} blocks={len(chosen)}")
        blocks_path = args.out.with_name(args.out.stem + "_blocks.csv")
        blocks_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"block_id": sorted(chosen)}).to_csv(blocks_path, index=False)
    result = (simulate_fast if args.method == "fast" else simulate)(
        blocks=blocks,
        adj=adj,
        ignitions=args.ignitions,
        duration_min=args.duration_min,
        seed=args.seed,
        wind_deg=args.wind_dir,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    summary = {k: v for k, v in result.items() if k != "burn_probability"}
    args.out.write_text(json.dumps(result))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
