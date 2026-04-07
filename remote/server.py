import socket
import threading

# ── Config ───────────────────────────────────────────────────────────────────

HOST = "0.0.0.0"
PORT = 5005


# ── Socket server ─────────────────────────────────────────────────────────────

class GestureServer:
    """
    Waits for one Pi client to connect, then lets you send commands to it.
    Automatically accepts a new connection if the Pi disconnects.
    """

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


def main():
    server = GestureServer(HOST, PORT)

if __name__ == "__main__":
    main()