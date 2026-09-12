import requests


class BaseClient:

    def __init__(self, base_url: str, session_manager: requests.Session) -> None:

        self.base_url = base_url
        self.session = requests.Session()
        self.session_manager = session_manager

        self.session_manager.session = self.session
        self.session_manager.load_cookies()

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:

        url = f"{self.base_url}{endpoint}"

        r = self.session.request(
            method,
            url,
            allow_redirects=False,
            **kwargs
        )

        if r.status_code == 302:
            self.session_manager.refresh_session()

            r = self.session.request(
                method,
                url,
                allow_redirects=False,
                **kwargs
            )

        return r

    def _get_data(self, response) -> list[dict]:
        return response.json().get("Data", [])