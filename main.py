import tkinter as tk
from ui.ui_handler import UI
from connection.connection_handler import ConnectionManager
from utils.qrcode.qrcode_display import QRCodeDisplay
from utils.reporter.experiment_reporter import ExperimentReporter

if __name__ == '__main__':
    ui = UI(None)
    conn_manager = ConnectionManager(ui, ui.update_next_notification_time)
    ui.connection_manager = conn_manager

    email_config = {
        "smtp_server": "smtp.gmail.com",
        "port": 465,
        "sender": "ema.report.camera@gmail.com",
        "password": "vixh tpoa tgrx whdz",
        "recipient": ["y.li7@columbia.edu", "joshua.jacobs@columbia.edu", "hz2555@columbia.edu"]
    }
    reporter = ExperimentReporter(ui_instance=ui, email_config=email_config)

    ui.start()