import os
import psutil
import subprocess
import time

script_path = "main.py"


def is_script_running(script_name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and script_name in proc.info['cmdline']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def start_script(script_path):
    subprocess.Popen(['python3', script_path])


if __name__ == "__main__":
    script_name = os.path.basename(script_path)

    while True:
        if not is_script_running(script_name):
            print(f"{script_name} не запущен. Запускаем...")
            start_script(script_path)
        else:
            print(f"{script_name} уже запущен.")

        # Ждем 60 секунд перед следующей проверкой
        time.sleep(60)