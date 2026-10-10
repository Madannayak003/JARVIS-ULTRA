from queue import Queue
import threading
from voice.manager import speak

queue = Queue()

def worker():

    while True:

        text = queue.get()

        speak(text)

        queue.task_done()

threading.Thread(target=worker, daemon=True).start()

def say(text):

    queue.put(text)