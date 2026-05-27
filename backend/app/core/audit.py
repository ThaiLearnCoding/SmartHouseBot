import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)


def write_audit_event(event: Dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.audit_log_enabled:
        return

    try:
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        payload = {"timestamp": timestamp, **event}
        log_path = Path(settings.audit_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        logger.error("Failed to write audit log", exc_info=True)
