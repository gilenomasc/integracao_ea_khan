from pathlib import Path

from playwright.sync_api import sync_playwright

from integracao_ea_khan.progress import log_progress


class KhanAuthenticator:

    def __init__(self, email, password, auth_file):
        self.email = email
        self.password = password
        self.auth_file = auth_file

    def login(self):
        log_progress("KHAN", "Iniciando fluxo de login via Playwright.")
        auth_path = Path(self.auth_file)
        auth_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=False)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()

            log_progress("KHAN", "Abrindo pagina de login.")
            page.goto("https://pt.khanacademy.org/login")

            page.click("#onetrust-accept-btn-handler")

            log_progress("KHAN", "Enviando credenciais.")
            page.fill("xpath=//input[@type='text']", self.email)
            page.fill("xpath=//input[@type='password']", self.password)
            page.click("xpath=//button[@type='submit']")

            page.wait_for_selector('[data-testid="teacher-tools-container"]')

            context.storage_state(path=str(auth_path))
            log_progress("KHAN", "Cookies/sessao salvos com sucesso.")

            browser.close()
