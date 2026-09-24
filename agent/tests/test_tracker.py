import os
import tempfile
import time
import unittest
from pathlib import Path
from pynput.mouse import Button

from agent.src.persistence import PersistenceManager
from agent.src.tracker import MouseTracker

class TestMouseTrackerAndPersistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_mouse.db")
        self.persistence = PersistenceManager(self.db_path)
        self.tracker = MouseTracker(persistence_mgr=self.persistence)

    def tearDown(self):
        if self.tracker.is_running:
            self.tracker.stop()
        self.temp_dir.cleanup()

    def test_record_clicks_and_calculations(self):
        """Verify left, right, middle increments and lifespan calculations."""
        mouse_id = "test-mouse-1"
        session_id = "test-session-1"

        # Record clicks: 100 left, 40 right, 10 middle
        self.persistence.record_clicks(mouse_id, session_id, left=100, right=40, middle=10)

        stats = self.persistence.get_lifetime_stats(mouse_id)
        self.assertEqual(stats["leftClicks"], 100)
        self.assertEqual(stats["rightClicks"], 40)
        self.assertEqual(stats["middleClicks"], 10)
        self.assertEqual(stats["totalClicks"], 150)
        self.assertEqual(stats["ratedClicks"], 3000000)
        self.assertEqual(stats["remainingClicks"], 2999850)
        self.assertAlmostEqual(stats["lifeUsedPercentage"], 0.01, places=2)

    def test_remaining_clicks_never_negative(self):
        """Verify remaining clicks never drops below 0 even if rated lifespan is exceeded."""
        mouse_id = "test-mouse-exceeded"
        session_id = "sess-exceeded"

        self.persistence.record_clicks(mouse_id, session_id, left=3500000, right=0, middle=0)
        stats = self.persistence.get_lifetime_stats(mouse_id)
        self.assertEqual(stats["totalClicks"], 3500000)
        self.assertEqual(stats["remainingClicks"], 0)
        self.assertTrue(stats["lifeUsedPercentage"] > 100.0)

    def test_batch_preparation_and_confirmation(self):
        """Verify uncommitted clicks are correctly packed into batches with unique UUID."""
        mouse_id = "test-mouse-batch"
        session_id = "sess-batch"

        self.persistence.record_clicks(mouse_id, session_id, left=50, right=20, middle=5)

        summary_before = self.persistence.get_pending_unsynced_summary(mouse_id)
        self.assertEqual(summary_before["total"], 75)

        batch = self.persistence.prepare_sync_batch(mouse_id)
        self.assertIsNotNone(batch)
        self.assertEqual(batch["totalClicks"], 75)
        self.assertEqual(batch["leftClicks"], 50)
        self.assertEqual(batch["rightClicks"], 20)
        self.assertEqual(batch["middleClicks"], 5)
        self.assertTrue(len(batch["batchId"]) > 10)

        # Confirm batch synced
        self.persistence.confirm_batch_synced(batch["batchId"], mouse_id)

        summary_after = self.persistence.get_pending_unsynced_summary(mouse_id)
        self.assertEqual(summary_after["total"], 0)

    def test_tracker_pause_resume(self):
        """Verify paused tracker ignores clicks and resumed tracker counts them."""
        self.tracker.event_handler.debounce_seconds = 0.001
        self.tracker.start()
        time.sleep(0.1)

        # 1. Click while active
        self.tracker._handle_click(100, 100, Button.left, pressed=True)
        self.tracker._handle_click(100, 100, Button.left, pressed=False)
        self.tracker._flush_to_persistence()

        stats1 = self.persistence.get_lifetime_stats(self.tracker.mouse_id)
        self.assertEqual(stats1["leftClicks"], 1)
        self.assertEqual(stats1["totalClicks"], 1)

        # 2. Pause and click
        self.tracker.pause()
        self.tracker._handle_click(100, 100, Button.left, pressed=True)
        self.tracker._handle_click(100, 100, Button.left, pressed=False)
        self.tracker._handle_click(100, 100, Button.right, pressed=True)
        self.tracker._handle_click(100, 100, Button.right, pressed=False)
        self.tracker._flush_to_persistence()

        stats2 = self.persistence.get_lifetime_stats(self.tracker.mouse_id)
        self.assertEqual(stats2["leftClicks"], 1)
        self.assertEqual(stats2["totalClicks"], 1)

        # 3. Resume and click
        self.tracker.resume()
        time.sleep(0.01)
        self.tracker._handle_click(100, 100, Button.right, pressed=True)
        self.tracker._handle_click(100, 100, Button.right, pressed=False)
        time.sleep(0.01)
        self.tracker._handle_click(100, 100, Button.middle, pressed=True)
        self.tracker._handle_click(100, 100, Button.middle, pressed=False)
        self.tracker._flush_to_persistence()

        stats3 = self.persistence.get_lifetime_stats(self.tracker.mouse_id)
        self.assertEqual(stats3["leftClicks"], 1)
        self.assertEqual(stats3["rightClicks"], 1)
        self.assertEqual(stats3["middleClicks"], 1)
        self.assertEqual(stats3["totalClicks"], 3)

        self.tracker.stop()

    def test_persistence_survives_restart(self):
        """Verify that shutting down the tracker and reopening from the same DB preserves exact counts."""
        tracker1 = MouseTracker(persistence_mgr=self.persistence)
        tracker1.event_handler.debounce_seconds = 0.001
        tracker1.start()
        time.sleep(0.1)

        tracker1._handle_click(50, 50, Button.left, pressed=True)
        tracker1._handle_click(50, 50, Button.left, pressed=False)
        time.sleep(0.01)
        tracker1._handle_click(50, 50, Button.left, pressed=True)
        tracker1._handle_click(50, 50, Button.left, pressed=False)
        time.sleep(0.01)
        tracker1._handle_click(50, 50, Button.right, pressed=True)
        tracker1._handle_click(50, 50, Button.right, pressed=False)
        tracker1.stop()

        # Reopen with new tracker instance pointing to same SQLite database
        persistence2 = PersistenceManager(self.db_path)
        tracker2 = MouseTracker(persistence_mgr=persistence2)
        stats = tracker2.get_stats()

        self.assertEqual(stats["totalClicks"], 3)
        self.assertEqual(stats["leftClicks"], 2)
        self.assertEqual(stats["rightClicks"], 1)
        self.assertEqual(stats["middleClicks"], 0)

if __name__ == "__main__":
    unittest.main()
