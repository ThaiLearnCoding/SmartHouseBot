import logging
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Optional

from backend.app.core.config import Settings, get_settings


logger = logging.getLogger(__name__)

_lock = Lock()
_connection: Optional[sqlite3.Connection] = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    led_on INTEGER,
    servo_angle INTEGER,
    collected_at_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(device_id, collected_at_ms)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_collected
    ON telemetry_snapshots(device_id, collected_at_ms);

CREATE TABLE IF NOT EXISTS device_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    command_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',
    success INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_device_commands_created
    ON device_commands(device_id, created_at);

CREATE TABLE IF NOT EXISTS voice_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript TEXT NOT NULL,
    intent TEXT NOT NULL,
    response_text TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_voice_logs_created ON voice_logs(created_at);
"""


def resolve_database_path(settings: Optional[Settings] = None) -> Path:
    settings = settings or get_settings()
    if settings.database_path.strip():
        return Path(settings.database_path.strip())
    return settings.database_dir / "smarthouse.db"


def init_db(settings: Optional[Settings] = None) -> None:
    settings = settings or get_settings()
    if not settings.database_enabled:
        return

    path = resolve_database_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        conn = sqlite3.connect(path)
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    logger.info("SQLite database initialized at %s", path)


def get_connection(settings: Optional[Settings] = None) -> sqlite3.Connection:
    settings = settings or get_settings()
    global _connection

    if not settings.database_enabled:
        raise RuntimeError("Database is disabled.")

    path = resolve_database_path(settings)
    with _lock:
        if _connection is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            _connection = sqlite3.connect(path, check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute("PRAGMA journal_mode=WAL")
            _connection.execute("PRAGMA busy_timeout=5000")
        return _connection


def reset_connection() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None
