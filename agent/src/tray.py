import threading
import webbrowser
from typing import Optional
from PIL import Image, ImageDraw
import pystray
from .config import config
from .logger import agent_logger
from .persistence import persistence

def create_tray_image(is_paused: bool = False, is_active: bool = True) -> Image.Image:
    """
    Generates a crisp 64x64 RGBA system tray icon representing the mouse and status dot.
    """
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Mouse body (modern dark rounded pill)
    draw.rounded_rectangle((12, 6, 52, 58), radius=18, fill=(30, 41, 59, 255), outline=(71, 85, 105, 255), width=3)

    # Middle divider line for left / right buttons
    draw.line((32, 6, 32, 28), fill=(100, 116, 139, 255), width=2)

    # Scroll wheel
    draw.rounded_rectangle((29, 14, 35, 26), radius=3, fill=(148, 163, 184, 255))

    # Status indicator dot
    if not is_active:
        dot_color = (156, 163, 175, 255) # Gray (offline / inactive)
    elif is_paused:
        dot_color = (245, 158, 11, 255) # Amber (paused)
    else:
        dot_color = (16, 185, 129, 255) # Emerald Green (active tracking)

    draw.ellipse((42, 42, 56, 56), fill=dot_color, outline=(255, 255, 255, 255), width=2)
    return image

class SystemTrayApp:
    """
    Windows System Tray integration providing background status,
    quick controls (Pause/Resume, Open Dashboard), and clean shutdown.
    """

    def __init__(self, tracker, sync_mgr):
        self.tracker = tracker
        self.sync_mgr = sync_mgr
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _get_status_text(self) -> str:
        if self.tracker.is_paused:
            return "Status: Paused"
        return "Status: Tracking"

    def _get_total_text(self) -> str:
        stats = self.tracker.get_stats()
        return f"Total: {stats['totalClicks']:,}"

    def _open_dashboard(self, icon, item):
        dashboard_url = config.DASHBOARD_URL
        agent_logger.info(f"Opening dashboard in browser: {dashboard_url}")
        try:
            webbrowser.open(dashboard_url)
        except Exception as e:
            agent_logger.error(f"Failed to open dashboard: {e}")

    def _toggle_pause(self, icon, item):
        if self.tracker.is_paused:
            self.tracker.resume()
        else:
            self.tracker.pause()
        self.update_tray()

    def _trigger_sync(self, icon, item):
        threading.Thread(target=self.sync_mgr.sync_now, daemon=True).start()

    def _exit_app(self, icon, item):
        agent_logger.info("Exit requested from system tray. Shutting down...")
        if self.icon:
            self.icon.stop()

    def update_tray(self):
        """Refreshes tray icon image and tooltip menu."""
        if not self.icon:
            return
        try:
            self.icon.icon = create_tray_image(
                is_paused=self.tracker.is_paused,
                is_active=self.tracker.is_running
            )
            stats = self.tracker.get_stats()
            self.icon.title = f"MouseLife: {stats['totalClicks']:,} clicks"
        except Exception as e:
            agent_logger.debug(f"Tray update exception: {e}")

    def run(self):
        """Starts the system tray icon loop."""
        def make_menu():
            return pystray.Menu(
                pystray.MenuItem("MouseLife Tracker", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(lambda text: self._get_status_text(), None, enabled=False),
                pystray.MenuItem(lambda text: self._get_total_text(), None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open Dashboard", self._open_dashboard),
                pystray.MenuItem(
                    lambda text: "Resume Tracking" if self.tracker.is_paused else "Pause Tracking",
                    self._toggle_pause
                ),
                pystray.MenuItem("Sync Now", self._trigger_sync),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self._exit_app)
            )

        self.icon = pystray.Icon(
            name="MouseLifeTracker",
            icon=create_tray_image(is_paused=False, is_active=True),
            title="MouseLife Tracker",
            menu=make_menu()
        )

        agent_logger.info("System Tray icon initialized.")
        self.icon.run()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
