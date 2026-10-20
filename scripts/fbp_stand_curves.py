"""Stand-scale FBP fire-behaviour curves for TSA23 analysis units.

For each TSA23 analysis unit, derive an FBP fuel type from the VRI stand
attributes (species composition, conifer share, dead share), then compute
head-fire rate of spread, head-fire intensity, crown fraction burned, and flame
length over stand age, for an untreated stand and a fuel-treated (thinned) stand,
under a set of fire-weather scenarios (median / 90th-percentile / extreme).

Stand height over age comes from the BatchTIPSY output (``HTcon_<age>`` columns),
mapped to the model AUs via ``au_table.source_managed_local_au_id``. Crown base
height and crown length are derived from height with allometric ratios; the
thinning effect on crown closure / CBH / crown length is a documented
simplification pending calibration.

Fuel typing (FBP families):
- broadleaf share >= 75% -> D1 (aspen);
- conifer-leading with dead share >= 50% and a fir-leading stand -> M3 (dead fir);
- conifer-leading pine -> C3; Douglas-fir -> C7; spruce/balsam -> C2;
- mixed (broadleaf 25-75%) -> M2 (boreal mixedwood).

Usage::

    python scripts/fbp_stand_curves.py \
        --checkpoint data/vri_vclr1p_checkpoint7.feather \
        --au-table data/model_input_bundle/au_table.csv \
        --tipsy-output data/04_output-tsa23.csv \
        --scenarios runtime/fire/fwi_scenarios.csv \
        --out runtime/fire/fbp_stand_curves.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from cffdrs.fbp import FBPInput, fbp

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
    """Aggregate per-stand VRI attributes to analysis units."""
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
                "fuel_type": _classify_fuel_type(
                    leading=leading_conifer,
                    conifer_share=conifer_pct,
                    broadleaf_share=broadleaf_pct,
                    dead_share=dead_share,
                ),
            }
        )
    return pd.DataFrame(rows)


def _height_curves(au_table: Path, tipsy_output: Path) -> dict[int, dict[int, float]]:
    """Return height-at-age (m) per model AU from the BatchTIPSY output."""
    au = pd.read_csv(au_table)
    tipsy = pd.read_csv(tipsy_output)
    height_cols = {c: int(c.split("_")[-1]) for c in tipsy.columns if c.startswith("HTcon_")}
    by_feature = tipsy.set_index("feature_id")
    curves: dict[int, dict[int, float]] = {}
    for row in au.itertuples(index=False):
        feature_id = int(row.source_managed_local_au_id)
        if feature_id not in by_feature.index:
            continue
        record = by_feature.loc[feature_id]
        curves[int(row.au_id)] = {
            age: float(record[col]) for col, age in height_cols.items() if pd.notna(record[col])
        }
    return curves


def _height_at_age(age: int, curve: dict[int, float], fallback: float = 20.0) -> float:
    """Return height (m) at an age, interpolating the curve."""
    if not curve:
        return fallback
    ages = sorted(curve)
    if age <= ages[0]:
        return curve[ages[0]]
    if age >= ages[-1]:
        return curve[ages[-1]]
    for lo, hi in zip(ages, ages[1:]):
        if lo <= age <= hi:
            frac = (age - lo) / (hi - lo)
            return curve[lo] + frac * (curve[hi] - curve[lo])
    return fallback


def compute_curves(
    au_attrs: pd.DataFrame,
    height_curves: dict[int, dict[int, float]],
    scenarios: pd.DataFrame,
) -> pd.DataFrame:
    """Compute FBP fire-metric curves per AU, scenario, state, and age."""
    rows: list[dict[str, object]] = []
    for au in au_attrs.itertuples(index=False):
        curve = height_curves.get(int(au.au_id), {})
        for scen in scenarios.itertuples(index=False):
            for age in range(0, MAX_AGE + 1, AGE_STEP):
                height = _height_at_age(age, curve)
                cbh = max(0.0, height * CBH_RATIO)
                crown_length = max(1.0, height * CROWN_LENGTH_RATIO)
                cc = (
                    min(au.crown_closure, au.crown_closure * (age / 30.0))
                    if age < 30
                    else au.crown_closure
                )
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
                            ffmc=float(scen.ffmc),
                            bui=float(scen.bui),
                            ws=float(scen.ws),
                            elv=DEFAULT_ELEV,
                            cc=max(0.0, cc_v),
                            cbh=cbh_v,
                            cfl=cfl_v,
                        )
                    )[0]
                    rows.append(
                        {
                            "au_id": int(au.au_id),
                            "fuel_type": au.fuel_type,
                            "scenario": scen.scenario,
                            "state": state,
                            "age": age,
                            "height_m": round(height, 2),
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
    parser.add_argument("--au-table", type=Path, required=True)
    parser.add_argument("--tipsy-output", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    au_attrs = _au_attributes(args.checkpoint)
    height_curves = _height_curves(args.au_table, args.tipsy_output)
    scenarios = pd.read_csv(args.scenarios)
    curves = compute_curves(au_attrs, height_curves, scenarios)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    curves.to_csv(args.out, index=False)
    print(
        f"wrote {args.out} ({len(curves)} rows; "
        f"{au_attrs.au_id.nunique()} AUs x {len(scenarios)} scenarios)"
    )


if __name__ == "__main__":
    main()
