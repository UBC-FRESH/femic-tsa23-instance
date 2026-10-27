"""Apply TSA23 fuel-treatment (FT) economics to a compiled WS4 dataset.

The FEMIC Patchworks export carries the FT treatment and its timber/biomass
volumes but no cost or valuation surface (matching the MKRF pattern, where
economics is an instance-level layer). This script adds the FT economics as
product accounts on the FT treatments:

- ``product.FuelTreatmentCost``: the per-hectare treatment cost, evaluated on the
  treated area.
- ``product.WoodyBiomass``: the woody-biomass product recovered by collecting
  fuels, for variants **without** in-block chipping. With ``--chipping`` the
  biomass product is omitted (chipped in block) and the cost rises by the
  chipping increment.

Usage::

    python scripts/apply_fuel_treatment_economics.py \
        --dataset runtime/ws4/compiled_ft \
        --out runtime/ws4/compiled_ft_econ
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ws4.model.api import Model

FT_TREATMENT = "FT"
COST_ACCOUNT = "product.FuelTreatmentCost"
BIOMASS_ACCOUNT = "product.WoodyBiomass"


def _next_curve_id(curves: pd.DataFrame) -> int:
    """Return an unused curve id."""
    return int(curves["curve_id"].max()) + 1


def apply_economics(
    *,
    dataset: Path,
    out: Path,
    cost_per_ha: float,
    biomass_per_ha: float,
    chipping: bool,
    chipping_cost_per_ha: float,
) -> Path:
    """Add FT cost and biomass product accounts to a compiled dataset.

    Parameters
    ----------
    dataset : Path
        The compiled dataset directory.
    out : Path
        The output directory for the augmented dataset.
    cost_per_ha : float
        Base treatment cost in CAD per treated hectare.
    biomass_per_ha : float
        Woody-biomass product in tonnes per treated hectare (non-chipping only).
    chipping : bool
        When true, omit the biomass product and add the chipping cost increment.
    chipping_cost_per_ha : float
        Extra cost in CAD per hectare when chipping.

    Returns
    -------
    Path
        The output dataset directory.
    """
    model = Model.from_dataset(dataset)
    curves = model.table("curves")
    products = model.table("products")

    effective_cost = float(cost_per_ha) + (float(chipping_cost_per_ha) if chipping else 0.0)
    cost_curve_id = _next_curve_id(curves)
    curves = pd.concat(
        [
            curves,
            pd.DataFrame(
                [
                    {"curve_id": cost_curve_id, "x": 0.0, "y": effective_cost},
                ]
            ),
        ],
        ignore_index=True,
    )
    model.tables["curves"] = curves

    ft_track_ids = sorted(
        products.loc[products["treatment"] == FT_TREATMENT, "track_id"].unique().tolist()
    )
    rows: list[dict[str, object]] = [
        {
            "track_id": int(track_id),
            "treatment": FT_TREATMENT,
            "label": COST_ACCOUNT,
            "curve_id": cost_curve_id,
        }
        for track_id in ft_track_ids
    ]

    if not chipping and biomass_per_ha > 0.0:
        biomass_curve_id = _next_curve_id(model.table("curves"))
        model.tables["curves"] = pd.concat(
            [
                model.table("curves"),
                pd.DataFrame(
                    [{"curve_id": biomass_curve_id, "x": 0.0, "y": float(biomass_per_ha)}]
                ),
            ],
            ignore_index=True,
        )
        rows.extend(
            {
                "track_id": int(track_id),
                "treatment": FT_TREATMENT,
                "label": BIOMASS_ACCOUNT,
                "curve_id": biomass_curve_id,
            }
            for track_id in ft_track_ids
        )

    model.tables["products"] = pd.concat(
        [model.table("products"), pd.DataFrame(rows)], ignore_index=True
    )
    return model.write(out)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cost-per-ha", type=float, default=10000.0)
    parser.add_argument("--biomass-per-ha", type=float, default=30.0)
    parser.add_argument("--chipping", action="store_true")
    parser.add_argument("--chipping-cost-per-ha", type=float, default=5000.0)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    out = apply_economics(
        dataset=args.dataset,
        out=args.out,
        cost_per_ha=args.cost_per_ha,
        biomass_per_ha=args.biomass_per_ha,
        chipping=args.chipping,
        chipping_cost_per_ha=args.chipping_cost_per_ha,
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
