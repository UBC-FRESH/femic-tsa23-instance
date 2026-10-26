"""Add a crown-fraction-burned (severity) feature to a compiled dataset.

Jones et al. (2026) note that increasing fire severity does not imply increasing fire size;
a model that reports only area burned cannot speak to that. The instance already computes
crown fraction burned per analysis unit, scenario, state and age
(`runtime/fire/fbp_stand_curves.csv`), so the feature is a build step, not a new model.

- ``feature.CrownFractionBurned`` — the FBP crown fraction burned for the track's analysis
  unit and silvicultural state at the track's age, under the chosen weather scenario.

The area-weighted sum of this feature is "crown-burn-hectares" at that weather, which is a
severity-weighted companion to ``feature.FuelHazard``.

Simplification, recorded rather than hidden: the FBP curves carry two states, ``untreated``
and ``thinned``, while the dataset has many (``baseline``, ``cc_pl``, ``fb_cc_pl``,
``cc_pl_ft30`` ...). A state containing ``_ft`` maps to ``thinned``; everything else maps to
``untreated``. Fuel-break and surface-fuel states therefore read as untreated, which is
conservative for severity.

Usage::

    python scripts/add_cfb_feature.py \
        --dataset runtime/ws4/compiled_sf \
        --curves runtime/fire/fbp_stand_curves.csv \
        --scenario p90 --out runtime/ws4/compiled_sf_sev
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

STATE_RE = re.compile(r"SILV_STATE\(([^)]*)\)")
AU_RE = re.compile(r"AU\((\d+)\)")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("runtime/ws4/compiled_sf"))
    parser.add_argument("--curves", type=Path, default=Path("runtime/fire/fbp_stand_curves.csv"))
    parser.add_argument("--scenario", default="p90")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    curves_csv = pd.read_csv(args.curves)
    sub = curves_csv[curves_csv["scenario"] == args.scenario]
    by_au_state: dict[tuple[int, str], list[tuple[float, float]]] = {}
    for (au, state), group in sub.groupby(["au_id", "state"]):
        points = sorted(zip(group["age"].astype(float), group["cfb"].astype(float)))
        # Extend past the last modelled age with its value: old stands do not vanish, and a
        # missing lookup would silently fall back to age 0.
        points.append((400.0, points[-1][1]))
        by_au_state[(int(au), str(state))] = points

    tracks = pd.read_parquet(args.dataset / "tracks.parquet")
    features = pd.read_parquet(args.dataset / "features.parquet")
    curves = pd.read_parquet(args.dataset / "curves.parquet")

    next_curve = int(curves["curve_id"].max()) + 1
    curve_id_by_key: dict[tuple[int, str], int] = {}
    new_points: list[dict[str, float]] = []
    new_rows: list[dict[str, object]] = []
    missing = 0
    for row in tracks.itertuples(index=False):
        name = str(row.name)
        au_match = AU_RE.search(name)
        state_match = STATE_RE.search(name)
        if not au_match or not state_match:
            missing += 1
            continue
        au = int(au_match.group(1))
        silv = state_match.group(1)
        fbp_state = "thinned" if "_ft" in silv else "untreated"
        key = (au, fbp_state)
        if key not in by_au_state:
            missing += 1
            continue
        if key not in curve_id_by_key:
            curve_id_by_key[key] = next_curve
            for age, value in by_au_state[key]:
                new_points.append({"curve_id": next_curve, "x": age, "y": value})
            next_curve += 1
        new_rows.append(
            {"track_id": int(row.track_id), "label": "feature.CrownFractionBurned",
             "curve_id": curve_id_by_key[key]}
        )

    features = pd.concat([features, pd.DataFrame(new_rows)], ignore_index=True)
    curves = pd.concat([curves, pd.DataFrame(new_points)], ignore_index=True)

    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("fragments", "blocks", "tracks", "strata", "treatments", "products",
                 "protoaccounts", "accounts", "groups", "messages"):
        source = args.dataset / f"{name}.parquet"
        if source.exists():
            pd.read_parquet(source).to_parquet(args.out / f"{name}.parquet", index=False)
    features.to_parquet(args.out / "features.parquet", index=False)
    curves.to_parquet(args.out / "curves.parquet", index=False)
    (args.out / "manifest.json").write_text(
        json.dumps(json.loads((args.dataset / "manifest.json").read_text()), indent=1)
    )

    print(f"scenario: {args.scenario}")
    print(f"tracks with a feature: {len(new_rows)} of {len(tracks)} (missing {missing})")
    print(f"distinct (au, state) curves: {len(curve_id_by_key)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
