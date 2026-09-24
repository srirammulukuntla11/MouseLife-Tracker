import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from pynput.mouse import Button

# Ensure agent package can be imported
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent.parent))

from agent.src.persistence import PersistenceManager
from agent.src.tracker import (
    LowLevelMouseEventHandler,
    MouseTracker,
    WM_LBUTTONDOWN,
    WM_LBUTTONUP,
    WM_RBUTTONDOWN,
    WM_RBUTTONUP,
    WM_MBUTTONDOWN,
    WM_MBUTTONUP,
    WM_MOUSEMOVE,
    WM_MOUSEWHEEL,
)

class TestClickCounterBugFix(unittest.TestCase):
    """
    Comprehensive verification tests proving the double-counting bug is completely resolved:
    - 1 DOWN event = 1 count
    - DOWN + UP = 1 count (UP events are never counted)
    - Repeated independent clicks = correct count
    - Left, right, and middle counts remain separate
    - Duplicate low-level hook deliveries and contact bounce are ignored
    """

    def setUp(self):
        self.clicks = []
        self.handler = LowLevelMouseEventHandler(on_click_detected=lambda btn: self.clicks.append(btn))
        self.handler.debounce_seconds = 0.001  # Lower debounce for fast unit testing

    def test_single_down_event_counts_exactly_one(self):
        """1 DOWN event must increase counter by exactly 1."""
        result = self.handler.process_hook_message(WM_LBUTTONDOWN, x=100, y=200, timestamp=1000)
        self.assertEqual(result, "left")
        self.assertEqual(len(self.clicks), 1)
        self.assertEqual(self.clicks, ["left"])

    def test_down_plus_up_counts_exactly_one(self):
        """A complete physical click (DOWN + UP) must result in EXACTLY 1 count."""
        # 1. Button DOWN
        res_down = self.handler.process_hook_message(WM_LBUTTONDOWN, x=100, y=200, timestamp=1000)
        self.assertEqual(res_down, "left")
        self.assertEqual(len(self.clicks), 1)

        # 2. Button UP (MUST NOT INCREMENT)
        res_up = self.handler.process_hook_message(WM_LBUTTONUP, x=100, y=200, timestamp=1050)
        self.assertIsNone(res_up)
        self.assertEqual(len(self.clicks), 1, "BUTTONUP must NEVER increment click count!")

    def test_repeated_independent_clicks(self):
        """Multiple independent physical clicks must each increment count by 1."""
        # Click 1
        self.handler.process_hook_message(WM_LBUTTONDOWN, x=100, y=200, timestamp=1000)
        self.handler.process_hook_message(WM_LBUTTONUP, x=100, y=200, timestamp=1050)
        time.sleep(0.01)

        # Click 2
        self.handler.process_hook_message(WM_LBUTTONDOWN, x=105, y=205, timestamp=1200)
        self.handler.process_hook_message(WM_LBUTTONUP, x=105, y=205, timestamp=1250)
        time.sleep(0.01)

        # Click 3
        self.handler.process_hook_message(WM_LBUTTONDOWN, x=110, y=210, timestamp=1400)
        self.handler.process_hook_message(WM_LBUTTONUP, x=110, y=210, timestamp=1450)

        self.assertEqual(len(self.clicks), 3, "3 physical clicks must result in exactly 3 counts!")
        self.assertEqual(self.clicks, ["left", "left", "left"])

    def test_left_right_middle_counts_remain_separate(self):
        """Left, Right, and Middle clicks must increment their respective counters independently."""
        # 1 Left click
        self.handler.process_hook_message(WM_LBUTTONDOWN, timestamp=1000)
        self.handler.process_hook_message(WM_LBUTTONUP, timestamp=1050)
        time.sleep(0.01)

        # 1 Right click
        self.handler.process_hook_message(WM_RBUTTONDOWN, timestamp=1200)
        self.handler.process_hook_message(WM_RBUTTONUP, timestamp=1250)
        time.sleep(0.01)

        # 1 Middle click
        self.handler.process_hook_message(WM_MBUTTONDOWN, timestamp=1400)
        self.handler.process_hook_message(WM_MBUTTONUP, timestamp=1450)

        self.assertEqual(self.clicks.count("left"), 1)
        self.assertEqual(self.clicks.count("right"), 1)
        self.assertEqual(self.clicks.count("middle"), 1)
        self.assertEqual(len(self.clicks), 3)

    def test_duplicate_down_without_up_ignored(self):
        """If a DOWN event is received while the button is already down, it must be ignored."""
        self.handler.process_hook_message(WM_LBUTTONDOWN, timestamp=1000)
        # Duplicate DOWN
        dup_result = self.handler.process_hook_message(WM_LBUTTONDOWN, timestamp=1010)
        self.assertIsNone(dup_result)
        self.assertEqual(len(self.clicks), 1, "Duplicate DOWN without UP must be ignored!")

        # Release and press again
        self.handler.process_hook_message(WM_LBUTTONUP, timestamp=1050)
        time.sleep(0.01)
        res_next = self.handler.process_hook_message(WM_LBUTTONDOWN, timestamp=1200)
        self.assertEqual(res_next, "left")
        self.assertEqual(len(self.clicks), 2)

    def test_identical_hook_packet_duplicate_ignored(self):
        """If the exact same hook packet is delivered twice (same msg, timestamp, coords), ignore it."""
        self.handler.process_hook_message(WM_RBUTTONDOWN, x=50, y=50, timestamp=5555)
        # Replay identical event
        dup = self.handler.process_hook_message(WM_RBUTTONDOWN, x=50, y=50, timestamp=5555)
        self.assertIsNone(dup)
        self.assertEqual(len(self.clicks), 1)

    def test_non_click_events_ignored(self):
        """Move and wheel events must never produce a click."""
        self.handler.process_hook_message(WM_MOUSEMOVE, x=100, y=100, timestamp=1000)
        self.handler.process_hook_message(WM_MOUSEWHEEL, x=100, y=100, timestamp=1010)
        self.assertEqual(len(self.clicks), 0)

    def test_mousetracker_integration_down_only(self):
        """Full MouseTracker integration with SQLite persistence verifying DOWN + UP = 1 count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_down_up.db")
            pm = PersistenceManager(db_path)
            tracker = MouseTracker(persistence_mgr=pm)
            tracker.event_handler.debounce_seconds = 0.001
            tracker.start()

            # Physical Click 1: Left Button DOWN then UP
            tracker._handle_click(10, 10, Button.left, pressed=True)
            tracker._handle_click(10, 10, Button.left, pressed=False)
            time.sleep(0.01)

            # Physical Click 2: Right Button DOWN then UP
            tracker._handle_click(20, 20, Button.right, pressed=True)
            tracker._handle_click(20, 20, Button.right, pressed=False)
            time.sleep(0.01)

            # Physical Click 3: Middle Button DOWN then UP
            tracker._handle_click(30, 30, Button.middle, pressed=True)
            tracker._handle_click(30, 30, Button.middle, pressed=False)

            # Flush to persistence
            tracker._flush_to_persistence()
            tracker.stop()

            stats = pm.get_lifetime_stats(tracker.mouse_id)
            self.assertEqual(stats["leftClicks"], 1, "Expected exactly 1 left click from 1 DOWN+UP pair")
            self.assertEqual(stats["rightClicks"], 1, "Expected exactly 1 right click from 1 DOWN+UP pair")
            self.assertEqual(stats["middleClicks"], 1, "Expected exactly 1 middle click from 1 DOWN+UP pair")
            self.assertEqual(stats["totalClicks"], 3, "Expected exactly 3 total clicks from 3 DOWN+UP pairs")

if __name__ == "__main__":
    unittest.main()
