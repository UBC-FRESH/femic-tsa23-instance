"""Stand-scale FBP fire-behaviour curves for TSA23 analysis units.

For each TSA23 analysis unit, derive an FBP fuel type from the VRI stand
attributes (species composition, conifer share, dead share), then compute
head-fire rate of spread, head-fire intensity, crown fraction burned, and flame
length over stand age, for an untreated stand and a fuel-treated (thinned) stand.
This is the aspatial half of the Paper 2 fire-behaviour bridge: the per-hectare
treatment effect that becomes a WS4 feature/product account.

Fuel typing follows the FBP fuel-type families from the leading species and the
conifer/broadleaf/dead shares:

- broadleaf share >= 75% -> D1 (aspen);
- conifer-leading with dead share >= 50% and a fir-leading stand -> M3 (dead fir);
- conifer-leading pine -> C3; Douglas-fir -> C7; spruce/balsam -> C2;
- mixed (broadleaf 25-75%) -> M2 (boreal mixedwood).

Crown base height and crown length are derived from the projected height with
allometric ratios. The attribute-age trajectory and the thinning effect are
documented simplifications pending calibration against the yield curves.

Usage::

    python scripts/fbp_stand_curves.py \
        --checkpoint data/ria_vri_vclr1p_checkpoint7.feather \
        --out runtime/fire/fbp_stand_curves.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from cffdrs.fbp import FBPInput, fbp

DEFAULT_FFMC = 90.0
DEFAULT_BUI = 60.0
DEFAULT_WIND = 15.0
DEFAULT_ELEV = 1000.0

CONIFER = {
    "PL", "PLI", "P", "PA", "PJ", "PM", "PF", "PY",
    "FD", "FDI", "FDC", "FDX", "F",
    "S", "SX", "SW", "SE", "SS", "SB", "SN", "SXE", "SXL", "SXW",
    "BL", "BA", "BG", "BB", "BM", "CW", "HW", "HM", "YC", "LW",
}
PINE = {"PL", "PLI", "P", "PA", "PJ", "PM", "PF", "PY"}
FIR = {"FD", "FDI", "FDC", "FDX", "F"}

THIN_CROWN_CLOSURE_FACTOR = 0.6
THIN_CBH_FACTOR = 1.6
THIN_CROWN_LENGTH_FACTOR = 0.7

MAX_AGE = 200
AGE_STEP = 10
CBH_RATIO = 0.15
CROWN_LENGTH_RATIO = 0.5


def _flame_length(hfi: float) -> float:
    """Return flame length (m) from head-fire intensity (kW/m)."""
    return 0.0775 * (hfi ** 0.46)


def _classify_fuel_type(
    *, leading: str, conifer_share: float, broadleaf_share: float, dead_share: float
) -> str:
    """Return an FBP fuel type from VRI composition shares."""
    if broadleaf_share >= 75.0:
        return "D1"
    if conifer_share >= 75.0:
        if dead_share >= 50.0 and leading in FIR:
            return "M3"
        if leading in PINE:
            return "C3"
        if leading in FIR:
            return "C7"
        return "C2"
    return "M2"


def _au_attributes(checkpoint: Path) -> pd.DataFrame:
    """Aggregate per-stand VRI attributes to analysis units.

    Parameters
    ----------
    checkpoint : Path
        The per-stand checkpoint feather with ``au`` and VRI attributes.

    Returns
    -------
    pandas.DataFrame
        One row per AU with ``fuel_type`` and mean stand attributes.
    """
    df = pd.read_feather(checkpoint)
    species_cols = [(f"SPECIES_CD_{i}", f"SPECIES_PCT_{i}") for i in range(1, 7)]
    area = df["Shape_Area"].fillna(0.0) if "Shape_Area" in df.columns else None

    rows: list[dict[str, object]] = []
    for au, group in df.groupby("au"):
        weight = area.loc[group.index].to_numpy() if area is not None else np.ones(len(group))
        weight = np.where(weight > 0, weight, 1.0)
        total = float(weight.sum())

        conifer_pct = 0.0
        broadleaf_pct = 0.0
        leading_conifer_pct = 0.0
        leading_conifer = ""
        for cd_col, pct_col in species_cols:
            if cd_col not in group.columns or pct_col not in group.columns:
                continue
            codes = group[cd_col].astype("string")
            pcts = pd.to_numeric(group[pct_col], errors="coerce").fillna(0.0).to_numpy()
            for code, pct, w in zip(codes, pcts, weight):
                if pd.isna(code) or not str(code).strip():
                    continue
                share = float(pct) * float(w) / total
                if str(code).upper() in CONIFER:
                    conifer_pct += share
                    if share > leading_conifer_pct:
                        leading_conifer_pct = share
                        leading_conifer = str(code).upper()
                else:
                    broadleaf_pct += share
        crown_closure = float(pd.to_numeric(group["CROWN_CLOSURE"], errors="coerce").mean())
        height = float(pd.to_numeric(group["PROJ_HEIGHT_1"], errors="coerce").mean())
        dead_share = float(
            pd.to_numeric(group["STAND_PERCENTAGE_DEAD"], errors="coerce").fillna(0.0).mean()
        )
        rows.append(
            {
                "au_id": int(au),
                "leading_species": leading_conifer,
                "conifer_share": conifer_pct,
                "broadleaf_share": broadleaf_pct,
                "dead_share": dead_share,
                "crown_closure": crown_closure,
                "height_m": height,
                "fuel_type": _classify_fuel_type(
                    leading=leading_conifer,
                    conifer_share=conifer_pct,
                    broadleaf_share=broadleaf_pct,
                    dead_share=dead_share,
                ),
            }
        )
    return pd.DataFrame(rows)


def _height_at_age(age: int, mature_height: float) -> float:
    """Return projected height (m) at an age, saturating at mature height."""
    if mature_height <= 0:
        mature_height = 20.0
    return mature_height * min(1.0, age / 60.0)


def compute_curves(au_attrs: pd.DataFrame) -> pd.DataFrame:
    """Compute untreated and thinned FBP fire-metric curves per AU."""
    rows: list[dict[str, object]] = []
    for au in au_attrs.itertuples(index=False):
        for age in range(0, MAX_AGE + 1, AGE_STEP):
            height = _height_at_age(age, au.height_m)
            cbh = max(0.0, height * CBH_RATIO)
            crown_length = max(1.0, height * CROWN_LENGTH_RATIO)
            cc = min(au.crown_closure, au.crown_closure * (age / 30.0)) if age < 30 else au.crown_closure
            for state, cc_v, cbh_v, cfl_v in (
                ("untreated", cc, cbh, crown_length),
                (
                    "thinned",
                    cc * THIN_CROWN_CLOSURE_FACTOR,
                    cbh * THIN_CBH_FACTOR,
                    crown_length * THIN_CROWN_LENGTH_FACTOR,
                ),
            ):
                out = fbp(
                    FBPInput(
                        fuel_type=au.fuel_type,
                        ffmc=DEFAULT_FFMC,
                        bui=DEFAULT_BUI,
                        ws=DEFAULT_WIND,
                        elv=DEFAULT_ELEV,
                        cc=max(0.0, cc_v),
                        cbh=cbh_v,
                        cfl=cfl_v,
                    )
                )[0]
                rows.append(
                    {
                        "au_id": int(au.au_id),
                        "leading_species": au.leading_species,
                        "fuel_type": au.fuel_type,
                        "conifer_share": round(au.conifer_share, 1),
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
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    au_attrs = _au_attributes(args.checkpoint)
    curves = compute_curves(au_attrs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    curves.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(curves)} rows, {au_attrs.au_id.nunique()} AUs)")
    print(au_attrs[["au_id", "leading_species", "conifer_share", "fuel_type"]].to_string(index=False))


if __name__ == "__main__":
    main()
