import logging
import os
import signal
import sys
from datetime import datetime, timezone, timedelta
from time import sleep
import threading
from aw_client import ActivityWatchClient
from aw_core.log import setup_logging
from aw_core.models import Event
from multiprocessing import Queue
import requests
from flask import Flask, request, render_template
from dateutil.parser import parse as parse_datetime
from datetime import datetime
import json

from .config import parse_args
from .exceptions import FatalError
from .lib import get_current_window

logger = logging.getLogger(__name__)
manual_input_queue = Queue()

# Declaração da variável global client
client = None

# run with LOG_LEVEL=DEBUG
log_level = os.environ.get("LOG_LEVEL")
if log_level:
    logger.setLevel(logging.__getattribute__(log_level.upper()))

# Global variable to store bucket_id
global_bucket_id = None

def kill_process(pid):
    logger.info("Killing process {}".format(pid))
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        logger.info("Process {} already dead".format(pid))



if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'Static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

def create_data_dict(name_value):
    from . import regex as regex_module
    regex_result = regex_module.regex(name_value)
    return {"app": name_value, "title": name_value, "regex": regex_result}

def run_flask():
    app.run(port=5020, debug=False)

def main():
    global global_bucket_id  # Accessing the global variable
    global client  # Accessing the global variable
    args = parse_args()

    if sys.platform.startswith("linux") and (
        "DISPLAY" not in os.environ or not os.environ["DISPLAY"]
    ):
        raise Exception("DISPLAY environment variable not set")

    setup_logging(
        name="aw-watcher-quattrod",
        testing=args.testing,
        verbose=args.verbose,
        log_stderr=True,
        log_file=True,
    )

    client = ActivityWatchClient(
        "aw-watcher-quattrod", host=args.host, port=args.port, testing=args.testing
    )

    bucket_id = f"aw-watcher-window_{client.client_hostname}"
    event_type = "currentwindow"

    # Assigning bucket_id to global variable
    global_bucket_id = bucket_id

    client.create_bucket(bucket_id, event_type, queued=True)

    logger.info("aw-watcher-quattrod started")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()


    sleep(1)  # wait for the server to start
    with client:
        heartbeat_loop(
            client,
            bucket_id,
            poll_time=args.poll_time,
            strategy=args.strategy,
            exclude_title=args.exclude_title,
        )


def heartbeat_loop(client, bucket_id, poll_time, strategy, exclude_title=False):
    while True:
        if os.getppid() == 1:
            logger.info("window-watcher stopped because the parent process died")
            break

        # Check for manual input
        if not manual_input_queue.empty():
            manual_input_event = manual_input_queue.get()
            client.heartbeat(bucket_id, manual_input_event, pulsetime=1.0, queued=True)

        current_window = None
        try:
            current_window = get_current_window(strategy)
            logger.debug(current_window)
        except (FatalError, OSError):
            # Fatal exceptions should quit the program
            try:
                logger.exception("Fatal error, stopping")
            except OSError:
                pass
            break
        except Exception:
            # Non-fatal exceptions should be logged
            try:
                # If stdout has been closed, this exception-print can cause (I think)
                #   OSError: [Errno 5] Input/output error
                # See: https://github.com/ActivityWatch/activitywatch/issues/756#issue-1296352264
                #
                # However, I'm unable to reproduce the OSError in a test (where I close stdout before logging),
                # so I'm in uncharted waters here... but this solution should work.
                logger.exception("Exception thrown while trying to get active window")
            except OSError:
                break

        if current_window is None:
            logger.debug("Unable to fetch window, trying again on the next poll")
        else:
            if exclude_title:
                current_window["title"] = "excluded"

            now = datetime.now(timezone.utc)
            current_window_event = Event(timestamp=now, data=current_window)

            client.heartbeat(
                bucket_id, current_window_event, pulsetime=poll_time + 1.0, queued=True
            )

        sleep(poll_time)
        

