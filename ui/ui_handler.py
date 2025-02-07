import tkinter as tk
from datetime import datetime

class UI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Treasure Hunt Remote Control")
        self.connection_manager = None

        self.is_bci_enabled = tk.BooleanVar(value=False)
        self.is_testmode_enabled = tk.BooleanVar(value=True)

        self.last_notification_time = None
        """
        # Create and configure the input field and label
        label = tk.Label(self.root, text="Enter Subject ID:")
        label.pack()

        self.entry = tk.Entry(self.root, width=50)
        self.entry.pack()

        # Bind the Enter key to the send_message function
        self.entry.bind('<Return>', lambda event: self.send_message())
        """

        # show last notification time
        self.last_start_label = tk.Label(self.root, text="Session Start: N/A")
        self.last_start_label.pack(pady=10)

        # show next notification time
        self.next_start_label = tk.Label(self.root, text="Next Notification: N/A")
        self.next_start_label.pack(pady=10)

        # button for "VIEW" signal
        view_button = tk.Button(self.root, text="Show INFO", command=self.send_view_signal)
        view_button.pack(pady=10)

        # button for "START" signal
        start_button = tk.Button(self.root, text="Start EMA", command=self.send_start_signal)
        start_button.pack(padx=5)

        # button for "CANCEL" signal
        cancel_button = tk.Button(self.root, text="Skip Current EMA", command=self.send_cancel_signal)
        cancel_button.pack(padx=5)

        # Create a frame for the BCI toggle and label
        bci_frame = tk.Frame(self.root)
        bci_frame.pack(pady=10)

        # Create a toggle for BCI Connection
        bci_toggle = tk.Checkbutton(bci_frame, text="Enable BCI2000", variable=self.is_bci_enabled)
        bci_toggle.pack(side=tk.LEFT)

        # Create a toggle for Test Mode
        test_toggle = tk.Checkbutton(bci_frame, text="Test Mode", variable=self.is_testmode_enabled)
        test_toggle.pack(side=tk.LEFT)

        # Set up the Tkinter close event to stop the server
        self.root.protocol("WM_DELETE_WINDOW", self.stop_server)

    def set_connection_manager(self, conn_manager):
        """Sets the connection manager to interact with."""
        self.connection_manager = conn_manager

    def send_message(self):
        message = self.entry.get()
        if message and self.connection_manager:
            self.connection_manager.send_message(message)
            self.entry.delete(0, tk.END)

    def send_view_signal(self):
        if self.connection_manager:
            self.connection_manager.send_view_signal()

    def send_start_signal(self):
        if self.connection_manager:
            # Determine mode based on BCI and Test Mode toggles
            if self.is_bci_enabled.get() and self.is_testmode_enabled.get():
                mode = "TestMode_BCI"
            elif self.is_testmode_enabled.get():
                mode = "TestMode"
            elif self.is_bci_enabled.get():
                mode = "EMA"
            
            current_time = datetime.now()
            self.last_start_label.config(text=f"Session Start: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Call send_start_signal with the determined mode
            self.connection_manager.send_start_signal(mode)


    def update_last_notification_time(self, current_time):
        self.last_start_label.config(text=f"Last Notification: {current_time}")

    def update_next_notification_time(self, next_time):
        if isinstance(next_time, datetime):
            if self.last_notification_time:
                self.last_start_label.config(text=f"Last Notification: {self.last_notification_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.next_start_label.config(text=f"Next Notification: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.next_start_label.config(text="Next Notification: N/A")

    def send_cancel_signal(self):
        if self.connection_manager:
            self.connection_manager.send_cancel_signal()

    def stop_server(self):
        if self.connection_manager:
            self.connection_manager.stop_server()
        self.root.quit()

    def start(self):
        self.root.mainloop()