import logging
from typing import Dict, List, Optional

import requests
from requests import Response
from requests.auth import HTTPBasicAuth

from config import settings

logger = logging.getLogger(__name__)


class IntraServiceAPI:
    """Работа с IntraService REST API"""

    def __init__(self, session: Optional[requests.Session] = None):
        self.base_url = settings.INTRASERVICE_URL.rstrip('/')
        self.eventlog_base = settings.EVENTLOG_BASE_URL.rstrip('/')
        self.username = settings.INTRASERVICE_USERNAME
        self.password = settings.INTRASERVICE_PASSWORD
        self.session = session or requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.cookies.set("seaf_user", settings.INTRASERVICE_SEAF_USER)
        self.authenticated = False

    def login(self) -> bool:
        """Логинимся в IntraService с Basic Auth и получаем cookie."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/",
                timeout=10,
            )

            if response.status_code == 200:
                self.authenticated = True
                logger.info("Успешно аутентифицированы в IntraService")
                return True

            logger.error("Ошибка при логине: %s", response.status_code)
            return False
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.error("Ошибка при логине: %s", exc)
            self.authenticated = False
            return False

    def _ensure_auth(self) -> bool:
        if not self.authenticated:
            return self.login()
        return True

    def _request(
        self,
        method: str,
        path: str,
        *,
        absolute: bool = False,
        **kwargs,
    ) -> Optional[Response]:
        if not self._ensure_auth():
            logger.error("Аутентификация не выполнена, пропускаем запрос %s", path)
            return None

        url = path if absolute else f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.error("Ошибка при запросе %s: %s", url, exc)
            return None

    def get_open_tickets(self, status_ids: Optional[List[int]] = None, limit: int = 50) -> List[Dict]:
        params: Dict[str, object] = {"limit": limit}
        statuses = status_ids or settings.INTRASERVICE_STATUS_IDS
        if statuses:
            params["StatusID"] = statuses

        response = self._request("get", "/api/task", params=params)
        if not response or not response.text:
            return []

        logger.info("Получено заявок: %s", len(response.json()))
        return response.json()

    def get_ticket_logs(self, ticket_id: int) -> str:
        response = self._request("get", f"/api/task/{ticket_id}/logs")
        if not response:
            return ""
        logger.info("Получены логи для заявки %s", ticket_id)
        return response.text

    def get_comments(self, ticket_id: int) -> List[Dict]:
        response = self._request("get", f"/api/task/{ticket_id}/comment")
        if not response or not response.text:
            return []
        return response.json()

    def add_comment(self, ticket_id: int, text: str, is_internal: bool = False) -> bool:
        payload = {"text": text, "internal": is_internal}
        response = self._request("post", f"/api/task/{ticket_id}/comment", json=payload)
        return bool(response)

    def get_categories(self) -> List[Dict]:
        response = self._request("get", "/api/task/category")
        if not response or not response.text:
            return []
        return response.json()

    def get_executors(self) -> List[Dict]:
        response = self._request("get", "/api/user")
        if not response or not response.text:
            return []
        return response.json()

    def fetch_eventlog_entry(self, event_id: int) -> Optional[str]:
        response = self._request(
            "get",
            f"{self.eventlog_base}/view/{event_id}",
            absolute=True,
        )
        return response.text if response else None
