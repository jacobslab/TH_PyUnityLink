import json
import os
import threading
from ui.ui_handler import UI
from connection.connection_handler import ConnectionManager
from utils.reporter.experiment_reporter import ExperimentReporter
from utils.datauploader.data_uploader import DataUploader


def load_email_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)["email"]


if __name__ == '__main__':
    ui = UI(None)

    email_config = load_email_config()
    reporter = ExperimentReporter(ui_instance=ui, email_config=email_config)

    conn_manager = ConnectionManager(ui, ui.update_next_notification_time, reporter)
    ui.connection_manager = conn_manager

    reporter.start()

    data_uploader = DataUploader()
    threading.Thread(target=data_uploader.schedule_daily_sync, daemon=True).start()

    ui.start()
