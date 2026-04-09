import os
import signal
import sys
import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from functions.popelnice import get_popelnice_value
from functions.klementinum import get_klementinum_values
from functions.menicka import scrape_menicka_ceske_budejovice
from functions.zemeplocha import zemeplocha_cs
from functions.fortunes import pratchet, plihal, cimrman, klsk_cz, vodnsnky, zemplcha
from functions.wiki import get_wiki_dnesek_v_minulosti

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
    """Generic function to call the API with a single value"""
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


def call_function_multiple(values_dict):
    """Call the API with multiple key-value pairs"""
    try:
        params = {"import_key": IMPORT_KEY}
        params.update(values_dict)
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        logger.info(f"✓ Multiple values sent | Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Multiple values failed: {e}")
        return False


def job_popelnice():
    """Job for popelnice function"""
    value = get_popelnice_value()
    call_function("popelnice", value)


def job_klementinum():
    """Job for klementinum function"""
    values = get_klementinum_values()
    if values:
        call_function_multiple(values)


def job_menicka():
    """Job for menicka function"""
    value = scrape_menicka_ceske_budejovice()
    call_function("menicka", value)


def job_zemeplocha_cs():
    """Job for zemeplocha_cs function"""
    values = zemeplocha_cs()
    if values:
        call_function_multiple(values)


def job_pratchet():
    """Job for pratchet function"""
    values = pratchet()
    if values:
        call_function_multiple(values)


def job_plihal():
    """Job for plihal function"""
    values = plihal()
    if values:
        call_function_multiple(values)


def job_cimrman():
    """Job for cimrman function"""
    values = cimrman()
    if values:
        call_function_multiple(values)


def job_klsk_cz():
    """Job for klsk_cz function"""
    values = klsk_cz()
    if values:
        call_function_multiple(values)


def job_vodnsnky():
    """Job for vodnsnky function"""
    values = vodnsnky()
    if values:
        call_function_multiple(values)


def job_zemplcha():
    """Job for zemplcha function"""
    values = zemplcha()
    if values:
        call_function_multiple(values)


def job_wiki_dnesek_v_minulosti():
    """Job for wiki_dnesek_v_minulosti function"""
    values = get_wiki_dnesek_v_minulosti()
    if values:
        call_function_multiple(values)


def signal_handler_run_all(signum, frame):
    """SIGUSR1: Run all jobs immediately"""
    logger.info("⚡ Signal SIGUSR1 received - running all jobs")
    job_popelnice()
    job_klementinum()
    job_menicka()
    job_zemeplocha_cs()
    job_pratchet()
    job_plihal()
    job_cimrman()
    job_klsk_cz()
    job_vodnsnky()
    job_zemplcha()
    job_wiki_dnesek_v_minulosti()


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

    # Schedule klementinum job every 6 hours
    scheduler.add_job(
        job_klementinum,
        'interval',
        hours=6,
        id='klementinum',
        name='Klementinum function',
        misfire_grace_time=15
    )

    # Schedule menicka job every 12 hours
    scheduler.add_job(
        job_menicka,
        'interval',
        hours=12,
        id='menicka',
        name='Menicka function',
        misfire_grace_time=15
    )

    # Schedule zemeplocha job every 12 hours
    scheduler.add_job(
        job_zemeplocha_cs,
        'interval',
        hours=12,
        id='zemeplocha_cs',
        name='Zemeplocha function',
        misfire_grace_time=15
    )

    # Schedule pratchet job every 12 hours
    scheduler.add_job(
        job_pratchet,
        'interval',
        hours=12,
        id='pratchet',
        name='Pratchet function',
        misfire_grace_time=15
    )

    # Schedule plihal job every 12 hours
    scheduler.add_job(
        job_plihal,
        'interval',
        hours=12,
        id='plihal',
        name='Plihal function',
        misfire_grace_time=15
    )

    # Schedule cimrman job every 12 hours
    scheduler.add_job(
        job_cimrman,
        'interval',
        hours=12,
        id='cimrman',
        name='Cimrman function',
        misfire_grace_time=15
    )

    # Schedule klsk_cz job every 12 hours
    scheduler.add_job(
        job_klsk_cz,
        'interval',
        hours=12,
        id='klsk_cz',
        name='Klsk CZ function',
        misfire_grace_time=15
    )

    # Schedule vodnsnky job every 12 hours
    scheduler.add_job(
        job_vodnsnky,
        'interval',
        hours=12,
        id='vodnsnky',
        name='Vodnsnky function',
        misfire_grace_time=15
    )

    # Schedule zemplcha job every 12 hours
    scheduler.add_job(
        job_zemplcha,
        'interval',
        hours=12,
        id='zemplcha',
        name='Zemplcha function',
        misfire_grace_time=15
    )

    # Schedule wiki_dnesek_v_minulosti job every 12 hours
    scheduler.add_job(
        job_wiki_dnesek_v_minulosti,
        'interval',
        hours=12,
        id='wiki_dnesek_v_minulosti',
        name='Wiki Dnesek v minulosti function',
        misfire_grace_time=15
    )

    # Run first jobs immediately
    logger.info("Running initial jobs...")
    job_popelnice()
    job_klementinum()
    job_menicka()
    job_zemeplocha_cs()
    job_pratchet()
    job_plihal()
    job_cimrman()
    job_klsk_cz()
    job_vodnsnky()
    job_zemplcha()
    job_wiki_dnesek_v_minulosti()

    logger.info("Scheduler started. Jobs will run every hour.")
    scheduler.start()

    # Keep the application running until signal is received
    signal.pause()


if __name__ == "__main__":
    main()
