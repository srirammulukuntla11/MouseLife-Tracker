"""
MouseLife Tracker — Backend Supervisor Daemon

Responsible for:
1. Ensuring strictly ONE backend supervisor runs (Win32 Named Mutex).
2. Starting Node.js backend silently in the background (CREATE_NO_WINDOW).
3. Redirecting stdout/stderr to backend/logs/backend.log.
4. Monitoring Node.js process and automatically restarting if it crashes.
5. Providing health checks against http://127.0.0.1:5000/api/health.
6. Graceful shutdown on SIGTERM/SIGINT.
"""

import os
import sys
import time
import signal
import shutil
import ctypes
import logging
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
LOGS_DIR = BACKEND_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SUPERVISOR_LOG = LOGS_DIR / "supervisor.log"
BACKEND_LOG = LOGS_DIR / "backend.log"
HEALTH_URL = "http://127.0.0.1:5000/api/health"

# Configure supervisor logger
logger = logging.getLogger("MouseLifeBackendSupervisor")
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(SUPERVISOR_LOG, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

# Also log to stdout if a console is attached
if sys.stdout and sys.stdout.isatty():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(console_handler)


def acquire_single_instance_mutex():
    """
    Acquires a Win32 Named Mutex to guarantee only one supervisor runs.
    Returns True if acquired, False if another instance is already running.
    """
    if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "kernel32"):
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, True, "Local\\MouseLifeBackend_Supervisor_Mutex")
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return False, None
        return True, mutex
    return True, None


def is_backend_healthy(timeout=2.0) -> bool:
    """Checks if the Node.js Express backend responds with status: ok."""
    try:
        req = urllib.request.Request(HEALTH_URL, headers={"User-Agent": "MouseLifeSupervisor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8", errors="ignore")
                return '"status":"ok"' in body or '"status": "ok"' in body
    except Exception:
        pass
    return False


def find_node_executable() -> str:
    """Finds the node.exe executable path."""
    candidates = [
        shutil.which("node"),
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs\node.exe"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return str(candidate)
    return "node"


class BackendSupervisor:
    def __init__(self):
        self.node_proc = None
        self.running = True
        self.node_exe = find_node_executable()
        self.server_js = str(BACKEND_DIR / "src" / "server.js")
        self.recent_crashes = []

    def start_node(self) -> subprocess.Popen:
        """Launches node src/server.js silently with output redirected to backend.log."""
        logger.info(f"Launching Node.js backend: {self.node_exe} {self.server_js}")

        # Rotate backend.log if > 10MB
        if BACKEND_LOG.exists() and BACKEND_LOG.stat().st_size > 10 * 1024 * 1024:
            try:
                backup = LOGS_DIR / "backend.log.1"
                if backup.exists():
                    backup.unlink()
                BACKEND_LOG.rename(backup)
            except Exception as e:
                logger.warning(f"Could not rotate backend.log: {e}")

        log_file = open(BACKEND_LOG, "a", encoding="utf-8")
        log_file.write(f"\n--- [MouseLife Backend Started at {time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n")
        log_file.flush()

        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        env = os.environ.copy()
        env["PORT"] = "5000"

        proc = subprocess.Popen(
            [self.node_exe, self.server_js],
            cwd=str(BACKEND_DIR),
            stdout=log_file,
            stderr=log_file,
            creationflags=creationflags,
            env=env
        )
        logger.info(f"Node.js backend process spawned (PID: {proc.pid})")
        return proc

    def stop_node(self):
        """Gracefully terminates the Node.js backend process."""
        if self.node_proc and self.node_proc.poll() is None:
            logger.info(f"Stopping Node.js backend (PID: {self.node_proc.pid})...")
            try:
                self.node_proc.terminate()
                self.node_proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, Exception):
                try:
                    self.node_proc.kill()
                except Exception:
                    pass
            logger.info("Node.js backend stopped.")
        self.node_proc = None

    def run(self):
        """Main supervisor loop with crash detection, rate limiting, and auto-restart."""
        logger.info("MouseLife Backend Supervisor starting...")

        # If already responding, wait before starting a duplicate
        if is_backend_healthy():
            logger.info("Backend is already running and healthy on port 5000.")
        else:
            self.node_proc = self.start_node()

        # Wait up to 10 seconds for initial health
        healthy = False
        for _ in range(20):
            if is_backend_healthy():
                healthy = True
                logger.info("Backend health check PASSED (http://127.0.0.1:5000/api/health is OK).")
                break
            time.sleep(0.5)

        if not healthy:
            logger.warning("Backend did not respond to initial health check within 10s. Continuing supervision.")

        while self.running:
            try:
                if self.node_proc:
                    ret = self.node_proc.poll()
                    if ret is not None:
                        # Process terminated
                        now = time.time()
                        self.recent_crashes.append(now)
                        # Keep only crashes within the last 60 seconds
                        self.recent_crashes = [t for t in self.recent_crashes if now - t <= 60]

                        logger.warning(f"Node.js backend exited unexpectedly with return code {ret}.")

                        if not self.running:
                            break

                        # Rate limiting: max 5 restarts per minute to avoid CPU spin if MongoDB is down
                        if len(self.recent_crashes) >= 5:
                            logger.error("High crash frequency detected (5 exits in 60s). Pausing 15s before restart...")
                            time.sleep(15)
                        else:
                            logger.info("Restarting backend in 3 seconds...")
                            time.sleep(3)

                        if self.running:
                            self.node_proc = self.start_node()
                else:
                    # If we didn't start node because it was already running, check if it's still alive
                    if not is_backend_healthy():
                        logger.info("External backend instance is no longer responding. Spawning managed backend...")
                        self.node_proc = self.start_node()

                time.sleep(2)
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.error(f"Supervisor exception: {e}")
                time.sleep(5)

        self.stop_node()
        logger.info("Supervisor loop ended.")


def main():
    has_mutex, mutex = acquire_single_instance_mutex()
    if not has_mutex:
        logger.warning("Another instance of MouseLifeBackendSupervisor is already running. Exiting.")
        sys.exit(0)

    supervisor = BackendSupervisor()

    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received. Shutting down supervisor and backend...")
        supervisor.running = False
        supervisor.stop_node()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        supervisor.run()
    finally:
        supervisor.stop_node()


if __name__ == "__main__":
    main()
