from datetime import datetime, timedelta
import threading
import random

def get_next_start_time():
    """Calculates the next start time within the 9am-9pm range, with next-day rescheduling if needed."""
    min_delay = 90
    max_delay = 150
    delay = random.randint(min_delay, max_delay)
    next_start_time = datetime.now() + timedelta(minutes=delay)

    # Check if it exceeds 9pm; if so, schedule for the next day at 9am with a new random delay
    if next_start_time.hour >= 21:
        delay_next_day = random.randint(0, min_delay)
        next_start_time = next_start_time.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1) + timedelta(minutes=delay_next_day)
    elif next_start_time.hour < 9:
        next_start_time = next_start_time.replace(hour=9, minute=0, second=0, microsecond=0)

    #next_start_time = datetime.now() + timedelta(seconds=30)
    
    return next_start_time

def schedule_start(connection_manager, mode, update_ui_callback):
    next_start_time = get_next_start_time()
    delay_seconds = (next_start_time - datetime.now()).total_seconds()

    #init_time = next_start_time - timedelta(minutes=2)
    #init_time = next_start_time - timedelta(seconds=5)
    #init_delay_seconds = (init_time - datetime.now()).total_seconds()

    if update_ui_callback:
        update_ui_callback(next_start_time)

    # Send init signal 2 min before start
    #if init_delay_seconds > 0:
    #    threading.Timer(init_delay_seconds, connection_manager.send_init_bci_signal).start()

    # Schedule sending the start signal after the calculated delay
    threading.Timer(delay_seconds, connection_manager.send_start_signal, args=[mode]).start()
    
    return next_start_time