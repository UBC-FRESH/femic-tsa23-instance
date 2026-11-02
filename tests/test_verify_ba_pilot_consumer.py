"""Tests for the BA-only WS4 consumer helper functions."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_ba_pilot_consumer


def test_cell_rows_cols_parses_ids() -> None:
    """The cell id encodes the raster row and column."""
    rows, cols = verify_ba_pilot_consumer.cell_rows_cols(
        pd.Series(["cell_02006_02548", "cell_00001_00002"])
    )
    assert rows.tolist() == [2006, 1]
    assert cols.tolist() == [2548, 2]


def test_cell_rows_cols_rejects_bad_ids() -> None:
    """A malformed cell id is rejected."""
    with pytest.raises(ValueError, match="cell_"):
        verify_ba_pilot_consumer.cell_rows_cols(pd.Series(["cell_bad"]))


def test_weighted_block_mean_uses_area_weights() -> None:
    """The block mean is area-weighted and ignores unavailable fragments."""
    fragments = pd.DataFrame({"block_id": [1, 1, 2]})
    values = pd.Series([10.0, 30.0, np.nan])
    area = pd.Series([1.0, 3.0, 1.0])
    result = verify_ba_pilot_consumer.weighted_block_mean(fragments, values, area).set_index(
        "block_id"
    )
    assert result.loc[1, "inventory_ba_m2_ha"] == pytest.approx(25.0)
    assert bool(result.loc[1, "inventory_ba_available"]) is True
    assert 2 not in result.index


def test_weighted_block_mean_handles_no_valid_fragments() -> None:
    """An all-unavailable input returns an empty frame with the right columns."""
    fragments = pd.DataFrame({"block_id": [1]})
    result = verify_ba_pilot_consumer.weighted_block_mean(
        fragments, pd.Series([np.nan]), pd.Series([1.0])
    )
    assert result.empty
    assert result.columns.tolist() == [
        "block_id",
        "inventory_ba_m2_ha",
        "inventory_ba_available",
    ]
