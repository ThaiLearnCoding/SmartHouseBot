import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from backend.app.core.config import get_settings
from backend.app.db.database import get_connection
from backend.app.schemas.audit import DeviceCommandLog, VoiceLogEntry
from backend.app.schemas.device import DeviceStatus
from backend.app.schemas.telemetry import TelemetryLatestResponse, TelemetryPoint


logger = logging.getLogger(__name__)


class StorageRepository:
    def _enabled(self) -> bool:
        return get_settings().database_enabled

    def save_telemetry_snapshot(
        self,
        snapshot: TelemetryLatestResponse,
        collected_at_ms: Optional[int] = None,
    ) -> None:
        if not self._enabled():
            return

        collected_at = collected_at_ms if collected_at_ms is not None else snapshot.collected_at
        if collected_at is None:
            return

        device_id = get_settings().coreiot_device_id
        status = snapshot.device_status
        led_on = None if status.led_on is None else int(status.led_on)

        try:
            conn = get_connection()
            conn.execute(
                """
                INSERT OR IGNORE INTO telemetry_snapshots
                    (device_id, temperature, humidity, led_on, servo_angle, collected_at_ms)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    snapshot.temperature,
                    snapshot.humidity,
                    led_on,
                    status.servo_angle,
                    collected_at,
                ),
            )
            conn.commit()
        except Exception:
            logger.warning("Failed to persist telemetry snapshot", exc_info=True)

    def get_telemetry_history(
        self,
        start_ts_ms: int,
        end_ts_ms: int,
        limit: int,
    ) -> List[TelemetryPoint]:
        if not self._enabled():
            return []

        device_id = get_settings().coreiot_device_id
        try:
            conn = get_connection()
            rows = conn.execute(
                """
                SELECT collected_at_ms, temperature, humidity
                FROM telemetry_snapshots
                WHERE device_id = ?
                  AND collected_at_ms BETWEEN ? AND ?
                ORDER BY collected_at_ms ASC
                LIMIT ?
                """,
                (device_id, start_ts_ms, end_ts_ms, limit),
            ).fetchall()
        except Exception:
            logger.warning("Failed to read telemetry history from database", exc_info=True)
            return []

        points: List[TelemetryPoint] = []
        for row in rows:
            timestamp = int(row["collected_at_ms"])
            iso_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat()
            points.append(
                TelemetryPoint(
                    timestamp=timestamp,
                    iso_time=iso_time,
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                )
            )
        return points

    def get_telemetry_history_aggregated(
        self,
        start_ts_ms: int,
        end_ts_ms: int,
        interval_ms: int,
        limit: int,
    ) -> List[TelemetryPoint]:
        if not self._enabled():
            return []

        device_id = get_settings().coreiot_device_id
        safe_interval = max(1, int(interval_ms))
        try:
            conn = get_connection()
            rows = conn.execute(
                """
                SELECT
                    ? + ((collected_at_ms - ?) / ?) * ? AS bucket_ts,
                    AVG(temperature) AS temperature,
                    AVG(humidity) AS humidity
                FROM telemetry_snapshots
                WHERE device_id = ?
                  AND collected_at_ms BETWEEN ? AND ?
                GROUP BY bucket_ts
                ORDER BY bucket_ts ASC
                LIMIT ?
                """,
                (
                    start_ts_ms,
                    start_ts_ms,
                    safe_interval,
                    safe_interval,
                    device_id,
                    start_ts_ms,
                    end_ts_ms,
                    limit,
                ),
            ).fetchall()
        except Exception:
            logger.warning("Failed to read aggregated telemetry history from database", exc_info=True)
            return []

        points: List[TelemetryPoint] = []
        for row in rows:
            timestamp = int(row["bucket_ts"])
            iso_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat()
            points.append(
                TelemetryPoint(
                    timestamp=timestamp,
                    iso_time=iso_time,
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                )
            )
        return points

    def log_device_command(
        self,
        command_type: str,
        payload: dict,
        *,
        source: str = "web",
        success: bool = True,
    ) -> None:
        if not self._enabled():
            return

        device_id = get_settings().coreiot_device_id
        try:
            conn = get_connection()
            conn.execute(
                """
                INSERT INTO device_commands
                    (device_id, command_type, payload, source, success)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    command_type,
                    json.dumps(payload, ensure_ascii=False),
                    source,
                    int(success),
                ),
            )
            conn.commit()
        except Exception:
            logger.warning("Failed to persist device command", exc_info=True)

    def log_voice_interaction(
        self,
        transcript: str,
        intent: str,
        response_text: str,
        *,
        success: bool = True,
    ) -> None:
        if not self._enabled():
            return

        try:
            conn = get_connection()
            conn.execute(
                """
                INSERT INTO voice_logs (transcript, intent, response_text, success)
                VALUES (?, ?, ?, ?)
                """,
                (transcript, intent, response_text, int(success)),
            )
            conn.commit()
        except Exception:
            logger.warning("Failed to persist voice interaction", exc_info=True)

    def list_device_commands(self, *, limit: int = 50, offset: int = 0) -> tuple[list[DeviceCommandLog], int]:
        if not self._enabled():
            return [], 0

        try:
            conn = get_connection()
            total_row = conn.execute("SELECT COUNT(*) AS c FROM device_commands").fetchone()
            total = int(total_row["c"]) if total_row else 0
            rows = conn.execute(
                """
                SELECT id, device_id, command_type, payload, source, success, created_at
                FROM device_commands
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        except Exception:
            logger.warning("Failed to read device command logs", exc_info=True)
            return [], 0

        items: list[DeviceCommandLog] = []
        for row in rows:
            try:
                payload = json.loads(row["payload"])
            except (TypeError, json.JSONDecodeError):
                payload = {"raw": row["payload"]}
            items.append(
                DeviceCommandLog(
                    id=int(row["id"]),
                    device_id=str(row["device_id"]),
                    command_type=str(row["command_type"]),
                    payload=payload,
                    source=str(row["source"]),
                    success=bool(row["success"]),
                    created_at=str(row["created_at"]),
                )
            )
        return items, total

    def list_voice_logs(self, *, limit: int = 50, offset: int = 0) -> tuple[list[VoiceLogEntry], int]:
        if not self._enabled():
            return [], 0

        try:
            conn = get_connection()
            total_row = conn.execute("SELECT COUNT(*) AS c FROM voice_logs").fetchone()
            total = int(total_row["c"]) if total_row else 0
            rows = conn.execute(
                """
                SELECT id, transcript, intent, response_text, success, created_at
                FROM voice_logs
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        except Exception:
            logger.warning("Failed to read voice logs", exc_info=True)
            return [], 0

        items = [
            VoiceLogEntry(
                id=int(row["id"]),
                transcript=str(row["transcript"]),
                intent=str(row["intent"]),
                response_text=str(row["response_text"]),
                success=bool(row["success"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]
        return items, total


storage_repository = StorageRepository()
