import os
import signal
import sys
import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
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

# Global scheduler reference for signal handlers
scheduler = None


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


def signal_handler_run_all(signum, frame):
    """SIGUSR1: Run all jobs immediately"""
    logger.info("⚡ Signal SIGUSR1 received - running all jobs")
    job_popelnice()


def signal_handler_shutdown(signum, frame):
    """SIGTERM/SIGINT: Graceful shutdown"""
    logger.info("🛑 Shutdown signal received...")
    if scheduler:
        scheduler.shutdown()
    sys.exit(0)


def main():
    global scheduler

    logger.info("Starting application...")
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"PID: {os.getpid()}")

    # Setup signal handlers
    signal.signal(signal.SIGUSR1, signal_handler_run_all)
    signal.signal(signal.SIGTERM, signal_handler_shutdown)
    signal.signal(signal.SIGINT, signal_handler_shutdown)

    logger.info("Signal handlers registered:")
    logger.info("  SIGUSR1 - Run all jobs")
    logger.info("  SIGTERM/SIGINT - Graceful shutdown")

    scheduler = BackgroundScheduler()

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
    scheduler.start()

    # Keep the application running until signal is received
    signal.pause()


if __name__ == "__main__":
    main()
