from os import name
import socket
import threading
import time

# ── Config ───────────────────────────────────────────────────────────────────

HOST = "0.0.0.0"
PORT = 5005


# ── Socket server ─────────────────────────────────────────────────────────────

class GestureServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._conn = None
        self._lock = threading.Lock()

        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(1)
        print(f"[server] Listening on {self.host}:{self.port} ...")

        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()

    def _accept_loop(self):
        while True:
            conn, addr = self._server_sock.accept()
            with self._lock:
                self._conn = conn
            print(f"[server] Pi connected from {addr}")

    def send(self, command: str) -> bool:
        with self._lock:
            if self._conn is None:
                print("[server] No client connected.")
                return False
            try:
                self._conn.sendall((command + "\n").encode())
                print(f"[server] Sent: {command}")
                return True
            except (BrokenPipeError, ConnectionResetError):
                print("[server] Pi disconnected.")
                self._conn = None
                return False

    @property
    def connected(self) -> bool:
        with self._lock:
            return self._conn is not None


Server = GestureServer(HOST, PORT)

# ── Action loop ───────────────────────────────────────────────────────────────

# A single Event that the current action thread checks each iteration.
# When main() is called, it sets this event to signal "stop what you're doing".
_stop_event = threading.Event()
_action_thread = None
_thread_lock = threading.Lock()


def _action_loop(command: str, stop_event: threading.Event):
    """Runs forever, sending `command` every 0.1s, until stop_event is set."""
    while not stop_event.is_set():
        Server.send(command)
        # Use stop_event.wait() instead of time.sleep() so it wakes up
        # immediately when cancelled, rather than sleeping the full interval.
        stop_event.wait(timeout=0.1)
    Server.send("stand")


def main(command: str):
    global _action_thread, _stop_event

    with _thread_lock:
        # 1. Signal the current thread (if any) to stop
        _stop_event.set()

        # 2. Wait for it to actually finish (brief, since it checks the event)
        if _action_thread is not None:
            _action_thread.join()

        # 3. Create a fresh stop event and launch the new action
        _stop_event = threading.Event()
        _action_thread = threading.Thread(
            target=_action_loop,
            args=(command, _stop_event),
            daemon=True
        )
        _action_thread.start()


def stop():
    """Explicitly stop the current action and send 'stand'."""
    with _thread_lock:
        _stop_event.set()
        if _action_thread is not None:
            _action_thread.join()