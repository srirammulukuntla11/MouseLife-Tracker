import os
import tempfile
import time
import unittest
from pynput.mouse import Controller, Button

from agent.src.persistence import PersistenceManager
from agent.src.tracker import MouseTracker

class TestRealGlobalMouseEvent(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "real_event_test.db")
        self.persistence = PersistenceManager(self.db_path)
        self.tracker = MouseTracker(persistence_mgr=self.persistence)
        self.controller = Controller()

    def tearDown(self):
        if self.tracker.is_running:
            self.tracker.stop()
        self.temp_dir.cleanup()

    def test_os_level_mouse_click_detection(self):
        """
        Triggers real OS-level mouse button events through the Windows input queue
        and validates that the background global listener captures them.
        """
        self.tracker.start()
        time.sleep(0.3)  # Allow listener thread to hook Windows input queue

        # Ensure the injecting thread is also on the input desktop if supported
        try:
            import ctypes
            if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "user32"):
                h = ctypes.windll.user32.OpenInputDesktop(0, False, 0x01FF)
                if h:
                    ctypes.windll.user32.SetThreadDesktop(h)
        except Exception:
            pass

        # Inject real OS mouse click event via Windows API
        self.controller.click(Button.left, 1)
        time.sleep(0.2)

        self.controller.click(Button.right, 1)
        time.sleep(0.2)

        # Allow flusher thread to commit
        time.sleep(0.6)

        stats = self.persistence.get_lifetime_stats(self.tracker.mouse_id)
        self.assertGreaterEqual(stats["leftClicks"], 1, "Real left click must be detected")
        self.assertGreaterEqual(stats["rightClicks"], 1, "Real right click must be detected")
        self.assertGreaterEqual(stats["totalClicks"], 2, "Total clicks must reflect detected clicks")

if __name__ == "__main__":
    unittest.main()
