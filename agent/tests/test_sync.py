import os
import tempfile
import time
import unittest
from agent.src.persistence import PersistenceManager
from agent.src.sync import SyncManager
from agent.src.config import config

class TestSyncManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_sync.db")
        self.persistence = PersistenceManager(self.db_path)
        self.sync_mgr = SyncManager(persistence_mgr=self.persistence)
        self.mouse_id = config.MOUSE_ID

    def tearDown(self):
        if self.sync_mgr.is_running:
            self.sync_mgr.stop()
        self.temp_dir.cleanup()

    def test_offline_retention_and_recovery(self):
        """
        Verify that clicks generated while the backend is offline are preserved
        in local SQLite and not lost, and that status correctly reflects offline state.
        """
        # Point to a deliberately unreachable backend port
        self.sync_mgr.api_url = "http://127.0.0.1:59999/api"

        # Record clicks locally
        self.persistence.record_clicks(self.mouse_id, "offline-sess-1", left=20, right=10, middle=2)

        # Pending count should be 32
        summary = self.persistence.get_pending_unsynced_summary(self.mouse_id)
        self.assertEqual(summary["total"], 32)

        # Trigger sync attempt
        success = self.sync_mgr.sync_now()
        self.assertFalse(success, "Sync should fail gracefully when backend is unreachable")
        self.assertFalse(self.sync_mgr.is_connected)
        self.assertGreaterEqual(self.sync_mgr.consecutive_failures, 1)

        # Clicks MUST still be retained locally in SQLite
        summary_after = self.persistence.get_pending_unsynced_summary(self.mouse_id)
        self.assertEqual(summary_after["total"], 32, "Offline clicks must not be discarded")

    def test_sync_status_reporting(self):
        """Verify get_status returns accurate pending counts and connectivity."""
        self.persistence.record_clicks(self.mouse_id, "sess-status", left=5, right=5, middle=0)
        status = self.sync_mgr.get_status()
        self.assertEqual(status["pendingClicks"], 10)
        self.assertIn("pendingBreakdown", status)

if __name__ == "__main__":
    unittest.main()
