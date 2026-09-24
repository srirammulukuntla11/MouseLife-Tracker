import os
import sys
import time
import requests
from pathlib import Path

# Setup paths
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir.parent))

from agent.src.config import config
from agent.src.persistence import PersistenceManager
from agent.src.tracker import MouseTracker
from agent.src.sync import SyncManager

def test_pause_resume():
    print("\n--- Test: Pause / Resume ---")
    db_file = agent_dir / "data" / "e2e_test.db"
    if db_file.exists():
        db_file.unlink()
    
    pm = PersistenceManager(str(db_file))
    tracker = MouseTracker(persistence_mgr=pm)
    tracker.start()
    
    # Send simulated click through handle_click (or physical)
    from pynput.mouse import Button
    tracker._handle_click(0, 0, Button.left, True)
    tracker._flush_to_persistence()
    stats = tracker.get_stats()
    assert stats["leftClicks"] == 1, f"Expected 1 left click, got {stats['leftClicks']}"
    print("  [PASS] Click recorded while tracking.")

    # Pause
    tracker.pause()
    assert tracker.is_paused is True, "Tracker should be paused"
    tracker._handle_click(0, 0, Button.left, True) # should be ignored
    tracker._flush_to_persistence()
    stats = tracker.get_stats()
    assert stats["leftClicks"] == 1, f"Expected 1 left click during pause, got {stats['leftClicks']}"
    print("  [PASS] Clicks ignored while paused.")

    # Resume
    tracker.resume()
    assert tracker.is_paused is False, "Tracker should not be paused"
    tracker._handle_click(0, 0, Button.right, True)
    tracker._flush_to_persistence()
    stats = tracker.get_stats()
    assert stats["rightClicks"] == 1 and stats["totalClicks"] == 2
    print("  [PASS] Tracking resumed successfully.")
    tracker.stop()

def test_restart_preserves_count():
    print("\n--- Test: Restart Agent Preserves Count ---")
    db_file = agent_dir / "data" / "e2e_test.db"
    pm = PersistenceManager(str(db_file))
    stats1 = pm.get_lifetime_stats(config.MOUSE_ID)
    assert stats1["totalClicks"] == 2
    print(f"  Before restart: {stats1['totalClicks']} clicks in SQLite.")

    # Re-instantiate persistence manager as if agent restarted
    pm2 = PersistenceManager(str(db_file))
    stats2 = pm2.get_lifetime_stats(config.MOUSE_ID)
    assert stats2["totalClicks"] == 2, f"Expected 2, got {stats2['totalClicks']}"
    print(f"  After restart: {stats2['totalClicks']} clicks preserved in SQLite.")
    print("  [PASS] Persistence survives agent restart.")

def test_offline_queuing_and_recovery():
    print("\n--- Test: Offline Queuing & Recovery ---")
    db_file = agent_dir / "data" / "e2e_test.db"
    pm = PersistenceManager(str(db_file))
    
    # Record offline clicks
    pm.record_clicks(config.MOUSE_ID, "offline-sess-1", left=5, right=3, middle=2)
    pending = pm.get_pending_unsynced_summary(config.MOUSE_ID)
    assert pending["total"] >= 10, f"Expected >= 10 pending clicks, got {pending['total']}"
    print(f"  [PASS] Recorded 10 offline clicks. Pending in SQLite: {pending['total']}")

    # Sync with dummy/unreachable backend
    sync = SyncManager(persistence_mgr=pm)
    sync.api_url = "http://127.0.0.1:59999/api" # Unreachable port
    success = sync.sync_now()
    assert success is False, "Sync to dead port should fail gracefully"
    pending_after_fail = pm.get_pending_unsynced_summary(config.MOUSE_ID)
    assert pending_after_fail["total"] == pending["total"], "No clicks should be lost on network failure!"
    print("  [PASS] Backend failure handled gracefully: clicks preserved in local SQLite.")

    # Now point back to live backend on port 5000
    sync.api_url = f"{config.API_BASE_URL}/api"
    success2 = sync.sync_now()
    assert success2 is True, "Sync to live backend should succeed"
    pending_after_recovery = pm.get_pending_unsynced_summary(config.MOUSE_ID)
    assert pending_after_recovery["total"] == 0, f"Expected 0 pending, got {pending_after_recovery['total']}"
    print("  [PASS] Recovered and synchronized all queued clicks to backend MongoDB.")

if __name__ == "__main__":
    test_pause_resume()
    test_restart_preserves_count()
    test_offline_queuing_and_recovery()
    print("\n>>> ALL SCENARIO TESTS PASSED SUCCESSFULLY! <<<\n")
