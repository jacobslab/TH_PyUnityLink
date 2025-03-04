import sys
sys.path.append('C:\\BCI2000.x64\\prog')
from BCI2000Remote import BCI2000Remote

class BCI2000Handler:
    def __init__(self):
        self.bci = BCI2000Remote()
        self.connected = False

    def connect_bci2000(self):
        if not self.connected:
            self.bci.Connect()
            self.connected = True

    # BCI2000 sync function for EMA input
    def process_bci_data(self, message):
        if not self.connected:
            self.connect_bci2000()
            self.connected = True

        try:
            key_value = message.split(":")[1].strip()  # Extract "session=1"
            key, value = key_value.split("=")  # Split into "session" and "1"
            self.sync_bci_event(key.strip(), int(value.strip()))
            print(f"Synced BCI event [EMA]: {key.strip()} = {int(value.strip())}")
        except (ValueError, IndexError):
            print(f"Invalid BCI_Sync message format: {message}")
        else:
            print(f"Unexpected BCI_Sync format: {message}")
    
    # BCI2000 sync function for Python input
    def sync_bci_event(self, event_variable, value_variable):
        self.bci.SetEventVariable(event_variable, value_variable)
        print(f"Synced BCI event [PyLink]: {event_variable} = {value_variable}")