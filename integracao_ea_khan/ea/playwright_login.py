from playwright.sync_api import sync_playwright

from integracao_ea_khan.progress import log_progress


class EAAuthenticator:

    def __init__(self, email, password, auth_file):
        self.email = email
        self.password = password
        self.auth_file = auth_file

    def login(self):
        log_progress("EA", "Iniciando fluxo de login via Playwright.")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=False)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()

            log_progress("EA", "Abrindo pagina de login.")
            page.goto("https://login.educacaoadventista.org.br")

            with page.expect_popup() as popup_info:
                page.click("button[type=button]")

            popup = popup_info.value
            popup.wait_for_load_state()

            log_progress("EA", "Enviando credenciais.")
            popup.fill('input[type="email"]', self.email)
            popup.press('input[type="email"]', 'Enter')

            popup.wait_for_selector("input[name='Passwd']")
            popup.fill("input[name='Passwd']", self.password)
            popup.press("input[name='Passwd']", "Enter")

            popup.wait_for_event("close")

            log_progress("EA", "Concluindo autorizacao no portal do professor.")
            page.goto("https://7edu-br.educadventista.org/teacherportal/Login/Google")

            page.click("[data-button-type='multipleChoiceIdentifier']")
            page.click("input[value='Acessar']")

            page.wait_for_load_state()

            context.storage_state(path=self.auth_file)
            log_progress("EA", "Cookies/sessao salvos com sucesso.")

            browser.close()
