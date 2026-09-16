import sys
import threading
import time
import psutil
from datetime import datetime, timedelta

# BCI2000Remote is the vendor SDK for the BCI2000 rig. It's only installed on
# the actual experiment PC, so importing it fails on any dev/test machine.
# BCI2000_AVAILABLE gates every BCI2000-specific action below so the rest of
# the app (EMA, email, data upload) keeps working when it's absent.
try:
    sys.path.append('C:\\BCI2000.x64\\prog')
    from BCI2000Remote import BCI2000Remote
    BCI2000_AVAILABLE = True
except ImportError:
    BCI2000Remote = None
    BCI2000_AVAILABLE = False

class BCI2000Handler:
    def __init__(self, log_bci_message, send_email):
        self.log_bci_message = log_bci_message  # Use ConnectionManager's logging function
        self.send_email = send_email    # Use ExperimentReporter's send email function
        self.connected = False
        self.stop_monitor = threading.Event()

        if BCI2000_AVAILABLE:
            self.bci = BCI2000Remote()
            self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
            self.monitor_thread.start()
        else:
            self.bci = None
            self.log_bci_message("BCI2000Remote module not found on this machine - BCI2000 features disabled.")
        #self.schedule_disconnect_reconnect()

    def connect_bci2000(self):
        if not BCI2000_AVAILABLE or self.connected:
            return
        try:
            self.bci.Connect()
            self.connected = True
            self.log_bci_message("Connected to BCI2000")
        except Exception as e:
            self.log_bci_message(f"Failed to connect to BCI2000: {e}")

    def disconnect_bci2000(self):
        if self.connected:
            self.bci.Disconnect()
            self.connected = False
            self.log_bci_message("Disconnected from BCI2000")

    def check_bci2000_running_status(self):
        if not BCI2000_AVAILABLE:
            return False

        # BCI2000 module name .exe
        target_names = {"SignalGenerator.exe"}
        for proc in psutil.process_iter(attrs=['name']):
            try:
                if proc.info['name'] in target_names:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False


    def handle_disconnection(self):
        if self.connected:
            self.connected = False
            self.log_bci_message("Lost connection to BCI2000. Attempting to reconnect...")
            self.connect_bci2000()

    def monitor_connection(self):
        while not self.stop_monitor.is_set():
            time.sleep(1)
            if self.connected:
                if not self.check_bci2000_running_status():
                    self.connected = False
                    self.log_bci_message("Lost connection to BCI2000. Waiting for watchdog to restart module...")
            else:
                if self.check_bci2000_running_status():
                    self.log_bci_message("BCI2000 module is back up. Attempting to reconnect...")
                    self.connect_bci2000()

    def process_bci_data(self, message):
        self.connect_bci2000()

        try:
            key_value = message.split(":")[1].strip()
            key, value = key_value.split("=")
            self.sync_bci_event(key.strip(), int(value.strip()))
            #self.log_bci_message(f"Synced BCI event [EMA]: {key.strip()} = {int(value.strip())}")
        except (ValueError, IndexError):
            self.log_bci_message(f"Invalid BCI_Sync message format: {message}")

    def sync_bci_event(self, event_variable, value_variable):
        if not BCI2000_AVAILABLE:
            return
        self.connect_bci2000()  # Ensure connection before sending data

        try:
            self.bci.SetEventVariable(event_variable, value_variable)
            self.log_bci_message(f"Synced BCI event: {event_variable} = {value_variable}")
        except Exception as e:
            self.log_bci_message(f"Failed to sync event: {e}")
            self.handle_disconnection()

    def mark_photodiode_event(self, is_white):
        """Marks the photodiode flicker color for BCI sync. No-op if BCI2000 is unavailable."""
        if not BCI2000_AVAILABLE:
            return
        self.connect_bci2000()
        try:
            self.bci.SetEventVariable("EmaColor", 1 if is_white else 2)
        except Exception as e:
            self.log_bci_message(f"Failed to set photodiode event: {e}")
            self.handle_disconnection()

    def get_bci_subjectName(self):
        if not BCI2000_AVAILABLE:
            self.log_bci_message("BCI2000Remote not available on this machine; skipping subject name lookup.")
            return "<BCI_SubjectName>"

        self.connect_bci2000()

        try:
            name = self.bci.GetParameter("SubjectName")
            return name if name else "<BCI_SubjectName>"
        except Exception:
            if self.send_email:
                subject = "[Alert] BCI2000 Not Running at triggered EMA"
                body = (
                    "An scheduled EMA was triggerred "
                    "and the iPad was attempting to connect BCI2000 modules,"
                    " but BCI2000 was NOT running at this time. \n"
                    "Please check the BCI2000 system status. \n\n"
                    "This is an autogenerated alert email, please do not reply"
                )
                self.send_email(subject, body)
            self.log_bci_message("BCI2000 not connected at EMA log file initialization")
            return "<BCI_SubjectName>"

    def get_bci_subjectID(self):
        if not BCI2000_AVAILABLE:
            self.log_bci_message("BCI2000Remote not available on this machine; skipping subject ID lookup.")
            return "<BCI_SubjectSession>"

        self.connect_bci2000()

        try:
            id = self.bci.GetParameter("SubjectSession")
            return id if id else "<BCI_SubjectSession>"
        except Exception:
            self.log_bci_message("BCI2000 not connected at EMA log file initialization")
            return "<BCI_SubjectSession>"
    

    def schedule_disconnect_reconnect(self):
        # Schedule disconnect at 9:01 PM
        self.schedule_task(self.disconnect_bci2000, "21:01")

        # Schedule reconnect at 8:59 AM
        self.schedule_task(self.connect_bci2000, "08:59")

    def schedule_task(self, task, target_time):
        # Calculate the time difference to the target time
        target_hour, target_minute = map(int, target_time.split(":"))
        now = datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        if target_time < now:
            target_time += timedelta(days=1)  # Schedule for the next day

        delay = (target_time - now).total_seconds()

        # Schedule the task using a timer
        threading.Timer(delay, task).start()

    def stop(self):
        self.stop_monitor.set()