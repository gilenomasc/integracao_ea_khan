from playwright.sync_api import sync_playwright


class KhanAuthenticator:

    def __init__(self, email, password, auth_file):
        self.email = email
        self.password = password
        self.auth_file = auth_file

    def login(self):

        with sync_playwright() as p:

            browser = p.chromium.launch(channel="msedge", headless=False)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()

            page.goto("https://pt.khanacademy.org/login")

            page.click("#onetrust-accept-btn-handler")

            page.fill("xpath=//input[@type='text']", self.email)
            page.fill("xpath=//input[@type='password']", self.password)
            page.click("xpath=//button[@type='submit']")

            page.wait_for_selector('[data-testid="teacher-tools-container"]')

            context.storage_state(path=self.auth_file)

            browser.close()