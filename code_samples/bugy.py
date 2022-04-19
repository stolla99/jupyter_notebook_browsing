import time
from alive_progress import alive_bar


with alive_bar(100, title='Download', force_tty=True) as bar:
    for i in range(100):
        time.sleep(0.01)
        bar()
