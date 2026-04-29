import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.app.clients.coreiot_client import CoreIotClient
from backend.app.core.config import get_settings
from backend.app.schemas.device import DeviceStatus
from backend.app.schemas.telemetry import TelemetryHistoryResponse, TelemetryLatestResponse, TelemetryPoint


logger = logging.getLogger(__name__)


class CoreIotService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._last_device_state: Dict[str, Optional[int | bool]] = {
            "led_on": None,
            "servo_angle": None,
        }

    def _get_client(self) -> CoreIotClient:
        if not self.settings.coreiot_email or not self.settings.coreiot_password:
            raise HTTPException(
                status_code=500,
                detail="COREIOT_EMAIL and COREIOT_PASSWORD must be configured.",
            )

        try:
            return CoreIotClient(
                email=self.settings.coreiot_email,
                password=self.settings.coreiot_password,
                device_id=self.settings.coreiot_device_id,
            )
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
            raw_attributes = client.fetch_attributes("LED_02,ledState,servoAngle")
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

    def get_latest_snapshot(self) -> TelemetryLatestResponse:
        client = self._get_client()
        try:
            raw = client.fetch_timeseries(
                keys="temperature,humidity,ledState,servoAngle",
                limit=1,
                order_by="DESC",
            )
        except Exception as exc:
            raise self._coreiot_error("telemetry read", exc) from exc
        attributes = self._fetch_device_attributes(client)
        temp_value, temp_ts = self._extract_latest_value(raw, "temperature")
        humidity_value, humidity_ts = self._extract_latest_value(raw, "humidity")
        collected_at = temp_ts or humidity_ts

        return TelemetryLatestResponse(
            temperature=self._coerce_float(temp_value),
            humidity=self._coerce_float(humidity_value),
            collected_at=collected_at,
            device_status=self._build_device_status(raw, attributes),
        )

    def get_device_status(self) -> DeviceStatus:
        return self.get_latest_snapshot().device_status

    def set_led(self, on: bool) -> DeviceStatus:
        client = self._get_client()
        try:
            client.send_rpc("setLED02", on)
        except Exception as exc:
            raise self._coreiot_error("LED command", exc) from exc
        self._last_device_state["led_on"] = on
        return self._build_device_status()

    def set_servo(self, angle: int) -> DeviceStatus:
        client = self._get_client()
        safe_angle = max(0, min(180, int(angle)))
        try:
            client.send_rpc("setServo", safe_angle)
        except Exception as exc:
            raise self._coreiot_error("servo command", exc) from exc
        self._last_device_state["servo_angle"] = safe_angle
        return self._build_device_status()

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

    def get_history(self, range_hours: int) -> TelemetryHistoryResponse:
        safe_hours = max(1, min(range_hours, self.settings.telemetry_max_hours))
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(hours=safe_hours)
        client = self._get_client()
        try:
            raw = client.fetch_timeseries(
                keys="temperature,humidity",
                start_ts=int(start_time.timestamp() * 1000),
                end_ts=int(end_time.timestamp() * 1000),
                limit=self.settings.telemetry_limit_points,
                order_by="ASC",
            )
        except Exception as exc:
            raise self._coreiot_error("telemetry history read", exc) from exc

        points = self._build_history_points(raw)
        if not points:
            try:
                latest_raw = client.fetch_timeseries(
                    keys="temperature,humidity",
                    limit=1,
                    order_by="DESC",
                )
            except Exception:
                logger.warning("Failed to fetch latest telemetry fallback for history", exc_info=True)
            else:
                points = self._build_history_points(latest_raw)

        return TelemetryHistoryResponse(range_hours=safe_hours, points=points)


coreiot_service = CoreIotService()
