import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests
from .config import config
from .logger import agent_logger
from .persistence import persistence

class SyncManager:
    """
    Background batch synchronizer for MouseLife Tracker.
    Dispatches accumulated click batches to the Express backend with idempotency,
    exponential backoff, and full offline resilience.
    """

    def __init__(self, persistence_mgr=None):
        self.persistence = persistence_mgr or persistence
        self.api_url = f"{config.API_BASE_URL}/api"
        self.mouse_id = config.MOUSE_ID
        self.interval = config.SYNC_INTERVAL_SECONDS

        self.is_running = False
        self.is_connected = False
        self.last_sync_time: Optional[str] = None
        self.consecutive_failures = 0

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sync_lock = threading.Lock()

    def start(self):
        """Starts the background periodic synchronization loop."""
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sync_loop, daemon=True, name="SyncWorker")
        self._thread.start()
        agent_logger.info(f"SyncManager background worker started (interval: {self.interval}s)")

    def stop(self):
        """Stops the sync worker and triggers a final flush sync."""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None

        # Final synchronous flush before exit
        try:
            self.sync_now()
        except Exception as e:
            agent_logger.warning(f"Error during final sync flush: {e}")

        agent_logger.info("SyncManager stopped.")

    def sync_now(self) -> bool:
        """
        Executes an immediate synchronization cycle.
        Returns True if batch was successfully sent and acknowledged, or if no data was pending.
        """
        with self._sync_lock:
            # 1. Prepare batch of unsynced clicks from SQLite
            batch = self.persistence.prepare_sync_batch(self.mouse_id)
            if not batch:
                return True

            try:
                sync_endpoint = f"{self.api_url}/clicks/sync"
                agent_logger.debug(f"Dispatching sync batch {batch['batchId']} ({batch['totalClicks']} clicks) to {sync_endpoint}")

                response = requests.post(
                    sync_endpoint,
                    json=batch,
                    timeout=5.0
                )

                if response.status_code == 200:
                    resp_data = response.json()
                    # Mark batch confirmed in local SQLite
                    self.persistence.confirm_batch_synced(batch["batchId"], self.mouse_id)

                    now_iso = datetime.now(timezone.utc).isoformat()
                    self.last_sync_time = now_iso
                    self.is_connected = True
                    self.consecutive_failures = 0

                    # Sync lifetime totals back to local state if server has authoritative counts
                    if "mouse" in resp_data:
                        server_mouse = resp_data["mouse"]
                        self.persistence.update_lifetime_from_server(self.mouse_id, server_mouse)

                    agent_logger.info(
                        f"Synced batch {batch['batchId']}: +{batch['totalClicks']} clicks "
                        f"(L:{batch['leftClicks']} R:{batch['rightClicks']} M:{batch['middleClicks']})."
                    )
                    return True
                else:
                    self.is_connected = False
                    self.consecutive_failures += 1
                    agent_logger.warning(f"Sync batch {batch['batchId']} rejected with HTTP {response.status_code}: {response.text}")
                    return False

            except requests.exceptions.RequestException as e:
                self.is_connected = False
                self.consecutive_failures += 1
                # FR-06: Offline Support - Unsynchronized clicks remain safe in local SQLite
                agent_logger.warning(
                    f"Backend unreachable ({e.__class__.__name__}). "
                    f"Clicks are stored safely offline in local SQLite. Retrying automatically..."
                )
                return False

    def _sync_loop(self):
        """Worker loop that ticks every `interval` seconds."""
        # Initial check immediately upon start
        self.sync_now()

        while not self._stop_event.is_set():
            # Wait for interval or stop signal
            if self._stop_event.wait(timeout=self.interval):
                break

            self.sync_now()

    def get_status(self) -> Dict[str, Any]:
        """Returns sync engine health and pending counts."""
        pending_summary = self.persistence.get_pending_unsynced_summary(self.mouse_id)
        return {
            "isConnected": self.is_connected,
            "lastSyncTime": self.last_sync_time,
            "consecutiveFailures": self.consecutive_failures,
            "pendingClicks": pending_summary["total"],
            "pendingBreakdown": pending_summary,
            "isRunning": self.is_running
        }

sync_manager = SyncManager()