@app.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    global global_bucket_id
    global client  # Accessing the global variable
    response_data = None
    message = ""  # Defina a mensagem como uma string vazia por padrão
    form_data = None  # Inicialize form_data como None

    if request.method == 'POST':
        date_value = request.form.get('date')
        time_value = request.form.get('time')
        end_time = request.form.get('endTime')
        name_value = request.form.get('title')

        name_value += " (Input Manual)"

        start_datetime = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
        start_datetime_utc = start_datetime.astimezone(timezone.utc)

        end_datetime = datetime.strptime(f"{date_value} {end_time}", "%Y-%m-%d %H:%M")
        end_datetime_utc = end_datetime.astimezone(timezone.utc)

        duration_in_seconds = int((end_datetime - start_datetime).total_seconds())
        print(duration_in_seconds)

        data_dict = create_data_dict(name_value)

        url = f"http://localhost:5600/api/0/buckets/{global_bucket_id}/events"

        params = {
            'start': start_datetime_utc.strftime("%Y-%m-%d %H:%M:%S%z"),
            'end': end_datetime_utc.strftime("%Y-%m-%d %H:%M:%S%z")
        }

        user_id = global_bucket_id.split('_')[1]
        afk_bucket_id = f"aw-watcher-afk_{user_id}"

        url_afk = f"http://localhost:5600/api/0/buckets/{afk_bucket_id}/events"

        response = requests.get(url, headers={'accept': 'application/json'}, params=params)
        responseAfk = requests.get(url_afk, headers={'accept': 'application/json'}, params=params)
        responseAfk_WD = requests.get(url_afk, headers={'accept': 'application/json'})

        if response.status_code == 200 and responseAfk.status_code == 200:
            response_data = response.json()
            responseAfk_data = responseAfk.json()
            responseAfkWD_data = responseAfk_WD.json()

            afk_event_ids = []
            for event_afk in responseAfk_data:
                if event_afk["data"]["status"] == "afk":
                    event_timestamp = parse_datetime(event_afk["timestamp"])
                    afk_event_ids.append({
                        "id": event_afk["id"],
                        "timestamp": event_timestamp,
                        "duration": event_afk["duration"]
                    })

            if not response_data:
                if duration_in_seconds > 3600:
                    num_segments = duration_in_seconds // 3600  # Número de segmentos completos (1 hora)
                    remaining_seconds = duration_in_seconds % 3600  # Tempo restante

                    for i in range(num_segments):
                        segment_start = start_datetime_utc + timedelta(hours=i)
                        segment_duration = 3600  # 1 hora em segundos

                        segment_event = Event(timestamp=segment_start, duration=segment_duration, data=data_dict)
                        client.heartbeat(global_bucket_id, segment_event, pulsetime=1.0, queued=True)

                    if remaining_seconds > 0:
                        final_segment_start = start_datetime_utc + timedelta(hours=num_segments)
                        final_segment_event = Event(timestamp=final_segment_start, duration=remaining_seconds, data=data_dict)
                        client.heartbeat(global_bucket_id, final_segment_event, pulsetime=1.0, queued=True)
                else:
                    for i in range(duration_in_seconds // 3600 + 1):
                        segment_start = start_datetime_utc + timedelta(hours=i)
                        segment_event = Event(timestamp=segment_start, duration=3600, data=data_dict)
                        client.heartbeat(global_bucket_id, segment_event, pulsetime=1.0, queued=True)
            elif 'confirm' in request.form:
                if duration_in_seconds > 3600:
                    num_segments = duration_in_seconds // 3600
                    remaining_seconds = duration_in_seconds % 3600

                    for i in range(num_segments):
                        segment_start = start_datetime_utc + timedelta(hours=i)
                        segment_duration = 3600

                        segment_event = Event(timestamp=segment_start, duration=segment_duration, data=data_dict)
                        client.heartbeat(global_bucket_id, segment_event, pulsetime=1.0, queued=True)

                    if remaining_seconds > 0:
                        final_segment_start = start_datetime_utc + timedelta(hours=num_segments)
                        final_segment_event = Event(timestamp=final_segment_start, duration=remaining_seconds, data=data_dict)
                        client.heartbeat(global_bucket_id, final_segment_event, pulsetime=1.0, queued=True)
                else:
                    for i in range(duration_in_seconds // 3600 + 1):
                        segment_start = start_datetime_utc + timedelta(hours=i)
                        segment_event = Event(timestamp=segment_start, duration=3600, data=data_dict)
                        client.heartbeat(global_bucket_id, segment_event, pulsetime=1.0, queued=True)

                requests.delete(url, headers={'accept': 'application/json'}, params=params)
                requests.delete(url_afk, headers={'accept': 'application/json'}, params=params)
                message = "Eventos deletados e evento manual criado com sucesso."
            else:
                message = "Eventos existentes encontrados no período especificado."

            form_data = {
                "title": name_value,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "existing_events": response_data,
                "afk_event_ids": afk_event_ids
            }

        else:
            message = "Erro ao buscar eventos existentes."

    return render_template('manual_input.html', message=message, form_data=form_data)


 #http://localhost:5600/
 #100.112.169.117:5600/