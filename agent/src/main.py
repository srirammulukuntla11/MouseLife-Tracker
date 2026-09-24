import argparse
import ctypes
import os
import signal
import sys
import time
from pathlib import Path

# Add parent paths to sys.path so imports work in both script & PyInstaller frozen mode
if getattr(sys, 'frozen', False):
    base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
else:
    current_dir = Path(__file__).resolve().parent
    agent_dir = current_dir.parent
    base_dir = agent_dir.parent

if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from agent.src.config import config
from agent.src.logger import agent_logger
from agent.src.persistence import persistence
from agent.src.tracker import MouseTracker
from agent.src.sync import sync_manager
from agent.src.tray import SystemTrayApp
from agent.src.startup import install_startup, uninstall_startup, is_startup_enabled

def parse_args():
    parser = argparse.ArgumentParser(description="MouseLife Tracker — Windows Background Agent")
    parser.add_argument("--headless", "--no-tray", action="store_true", help="Run without system tray icon (headless background mode)")
    parser.add_argument("--install-startup", action="store_true", help="Configure agent to start automatically with Windows")
    parser.add_argument("--uninstall-startup", action="store_true", help="Remove agent from Windows startup")
    parser.add_argument("--status", action="store_true", help="Print current tracking stats and exit")
    parser.add_argument("--sync-now", action="store_true", help="Trigger an immediate synchronization and exit")
    return parser.parse_args()

def main():
    args = parse_args()

    # Startup setup commands
    if args.install_startup:
        success = install_startup()
        if success:
            print("[MouseLife Tracker] Automatic Windows startup installed successfully.")
        else:
            print("[MouseLife Tracker] Failed to install Windows startup.")
        sys.exit(0 if success else 1)

    if args.uninstall_startup:
        success = uninstall_startup()
        if success:
            print("[MouseLife Tracker] Removed from Windows startup.")
        else:
            print("[MouseLife Tracker] Failed to remove from Windows startup.")
        sys.exit(0 if success else 1)

    # Status check
    if args.status:
        stats = persistence.get_lifetime_stats(config.MOUSE_ID)
        pending = persistence.get_pending_unsynced_summary(config.MOUSE_ID)
        startup_active = is_startup_enabled()
        print("=== MouseLife Tracker Status ===")
        print(f"Mouse ID:             {stats['mouseId']}")
        print(f"Total Clicks:         {stats['totalClicks']:,}")
        print(f"Left Clicks:          {stats['leftClicks']:,}")
        print(f"Right Clicks:         {stats['rightClicks']:,}")
        print(f"Middle Clicks:        {stats['middleClicks']:,}")
        print(f"Rated Lifespan:       {stats['ratedClicks']:,}")
        print(f"Remaining Clicks:     {stats['remainingClicks']:,}")
        print(f"Lifespan Used:        {stats['lifeUsedPercentage']}%")
        print(f"Unsynced In SQLite:   {pending['total']:,}")
        print(f"Windows Auto-Startup: {'Enabled' if startup_active else 'Disabled'}")
        print(f"Last Server Sync:     {stats['lastSyncTime'] or 'Never'}")
        sys.exit(0)

    # Immediate sync command
    if args.sync_now:
        print("[MouseLife Tracker] Triggering immediate batch synchronization...")
        result = sync_manager.sync_now()
        print(f"[MouseLife Tracker] Sync completed: {'Success' if result else 'Failed (clicks remain safe locally)'}")
        sys.exit(0 if result else 1)

    # Standard execution: Initialize Tracker & Sync Manager
    # Enforce single instance to prevent duplicate hooks or double-counting
    mutex = None
    if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "kernel32"):
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, True, "Local\\MouseLifeTracker_SingleInstance_Mutex")
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            agent_logger.warning("Another instance of MouseLifeTracker is already running. Exiting duplicate instance.")
            sys.exit(0)

    agent_logger.info("Initializing MouseLife Tracker Windows Agent...")
    tracker = MouseTracker(persistence_mgr=persistence)
    tray_app = None

    is_shutting_down = False

    def shutdown(signum=None, frame=None):
        nonlocal is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        agent_logger.info("Shutdown signal received. Stopping services gracefully...")

        tracker.stop()
        sync_manager.stop()

        if tray_app:
            tray_app.stop()

        agent_logger.info("MouseLife Tracker agent exited cleanly.")
        sys.exit(0)

    # Register signal handlers for clean exit
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Start tracking and synchronization
    tracker.start()
    sync_manager.start()

    # Run system tray or daemon loop
    if not args.headless:
        try:
            tray_app = SystemTrayApp(tracker, sync_manager)
            tracker.on_click_callback = lambda btn, total: tray_app.update_tray()
            agent_logger.info("Starting system tray loop...")
            tray_app.run()
        except Exception as e:
            agent_logger.warning(f"Could not initialize system tray GUI ({e}). Falling back to background daemon mode.")
            # Fall back to background loop
            while not is_shutting_down:
                time.sleep(1)
    else:
        agent_logger.info("Running in headless daemon mode (no system tray). Press Ctrl+C to stop.")
        try:
            while not is_shutting_down:
                time.sleep(1)
        except KeyboardInterrupt:
            shutdown()

if __name__ == "__main__":
    main()
