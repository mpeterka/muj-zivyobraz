import os
import signal
import sys
import requests
import logging
import time
from functools import wraps
from opentelemetry import trace
from opentelemetry.trace import StatusCode
from tracing import configure as configure_tracing
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
from apscheduler.schedulers.background import BackgroundScheduler
from functions.popelnice import get_popelnice_value
from functions.klementinum import get_klementinum_values
from functions.menicka import get_menicka_values
from functions.zemeplocha import zemeplocha_cs
from functions.faze_mesice import faze_mesice
from functions.fortunes import pratchet, plihal, cimrman, klsk_cz, vodnsnky, zemplcha
from functions.wiki import get_wiki_dnesek_v_minulosti, get_wiki_aktuality
from functions.vtipy import get_vtipy_values
from functions.detske_prace import get_detske_prace_values
from functions.slunce import get_slunce_zitra_values
from functions.pranostika import get_pranostika_values

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
metrics_server = None
tracing_provider = None
tracer = trace.get_tracer('muj-zivyobraz.jobs')
deployment_version = os.getenv('APP_DEPLOYMENT_VERSION', 'unknown')
if len(deployment_version) > 80 or not all(char.isalnum() or char in '._-' for char in deployment_version):
    deployment_version = 'unknown'
Info('zivyobraz_build', 'Deployed application version').info({'version': deployment_version})
Gauge('zivyobraz_application_start_timestamp_seconds', 'Application startup timestamp').set(time.time())

UPLOADS = Counter('zivyobraz_uploads_total', 'API uploads by result', ['result'])
LAST_UPLOAD_SUCCESS = Gauge('zivyobraz_last_upload_success_timestamp_seconds', 'Last successful API upload')
JOB_RUNS = Counter('zivyobraz_job_runs_total', 'Job completions; completed does not imply data was available', ['task', 'result'])
JOB_DURATION = Histogram('zivyobraz_job_duration_seconds', 'Job execution duration', ['task'], buckets=(1, 5, 15, 60, 300, 900))
JOB_LAST_RUN = Gauge('zivyobraz_job_last_run_timestamp_seconds', 'Last finished job execution', ['task'])
for result in ('success', 'error'):
    UPLOADS.labels(result=result)


def track_job(function):
    job = function.__name__.removeprefix('job_')
    for result in ('completed', 'error'):
        JOB_RUNS.labels(task=job, result=result)
    JOB_LAST_RUN.labels(task=job)

    @wraps(function)
    def measured(*args, **kwargs):
        started = time.monotonic()
        result = 'completed'
        with tracer.start_as_current_span('scheduled job', attributes={'job.name': job}, record_exception=False, set_status_on_exception=False) as span:
            try:
                return function(*args, **kwargs)
            except Exception:
                result = 'error'
                span.set_status(StatusCode.ERROR)
                raise
            finally:
                JOB_RUNS.labels(task=job, result=result).inc()
                JOB_DURATION.labels(task=job).observe(time.monotonic() - started)
                JOB_LAST_RUN.labels(task=job).set_to_current_time()
    return measured


