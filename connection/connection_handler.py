import socket
import threading
import select
import time
import os
from datetime import datetime
from utils.scheduler.scheduler import get_next_start_time, schedule_start
from utils.audio.audio_alert import AudioAlert

class ConnectionManager:
    def __init__(self, update_ui_callback):
        self.server_running = True
        self.connection = None
        self.address = None
        self.update_ui_callback = update_ui_callback

        # Initialize AudioAlert
        self.audio_alert = AudioAlert(alert_interval=120, cancel_callback=self.send_cancel_signal)

        # Set up the Python server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('localhost', 4100))
        #self.server.bind(('192.168.1.164', 4100))
        #self.server.bind(('192.168.0.101', 4100))
        self.server.listen(1)

        # Get script path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        log_base_dir = os.path.join(project_root, "logs")
        server_log_dir = os.path.join(log_base_dir, "server_log")
        self.ema_log_dir = os.path.join(log_base_dir, "ema_log")

        # Ensure all log directories exist
        for directory in [log_base_dir, server_log_dir, self.ema_log_dir]:
            os.makedirs(directory, exist_ok=True)

        # Generate unique log file names
        self.server_log_file = os.path.join(server_log_dir, f"server_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        self.ema_log_file = None

        # Start a background thread to accept connections
        self.connection_thread = threading.Thread(target=self.accept_connections, daemon=True)
        self.connection_thread.start()

        # Live check thread
        self.live_check_running = False
        self.live_check_interval = 3
        self.last_live_check_time = None  # Store timestamp for latency check
        self.live_check_thread = threading.Thread(target=self.live_check_loop, daemon=True)
        self.live_check_thread.start()

    # accept new connections and handle disconnections
    def accept_connections(self):
        try:
            while self.server_running:
                readable, _, _ = select.select([self.server], [], [], 0.1)
                if self.server in readable:
                    if self.connection is None:
                        self.log_timestamped("Waiting for a new client to connect...")
                        self.connection, self.address = self.server.accept()
                        self.log_timestamped(f"Connected to {self.address}")
                        self.connection.sendall("Server Initiated".encode('utf-8'))
                        self.log_timestamped("Sent INIT message to Unity client")

                        # Start live check once a connection is established
                        self.live_check_running = True
                    else:
                        try:
                            data = self.connection.recv(1024)
                            if not data:
                                self.handle_disconnection()
                        except (ConnectionResetError, BrokenPipeError):
                            self.handle_disconnection()
                if self.connection:
                    try:
                        data = self.connection.recv(4096)
                        if data:
                            message = data.decode('utf-8')
                            """
                            if message.startswith("CAM_"):
                                self.receive_logs(message)
                            """
                            self.log_ema_message(message)
                            if message == "Unity_Command_EMA_START":
                                self.audio_alert.stop_audio()
                                self.log_timestamped(f"Unity EMA starts: {message}")
                            elif message == "LIVE_CHECK_ACK":
                                latency = time.time() - self.last_live_check_time
                                self.log_timestamped(f"conn Received LIVE_CHECK_ACK. Latency: {latency:.3f} sec")
                            else:   
                                self.log_timestamped(f"Received message from iPad EMA: {message}")
        
                        else:
                            self.handle_disconnection()
                    except (ConnectionResetError, BrokenPipeError):
                        self.handle_disconnection()
        except OSError:
            self.log_timestamped("Server socket closed, stopping accept_connections.")

    # send messages to unity
    def send_message(self, message):
        if self.connection:
            self.connection.sendall(message.encode('utf-8'))
            self.log_timestamped(f"Sent message to iPad EMA: {message}")
        else:
            self.log_timestamped("No client connected!")

    # send the "View" signal to unity
    def send_view_signal(self):
        if self.connection:
            self.connection.sendall("EMA_Command_INFO".encode('utf-8'))
            self.log_timestamped("Show Info on Unity client")
        else:
            self.log_timestamped("No client connected!")
    
    def send_start_signal(self, mode="TestMode"):
        if self.connection:
            self.ema_log_file = os.path.join(self.ema_log_dir, f"ema_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

            # Send the appropriate signal based on the mode
            if mode == "TestMode_BCI":
                self.connection.sendall("EMA_Command_START_TESTMODE_BCI".encode('utf-8'))    
                #self.send_bci_command("Set event SessionState 1")
            elif mode == "TestMode":
                self.connection.sendall("EMA_Command_START_TESTMODE".encode('utf-8'))
            elif mode == "EMA":
                self.connection.sendall("EMA_Command_START".encode('utf-8'))
                
                #self.send_bci_command("Set event SessionState 1")
            self.log_timestamped(f"Initiate an EMA session to Unity client with mode: {mode}")
            self.audio_alert.play_audio()
            
        else:
            self.log_timestamped("No client connected!")
        
        schedule_start(self, mode, self.update_ui_callback)

    def send_init_bci_signal(self):
        self.connection.send("EMA_Command_INIT_BCI".encode('utf-8'))
        self.log_timestamped("Inti BCI signal sent")

    # send the "Cancel" signal to unity
    def send_cancel_signal(self):
        if self.connection:
            self.audio_alert.stop_audio()
            self.connection.sendall("EMA_Command_CANCEL".encode('utf-8'))
            self.log_timestamped("EMA session skipped on Unity client")
        else:
            self.log_timestamped("No client connected!")


    # Periodically sends a live check signal
    def live_check_loop(self):
        if self.server_running and self.live_check_running and self.connection:
            try:
                self.last_live_check_time = time.time()
                self.connection.sendall("LIVE_CHECK".encode('utf-8'))
                self.log_timestamped("Sent live check message to Unity.")

                #while self.server_running and self.live_check_running and self.connection:
                readable, _, _ = select.select([self.connection], [], [], 5)  # 5 secconds of timeout for no response
                if readable:
                    data = self.connection.recv(1024).decode('utf-8')
                    if data == "LIVE_CHECK_ACK":
                        latency = time.time() - self.last_live_check_time
                        self.log_timestamped(f"Received LIVE_CHECK_ACK. Latency: {latency:.3f} sec")
                #           break  # Exit the loop and schedule the next check
                # If no response, keep looping until an acknowledgment is received

            except Exception as e:
                self.log_timestamped(f"Error in live check: {e}")

        # Schedule the next live check in exactly 15 seconds
        if self.server_running:
            threading.Timer(self.live_check_interval, self.live_check_loop).start()

    # Handles client disconnection
    def handle_disconnection(self):
        """Handles client disconnection."""
        if self.connection:
            self.log_timestamped(f"Client {self.address} disconnected.")
            self.connection.close()
            self.connection = None
            self.live_check_running = False

    def send_bci_command(self, command):
        """Send a command to the BCI2000 system."""
        try:
            bci_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            bci_socket.connect(("192.168.0.101", 4000))
            self.log_timestamped("Connected to BCI2000")
            bci_socket.sendall(command.encode('utf-8'))
            self.log_timestamped(f"Sent command to BCI2000: {command}")
            bci_socket.close()
        except Exception as e:
            self.log_timestamped(f"Error sending command to BCI2000: {e}")
    
    
    def get_next_start_time(self):
        """Returns the next scheduled start time."""
        return self.next_start_time

    # exit
    def stop_server(self):
        """Safely stops the server and closes the socket."""
        self.server_running = False
        self.live_check_running = False
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.server:
            self.server.close()
            self.server = None
        self.log_timestamped("Server stopped.")

    # write server log with timestamp and save on file
    def log_timestamped(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        server_log_message = f"{timestamp} - {message}"
        print(server_log_message)
        with open(self.server_log_file, "a") as log_file:
            log_file.write(server_log_message + "\n")
    
    # write ema log and save on file
    def log_ema_message(self, message):
        if not self.ema_log_file:  # Safety check in case no EMA session has started yet
            self.log_timestamped("Warning: Attempted to log EMA message before EMA session started.")
            return  
        with open(self.ema_log_file, "a") as log_file:
            log_file.write(message + "\n")