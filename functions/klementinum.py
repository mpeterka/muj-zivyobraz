from datetime import datetime
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

URL = "https://www.chmi.cz/namerena-data/historicka-data/klementinum"


def get_klementinum_values():
    """
    Fetches historical temperature data from Klementinum and returns
    min, max, and average for the current date (month/day).

    The webpage has transposed tables: rows are data types (Průměr, Maximum, etc.)
    and columns are days (1-31).

    Returns:
        dict: {
            "klementinum_min": "X°C YYYY",
            "klementinum_max": "X°C YYYY",
            "klementinum_avg": "X°C"
        } or empty dict if failed
    """
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.content, 'html.parser')
        today = datetime.now()
        current_month = today.month
        current_day = today.day

        result = {
            "klementinum_min": "",
            "klementinum_max": "",
            "klementinum_avg": ""
        }

        # Find all tables on the page
        tables = soup.find_all('table')
        logger.debug(f"Found {len(tables)} tables on the page")

        if len(tables) < current_month:
            logger.warning(f"Not enough tables found. Expected at least {current_month}, got {len(tables)}")
            return result

        # Get the table for the current month (0-indexed, so month-1)
        month_table = tables[current_month - 1]

        # Extract headers to find the column index for the current day
        header_row = month_table.find('thead')
        if not header_row:
            logger.warning("Could not find table header")
            return result

        headers = header_row.find_all('th')
        day_column_index = None

        for idx, header in enumerate(headers):
            header_text = header.get_text(strip=True)
            if header_text == str(current_day):
                day_column_index = idx
                break

        if day_column_index is None:
            logger.warning(f"Could not find column for day {current_day} in month {current_month}")
            logger.debug(f"Available headers: {[h.get_text(strip=True) for h in headers[:10]]}")
            return result

        logger.debug(f"Found day {current_day} at column index {day_column_index}")

        # Parse the data rows from tbody
        # Structure: Row 0=Průměr, Row 1=Maximum, Row 2=Rok výskytu (max), Row 3=Minimum, Row 4=Rok výskytu (min)
        tbody = month_table.find('tbody')
        if not tbody:
            logger.warning("Could not find table body")
            return result

        body_rows = tbody.find_all('tr')

        if len(body_rows) < 5:
            logger.warning(f"Not enough data rows. Found {len(body_rows)}, expected at least 5")
            return result

        try:
            # Row 0: Průměr (Average)
            avg_cells = body_rows[0].find_all('td')
            avg_temp = avg_cells[day_column_index].get_text(strip=True)

            # Row 1: Maximum
            max_cells = body_rows[1].find_all('td')
            max_temp = max_cells[day_column_index].get_text(strip=True)

            # Row 2: Rok výskytu (for maximum)
            max_year_cells = body_rows[2].find_all('td')
            max_year = max_year_cells[day_column_index].get_text(strip=True)

            # Row 3: Minimum
            min_cells = body_rows[3].find_all('td')
            min_temp = min_cells[day_column_index].get_text(strip=True)

            # Row 4: Rok výskytu (for minimum)
            min_year_cells = body_rows[4].find_all('td')
            min_year = min_year_cells[day_column_index].get_text(strip=True)

            # Format results as "X°C" or "X°C YYYY"
            result["klementinum_avg"] = f"{avg_temp}°C".strip()
            result["klementinum_max"] = f"{max_temp}°C {max_year}".strip()
            result["klementinum_min"] = f"{min_temp}°C {min_year}".strip()

            logger.info(f"✓ Klementinum data for {current_day}.{current_month}.")
            logger.debug(f"  Avg: {result['klementinum_avg']}")
            logger.debug(f"  Max: {result['klementinum_max']}")
            logger.debug(f"  Min: {result['klementinum_min']}")

            return result

        except IndexError as e:
            logger.error(f"✗ Index error accessing table cells: {e}")
            logger.debug(f"  day_column_index: {day_column_index}, cells count: {len(avg_cells) if avg_cells else 'N/A'}")
            return result

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Failed to fetch Klementinum data: {e}")
        return {}
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return {}
