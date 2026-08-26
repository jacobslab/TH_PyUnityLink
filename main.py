import tkinter as tk
from ui.ui_handler import UI
from connection.connection_handler import ConnectionManager
from utils.qrcode.qrcode_display import QRCodeDisplay
from utils.reporter.experiment_reporter import ExperimentReporter

if __name__ == '__main__':
    ui = UI(None)

    email_config = {
        "smtp_server": "smtp.gmail.com",
        "port": 465,
        "sender": "ema.report.camera@gmail.com",
        "password": "gkoz pboj avun ovnk",
        "recipient": ["camerabrainstudy@cumc.columbia.edu",
                     "joshuajacobs@uchicago.edu",
                     "bey2103@cumc.columbia.edu",
                     "cz2715@columbia.edu",
                     "hz2555@uchicago.edu",
                     "francisyli@uchicago.edu",
                     "agv2113@cumc.columbia.edu",
                     "ys3799@cumc.columbia.edu",
                     "ac4495@cumc.columbia.edu",
                     ]
        # "recipient": ["cz2715@columbia.edu",
        #               "hz2555@uchicago.edu",
        #               "francisyli@uchicago.edu"
        #               ]
        #"recipient": ["francisyli@uchicago.edu"]
    }
    reporter = ExperimentReporter(ui_instance=ui, email_config=email_config)

    conn_manager = ConnectionManager(ui, ui.update_next_notification_time, reporter)
    ui.connection_manager = conn_manager

    reporter.start()

    ui.start()