"""Complete a per-track fuel-hazard feature across a compiled WS4 dataset.

Adds ``feature.FuelHazard`` to every track, by silviculture state:

- ``fb_*``         fuel-break destination: near-null for N years, then recovery;
- ``cc_pl_ct*``    thinned (FT) residual: reduced for the residual period;
- everything else  baseline hazard.

This turns hazard into a landscape account the scheduler can target, so a
treatment that lowers it (FT, FB) can be chosen on merit rather than by label.

Usage::

    python scripts/complete_hazard_feature.py \
        --dataset runtime/ws4/compiled_fb --out runtime/ws4/compiled_fb_haz
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

STATE_RE = re.compile(r"SILV_STATE\(([^)]*)\)")


def _hazard_curve(state: str, near_null_years: int) -> list[tuple[float, float]]:
    """Return hazard curve points (x, y) for a silviculture state."""
    if state.startswith("fb_"):
        return [(0.0, 0.05), (float(max(1, near_null_years)), 0.05), (40.0, 1.0), (400.0, 1.0)]
    # Thinned (FT) residual. The model's states are cc_pl_ft30/40/50/60; the earlier
    # rule matched "cc_pl_ct", which never occurs, so FT silently read as baseline and
    # the hazard account ignored the treatment entirely.
    if state.startswith("cc_pl_ft"):
        return [(0.0, 0.4), (20.0, 0.4), (40.0, 1.0), (400.0, 1.0)]
    return [(0.0, 1.0), (400.0, 1.0)]


def complete_hazard(*, dataset: Path, out: Path, near_null_years: int) -> Path:
    """Add a hazard feature to every track in a compiled dataset."""
    dataset = Path(dataset)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    tracks = pd.read_parquet(dataset / "tracks.parquet")
    features = pd.read_parquet(dataset / "features.parquet")
    curves = pd.read_parquet(dataset / "curves.parquet")

    next_curve = int(curves["curve_id"].max()) + 1
    states = tracks["name"].map(
        lambda n: (STATE_RE.search(str(n)).group(1) if STATE_RE.search(str(n)) else "")
    )
    curve_by_state = {state: _hazard_curve(state, near_null_years) for state in set(states)}

    curve_id_by_state: dict[str, int] = {}
    curve_rows: list[dict[str, float]] = []
    for state, points in curve_by_state.items():
        curve_id = next_curve
        next_curve += 1
        curve_id_by_state[state] = curve_id
        curve_rows.extend({"curve_id": curve_id, "x": x, "y": y} for x, y in points)

    # Replace any existing hazard feature rows and add one per track.
    features = features[features["label"] != "feature.FuelHazard"].copy()
    hazard_rows = pd.DataFrame(
        {
            "track_id": tracks["track_id"].to_numpy(),
            "label": "feature.FuelHazard",
            "curve_id": states.map(curve_id_by_state).to_numpy(),
        }
    )
    features = pd.concat([features, hazard_rows], ignore_index=True)
    curves = pd.concat([curves, pd.DataFrame(curve_rows)], ignore_index=True)

    features.to_parquet(out / "features.parquet", index=False)
    curves.to_parquet(out / "curves.parquet", index=False)
    # Copy the rest unchanged.
    for name in (
        "fragments", "blocks", "tracks", "strata", "treatments",
        "products", "protoaccounts", "accounts", "groups", "messages",
    ):
        if name in ("features", "curves"):
            continue
        pd.read_parquet(dataset / f"{name}.parquet").to_parquet(out / f"{name}.parquet", index=False)
    manifest = json.loads((dataset / "manifest.json").read_text())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--near-null-years", type=int, default=8, dest="near_null_years")
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    out = complete_hazard(
        dataset=args.dataset, out=args.out, near_null_years=args.near_null_years
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
