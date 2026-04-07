import socket
import time
import threading
from picrawler import Picrawler

LAPTOP_IP = "172.17.10.182"
PORT = 5005
RECONNECT_DELAY = 3

# ── Actions ───────────────────────────────────────────────────────────────────

def action_good(robot, stop_event):
    while not stop_event.is_set():
        robot.do_action("wave", 1, 80)

def action_spin(robot, stop_event):
    while not stop_event.is_set():
        robot.do_action("turn right", 1, 80)  # 1 rep at a time so loop can check stop_event

def action_stand(robot, stop_event):
    robot.do_action("stand", 1, 50)

def action_sit(robot, stop_event):
    while not stop_event.is_set():
        robot.do_action("sit", 1, 50)
        break  # run once, but still allows interruption timing
def action_stop(robot, stop_event):
    robot.do_action("stand", 1, 50)

ACTIONS = {
    "good":  action_good,
    "spin":  action_spin,
    "stand": action_stand,
    "sit":   action_sit,
    "stop":  action_stop,
}

# ── Action runner ─────────────────────────────────────────────────────────────

class ActionRunner:
    def __init__(self, robot):
        self.robot = robot
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def run(self, cmd):
        if cmd not in ACTIONS:
            print(f"[client] Unknown command: '{cmd}'")
            return

        with self._lock:
            # Stop current action
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join()

            # Start new action
            self._stop_event = threading.Event()
            stop = self._stop_event

            def target():
                print(f"[client] Executing: {cmd}")
                ACTIONS[cmd](self.robot, stop)
                # When interrupted, return to stand
                if stop.is_set():
                    self.robot.do_action("stand", 1, 50)

            self._thread = threading.Thread(target=target, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join()

# ── Client loop ───────────────────────────────────────────────────────────────

def run(robot):
    runner = ActionRunner(robot)

    while True:
        try:
            print(f"[client] Connecting to {LAPTOP_IP}:{PORT} ...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((LAPTOP_IP, PORT))
            print("[client] Connected. Waiting for commands...")

            buffer = ""
            while True:
                data = sock.recv(1024).decode()
                if not data:
                    print("[client] Server disconnected.")
                    break

                buffer += data
                while "\n" in buffer:
                    cmd, buffer = buffer.split("\n", 1)
                    cmd = cmd.strip()
                    if cmd:
                        runner.run(cmd)

        except (ConnectionRefusedError, OSError) as e:
            print(f"[client] Connection failed: {e}")
        finally:
            runner.stop()
            sock.close()

        print(f"[client] Retrying in {RECONNECT_DELAY}s...")
        time.sleep(RECONNECT_DELAY)


def main():
    print("in main")
    robot = Picrawler()
    robot.do_action("stand", 1, 50)
    run(robot)


if __name__ == "__main__":
    main()