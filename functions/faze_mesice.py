from __future__ import annotations

from datetime import datetime, timezone
import logging

import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.met.no/weatherapi/sunrise/3.0/moon"
LATITUDE = 50.0755
LONGITUDE = 14.4378
USER_AGENT = "muj-zivyobraz/1.0"

PHASE_SYMBOLS = {
    "New Moon": "🌑",
    "Waxing Crescent": "🌒",
    "First Quarter": "🌓",
    "Waxing Gibbous": "🌔",
    "Full Moon": "🌕",
    "Waning Gibbous": "🌖",
    "Last Quarter": "🌗",
    "Waning Crescent": "🌘",
}


def _timezone_offset() -> str:
    offset = datetime.now().astimezone().utcoffset()
    if offset is None:
        return "+00:00"

    total_minutes = int(offset.total_seconds() / 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def _phase_name_from_degrees(degrees: float) -> str:
    degrees %= 360.0
    if degrees < 22.5 or degrees >= 337.5:
        return "New Moon"
    if degrees < 67.5:
        return "Waxing Crescent"
    if degrees < 112.5:
        return "First Quarter"
    if degrees < 157.5:
        return "Waxing Gibbous"
    if degrees < 202.5:
        return "Full Moon"
    if degrees < 247.5:
        return "Waning Gibbous"
    if degrees < 292.5:
        return "Last Quarter"
    return "Waning Crescent"


def _extract_degrees(payload: dict) -> float | None:
    properties = payload.get("properties")
    if not properties:
        return None

    raw_degree = properties.get("moonphase")
    if isinstance(raw_degree, dict):
        raw_degree = raw_degree.get("value")
    if raw_degree is None:
        return None

    try:
        return float(raw_degree)
    except (TypeError, ValueError):
        return None


def faze_mesice() -> dict | None:
    """Fetch the current lunar degree and return the phase symbol + metadata."""

    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "offset": _timezone_offset(),
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        phase_degrees = _extract_degrees(response.json())
        if phase_degrees is None:
            logger.error("faze_mesice: moonphase value missing in response")
            return None

        phase_name = _phase_name_from_degrees(phase_degrees)
        symbol = PHASE_SYMBOLS.get(phase_name, "🌑")
        return {
            "symbol": symbol,
            "name": phase_name,
            "degrees": phase_degrees,
        }
    except requests.exceptions.RequestException as exc:
        logger.error("faze_mesice: %s", exc)
        return None
