import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class RebootHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = subprocess.Popen(['python3', 'bot.py'])

    def on_modified(self, event):
        if event.src_path.endswith('bot.py'):
            print("Изменения в bot.py — перезапуск бота...")
            self.process.terminate()
            self.process.wait()
            self.process = subprocess.Popen(['python3', 'bot.py'])

if __name__ == "__main__":
    path = '.'
    event_handler = RebootHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=False)
    observer.start()
    print("Слежение за изменениями bot.py...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        event_handler.process.terminate()
    observer.join()
