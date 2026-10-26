"""Neighbourhood wildfire-resistance indicator over a replayed schedule.

Prototype of the account proposed in `planning/paper_ideas_ws4_wiring.md` (idea C), following
the stand-level resistance indicator in Bhusal et al. (2026, *Forests* 17(8):886): a stand's
resistance depends not only on its own fuel state but on that of its neighbours.

For each period and block:

    h_i        = feature.FuelHazard at the block (area-weighted over its fragments)
    s_i        = (h_i + sum_j h_j) / (1 + number of neighbours j)
    resistance = 1 - s_i

so a block beside treated neighbours scores higher even if it is untreated itself. The
landscape value is the area-weighted mean; the minimum is the worst neighbourhood.

The replay uses WS4's own simulator (`apply_treatments` + `block_criteria`), so the hazard
values are the ones the model actually carries, not a reimplementation.

Usage::

    python scripts/resistance_metric.py \
        --dataset runtime/ws4/compiled_sf \
        --topology runtime/ws4/topology_tsa23.csv \
        --schedule runtime/fire/bridge_barrier_sched.csv \
        --years 5 --out runtime/fire/resistance_barrier.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ws4.sim.engine import Simulator  # noqa: E402


def _adjacency(topology: Path, search_distance: float | None) -> dict[int, list[int]]:
    """Return an undirected adjacency map, optionally bounded by edge length."""
    frame = pd.read_csv(topology)
    adj: dict[int, list[int]] = {}
    for src, dst, distance in frame.itertuples(index=False):
        if search_distance is not None and float(distance) > search_distance:
            continue
        adj.setdefault(int(src), []).append(int(dst))
        adj.setdefault(int(dst), []).append(int(src))
    return adj


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_sf"))
    parser.add_argument("--topology", type=Path, default=Path("runtime/ws4/topology_tsa23.csv"))
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--criteria", default="feature.FuelHazard")
    parser.add_argument("--search-distance", type=float, default=None, dest="search_distance")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    adj = _adjacency(args.topology, args.search_distance)
    blocks = pd.read_parquet(args.dataset / "blocks.parquet")
    area = blocks.groupby("block_id")["area_ha"].sum().to_dict()
    schedule = pd.read_csv(args.schedule)

    sim = Simulator.from_dataset(args.dataset)
    rows: list[dict[str, float]] = []
    for offset in range(args.years):
        sim.apply_treatments(schedule, offset)
        values = sim.block_criteria(args.criteria)
        if not values:
            continue
        resistance: dict[int, float] = {}
        for block, h in values.items():
            neighbours = adj.get(block, [])
            if not neighbours:
                resistance[block] = 1.0 - h
                continue
            neighbour_hazard = [values.get(n, 0.0) for n in neighbours]
            mean = (h + sum(neighbour_hazard)) / (1 + len(neighbours))
            resistance[block] = 1.0 - mean
        weights = np.array([area.get(b, 0.0) for b in resistance])
        total = weights.sum()
        values_array = np.array(list(resistance.values()))
        rows.append(
            {
                "offset": offset,
                "blocks": len(resistance),
                "resistance_area_weighted": float((values_array * weights).sum() / total)
                if total > 0 else float(values_array.mean()),
                "resistance_min": float(values_array.min()),
                "resistance_p05": float(np.quantile(values_array, 0.05)),
                "hazard_area_weighted": float(
                    (np.array(list(values.values())) * weights).sum() / total
                ) if total > 0 else float(np.mean(list(values.values()))),
            }
        )

    frame = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(frame.round(4).to_string(index=False))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
