# Experiment night reporter
import schedule
import threading
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class ExperimentReporter:
    def __init__(self, ui_instance, email_config):
        self.ui = ui_instance
        self.email_config = email_config

        # Schedule the report to run every day at 9:30 PM
        schedule.every().day.at("21:30").do(self.send_report)
        #schedule.every(1).minutes.do(self.send_report)     # (TESTING) sends reports after 1 min

        # Run schedule in a background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def _run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(30)

    def send_report(self):
        subject = "Daily EMA Report"
        body = (
                "Automated daily summary for today's EMA sessions:\n\n"
                f"Total EMAs Triggered: {self.ui.triggered_count}\n"
                f"  - Responded: {self.ui.responded_count}\n"
                f"    - Of those responded, {self.ui.completed_count} were fully completed.\n"
                f"  - Ignored: {self.ui.ignored_count}\n\n"
                f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "Please do not reply to this email."
            )

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.email_config['sender']
        msg['To'] = ", ".join(self.email_config['recipient'])

        try:
            with smtplib.SMTP_SSL(self.email_config['smtp_server'], self.email_config['port']) as server:
                server.login(self.email_config['sender'], self.email_config['password'])
                server.send_message(msg)
            print(f"[{datetime.now()}] - Email sent successfully.")
            self.ui.connection_manager.log_timestamped("Night report email sent.")
        except Exception as e:
            print(f"[{datetime.now()}] - Failed to send email: {e}")
            self.ui.connection_manager.log_timestamped(f"Failed to send night report email: {e}")