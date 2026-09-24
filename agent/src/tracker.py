import ctypes
import threading
import time
import uuid
from typing import Callable, Optional, Dict
from pynput import mouse
from .config import config
from .logger import agent_logger
from .persistence import persistence

# Standard Windows Low-Level Mouse Hook (WH_MOUSE_LL) message constants
WM_MOUSEMOVE   = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP   = 0x0208
WM_MOUSEWHEEL  = 0x020A
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP   = 0x020C
WM_MOUSEHWHEEL = 0x020E


class LowLevelMouseEventHandler:
    """
    Dedicated stateful handler for Windows low-level mouse hook (WH_MOUSE_LL) events.
    Guarantees:
    - Counts ONLY button DOWN events (WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_MBUTTONDOWN).
    - Strictly ignores all button UP events (WM_LBUTTONUP, WM_RBUTTONUP, WM_MBUTTONUP).
    - Rejects duplicate / repeated hook deliveries for the same event packet.
    - Enforces button state tracking (button must be released before next down counts).
    - Rejects microswitch contact chatter / debounce bounces (< 35ms).
    """

    def __init__(self, on_click_detected: Optional[Callable[[str], None]] = None):
        self._on_click_detected = on_click_detected
        self._lock = threading.Lock()

        # Physical button depression state
        self._left_is_down = False
        self._right_is_down = False
        self._middle_is_down = False

        # Event deduplication cache
        self._last_event_fp = None  # (msg, timestamp, x, y)
        self._last_down_monotonic: Dict[str, float] = {
            "left": 0.0,
            "right": 0.0,
            "middle": 0.0
        }
        self.debounce_seconds = 0.035  # 35ms debounce threshold

    def reset_state(self):
        """Resets in-memory button depression flags and deduplication cache."""
        with self._lock:
            self._left_is_down = False
            self._right_is_down = False
            self._middle_is_down = False
            self._last_event_fp = None
            self._last_down_monotonic = {"left": 0.0, "right": 0.0, "middle": 0.0}

    def process_hook_message(
        self,
        msg: int,
        x: int = 0,
        y: int = 0,
        timestamp: int = 0,
        extra_info: int = 0
    ) -> Optional[str]:
        """
        Processes a raw WH_MOUSE_LL hook message.
        Returns the button name ('left', 'right', 'middle') if a new valid click was counted, else None.
        """
        with self._lock:
            # 1. Exact hook event duplicate check (identical event packet delivered twice)
            if timestamp > 0:
                current_fp = (msg, timestamp, x, y)
                if current_fp == self._last_event_fp:
                    return None
                self._last_event_fp = current_fp

            now = time.monotonic()

            # 2. Left Button Handling
            if msg == WM_LBUTTONDOWN:
                if self._left_is_down:
                    # Ignore repeated DOWN while already depressed
                    return None
                if (now - self._last_down_monotonic["left"]) < self.debounce_seconds:
                    # Debounce hardware contact chatter
                    return None
                self._left_is_down = True
                self._last_down_monotonic["left"] = now
                if self._on_click_detected:
                    self._on_click_detected("left")
                return "left"

            elif msg == WM_LBUTTONUP:
                # Button released: update state, NEVER increment count
                self._left_is_down = False
                return None

            # 3. Right Button Handling
            elif msg == WM_RBUTTONDOWN:
                if self._right_is_down:
                    return None
                if (now - self._last_down_monotonic["right"]) < self.debounce_seconds:
                    return None
                self._right_is_down = True
                self._last_down_monotonic["right"] = now
                if self._on_click_detected:
                    self._on_click_detected("right")
                return "right"

            elif msg == WM_RBUTTONUP:
                self._right_is_down = False
                return None

            # 4. Middle Button Handling
            elif msg == WM_MBUTTONDOWN:
                if self._middle_is_down:
                    return None
                if (now - self._last_down_monotonic["middle"]) < self.debounce_seconds:
                    return None
                self._middle_is_down = True
                self._last_down_monotonic["middle"] = now
                if self._on_click_detected:
                    self._on_click_detected("middle")
                return "middle"

            elif msg == WM_MBUTTONUP:
                self._middle_is_down = False
                return None

            # 5. All other mouse events (move, scroll, xbuttons, etc.) are ignored
            return None

    def process_pynput_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> Optional[str]:
        """
        Maps high-level pynput click events to the exact low-level hook state machine.
        Ensures consistent down-only counting and deduplication across environments.
        """
        msg = None
        if button == mouse.Button.left:
            msg = WM_LBUTTONDOWN if pressed else WM_LBUTTONUP
        elif button == mouse.Button.right:
            msg = WM_RBUTTONDOWN if pressed else WM_RBUTTONUP
        elif button == mouse.Button.middle:
            msg = WM_MBUTTONDOWN if pressed else WM_MBUTTONUP

        if msg is not None:
            return self.process_hook_message(msg, x=x, y=y)
        return None


class WindowsMouseListener(mouse.Listener):
    """
    Enhanced Windows Mouse Listener that ensures the thread's input desktop
    is bound to the interactive user desktop (WinSta0\\Default) so global mouse
    events are captured reliably in any execution mode (interactive, startup, or background).
    """

    def __init__(self, event_filter=None, on_click=None, **kwargs):
        super().__init__(win32_event_filter=event_filter, on_click=on_click, **kwargs)

    def _run(self):
        try:
            if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "user32"):
                user32 = ctypes.windll.user32
                h_desktop = user32.OpenInputDesktop(0, False, 0x01FF)
                if h_desktop:
                    user32.SetThreadDesktop(h_desktop)
        except Exception as e:
            agent_logger.debug(f"Input desktop attachment notice: {e}")
        super()._run()


