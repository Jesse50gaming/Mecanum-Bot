"""
website.py - local web control panel for the robot.

Usage in main.py:
    website = Website(port=8000)
    website.start()

    forward, strafe, rotation = website.get_command()   # every loop
    website.set_telemetry({...})                        # every loop

    website.stop()                                      # on shutdown

Install:  pip install fastapi "uvicorn[standard]"
Open:     http://<pi-hostname>.local:8000
"""

import asyncio
import csv
import threading
import time
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse


def _clamp(value):
    """Turn anything into a float between -1 and 1 (bad input becomes 0)."""
    try:
        return max(-1.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


class Website:
    def __init__(self, port=8000, command_timeout=0.5, max_speed=1.0,
                 token=None, log_dir="logs", log_period=0.1):
        """
        port             - port the page is served on
        command_timeout  - seconds without a command before the robot is told to stop
        max_speed        - scales every command (0.5 = half speed limit)
        token            - optional password. If set, open the page with ?token=YOURTOKEN
        log_dir          - folder for CSV logs
        log_period       - seconds between log rows (0.1 = 10 rows per second)
        """
        self.port = port
        self.command_timeout = command_timeout
        self.max_speed = max_speed
        self.token = token
        self.log_dir = Path(log_dir)
        self.log_period = log_period
        self._html_path = Path(__file__).with_name("index.html")

        # Shared state. Touched by the web thread and the robot loop, so always use the lock.
        self._lock = threading.Lock()
        self._command = (0.0, 0.0, 0.0)      # forward, strafe, rotation
        self._command_time = 0.0
        self._estop = False
        self._clients = 0
        self._telemetry = {}

        # Logging state (only touched by whoever calls set_telemetry)
        self._log_file = None
        self._log_writer = None
        self._log_keys = None
        self._last_log_time = 0.0

        self._app = self._build_app()
        self._server = None
        self._thread = None

    # ------------------------------------------------------------------
    # Public API (call these from main.py)
    # ------------------------------------------------------------------

    def start(self):
        """Start the web server in a background thread."""
        config = uvicorn.Config(self._app, host="0.0.0.0", port=self.port,
                                log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        print(f"Control page running on port {self.port}")

    def stop(self):
        """Stop the server and close the log file."""
        with self._lock:
            self._command = (0.0, 0.0, 0.0)
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=2)
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

    def get_command(self):
        """
        Returns (forward, strafe, rotation), each from -1 to 1 and scaled by max_speed.
        Returns (0, 0, 0) if the e-stop is on, nobody is connected,
        or no command has arrived within command_timeout.
        """
        with self._lock:
            age = time.monotonic() - self._command_time
            if self._estop or self._clients == 0 or age > self.command_timeout:
                return (0.0, 0.0, 0.0)
            forward, strafe, rotation = self._command
        return (forward * self.max_speed,
                strafe * self.max_speed,
                rotation * self.max_speed)

    @property
    def estopped(self):
        """True while the e-stop button is latched."""
        with self._lock:
            return self._estop

    @property
    def connected(self):
        """True if at least one browser is connected."""
        with self._lock:
            return self._clients > 0

    def set_telemetry(self, data):
        """
        Send a dictionary to the page and write it to the log.
        Nested dictionaries are flattened:  {"rpm": {"fl": 10}}  becomes  rpm_fl.
        Safe to call every loop. Log rows are written at log_period.
        """
        flat = {"time": round(time.time(), 3)}
        flat.update(self._flatten(data))
        with self._lock:
            self._telemetry = flat
        self._log(flat)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, row):
        now = time.monotonic()
        if now - self._last_log_time < self.log_period:
            return
        self._last_log_time = now

        if self._log_file is None:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            name = datetime.now().strftime("run_%Y-%m-%d_%H-%M-%S.csv")
            self._log_file = open(self.log_dir / name, "w", newline="")
            self._log_keys = list(row.keys())
            self._log_writer = csv.DictWriter(self._log_file, fieldnames=self._log_keys,
                                              extrasaction="ignore", restval="")
            self._log_writer.writeheader()

        self._log_writer.writerow(row)
        self._log_file.flush()

    @staticmethod
    def _flatten(data, prefix=""):
        out = {}
        for key, value in data.items():
            name = f"{prefix}{key}"
            if isinstance(value, dict):
                out.update(Website._flatten(value, name + "_"))
            else:
                out[name] = value
        return out

    # ------------------------------------------------------------------
    # Web server internals
    # ------------------------------------------------------------------

    def _authorized(self, token):
        return self.token is None or token == self.token

    def _handle_message(self, msg):
        """Process one message from the browser."""
        with self._lock:
            if msg.get("estop"):
                self._estop = True
                self._command = (0.0, 0.0, 0.0)
            elif msg.get("reset"):
                self._estop = False
            elif any(k in msg for k in ("x", "y", "w")):
                self._command = (_clamp(msg.get("y", 0)),   # forward
                                 _clamp(msg.get("x", 0)),   # strafe
                                 _clamp(msg.get("w", 0)))   # rotation
                self._command_time = time.monotonic()

    def _build_app(self):
        app = FastAPI()

        @app.get("/")
        def index():
            return FileResponse(self._html_path)

        @app.get("/logs")
        def list_logs(token: str = None):
            if not self._authorized(token):
                raise HTTPException(status_code=403)
            if not self.log_dir.exists():
                return []
            return sorted((p.name for p in self.log_dir.glob("*.csv")), reverse=True)

        @app.get("/logs/{name}")
        def download_log(name: str, token: str = None):
            if not self._authorized(token):
                raise HTTPException(status_code=403)
            path = self.log_dir / Path(name).name      # strips any folder tricks
            if not path.is_file():
                raise HTTPException(status_code=404)
            return FileResponse(path, filename=path.name)

        @app.websocket("/ws")
        async def ws_endpoint(ws: WebSocket):
            if not self._authorized(ws.query_params.get("token")):
                await ws.close(code=1008)
                return
            await ws.accept()
            with self._lock:
                self._clients += 1

            async def sender():
                while True:
                    with self._lock:
                        payload = {"estop": self._estop,
                                   "telemetry": dict(self._telemetry)}
                    await ws.send_json(payload)
                    await asyncio.sleep(0.1)          # 10 updates per second

            task = asyncio.create_task(sender())
            try:
                while True:
                    self._handle_message(await ws.receive_json())
            except (WebSocketDisconnect, ValueError):
                pass
            finally:
                task.cancel()
                with self._lock:
                    self._clients -= 1
                    self._command = (0.0, 0.0, 0.0)   # stop when the connection drops

        return app