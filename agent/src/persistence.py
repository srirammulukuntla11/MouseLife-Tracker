import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .config import config
from .logger import agent_logger

class PersistenceManager:
    """
    Transactional SQLite persistence layer for MouseLife Tracker.
    Ensures zero clicks are lost during network outages, system crashes, or app restarts.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high performance concurrent read/writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # Lifetime statistics table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS lifetime_stats (
                            mouse_id TEXT PRIMARY KEY,
                            total_clicks INTEGER DEFAULT 0,
                            left_clicks INTEGER DEFAULT 0,
                            right_clicks INTEGER DEFAULT 0,
                            middle_clicks INTEGER DEFAULT 0,
                            rated_clicks INTEGER DEFAULT 3000000,
                            last_sync_time TEXT,
                            tracking_started_at TEXT,
                            updated_at TEXT
                        );
                    """)

                    # Pending / uncommitted clicks table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS pending_clicks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            mouse_id TEXT NOT NULL,
                            batch_id TEXT,
                            client_session_id TEXT NOT NULL,
                            left_clicks INTEGER DEFAULT 0,
                            right_clicks INTEGER DEFAULT 0,
                            middle_clicks INTEGER DEFAULT 0,
                            total_clicks INTEGER DEFAULT 0,
                            created_at TEXT NOT NULL,
                            synced INTEGER DEFAULT 0,
                            synced_at TEXT
                        );
                    """)

                    # Tracking sessions table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS sessions (
                            session_id TEXT PRIMARY KEY,
                            mouse_id TEXT NOT NULL,
                            started_at TEXT NOT NULL,
                            ended_at TEXT,
                            duration_seconds REAL DEFAULT 0,
                            left_clicks INTEGER DEFAULT 0,
                            right_clicks INTEGER DEFAULT 0,
                            middle_clicks INTEGER DEFAULT 0,
                            total_clicks INTEGER DEFAULT 0,
                            synced INTEGER DEFAULT 0
                        );
                    """)

                    # Indexes for rapid query performance
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pending_synced 
                        ON pending_clicks(synced, mouse_id);
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pending_batch 
                        ON pending_clicks(batch_id);
                    """)

                # Ensure default mouse record exists
                self._ensure_mouse_record(conn, config.MOUSE_ID, config.RATED_CLICKS)
                agent_logger.info(f"Local SQLite database initialized at {self.db_path}")
            finally:
                conn.close()

    def _ensure_mouse_record(self, conn: sqlite3.Connection, mouse_id: str, rated_clicks: int):
        cur = conn.execute("SELECT mouse_id FROM lifetime_stats WHERE mouse_id = ?", (mouse_id,))
        if not cur.fetchone():
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                INSERT INTO lifetime_stats (
                    mouse_id, total_clicks, left_clicks, right_clicks, middle_clicks,
                    rated_clicks, tracking_started_at, updated_at
                ) VALUES (?, 0, 0, 0, 0, ?, ?, ?)
            """, (mouse_id, rated_clicks, now_iso, now_iso))

    def record_clicks(self, mouse_id: str, session_id: str, left: int = 0, right: int = 0, middle: int = 0):
        """
        Atomically records incremented clicks to both lifetime stats and pending synchronization queue.
        """
        total = left + right + middle
        if total <= 0:
            return

        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # 1. Update lifetime stats atomically via upsert
                    conn.execute("""
                        INSERT INTO lifetime_stats (
                            mouse_id, total_clicks, left_clicks, right_clicks, middle_clicks,
                            rated_clicks, tracking_started_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(mouse_id) DO UPDATE SET
                            total_clicks = total_clicks + excluded.total_clicks,
                            left_clicks = left_clicks + excluded.left_clicks,
                            right_clicks = right_clicks + excluded.right_clicks,
                            middle_clicks = middle_clicks + excluded.middle_clicks,
                            updated_at = excluded.updated_at
                    """, (mouse_id, total, left, right, middle, config.RATED_CLICKS, now_iso, now_iso))

                    # 2. Append to pending_clicks for batch synchronization
                    conn.execute("""
                        INSERT INTO pending_clicks (
                            mouse_id, client_session_id, left_clicks, right_clicks, middle_clicks,
                            total_clicks, created_at, synced
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """, (mouse_id, session_id, left, right, middle, total, now_iso))

                    # 3. Update active session if present
                    conn.execute("""
                        UPDATE sessions
                        SET total_clicks = total_clicks + ?,
                            left_clicks = left_clicks + ?,
                            right_clicks = right_clicks + ?,
                            middle_clicks = middle_clicks + ?
                        WHERE session_id = ?
                    """, (total, left, right, middle, session_id))
            finally:
                conn.close()

    def get_lifetime_stats(self, mouse_id: str) -> Dict[str, Any]:
        """Returns the current lifetime stats from local SQLite."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.execute("SELECT * FROM lifetime_stats WHERE mouse_id = ?", (mouse_id,))
                row = cur.fetchone()
                if row:
                    rated = row["rated_clicks"] or config.RATED_CLICKS
                    total = row["total_clicks"] or 0
                    remaining = max(rated - total, 0)
                    life_used = round((total / rated * 100), 2) if rated > 0 else 0.0

                    return {
                        "mouseId": row["mouse_id"],
                        "totalClicks": total,
                        "leftClicks": row["left_clicks"] or 0,
                        "rightClicks": row["right_clicks"] or 0,
                        "middleClicks": row["middle_clicks"] or 0,
                        "ratedClicks": rated,
                        "remainingClicks": remaining,
                        "lifeUsedPercentage": life_used,
                        "lastSyncTime": row["last_sync_time"],
                        "trackingStartedAt": row["tracking_started_at"],
                        "updatedAt": row["updated_at"]
                    }
                return {
                    "mouseId": mouse_id,
                    "totalClicks": 0,
                    "leftClicks": 0,
                    "rightClicks": 0,
                    "middleClicks": 0,
                    "ratedClicks": config.RATED_CLICKS,
                    "remainingClicks": config.RATED_CLICKS,
                    "lifeUsedPercentage": 0.0,
                    "lastSyncTime": None,
                    "trackingStartedAt": datetime.now(timezone.utc).isoformat(),
                    "updatedAt": datetime.now(timezone.utc).isoformat()
                }
            finally:
                conn.close()

    def get_pending_unsynced_summary(self, mouse_id: str) -> Dict[str, int]:
        """Calculates total unsynced clicks pending dispatch."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.execute("""
                    SELECT 
                        COALESCE(SUM(left_clicks), 0) as left,
                        COALESCE(SUM(right_clicks), 0) as right,
                        COALESCE(SUM(middle_clicks), 0) as middle,
                        COALESCE(SUM(total_clicks), 0) as total
                    FROM pending_clicks
                    WHERE mouse_id = ? AND synced = 0
                """, (mouse_id,))
                row = cur.fetchone()
                return {
                    "left": row["left"],
                    "right": row["right"],
                    "middle": row["middle"],
                    "total": row["total"]
                }
            finally:
                conn.close()

    def prepare_sync_batch(self, mouse_id: str) -> Optional[Dict[str, Any]]:
        """
        Gathers all currently unsynced clicks, assigns a unique batchId,
        and returns the synchronization payload.
        """
        with self._lock:
            conn = self._get_connection()
            try:
                # Find all unassigned or unsynced rows
                cur = conn.execute("""
                    SELECT id, client_session_id, left_clicks, right_clicks, middle_clicks, total_clicks
                    FROM pending_clicks
                    WHERE mouse_id = ? AND synced = 0
                """, (mouse_id,))
                rows = cur.fetchall()

                if not rows:
                    return None

                batch_id = str(uuid.uuid4())
                ids = [r["id"] for r in rows]
                session_id = rows[0]["client_session_id"] if rows else "unknown-session"

                sum_left = sum(r["left_clicks"] for r in rows)
                sum_right = sum(r["right_clicks"] for r in rows)
                sum_middle = sum(r["middle_clicks"] for r in rows)
                sum_total = sum(r["total_clicks"] for r in rows)

                # Assign batch_id to these rows
                placeholders = ",".join("?" for _ in ids)
                with conn:
                    conn.execute(f"""
                        UPDATE pending_clicks
                        SET batch_id = ?
                        WHERE id IN ({placeholders})
                    """, [batch_id] + ids)

                return {
                    "batchId": batch_id,
                    "mouseId": mouse_id,
                    "clientSessionId": session_id,
                    "leftClicks": sum_left,
                    "rightClicks": sum_right,
                    "middleClicks": sum_middle,
                    "totalClicks": sum_total,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            finally:
                conn.close()

    def confirm_batch_synced(self, batch_id: str, mouse_id: str):
        """Marks all rows in the given batch as successfully synchronized."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        UPDATE pending_clicks
                        SET synced = 1, synced_at = ?
                        WHERE batch_id = ?
                    """, (now_iso, batch_id))

                    conn.execute("""
                        UPDATE lifetime_stats
                        SET last_sync_time = ?
                        WHERE mouse_id = ?
                    """, (now_iso, mouse_id))
                agent_logger.debug(f"Batch {batch_id} confirmed and marked synced.")
            finally:
                conn.close()

    def start_session(self, session_id: str, mouse_id: str):
        """Records the start of a tracking session in SQLite."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO sessions (
                            session_id, mouse_id, started_at, total_clicks, left_clicks, right_clicks, middle_clicks
                        ) VALUES (?, ?, ?, 0, 0, 0, 0)
                    """, (session_id, mouse_id, now_iso))
            finally:
                conn.close()

    def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Finalizes an active session and returns its summary."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
                row = cur.fetchone()
                if not row:
                    return None

                started = datetime.fromisoformat(row["started_at"])
                ended = datetime.now(timezone.utc)
                duration = max((ended - started).total_seconds(), 0.0)

                with conn:
                    conn.execute("""
                        UPDATE sessions
                        SET ended_at = ?, duration_seconds = ?
                        WHERE session_id = ?
                    """, (now_iso, duration, session_id))

                return {
                    "sessionId": session_id,
                    "mouseId": row["mouse_id"],
                    "startedAt": row["started_at"],
                    "endedAt": now_iso,
                    "durationSeconds": duration,
                    "totalClicks": row["total_clicks"],
                    "leftClicks": row["left_clicks"],
                    "rightClicks": row["right_clicks"],
                    "middleClicks": row["middle_clicks"]
                }
            finally:
                conn.close()

    def update_lifetime_from_server(self, mouse_id: str, server_totals: Dict[str, int]):
        """
        Synchronizes server authoritative totals back into local lifetime state
        if server totals are greater (e.g. tracking resumed on a new install).
        """
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        UPDATE lifetime_stats
                        SET total_clicks = MAX(total_clicks, ?),
                            left_clicks = MAX(left_clicks, ?),
                            right_clicks = MAX(right_clicks, ?),
                            middle_clicks = MAX(middle_clicks, ?),
                            updated_at = ?
                        WHERE mouse_id = ?
                    """, (
                        server_totals.get("totalClicks", 0),
                        server_totals.get("leftClicks", 0),
                        server_totals.get("rightClicks", 0),
                        server_totals.get("middleClicks", 0),
                        datetime.now(timezone.utc).isoformat(),
                        mouse_id
                    ))
            finally:
                conn.close()

persistence = PersistenceManager()
