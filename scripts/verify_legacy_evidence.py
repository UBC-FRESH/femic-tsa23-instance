"""Verify the recorded E2/E2b/E2c/E2d landscape-bridge numbers.

The evidence log entries E2-E2d predate the shared-ignition fix. They are unaffected
by it — the block table and the seed are fixed while the pattern varies, so the
ignition draw is identical across patterns — but that claim should be a test, not an
assertion. This script re-runs the recorded cells through the same CLI path and fails
if any value moves by more than ``--tolerance`` hectares.

Expected values are the ones written in ``planning/paper2_evidence_log.md``, rounded to
0.1 ha there; the tolerance default of 1.0 ha covers that rounding.

Usage::

    python scripts/verify_legacy_evidence.py
    python scripts/verify_legacy_evidence.py --reuse   # read existing legacy_*.json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

# (density, pattern, factor) -> (mean burned ha, p90 burned ha or None if not recorded)
EXPECTED: dict[tuple[float, str, float], tuple[float, float | None]] = {
    # E2, 20% treated, ROS x0.3
    (0.2, "random", 0.3): (20298.0, 39483.2),
    (0.2, "clumped", 0.3): (19869.7, 39404.0),
    (0.2, "barrier", 0.3): (19640.4, 37637.1),
    # E2, 10% treated, ROS x0.3
    (0.1, "random", 0.3): (23300.0, None),
    (0.1, "clumped", 0.3): (23055.0, None),
    (0.1, "barrier", 0.3): (22771.0, None),
    # E2b, 20%, near-hard stop and continuous band
    (0.2, "random", 0.05): (17309.0, 34111.5),
    (0.2, "barrier", 0.05): (16549.0, 31743.0),
    (0.2, "band", 0.05): (19122.0, 51130.1),
    (0.2, "band", 0.3): (20103.0, 51130.1),
    # E2c, 20%, impassable treated blocks
    (0.2, "random", 0.0): (16690.0, 32734.5),
    (0.2, "clumped", 0.0): (15742.0, 31625.9),
    (0.2, "barrier", 0.0): (16118.0, 31608.5),
    # E2d, the model's own hazard multipliers
    (0.2, "random", 0.4): (21096.0, 41526.9),
    (0.2, "clumped", 0.4): (20669.0, 41632.2),
    (0.2, "barrier", 0.4): (20583.0, 40354.7),
    (0.2, "random", 0.2): (19406.0, 38028.0),
    (0.2, "clumped", 0.2): (18897.0, 37577.4),
    (0.2, "barrier", 0.2): (18581.0, 35427.8),
}

GRID = {
    "densities": (0.1, 0.2),
    "patterns": ("random", "clumped", "barrier"),
    "factors": (0.0, 0.05, 0.2, 0.3, 0.4),
    "extra": ((0.2, "band", 0.05), (0.2, "band", 0.3)),
}


def _run_cell(
    density: float, pattern: str, factor: float, out_dir: Path, reuse: bool
) -> Path:
    """Run one cell through the CLI and return its JSON path."""
    out = out_dir / f"legacy_{density}_{pattern}_{factor}.json"
    if reuse and out.exists():
        return out
    cmd = [
        sys.executable,
        "scripts/landscape_spread.py",
        "--blocks", "output/patchworks_ft/fragments/fragments.shp",
        "--fuel-types", "runtime/fire/fbp_stand_curves.csv",
        "--topology", "runtime/ws4/topology_tsa23.csv",
        "--scenario", "p90",
        "--treat-fraction", str(density),
        "--treat-pattern", pattern,
        "--treat-ros-factor", str(factor),
        "--ignitions", "50",
        "--duration-min", "480",
        "--wind-dir", "225",
        "--seed", "1",
        "--out", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
    return out


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("runtime/fire"))
    parser.add_argument("--tolerance", type=float, default=1.0)
    parser.add_argument("--reuse", action="store_true", help="do not re-run missing cells")
    args = parser.parse_args()

    import json

    failures: list[str] = []
    checked = 0
    for density in GRID["densities"]:
        for factor in GRID["factors"]:
            for pattern in GRID["patterns"]:
                key = (density, pattern, factor)
                path = args.out_dir / f"legacy_{density}_{pattern}_{factor}.json"
                if args.reuse and not path.exists():
                    continue
                _run_cell(density, pattern, factor, args.out_dir, args.reuse)
                if key not in EXPECTED:
                    continue
                checked += 1
                got = json.loads(path.read_text())
                want_mean, want_p90 = EXPECTED[key]
                if abs(got["mean_area_burned_ha"] - want_mean) > args.tolerance:
                    failures.append(
                        f"{key}: mean {got['mean_area_burned_ha']:.1f} != {want_mean:.1f}"
                    )
                if want_p90 is not None and abs(got["p90_area_burned_ha"] - want_p90) > args.tolerance:
                    failures.append(
                        f"{key}: p90 {got['p90_area_burned_ha']:.1f} != {want_p90:.1f}"
                    )
    for density, pattern, factor in GRID["extra"]:
        key = (density, pattern, factor)
        path = args.out_dir / f"legacy_{density}_{pattern}_{factor}.json"
        if args.reuse and not path.exists():
            continue
        _run_cell(density, pattern, factor, args.out_dir, args.reuse)
        checked += 1
        got = json.loads(path.read_text())
        want_mean, want_p90 = EXPECTED[key]
        if abs(got["mean_area_burned_ha"] - want_mean) > args.tolerance:
            failures.append(f"{key}: mean {got['mean_area_burned_ha']:.1f} != {want_mean:.1f}")
        if want_p90 is not None and abs(got["p90_area_burned_ha"] - want_p90) > args.tolerance:
            failures.append(f"{key}: p90 {got['p90_area_burned_ha']:.1f} != {want_p90:.1f}")

    print(f"checked {checked} recorded cells, {len(EXPECTED)} expected")
    for line in failures:
        print(f"  MISMATCH {line}")
    print("PASS" if not failures else "FAIL")
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
