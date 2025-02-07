from ui.ui_handler import UI
from connection.connection_handler import ConnectionManager

if __name__ == '__main__':
    ui = UI()
    
    conn_manager = ConnectionManager(ui.update_next_notification_time)

    ui.set_connection_manager(conn_manager)
    
    ui.start()