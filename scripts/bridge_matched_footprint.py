"""Matched-footprint bridge test: does a connectivity account rank the fire outcome?

The existing bridge test compares treatment patterns at equal *area* but different
*footprints*, which confounds "where" with "how". This script fixes the footprint
(a contiguous block cluster), lays out the patterns **inside** it at equal treated
area and equal block count, ignites fires inside it, and then compares:

- the fire-spread outcome (mean area burned), against
- simple connectivity metrics of the treated/untreated partition
  (largest untreated component, mean component size, treated-crossing edges).

If the connectivity metrics rank the patterns the way the fire model does
(``barrier < clumped < random``), the bridge has a signal to compile into WS4.

Usage::

    python scripts/bridge_matched_footprint.py \
        --blocks output/patchworks_ft/fragments/fragments.shp \
        --fuel-types runtime/fire/fbp_stand_curves.csv \
        --topology runtime/ws4/topology_tsa23.csv \
        --footprint-ha 20000 --treat-fraction 0.2 --treatment fb \
        --ignitions 40 --duration-min 480 --wind-dir 225 \
        --out runtime/fire/footprint_bridge.json
"""

from __future__ import annotations

import argparse
import heapq
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape_spread import (  # noqa: E402
    TREATMENT_HAZARD,
    _adjacency,
    _bearing_deg,
    _block_fuel_types,
    _directional_factor,
    _travel_times,
)


def _footprint(
    adj: dict[int, list[tuple[int, float]]],
    area: dict[int, float],
    eligible: set[int],
    seed: int,
    target_area: float,
) -> set[int]:
    """Grow a contiguous footprint from a seed to a target area."""
    footprint: set[int] = set()
    queue = deque([seed])
    covered = 0.0
    while queue and covered < target_area:
        node = queue.popleft()
        if node in footprint or node not in eligible:
            continue
        footprint.add(node)
        covered += area.get(node, 0.0)
        for neighbour, _d in adj.get(node, []):
            if neighbour not in footprint:
                queue.append(neighbour)
    return footprint


def _padded_jitter(rng: np.random.Generator, count: int) -> np.ndarray:
    """Return `count` jitter values in [0, 1)."""
    return rng.random(count)


def _select_pattern(
    *,
    pattern: str,
    footprint: list[int],
    adj: dict[int, list[tuple[int, float]]],
    area: dict[int, float],
    centroids: dict[int, tuple[float, float]],
    wind_deg: float,
    target_area: float,
    rng: np.random.Generator,
) -> set[int]:
    """Select treated blocks inside a fixed footprint for one pattern."""
    chosen: set[int] = set()
    treated = 0.0
    if pattern == "random":
        order = list(footprint)
        rng.shuffle(order)
        for node in order:
            if treated >= target_area:
                break
            chosen.add(node)
            treated += area.get(node, 0.0)
    elif pattern == "clumped":
        seeds = rng.choice(footprint, size=3, replace=False)
        queue = deque(int(s) for s in seeds)
        while queue and treated < target_area:
            node = queue.popleft()
            if node in chosen:
                continue
            chosen.add(node)
            treated += area.get(node, 0.0)
            neighbours = [n for n, _d in adj.get(node, []) if n in footprint]
            rng.shuffle(neighbours)
            queue.extend(neighbours)
    elif pattern == "barrier":
        wx = np.sin(np.radians(wind_deg))
        wy = np.cos(np.radians(wind_deg))
        proj = {b: centroids[b][0] * wx + centroids[b][1] * wy for b in footprint}
        lo = min(proj.values())
        hi = max(proj.values())
        stripes = 10
        for node in sorted(footprint, key=lambda b: abs(proj[b] - (lo + hi) / 2)):
            stripe = int((proj[node] - lo) / max(hi - lo, 1e-9) * stripes)
            if stripe % 2 != 0:
                continue
            chosen.add(node)
            treated += area.get(node, 0.0)
            if treated >= target_area:
                break
    else:
        raise ValueError(f"unknown pattern {pattern!r}")
    return chosen


def _components(nodes: set[int], adj: dict[int, list[tuple[int, float]]]) -> list[int]:
    """Return connected-component sizes of a node set."""
    remaining = set(nodes)
    sizes: list[int] = []
    while remaining:
        start = remaining.pop()
        size = 1
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbour, _d in adj.get(node, []):
                if neighbour in remaining:
                    remaining.discard(neighbour)
                    queue.append(neighbour)
                    size += 1
        sizes.append(size)
    return sizes


def _downwind(
    u: int, v: int, centroids: dict[int, tuple[float, float]], wind_deg: float
) -> bool:
    """Return True when u -> v points downwind (within +/-90 degrees)."""
    x0, y0 = centroids[u]
    x1, y1 = centroids[v]
    bearing = _bearing_deg(x0, y0, x1, y1)
    delta = abs(((bearing - wind_deg + 180.0) % 360.0) - 180.0)
    return delta <= 90.0


