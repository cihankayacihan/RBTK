import contextlib
from multiprocessing import connection
import os
import queue
import threading

from rbtk import dirs

_ADDRESS_FILE = os.path.join(dirs.cachedir, 'ipc_address.txt')

def send(objects):
    """Send objects from an iterable to a process running session().

    Raise ConnectionRefusedError if session() is not running.
    """
    # reading the address file, connecting to a windows named pipe and
    # connecting to an AF_UNIX socket all raise FileNotFoundError :D
    try:
        with open(_ADDRESS_FILE, 'r') as file:
            address = file.read().strip()
        client = connection.Client(address)
    except FileNotFoundError:
        raise ConnectionRefusedError("session() is not running") from None

    with client:
        for message in objects:
            client.send(message)


def _listener2queue(listener, object_queue):
    """Accept connections. Receive and queue objects."""
    while True:
        try:
            client = listener.accept()
        except OSError:
            # it's closed
            break

        with client:
            while True:
                try:
                    object_queue.put(client.recv())
                except EOFError:
                    break


@contextlib.contextmanager
def session():
    """Context manager that listens for send().

    Use this as a context manager:

        # the queue will contain objects from send()
        with session() as message_queue:
            # start something that processes items in the queue and run
            # the application
    """
    message_queue = queue.Queue()
    with connection.Listener() as listener:
        with open(_ADDRESS_FILE, 'w') as file:
            print(listener.address, file=file)
        thread = threading.Thread(target=_listener2queue,
                                  args=[listener, message_queue], daemon=True)
        thread.start()
        yield message_queue


if __name__ == '__main__':
    # simple test
    try:
        send([1, 2, 3])
        print("a server is running, a message was sent to it")
    except ConnectionRefusedError:
        print("a server is not running, let's become the server...")
        with session() as message_queue:
            while True:
                print(message_queue.get())
