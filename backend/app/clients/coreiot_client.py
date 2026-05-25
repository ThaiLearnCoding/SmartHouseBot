import logging
from typing import Any, Dict, Optional

import requests

from backend.app.core.config import get_settings


logger = logging.getLogger(__name__)


class CoreIotClient:
    def __init__(
        self,
        email: str,
        password: str,
        device_id: str,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        settings = get_settings()
        self.email = email
        self.password = password
        self.device_id = device_id
        self.base_url = (base_url or settings.coreiot_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.coreiot_timeout_seconds
        self.token: Optional[str] = None
        self._session = requests.Session()

    def login(self) -> None:
        payload = {"username": self.email, "password": self.password}
        response = self._session.post(
            f"{self.base_url}/api/auth/login",
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        token = response.json().get("token")
        if not token:
            raise RuntimeError("CoreIoT login succeeded but no token was returned.")

        self.token = token

    def _ensure_logged_in(self) -> None:
        if not self.token:
            self.login()

    def _auth_headers(self) -> Dict[str, str]:
        if not self.token:
            raise RuntimeError("CoreIoT client is not authenticated.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        self._ensure_logged_in()
        kwargs.setdefault("timeout", self.timeout_seconds)

        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("Authorization", f"Bearer {self.token}")
        kwargs["headers"] = headers

        response = self._session.request(method, url, **kwargs)
        if response.status_code == 401:
            self.login()
            headers["Authorization"] = f"Bearer {self.token}"
            kwargs["headers"] = headers
            response = self._session.request(method, url, **kwargs)

        response.raise_for_status()
        return response

    def send_rpc(self, method: str, params: Any) -> Dict[str, Any]:
        response = self._request(
            "POST",
            f"{self.base_url}/api/rpc/twoway/{self.device_id}",
            json={"method": method, "params": params},
            headers=self._auth_headers(),
        )
        return response.json()

    def fetch_timeseries(
        self,
        keys: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        limit: Optional[int] = None,
        order_by: str = "DESC",
        interval_ms: Optional[int] = None,
        agg: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"keys": keys}
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        if limit is not None:
            params["limit"] = limit
        if order_by:
            params["orderBy"] = order_by
        if interval_ms is not None:
            params["interval"] = interval_ms
        if agg:
            params["agg"] = agg

        response = self._request(
            "GET",
            f"{self.base_url}/api/plugins/telemetry/DEVICE/{self.device_id}/values/timeseries",
            headers={"Authorization": f"Bearer {self.token}"},
            params=params,
        )
        return response.json()

    def fetch_attributes(self, keys: str) -> Dict[str, Any]:
        response = self._request(
            "GET",
            f"{self.base_url}/api/plugins/telemetry/DEVICE/{self.device_id}/values/attributes",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"keys": keys},
        )
        return response.json()
