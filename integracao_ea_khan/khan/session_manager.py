import json
import os

from .playwright_login import KhanAuthenticator


class SessionManager:

    def __init__(self, session, auth_file, email=None, password=None):
        self.session = session
        self.auth_file = auth_file
        self.email = email
        self.password = password

    def load_cookies(self):

        if not os.path.exists(self.auth_file):
            self._login_and_save()

        with open(self.auth_file) as f:
            state = json.load(f)

        cookies = {c["name"]: c["value"] for c in state["cookies"]}

        self.session.cookies.clear()
        self.session.cookies.update(cookies)

    def refresh_session(self):

        print("[Session] Sessão expirada. Reautenticando...")

        self._login_and_save()
        self.load_cookies()

    def _login_and_save(self):

        if not self.email or not self.password:
            raise Exception("Credenciais não fornecidas para relogin")

        auth = KhanAuthenticator(
            self.email,
            self.password,
            self.auth_file
        )

        auth.login()
