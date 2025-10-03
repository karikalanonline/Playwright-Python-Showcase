from playwright.sync_api import Page, expect
from base.base_page import BasePage
from pages.salesforce_home_page import SalesforceHomePage
from pages.webform_home_page import WebFormHomePage
from pages.mailbox_home_page import MailboxSyncHomePage
from utils.logger import logger


class MailboxApp(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.sf_home = SalesforceHomePage(page)
        # Generic app/webform names (safe)
        self.webform_locator = (
            "p[class='slds-truncate']:has-text('Demo Mailbox WebForm')"
        )
        self.mailbox_sync_tab = "a[title='Mailbox Sync']"

    def search_and_select_webform(self):
        logger.info("Searching the Demo WebForm via app launcher")
        self.click_app_launcher()
        self.page.get_by_label("Search apps and items...").fill("Demo Mailbox WebForm")
        self.page.wait_for_selector(self.webform_locator)
        self.click_and_wait_navi(self.webform_locator)
        return WebFormHomePage(self.page)

    def click_mailbox_sync_tab(self):
        self.click_element(self.mailbox_sync_tab)
        self.page.wait_for_timeout(4000)
        return MailboxSyncHomePage(self.page)
