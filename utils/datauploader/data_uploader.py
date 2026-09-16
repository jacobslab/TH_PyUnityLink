import subprocess
import schedule
import time

class DataUploader:
    def __init__(self):
        pass

    def run_sync(self):
        subprocess.run(['wsl', 'bash', '-c', 'bash -l -c "/mnt/c/Users/BBQS_CAMERA/Desktop/DataAutoSync/sync.sh"'])

    def schedule_daily_sync(self):
        schedule.every().day.at("02:00").do(self.run_sync)
        while True:
            schedule.run_pending()
            time.sleep(60)