import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

'''
Watch for new FITs files, add them to some queue...
'''

class Watcher:
    
    def __init__(self,P):
        self.observer = Observer()
        self.DIRECTORY_TO_WATCH = P['FIT_Directory']

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print "Error"

        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print "Received created event - %s." % event.src_path


if __name__ == '__main__':
    w = Watcher()
    w.run()