class MouseTracker:
    """
    Global Windows mouse event detector.
    Captures Left, Right, and Middle clicks across all applications without requiring window focus.
    Adheres strictly to privacy requirements (no coordinates, no keystrokes, no screen capture).
    """

    def __init__(self, persistence_mgr=None):
        self.persistence = persistence_mgr or persistence
        self.mouse_id = config.MOUSE_ID
        self.session_id = str(uuid.uuid4())

        self.is_paused = False
        self.is_running = False
        self._listener: Optional[mouse.Listener] = None

        # Lock for thread-safe memory counters
        self._lock = threading.Lock()
        self._pending_left = 0
        self._pending_right = 0
        self._pending_middle = 0

        # Dedicated low-level hook event handler
        self.event_handler = LowLevelMouseEventHandler(on_click_detected=self._on_valid_click)

        # Optional listener callback for UI/tray notifications
        self.on_click_callback: Optional[Callable[[str, int], None]] = None

        # Flusher worker to write accumulated clicks to SQLite
        self._flusher_stop_event = threading.Event()
        self._flusher_thread: Optional[threading.Thread] = None

    def _on_valid_click(self, button_name: str):
        """Callback invoked strictly when a valid DOWN event is confirmed."""
        if self.is_paused or not self.is_running:
            return

        with self._lock:
            if button_name == "left":
                self._pending_left += 1
            elif button_name == "right":
                self._pending_right += 1
            elif button_name == "middle":
                self._pending_middle += 1
            else:
                return

        if self.on_click_callback:
            try:
                stats = self.persistence.get_lifetime_stats(self.mouse_id)
                self.on_click_callback(button_name, stats["totalClicks"])
            except Exception:
                pass

    def start(self):
        """Starts the global mouse listener and local persistence flusher."""
        with self._lock:
            if self.is_running:
                agent_logger.warning("MouseTracker is already running.")
                return

            self.is_running = True
            self.session_id = str(uuid.uuid4())
            self.event_handler.reset_state()
            self.persistence.start_session(self.session_id, self.mouse_id)

        # Start flusher thread
        self._flusher_stop_event.clear()
        self._flusher_thread = threading.Thread(target=self._flush_worker, daemon=True, name="TrackerFlusher")
        self._flusher_thread.start()

        # Connect directly to WH_MOUSE_LL low-level hook
        def hook_filter(msg, data):
            self.event_handler.process_hook_message(
                msg=msg,
                x=data.pt.x,
                y=data.pt.y,
                timestamp=data.time,
                extra_info=data.dwExtraInfo
            )
            # Never block or suppress normal mouse operations in Windows
            return True

        self._listener = WindowsMouseListener(event_filter=hook_filter, on_click=None)
        self._listener.daemon = True
        self._listener.start()

        agent_logger.info(f"MouseTracker started successfully. Session ID: {self.session_id}")

    def stop(self):
        """Stops listener, flushes pending counts, and finalizes session."""
        with self._lock:
            if not self.is_running:
                return
            self.is_running = False

        if self._listener:
            try:
                self._listener.stop()
            except Exception as e:
                agent_logger.warning(f"Error stopping mouse listener: {e}")
            self._listener = None

        # Stop flusher thread and perform final flush
        self._flusher_stop_event.set()
        if self._flusher_thread:
            self._flusher_thread.join(timeout=2.0)
            self._flusher_thread = None

        self._flush_to_persistence()
        self.event_handler.reset_state()

        summary = self.persistence.end_session(self.session_id)
        agent_logger.info(f"MouseTracker stopped. Session summary: {summary}")

    def pause(self):
        """Pauses tracking. Clicks while paused are ignored."""
        with self._lock:
            self.is_paused = True
        self._flush_to_persistence()
        agent_logger.info("Mouse tracking paused.")

    def resume(self):
        """Resumes click tracking."""
        with self._lock:
            self.is_paused = False
        self.event_handler.reset_state()
        agent_logger.info("Mouse tracking resumed.")

    def _handle_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        """
        Direct callback entrypoint for pynput-style events and unit tests.
        Delegates through the dedicated low-level event state machine.
        """
        if self.is_paused or not self.is_running:
            return
        self.event_handler.process_pynput_click(x, y, button, pressed)

    def _flush_to_persistence(self):
        """Atomically moves accumulated in-memory clicks into local SQLite persistence."""
        with self._lock:
            left = self._pending_left
            right = self._pending_right
            middle = self._pending_middle
            self._pending_left = 0
            self._pending_right = 0
            self._pending_middle = 0

        if (left + right + middle) > 0:
            self.persistence.record_clicks(
                mouse_id=self.mouse_id,
                session_id=self.session_id,
                left=left,
                right=right,
                middle=middle
            )

    def _flush_worker(self):
        """Background thread that commits clicks to SQLite every 500ms."""
        while not self._flusher_stop_event.is_set():
            time.sleep(0.5)
            self._flush_to_persistence()

    def get_stats(self):
        """Returns the lifetime statistics and status for the mouse."""
        stats = self.persistence.get_lifetime_stats(self.mouse_id)
        stats["isPaused"] = self.is_paused
        stats["isRunning"] = self.is_running
        stats["sessionId"] = self.session_id
        return stats
