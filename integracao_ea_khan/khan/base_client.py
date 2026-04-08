from __future__ import annotations

from collections.abc import Callable

import requests


AuthExpiryChecker = Callable[[requests.Response], bool]


class BaseClient:
    def __init__(
        self,
        base_url: str,
        session_manager,
        auth_expiry_checker: AuthExpiryChecker | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session_manager = session_manager
        self.session_manager.session = self.session
        self.session_manager.load_cookies()
        self._auth_expiry_checker = auth_expiry_checker

    def request(self, method: str, endpoint: str, retry_on_auth_expired: bool = True, **kwargs):
        response = self.session.request(method, self._build_url(endpoint), **kwargs)

        if retry_on_auth_expired and self._is_auth_expired(response):
            self.session_manager.refresh_session()
            response = self.session.request(method, self._build_url(endpoint), **kwargs)

        return response

    def request_EA(self, method, endpoint, **kwargs):
        kwargs.setdefault("allow_redirects", False)
        return self.request(method, endpoint, **kwargs)

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.base_url}{endpoint}"

    def _is_auth_expired(self, response: requests.Response) -> bool:
        if self._auth_expiry_checker is not None:
            return self._auth_expiry_checker(response)
        return response.status_code in {401, 302}

    def _get_json(self, response: requests.Response):
        response.raise_for_status()
        return response.json()

    def _get_data(self, response: requests.Response):
        return self._get_json(response).get("Data", [])
