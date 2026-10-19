"""Stand-scale FBP fire-behaviour curves for TSA23 analysis units.

For each TSA23 analysis unit, map the leading species to an FBP fuel type and
compute head-fire rate of spread, head-fire intensity, crown fraction burned, and
flame length over stand age, for an untreated stand and a fuel-treated (thinned)
stand. This is the aspatial half of the Paper 2 fire-behaviour bridge: the
per-hectare treatment effect that becomes a WS4 feature/product account.

Stand attributes over age are simplified proxies pending calibration:
- crown closure saturates with age;
- canopy base height rises with height;
- thinning (FT) reduces crown closure and raises canopy base height.

Usage::

    python scripts/fbp_stand_curves.py --au-table data/model_input_bundle/au_table.csv \
        --out runtime/fire/fbp_stand_curves.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from cffdrs.fbp import FBPInput, fbp

# Representative fire-weather day (median-ish): FFMC 90, BUI 60, wind 15 km/h.
DEFAULT_FFMC = 90.0
DEFAULT_BUI = 60.0
DEFAULT_WIND = 15.0
DEFAULT_ELEV = 1000.0

# Leading-species suffix -> FBP fuel type.
FUEL_TYPE_BY_SPECIES = {
    "AT": "D1",   # aspen
    "FD": "C7",   # Douglas-fir
    "FDI": "C7",
    "PL": "C3",   # mature pine
    "PLI": "C3",
    "SX": "C2",   # spruce
    "SW": "C2",
    "SE": "C2",
    "BL": "C2",   # balsam
    "CW": "C7",
    "HW": "C2",
}

# Thinning (FT) effect on stand structure (provisional).
THIN_CROWN_CLOSURE_FACTOR = 0.6
THIN_CBH_FACTOR = 1.6
THIN_CROWN_LENGTH_FACTOR = 0.7

MAX_AGE = 200
AGE_STEP = 10


def _flame_length(hfi: float) -> float:
    """Return flame length (m) from head-fire intensity (kW/m)."""
    return 0.0775 * (hfi ** 0.46)


def _species_token(stratum_code: str) -> str:
    """Return the trailing species token of a stratum code (e.g. IDF_FDI -> FDI)."""
    return str(stratum_code).split("_")[-1].upper()


def _crown_closure(age: int, base: float) -> float:
    """Return crown closure (percent) saturating with age."""
    return min(base, base * (age / 30.0)) if age < 30 else base


def _cbh(age: int) -> float:
    """Return canopy base height (m), rising with age."""
    return max(0.0, min(6.0, (age - 10) * 0.08))


def _crown_length(age: int) -> float:
    """Return crown length (m), rising then saturating."""
    return max(1.0, min(8.0, 1.0 + age * 0.05))


def compute_curves(au_table: pd.DataFrame) -> pd.DataFrame:
    """Compute untreated and thinned FBP fire-metric curves per AU.

    Parameters
    ----------
    au_table : pandas.DataFrame
        The analysis-unit table with ``au_id``, ``stratum_code``, ``si_level``.

    Returns
    -------
    pandas.DataFrame
        One row per (au_id, state, age).
    """
    rows: list[dict[str, object]] = []
    for au in au_table.itertuples(index=False):
        token = _species_token(au.stratum_code)
        fuel_type = FUEL_TYPE_BY_SPECIES.get(token)
        if fuel_type is None:
            continue
        for age in range(0, MAX_AGE + 1, AGE_STEP):
            base_cc = 65.0
            for state, cc, cbh, cfl in (
                (
                    "untreated",
                    _crown_closure(age, base_cc),
                    _cbh(age),
                    _crown_length(age),
                ),
                (
                    "thinned",
                    _crown_closure(age, base_cc) * THIN_CROWN_CLOSURE_FACTOR,
                    _cbh(age) * THIN_CBH_FACTOR,
                    _crown_length(age) * THIN_CROWN_LENGTH_FACTOR,
                ),
            ):
                out = fbp(
                    FBPInput(
                        fuel_type=fuel_type,
                        ffmc=DEFAULT_FFMC,
                        bui=DEFAULT_BUI,
                        ws=DEFAULT_WIND,
                        elv=DEFAULT_ELEV,
                        cc=cc,
                        cbh=cbh,
                        cfl=cfl,
                    )
                )[0]
                rows.append(
                    {
                        "au_id": int(au.au_id),
                        "stratum_code": au.stratum_code,
                        "si_level": au.si_level,
                        "fuel_type": fuel_type,
                        "state": state,
                        "age": age,
                        "ros_m_per_min": out.ros,
                        "hfi_kw_per_m": out.hfi,
                        "cfb": out.cfb,
                        "cfc": out.cfc,
                        "flame_length_m": _flame_length(out.hfi),
                        "fire_type": out.fd,
                    }
                )
    return pd.DataFrame(rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--au-table", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    au_table = pd.read_csv(args.au_table)
    curves = compute_curves(au_table)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    curves.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(curves)} rows)")


if __name__ == "__main__":
    main()