def _connectivity(
    footprint: set[int],
    treated: set[int],
    adj: dict[int, list[tuple[int, float]]],
    centroids: dict[int, tuple[float, float]],
    wind_deg: float,
) -> dict[str, float]:
    """Connectivity metrics of the untreated part of a footprint (undirected + directed)."""
    untreated = footprint - treated
    sizes = _components(untreated, adj)
    crossed = sum(
        1
        for node in treated
        for neighbour, _d in adj.get(node, [])
        if neighbour in untreated
    )
    # Directed (downwind) reach from each untreated block; the largest reach and
    # the count of treated crossings that are aligned with the wind.
    directed_sizes: list[int] = []
    for start in untreated:
        seen = {start}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbour, _d in adj.get(node, []):
                if (
                    neighbour in untreated
                    and neighbour not in seen
                    and _downwind(node, neighbour, centroids, wind_deg)
                ):
                    seen.add(neighbour)
                    queue.append(neighbour)
        directed_sizes.append(len(seen))
    directed_best = max(directed_sizes) if directed_sizes else 0
    directed_mean = float(np.mean(directed_sizes)) if directed_sizes else 0.0
    aligned_cut = sum(
        1
        for node in treated
        for neighbour, _d in adj.get(node, [])
        if neighbour in untreated and _downwind(node, neighbour, centroids, wind_deg)
    )
    return {
        "untreated_blocks": len(untreated),
        "largest_component": float(max(sizes) if sizes else 0),
        "mean_component": float(np.mean(sizes) if sizes else 0.0),
        "component_count": float(len(sizes)),
        "treated_crossing_edges": float(crossed),
        "directed_largest_reach": float(directed_best),
        "directed_mean_reach": directed_mean,
        "aligned_edge_cut": float(aligned_cut),
    }


def run(
    *,
    blocks_path: Path,
    fuel_types: Path,
    topology: Path,
    footprint_ha: float,
    treat_fraction: float,
    treatment: str,
    ignitions: int,
    duration_min: float,
    wind_deg: float,
    seed: int,
) -> dict[str, object]:
    """Run the matched-footprint comparison."""
    blocks = _block_fuel_types(blocks_path, fuel_types, "p90", 60)
    adj = _adjacency(topology)
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
    rng = np.random.default_rng(seed)
    seed_block = int(rng.choice(sorted(eligible)))
    footprint = _footprint(adj, area, eligible, seed_block, footprint_ha)
    footprint_area = sum(area[b] for b in footprint)
    target_area = min(footprint_area, treat_fraction * footprint_area)
    factor = TREATMENT_HAZARD[treatment]

    results: dict[str, object] = {
        "footprint_ha": footprint_area,
        "treated_target_ha": target_area,
        "treatment": treatment,
        "patterns": {},
    }
    for pattern in ("random", "clumped", "barrier"):
        treated = _select_pattern(
            pattern=pattern,
            footprint=sorted(footprint),
            adj=adj,
            area=area,
            centroids=centroids,
            wind_deg=wind_deg,
            target_area=target_area,
            rng=np.random.default_rng(seed),
        )
        ros_by_block = blocks.set_index("block_id")["ros_m_per_min"].to_dict()
        ros_eff = {
            b: (ros_by_block[b] * factor if b in treated else ros_by_block[b])
            for b in footprint
        }
        traversal = {
            b: (np.sqrt(max(area[b], 0.0) * 10000.0) / r) if r > 0 else float("inf")
            for b, r in ros_eff.items()
        }
        started = rng.choice(sorted(footprint), size=min(ignitions, len(footprint)), replace=False)
        burned: list[float] = []
        for source in started:
            times = _travel_times(adj, traversal, centroids, wind_deg, int(source))
            burned.append(sum(area[b] for b, t in times.items() if t <= duration_min and b in footprint))
        results["patterns"][pattern] = {
            "treated_ha": float(sum(area[b] for b in treated)),
            "treated_blocks": len(treated),
            "mean_burned_ha": float(np.mean(burned)),
            "p90_burned_ha": float(np.quantile(burned, 0.9)),
            **_connectivity(footprint, treated, adj, centroids, wind_deg),
        }
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=Path, required=True)
    parser.add_argument("--fuel-types", type=Path, required=True, dest="fuel_types")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--footprint-ha", type=float, default=20000.0, dest="footprint_ha")
    parser.add_argument("--treat-fraction", type=float, default=0.2, dest="treat_fraction")
    parser.add_argument("--treatment", choices=sorted(TREATMENT_HAZARD), default="fb")
    parser.add_argument("--ignitions", type=int, default=40)
    parser.add_argument("--duration-min", type=float, default=480.0, dest="duration_min")
    parser.add_argument("--wind-dir", type=float, default=225.0, dest="wind_dir")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    result = run(
        blocks_path=args.blocks,
        fuel_types=args.fuel_types,
        topology=args.topology,
        footprint_ha=args.footprint_ha,
        treat_fraction=args.treat_fraction,
        treatment=args.treatment,
        ignitions=args.ignitions,
        duration_min=args.duration_min,
        wind_deg=args.wind_dir,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    frame = pd.DataFrame(result["patterns"]).T
    print(frame.to_string())
    fire_rank = list(frame.sort_values("mean_burned_ha").index)
    print("\nfire rank (best first):", fire_rank)
    for metric in (
        "largest_component",
        "directed_largest_reach",
        "directed_mean_reach",
        "aligned_edge_cut",
    ):
        rank = list(frame.sort_values(metric).index)
        print(f"{metric}: {rank}  agree={rank == fire_rank}")


if __name__ == "__main__":
    main()