def call_function(function_name, value):
    """Generic function to call the API with a single value"""
    try:
        params = {
            "import_key": IMPORT_KEY,
            function_name: value
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        UPLOADS.labels(result='success').inc()
        LAST_UPLOAD_SUCCESS.set_to_current_time()
        logger.info(f"✓ {function_name}={value} | Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        trace.get_current_span().set_status(StatusCode.ERROR)
        UPLOADS.labels(result='error').inc()
        logger.error(f"✗ {function_name} failed: {e}")
        return False


def call_function_multiple(values_dict):
    """Call the API with multiple key-value pairs"""
    try:
        params = {"import_key": IMPORT_KEY}
        params.update(values_dict)
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        UPLOADS.labels(result='success').inc()
        LAST_UPLOAD_SUCCESS.set_to_current_time()
        logger.info(f"✓ Multiple values sent | Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        trace.get_current_span().set_status(StatusCode.ERROR)
        UPLOADS.labels(result='error').inc()
        logger.error(f"✗ Multiple values failed: {e}")
        return False


@track_job
def job_popelnice():
    """Job for popelnice function"""
    value = get_popelnice_value()
    call_function("popelnice", value)


@track_job
def job_klementinum():
    """Job for klementinum function"""
    values = get_klementinum_values()
    if values:
        call_function_multiple(values)


@track_job
def job_menicka():
    """Job for menicka function"""
    call_function_multiple(get_menicka_values())


@track_job
def job_detske_prace():
    call_function_multiple(get_detske_prace_values())


@track_job
def job_slunce_zitra():
    values = get_slunce_zitra_values()
    if values:
        call_function_multiple(values)


@track_job
def job_pranostika():
    values = get_pranostika_values()
    if values:
        call_function_multiple(values)


@track_job
def job_zemeplocha_cs():
    """Job for zemeplocha_cs function"""
    values = zemeplocha_cs()
    if values:
        call_function_multiple(values)


@track_job
def job_pratchet():
    """Job for pratchet function"""
    values = pratchet()
    if values:
        call_function_multiple(values)


@track_job
def job_plihal():
    """Job for plihal function"""
    values = plihal()
    if values:
        call_function_multiple(values)


@track_job
def job_cimrman():
    """Job for cimrman function"""
    values = cimrman()
    if values:
        call_function_multiple(values)


@track_job
def job_klsk_cz():
    """Job for klsk_cz function"""
    values = klsk_cz()
    if values:
        call_function_multiple(values)


@track_job
def job_vodnsnky():
    """Job for vodnsnky function"""
    values = vodnsnky()
    if values:
        call_function_multiple(values)


@track_job
def job_zemplcha():
    """Job for zemplcha function"""
    values = zemplcha()
    if values:
        call_function_multiple(values)


@track_job
def job_faze_mesice():
    """Job for faze_mesice function"""
    payload = faze_mesice()
    if payload:
        call_function("faze_mesice", payload["symbol"])


@track_job
def job_wiki_dnesek_v_minulosti():
    """Job for wiki_dnesek_v_minulosti function"""
    values = get_wiki_dnesek_v_minulosti()
    if values:
        call_function_multiple(values)


@track_job
def job_wiki_aktuality():
    values = get_wiki_aktuality()
    if values:
        call_function_multiple(values)


@track_job
def job_vtipy():
    values = get_vtipy_values()
    if values:
        call_function_multiple(values)


def signal_handler_run_all(signum, frame):
    """SIGUSR1: Run all jobs immediately"""
    logger.info("⚡ Signal SIGUSR1 received - running all jobs")
    job_popelnice()
    job_klementinum()
    job_menicka()
    job_detske_prace()
    job_slunce_zitra()
    job_pranostika()
    job_zemeplocha_cs()
    job_pratchet()
    job_plihal()
    job_cimrman()
    job_klsk_cz()
    job_vodnsnky()
    job_zemplcha()
    job_faze_mesice()
    job_wiki_dnesek_v_minulosti()
    job_wiki_aktuality()
    job_vtipy()


def signal_handler_shutdown(signum, frame):
    """SIGTERM/SIGINT: Graceful shutdown"""
    logger.info("🛑 Shutdown signal received...")
    if scheduler:
        scheduler.shutdown()
    if metrics_server:
        metrics_server.shutdown()
        metrics_server.server_close()
    if tracing_provider:
        tracing_provider.shutdown()
    sys.exit(0)


def main():
    global scheduler, metrics_server, tracing_provider
    tracing_provider = configure_tracing()

    logger.info("Starting application...")
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"PID: {os.getpid()}")
    metrics_server, _ = start_http_server(8000, addr='0.0.0.0')

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

    # Refresh while restaurants publish lunch menus, using Czech local time.
    scheduler.add_job(
        job_menicka,
        'cron',
        hour='7-14,18',
        minute=0,
        timezone='Europe/Prague',
        id='menicka',
        name='Menicka function',
        misfire_grace_time=300
    )

    scheduler.add_job(
        job_detske_prace,
        'cron',
        hour='0,6,12,18',
        minute=0,
        timezone='Europe/Prague',
        id='detske_prace',
        name='Detske prace function',
        misfire_grace_time=300
    )

    scheduler.add_job(
        job_slunce_zitra, 'cron', hour='0,6,12,18', minute=0,
        timezone='Europe/Prague', id='slunce_zitra',
        misfire_grace_time=300
    )

    scheduler.add_job(
        job_pranostika, 'cron', hour='0,6,12,18', minute=0,
        timezone='Europe/Prague', id='pranostika', misfire_grace_time=300
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

    # Refresh before the morning screen and later in the day, in Czech time.
    scheduler.add_job(
        job_wiki_dnesek_v_minulosti,
        'cron',
        hour='5,12,18',
        minute=0,
        timezone='Europe/Prague',
        id='wiki_dnesek_v_minulosti',
        name='Wiki Dnesek v minulosti function',
        misfire_grace_time=300
    )

    scheduler.add_job(
        job_wiki_aktuality,
        'cron',
        hour='5,12,18',
        minute=0,
        timezone='Europe/Prague',
        id='wiki_aktuality',
        name='Wiki Aktuality function',
        misfire_grace_time=300
    )

    scheduler.add_job(
        job_faze_mesice,
        'interval',
        hours=6,
        id='faze_mesice',
        name='Faze mesice function',
        misfire_grace_time=15
    )

    # Refresh the joke every six hours.
    scheduler.add_job(
        job_vtipy,
        'interval',
        hours=6,
        id='vtipy',
        name='Vtipy function',
        misfire_grace_time=300
    )

    # Run first jobs immediately
    logger.info("Running initial jobs...")
    job_popelnice()
    job_klementinum()
    job_menicka()
    job_detske_prace()
    job_slunce_zitra()
    job_pranostika()
    job_zemeplocha_cs()
    job_pratchet()
    job_plihal()
    job_cimrman()
    job_klsk_cz()
    job_vodnsnky()
    job_zemplcha()
    job_faze_mesice()
    job_wiki_dnesek_v_minulosti()
    job_wiki_aktuality()
    job_vtipy()

    logger.info("Scheduler started. Jobs will run every hour.")
    scheduler.start()

    # Keep the application running until signal is received
    signal.pause()


if __name__ == "__main__":
    main()
