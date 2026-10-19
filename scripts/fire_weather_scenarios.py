"""Fire-weather scenarios for TSA23 from ERA5 (via Open-Meteo).

Fetch daily weather for the TSA23 area from the Open-Meteo ERA5 archive (no API
key), run the Canadian Forest Fire Weather Index (FWI) System with ``cffdrs``,
and derive representative fire-weather scenarios (median and 90th-percentile
fire-weather days) as FFMC/BUI/ISI/wind combinations for the FBP runs.

Open-Meteo daily fields are proxies for the standard noon observations: max
temperature, minimum relative humidity, max 10 m wind, and total precipitation.

Usage::

    python scripts/fire_weather_scenarios.py --out runtime/fire/fwi_scenarios.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd
from cffdrs import fwi

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# A small set of points spanning the TSA23 area (lat, lon).
TSA23_POINTS = [(51.6, -121.6), (51.5, -121.3), (51.3, -120.9)]
DEFAULT_LAT = 51.5
START_FFMC = 85.0
START_DMC = 6.0
START_DC = 15.0
START_MONTH = 5  # May


def _fetch_point(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    """Fetch daily ERA5 weather for one point from Open-Meteo."""
    query = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": start,
            "end_date": end,
            "daily": "temperature_2m_max,relative_humidity_2m_min,wind_speed_10m_max,precipitation_sum",
            "timezone": "UTC",
        }
    )
    with urlopen(f"{ARCHIVE_URL}?{query}", timeout=60) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    daily = payload["daily"]
    return pd.DataFrame(
        {
            "date": daily["time"],
            "temp": daily["temperature_2m_max"],
            "rh": daily["relative_humidity_2m_min"],
            "ws": daily["wind_speed_10m_max"],
            "prec": daily["precipitation_sum"],
        }
    )


def _compute_fwi(frame: pd.DataFrame, lat: float) -> pd.DataFrame:
    """Run the FWI System over a daily weather series."""
    ffmc = START_FFMC
    dmc = START_DMC
    dc = START_DC
    rows: list[dict[str, float]] = []
    for row in frame.itertuples(index=False):
        month = int(str(row.date)[5:7])
        ffmc = float(fwi.fine_fuel_moisture_code(ffmc, row.temp, row.rh, row.ws, row.prec))
        dmc = float(fwi.duff_moisture_code(dmc, row.temp, row.rh, row.prec, lat, month))
        dc = float(fwi.drought_code(dc, row.temp, row.rh, row.prec, lat, month))
        bui = float(fwi.buildup_index(dmc, dc))
        isi = float(fwi.initial_spread_index(ffmc, row.ws))
        fwi_value = float(fwi.fire_weather_index(isi, bui))
        rows.append(
            {"date": row.date, "ffmc": ffmc, "bui": bui, "isi": isi, "fwi": fwi_value, "ws": row.ws}
        )
    return pd.DataFrame(rows)


def build_scenarios(*, start: str, end: str) -> pd.DataFrame:
    """Fetch, compute, and summarize fire-weather scenarios for TSA23."""
    frames = [_compute_fwi(_fetch_point(lat, lon, start, end), lat) for lat, lon in TSA23_POINTS]
    allfwi = pd.concat(frames, ignore_index=True)
    allfwi["month"] = allfwi["date"].str[5:7].astype(int)
    fire_season = allfwi[allfwi["month"].between(5, 9)]

    scenarios: list[dict[str, object]] = []
    for name, quantile in (("median", 0.5), ("p90", 0.9), ("extreme", 0.98)):
        scenarios.append(
            {
                "scenario": name,
                "ffmc": round(float(np.quantile(fire_season["ffmc"], quantile)), 1),
                "bui": round(float(np.quantile(fire_season["bui"], quantile)), 1),
                "isi": round(float(np.quantile(fire_season["isi"], quantile)), 1),
                "ws": round(float(np.quantile(fire_season["ws"], quantile)), 1),
                "fwi": round(float(np.quantile(fire_season["fwi"], quantile)), 1),
            }
        )
    return pd.DataFrame(scenarios)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--start", default="2015-05-01")
    parser.add_argument("--end", default="2024-09-30")
    return parser


def main() -> None:
    """Entry point."""
    args = _build_parser().parse_args()
    scenarios = build_scenarios(start=args.start, end=args.end)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    scenarios.to_csv(args.out, index=False)
    print(scenarios.to_string(index=False))


if __name__ == "__main__":
    main()
