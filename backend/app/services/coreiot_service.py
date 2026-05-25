import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.app.clients.coreiot_client import CoreIotClient
from backend.app.core.config import get_settings
from backend.app.db.repository import storage_repository
from backend.app.schemas.device import DeviceStatus
from backend.app.schemas.telemetry import TelemetryHistoryResponse, TelemetryLatestResponse, TelemetryPoint


logger = logging.getLogger(__name__)

_DEVICE_STATUS_CACHE_TTL_SECONDS = 30


class CoreIotService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._last_device_state: Dict[str, Optional[int | bool]] = {
            "led_on": None,
            "servo_angle": None,
        }
        self._client: Optional[CoreIotClient] = None
        self._client_cache_key: Optional[tuple[str, str, str, str]] = None
        self._device_status_cache: Optional[DeviceStatus] = None
        self._device_status_cached_at: float = 0.0

    def _client_config_key(self) -> tuple[str, str, str, str]:
        return (
            self.settings.coreiot_email,
            self.settings.coreiot_password,
            self.settings.coreiot_device_id,
            self.settings.coreiot_base_url.rstrip("/"),
        )

    def _telemetry_keys_csv(self) -> str:
        return ",".join(self.settings.get_telemetry_keys())

    def _sensor_keys_csv(self) -> str:
        keys = [key for key in self.settings.get_telemetry_keys() if key in ("temperature", "humidity")]
        return ",".join(keys) if keys else "temperature,humidity"

    def _device_attribute_keys_csv(self) -> str:
        keys = [key for key in self.settings.get_telemetry_keys() if key in ("LED_02", "ledState", "servoAngle")]
        if keys:
            return ",".join(keys)
        return "LED_02,ledState,servoAngle"

    def _get_client(self) -> CoreIotClient:
        if not self.settings.coreiot_email or not self.settings.coreiot_password:
            raise HTTPException(
                status_code=500,
                detail="COREIOT_EMAIL and COREIOT_PASSWORD must be configured.",
            )

        cache_key = self._client_config_key()
        if self._client is not None and self._client_cache_key == cache_key:
            return self._client

        try:
            self._client = CoreIotClient(
                email=self.settings.coreiot_email,
                password=self.settings.coreiot_password,
                device_id=self.settings.coreiot_device_id,
            )
            self._client_cache_key = cache_key
            return self._client
        except Exception as exc:
            logger.error("Failed to initialize CoreIoT client", exc_info=True)
            raise HTTPException(status_code=502, detail=f"CoreIoT unavailable: {exc}") from exc

    def _coreiot_error(self, action: str, exc: Exception) -> HTTPException:
        logger.error("CoreIoT %s failed", action, exc_info=True)
        return HTTPException(status_code=502, detail=f"CoreIoT {action} failed: {exc}")

    def _coerce_float(self, value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _coerce_bool(self, value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "on", "yes"}:
            return True
        if normalized in {"0", "false", "off", "no"}:
            return False
        return None

    def _coerce_int(self, value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _extract_latest_value(self, raw: Dict[str, list], key: str) -> tuple[Optional[str], Optional[int]]:
        values = raw.get(key, [])
        if values and isinstance(values, list):
            item = values[0]
            return item.get("value"), item.get("ts")
        return None, None

    def _attribute_map(self, raw: Any) -> Dict[str, Any]:
        if not isinstance(raw, list):
            return {}
        return {
            str(item.get("key")): item.get("value")
            for item in raw
            if isinstance(item, dict) and item.get("key") is not None
        }

    def _extract_first_attribute(self, attributes: Dict[str, Any], keys: tuple[str, ...]) -> Any:
        for key in keys:
            if key in attributes:
                return attributes[key]
        return None

    def _fetch_device_attributes(self, client: CoreIotClient) -> Dict[str, Any]:
        try:
            raw_attributes = client.fetch_attributes(self._device_attribute_keys_csv())
        except Exception:
            logger.warning("Failed to fetch CoreIoT device attributes", exc_info=True)
            return {}
        return self._attribute_map(raw_attributes)

    def _build_device_status(
        self,
        raw: Optional[Dict[str, list]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> DeviceStatus:
        raw = raw or {}
        attributes = attributes or {}

        led_value = self._extract_first_attribute(attributes, ("LED_02", "ledState"))
        servo_value = self._extract_first_attribute(attributes, ("servoAngle",))

        if led_value is None:
            led_value, _ = self._extract_latest_value(raw, "ledState")
        if servo_value is None:
            servo_value, _ = self._extract_latest_value(raw, "servoAngle")

        led_on = self._coerce_bool(led_value)
        servo_angle = self._coerce_int(servo_value)
        source = "coreiot_attributes" if attributes else "telemetry"

        if led_on is None and self._last_device_state["led_on"] is not None:
            led_on = bool(self._last_device_state["led_on"])
            source = "cache"
        if servo_angle is None and self._last_device_state["servo_angle"] is not None:
            servo_angle = int(self._last_device_state["servo_angle"])
            source = "cache"

        if led_on is None and servo_angle is None:
            source = "unknown"

        active_devices = 0
        if led_on:
            active_devices += 1
        if servo_angle not in (None, 0):
            active_devices += 1

        return DeviceStatus(
            led_on=led_on,
            servo_angle=servo_angle,
            active_devices=active_devices,
            status_source=source,
        )

    def _cache_device_status(self, status: DeviceStatus) -> DeviceStatus:
        self._device_status_cache = status
        self._device_status_cached_at = time.monotonic()
        return status

    def get_latest_snapshot(self) -> TelemetryLatestResponse:
        client = self._get_client()
        try:
            raw = client.fetch_timeseries(
                keys=self._telemetry_keys_csv(),
                limit=1,
                order_by="DESC",
            )
        except Exception as exc:
            raise self._coreiot_error("telemetry read", exc) from exc
        attributes = self._fetch_device_attributes(client)
        temp_value, temp_ts = self._extract_latest_value(raw, "temperature")
        humidity_value, humidity_ts = self._extract_latest_value(raw, "humidity")
        collected_at = temp_ts or humidity_ts

        device_status = self._build_device_status(raw, attributes)
        self._cache_device_status(device_status)

        return TelemetryLatestResponse(
            temperature=self._coerce_float(temp_value),
            humidity=self._coerce_float(humidity_value),
            collected_at=collected_at,
            device_status=device_status,
        )

    def get_device_status(self) -> DeviceStatus:
        now = time.monotonic()
        if (
            self._device_status_cache is not None
            and now - self._device_status_cached_at < _DEVICE_STATUS_CACHE_TTL_SECONDS
        ):
            return self._device_status_cache

        client = self._get_client()
        attributes = self._fetch_device_attributes(client)
        return self._cache_device_status(self._build_device_status(attributes=attributes))

    def set_led(self, on: bool, *, source: str = "web") -> DeviceStatus:
        client = self._get_client()
        try:
            client.send_rpc("setLED02", on)
        except Exception as exc:
            storage_repository.log_device_command("led", {"on": on}, source=source, success=False)
            raise self._coreiot_error("LED command", exc) from exc
        self._last_device_state["led_on"] = on
        storage_repository.log_device_command("led", {"on": on}, source=source, success=True)
        status = self._build_device_status()
        return self._cache_device_status(status)

    def set_servo(self, angle: int, *, source: str = "web") -> DeviceStatus:
        client = self._get_client()
        safe_angle = max(0, min(180, int(angle)))
        try:
            client.send_rpc("setServo", safe_angle)
        except Exception as exc:
            storage_repository.log_device_command(
                "servo",
                {"angle": safe_angle},
                source=source,
                success=False,
            )
            raise self._coreiot_error("servo command", exc) from exc
        self._last_device_state["servo_angle"] = safe_angle
        storage_repository.log_device_command(
            "servo",
            {"angle": safe_angle},
            source=source,
            success=True,
        )
        status = self._build_device_status()
        return self._cache_device_status(status)

    def _build_history_points(self, raw: Dict[str, list]) -> List[TelemetryPoint]:
        points_by_timestamp: Dict[int, Dict[str, Optional[float]]] = {}
        for key in ("temperature", "humidity"):
            for item in raw.get(key, []):
                timestamp = item.get("ts")
                if timestamp is None:
                    continue
                points_by_timestamp.setdefault(timestamp, {"temperature": None, "humidity": None})
                points_by_timestamp[timestamp][key] = self._coerce_float(item.get("value"))

        points: List[TelemetryPoint] = []
        for timestamp in sorted(points_by_timestamp.keys()):
            payload = points_by_timestamp[timestamp]
            iso_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat()
            points.append(
                TelemetryPoint(
                    timestamp=timestamp,
                    iso_time=iso_time,
                    temperature=payload["temperature"],
                    humidity=payload["humidity"],
                )
            )
        return points

    def _history_bucket_count(self) -> int:
        return max(1, self.settings.telemetry_history_buckets)

    def _history_query(self, start_ts_ms: int, end_ts_ms: int) -> tuple[int, int]:
        bucket_count = self._history_bucket_count()
        span = max(end_ts_ms - start_ts_ms, 1)
        interval_ms = max(1, span // bucket_count)
        return interval_ms, bucket_count

    def _align_points_to_grid(
        self,
        points: List[TelemetryPoint],
        start_ts_ms: int,
        end_ts_ms: int,
        interval_ms: int,
        bucket_count: int,
    ) -> List[TelemetryPoint]:
        if interval_ms <= 0:
            return points

        values_by_bucket: Dict[int, TelemetryPoint] = {}
        for point in points:
            if point.timestamp < start_ts_ms or point.timestamp > end_ts_ms:
                continue
            bucket_index = int((point.timestamp - start_ts_ms) / interval_ms)
            if bucket_index >= bucket_count:
                continue
            bucket_ts = start_ts_ms + bucket_index * interval_ms
            values_by_bucket[bucket_ts] = TelemetryPoint(
                timestamp=bucket_ts,
                iso_time=datetime.fromtimestamp(bucket_ts / 1000, tz=timezone.utc).isoformat(),
                temperature=point.temperature,
                humidity=point.humidity,
            )

        aligned: List[TelemetryPoint] = []
        for bucket_index in range(bucket_count):
            bucket_ts = start_ts_ms + bucket_index * interval_ms
            if bucket_ts > end_ts_ms:
                break
            existing = values_by_bucket.get(bucket_ts)
            if existing:
                aligned.append(existing)
                continue
            aligned.append(
                TelemetryPoint(
                    timestamp=bucket_ts,
                    iso_time=datetime.fromtimestamp(bucket_ts / 1000, tz=timezone.utc).isoformat(),
                    temperature=None,
                    humidity=None,
                )
            )
        return aligned

    def _fetch_history_aggregated(
        self,
        client: CoreIotClient,
        keys: str,
        start_ts_ms: int,
        end_ts_ms: int,
        interval_ms: int,
        bucket_count: int,
    ) -> Dict[str, list]:
        return client.fetch_timeseries(
            keys=keys,
            start_ts=start_ts_ms,
            end_ts=end_ts_ms,
            limit=bucket_count,
            order_by="ASC",
            interval_ms=interval_ms,
            agg="AVG",
        )

    def _load_history_points(
        self,
        client: CoreIotClient,
        start_ts_ms: int,
        end_ts_ms: int,
    ) -> tuple[List[TelemetryPoint], int, int]:
        keys = self._sensor_keys_csv()
        interval_ms, bucket_count = self._history_query(start_ts_ms, end_ts_ms)

        try:
            raw = self._fetch_history_aggregated(
                client,
                keys,
                start_ts_ms,
                end_ts_ms,
                interval_ms,
                bucket_count,
            )
            points = self._build_history_points(raw)
            if points:
                return points, interval_ms, bucket_count
        except Exception:
            logger.warning(
                "Aggregated telemetry fetch failed (interval=%sms, buckets=%s), trying SQLite",
                interval_ms,
                bucket_count,
                exc_info=True,
            )

        if self.settings.database_enabled:
            points = storage_repository.get_telemetry_history_aggregated(
                start_ts_ms=start_ts_ms,
                end_ts_ms=end_ts_ms,
                interval_ms=interval_ms,
                limit=bucket_count,
            )
            if points:
                return points, interval_ms, bucket_count

        try:
            latest_raw = client.fetch_timeseries(
                keys=keys,
                limit=1,
                order_by="DESC",
            )
        except Exception:
            logger.warning("Failed to fetch latest telemetry fallback for history", exc_info=True)
        else:
            points = self._build_history_points(latest_raw)
            if points:
                return points, interval_ms, bucket_count

        return [], interval_ms, bucket_count

    def _finalize_history_points(
        self,
        points: List[TelemetryPoint],
        safe_hours: int,
        start_ts_ms: int,
        end_ts_ms: int,
        interval_ms: int,
        bucket_count: int,
    ) -> TelemetryHistoryResponse:
        return TelemetryHistoryResponse(
            range_hours=safe_hours,
            sample_interval_seconds=max(1, interval_ms // 1000),
            points=self._align_points_to_grid(
                points,
                start_ts_ms,
                end_ts_ms,
                interval_ms,
                bucket_count,
            ),
        )

    def get_history(self, range_hours: int) -> TelemetryHistoryResponse:
        safe_hours = max(1, min(range_hours, self.settings.telemetry_max_hours))
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(hours=safe_hours)
        start_ts_ms = int(start_time.timestamp() * 1000)
        end_ts_ms = int(end_time.timestamp() * 1000)

        client = self._get_client()
        points, interval_ms, bucket_count = self._load_history_points(
            client,
            start_ts_ms,
            end_ts_ms,
        )
        return self._finalize_history_points(
            points,
            safe_hours,
            start_ts_ms,
            end_ts_ms,
            interval_ms,
            bucket_count,
        )


coreiot_service = CoreIotService()
