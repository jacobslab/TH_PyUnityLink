import tkinter as tk
from ui.ui_handler import UI
from connection.connection_handler import ConnectionManager
from utils.qrcode.qrcode_display import QRCodeDisplay

if __name__ == '__main__':
    ui = UI(None)
    conn_manager = ConnectionManager(ui, ui.update_next_notification_time)
    ui.connection_manager = conn_manager
    ui.start()