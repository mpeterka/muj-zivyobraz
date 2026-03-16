import os
import time
import requests
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from functions.popelnice import get_popelnice_value

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://in.zivyobraz.eu/"
IMPORT_KEY = os.getenv("IMPORT_KEY")

if not IMPORT_KEY:
    logger.error("IMPORT_KEY environment variable not set")
    exit(1)


def call_function(function_name, value):
    """Generic function to call the API with a specific function"""
    try:
        params = {
            "import_key": IMPORT_KEY,
            function_name: value
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        logger.info(f"✓ {function_name}={value} | Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ {function_name} failed: {e}")
        return False


def job_popelnice():
    """Job for popelnice function"""
    value = get_popelnice_value()
    call_function("popelnice", value)


def job_heartbeat():
    """Job to keep the application responsive"""
    logger.info("Heartbeat")


def main():
    logger.info("Starting application...")
    logger.info(f"Base URL: {BASE_URL}")

    scheduler = BlockingScheduler()

    # Schedule popelnice job every hour
    scheduler.add_job(
        job_popelnice,
        'interval',
        hours=1,
        id='popelnice',
        name='Popelnice function',
        misfire_grace_time=15
    )

    # Run first job immediately
    logger.info("Running initial job...")
    job_popelnice()

    logger.info("Scheduler started. Jobs will run every hour.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
