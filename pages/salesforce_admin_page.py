from playwright.sync_api import Page
from base.base_page import BasePage
from utils.logger import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pages.salesforce_home_page import SalesforceHomePage


class SalesforceAdminPage(BasePage):
    """
    Page Object for Salesforce Setup Admin page.
    Provides support for proxy login as another user.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self.user_search_box = "input[title='Search Setup']"
        self.iframe_locator = "iframe[title*='User:']"
        self.login_button = "input[title='Login']"

    def proxy_login(self, username: str) -> "SalesforceHomePage":
        """
        Perform a proxy login into Salesforce as the given username.
        Returns: SalesforceHomePage
        """
        logger.info(f"Proxy logging in as {username}")

        # Search and select the user in Setup
        self.fill(self.user_search_box, username)
        select_username = self.page.locator(f"span[title='{username}']")
        self.click_element(select_username)

        # Switch into user details iframe and click Login
        frame = self.page.frame_locator(self.iframe_locator)
        with self.page.expect_navigation():
            frame.locator(self.login_button).first.click()

        # Handle possible session timeout popup
        if self.page.locator("text=Your session has ended").is_visible(timeout=5000):
            logger.warning("Session expired popup appeared - clicking login button")
            self.page.locator("button:has-text('Log In')").click()

        print("DEBUG: page url after proxy login:", self.page.url)
        print("DEBUG: pages:", [p.url for p in self.page.context.pages])

        from pages.salesforce_home_page import SalesforceHomePage

        return SalesforceHomePage(self.page)
