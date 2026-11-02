"""Validate the published TSA 23 forest-condition card.

The card follows the WS4 P90 ``ws4.forest_condition.report.v1`` contract. This
test keeps a local, dependency-free guard until the instance depends on the
released WS4 module.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

import pytest

CARD_PATH = Path(__file__).resolve().parents[1] / "reports/tsa23-forest-condition-2026.json"
REVIEW_STATUSES = {"draft", "provisional", "reviewed"}
INDICATOR_STATUSES = {"ok", "outside_domain", "missing", "review_required"}
ALERT_SEVERITIES = {"info", "watch", "warning"}


def load_card(path: Path = CARD_PATH) -> dict[str, Any]:
    """Load the card JSON.

    Parameters
    ----------
    path : pathlib.Path, optional
        Card path.

    Returns
    -------
    dict[str, Any]
        Decoded card.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def validate_card(card: dict[str, Any]) -> None:
    """Validate the small report-card contract used by this repository.

    Parameters
    ----------
    card : dict[str, Any]
        Decoded card.

    Raises
    ------
    ValueError
        If a required field is missing or invalid.
    """
    if card.get("schema_version") != "ws4.forest_condition.report.v1":
        raise ValueError("schema_version must be ws4.forest_condition.report.v1")
    for field in ("report_id", "scenario_id", "generated_utc", "period"):
        value = card.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")
    if card.get("review_status") not in REVIEW_STATUSES:
        raise ValueError("review_status is invalid")
    indicators = card.get("indicators")
    if not isinstance(indicators, list) or not indicators:
        raise ValueError("indicators must be a non-empty list")
    names: set[str] = set()
    for indicator in indicators:
        name = indicator.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("indicator.name must be a non-empty string")
        if name in names:
            raise ValueError("indicator names must be unique")
        names.add(name)
        for field in ("unit", "source", "source_version"):
            value = indicator.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"indicator.{field} must be a non-empty string")
        value = indicator.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("indicator.value must be a finite number")
        if not math.isfinite(float(value)):
            raise ValueError("indicator.value must be finite")
        if indicator.get("status", "ok") not in INDICATOR_STATUSES:
            raise ValueError("indicator.status is invalid")
        uncertainty = indicator.get("uncertainty")
        if uncertainty is not None and (
            isinstance(uncertainty, bool)
            or not isinstance(uncertainty, (int, float))
            or not math.isfinite(float(uncertainty))
            or float(uncertainty) < 0
        ):
            raise ValueError("indicator.uncertainty must be finite and non-negative")
    for alert in card.get("alerts", []):
        if alert.get("advisory") is not True:
            raise ValueError("alerts must be advisory")
        if alert.get("severity") not in ALERT_SEVERITIES:
            raise ValueError("alert.severity is invalid")
        for field in ("code", "message"):
            value = alert.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"alert.{field} must be a non-empty string")
    provenance = card.get("provenance", {})
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError("provenance must be a non-empty object")
    for key, value in provenance.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("provenance keys must be non-empty strings")
        if not isinstance(value, str) or not value.strip():
            raise ValueError("provenance values must be non-empty strings")


def test_published_card_is_valid() -> None:
    """The published card passes the local contract guard."""
    validate_card(load_card())


def test_missing_source_is_rejected() -> None:
    """An indicator without a source is rejected."""
    card = copy.deepcopy(load_card())
    card["indicators"][0]["source"] = ""
    with pytest.raises(ValueError, match="indicator.source"):
        validate_card(card)


def test_non_finite_value_is_rejected() -> None:
    """A NaN or infinity is rejected."""
    card = copy.deepcopy(load_card())
    card["indicators"][0]["value"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        validate_card(card)


def test_invalid_review_status_is_rejected() -> None:
    """An operational review status is rejected."""
    card = copy.deepcopy(load_card())
    card["review_status"] = "operational"
    with pytest.raises(ValueError, match="review_status"):
        validate_card(card)


def test_non_advisory_alert_is_rejected() -> None:
    """An alert cannot opt out of the advisory boundary."""
    card = copy.deepcopy(load_card())
    card["alerts"][0]["advisory"] = False
    with pytest.raises(ValueError, match="advisory"):
        validate_card(card)
