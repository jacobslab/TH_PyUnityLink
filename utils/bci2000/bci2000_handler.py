import sys
import threading
import time

sys.path.append('C:\\BCI2000.x64\\prog')
from BCI2000Remote import BCI2000Remote

class BCI2000Handler:
    def __init__(self, log_bci_message):
        self.bci = BCI2000Remote()
        self.connected = False
        self.stop_monitor = threading.Event()
        self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
        self.monitor_thread.start()
        self.log_bci_message = log_bci_message  # Use ConnectionManager's logging function

    def connect_bci2000(self):
        if self.connected:
            return
        
        try:
            self.bci.Connect()
            self.connected = True
            self.log_bci_message("Connected to BCI2000")
        except Exception as e:
            self.log_bci_message(f"Failed to connect to BCI2000: {e}")

    def handle_disconnection(self):
        if self.connected:
            self.connected = False
            self.log_bci_message("Lost connection to BCI2000. Attempting to reconnect...")
            self.connect_bci2000()

    def monitor_connection(self):
        while not self.stop_monitor.is_set():
            time.sleep(1)
            if not self.connected:
                continue

            try:
                if not self.bci.GetParameter("SubjectName"):  # Empty or None means disconnected
                    self.handle_disconnection()
            except Exception:
                self.handle_disconnection()

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
        self.connect_bci2000()  # Ensure connection before sending data
        
        try:
            self.bci.SetEventVariable(event_variable, value_variable)
            self.log_bci_message(f"Synced BCI event: {event_variable} = {value_variable}")
        except Exception as e:
            self.log_bci_message(f"Failed to sync event: {e}")
            self.handle_disconnection()
    
    def get_bci_subjectName(self):
        self.connect_bci2000()
        
        try:
            name = self.bci.GetParameter("SubjectName")
            return name if name else "<BCI_SubjectName>"
        except Exception:
            self.log_bci_message("BCI2000 not connected at EMA log file initialization")
            return "<BCI_SubjectName>"
    
    def get_bci_subjectID(self):
        self.connect_bci2000()

        try:
            id = self.bci.GetParameter("SubjectSession")
            return id if id else "<BCI_SubjectSession>"
        except Exception:
            self.log_bci_message("BCI2000 not connected at EMA log file initialization")
            return "<BCI_SubjectSession>"

    def stop(self):
        self.stop_monitor.set()