import csv
import logging
import math
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)
STATION = "0-203-0-11514"
BASE_URL = "https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/temperature/"


@lru_cache(maxsize=1)
def _monthly_records(year, month):
    """Stream CHMI history and cache daily records for the current month.

    Historical data are updated annually; recheck each month. Only good
    observations from completed years enter records and the long-term mean.
    """
    records = {}
    for element in ("T", "TMA", "TMI"):
        url = f"{BASE_URL}dly-{STATION}-{element}.csv"
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            lines = (line.decode("utf-8-sig") for line in response.iter_lines())
            rows = csv.DictReader(lines)
            required = {"STATION", "ELEMENT", "TIMEFUNC", "DT", "VALUE", "QUALITY"}
            if not required.issubset(rows.fieldnames or []):
                raise ValueError("CHMI CSV header is missing")
            for row in rows:
                if row["STATION"] != STATION or row["ELEMENT"] != element:
                    continue
                if element == "T" and row["TIMEFUNC"] != "AVG":
                    continue
                if row["QUALITY"] not in ("0", "0.0") or not row["VALUE"]:
                    continue
                date = datetime.fromisoformat(row["DT"][:10]).date()
                if date.month != month or date.year >= year:
                    continue
                value = float(row["VALUE"])
                if not math.isfinite(value):
                    continue
                day = records.setdefault(date.day, {"sum": 0.0, "count": 0})
                if element == "T":
                    day["sum"] += value
                    day["count"] += 1
                else:
                    previous = day.get(element)
                    better = previous is None or (value > previous[0] if element == "TMA" else value < previous[0])
                    if better or (value == previous[0] and date.year < previous[1]):
                        day[element] = (value, date.year)
    if not records or any(not day["count"] or "TMA" not in day or "TMI" not in day for day in records.values()):
        raise ValueError("CHMI historical data are incomplete")
    return records


def get_klementinum_values():
    """Daily extremes and mean from available CHMI history since 1775."""
    try:
        today = datetime.now(ZoneInfo("Europe/Prague"))
        day = _monthly_records(today.year, today.month)[today.day]
        avg = f'{day["sum"] / day["count"]:.1f}'.replace(".", ",")
        maximum, max_year = day["TMA"]
        minimum, min_year = day["TMI"]
        return {
            "klementinum_avg": f"{avg}\u00b0C",
            "klementinum_max": f"{maximum:.1f}\u00b0C {max_year}".replace(".", ","),
            "klementinum_min": f"{minimum:.1f}\u00b0C {min_year}".replace(".", ","),
        }
    except (requests.exceptions.RequestException, ValueError, KeyError) as error:
        logger.error("Failed to fetch Klementinum history: %s", error)
        return {}
