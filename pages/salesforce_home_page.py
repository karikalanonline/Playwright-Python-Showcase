from base.base_page import BasePage
from playwright.sync_api import Page, expect, TimeoutError as PWTimeoutError
from utils.logger import logger
from pages.record_home_page import RecordHomePage
from pages.salesforce_admin_page import SalesforceAdminPage
from pages.mailbox_home_page import MailboxSyncHomePage

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pages.mailbox_app_page import MailboxApp


class SalesforceHomePage(BasePage):
    """
    Page Object for Salesforce Home Page.
    Provides navigation to Lightning, apps, modules, and setup/admin page.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self.spinner = ".slds-spinner:not([hidden])"
        self.home_tab = "a[title='Home']"
        self.account_tab = "a[href='/lightning/o/Account/home'] span.slds-truncate:has-text('Accounts')"
        self.switch_to_lightning_link = (
            "div.navLinks div.linkElements a.switch-to-lightning"
        )
        self.demo_module = ":text-is('Demo Module')"
        self.mailbox_app = "p[class='slds-truncate']:has-text('Demo Mailbox App')"
        self.gear_icon = "div.setupGear"
        self.setup_option = "#related_setup_app_home"
        self.mailbox_sync_tab = "#Demo_Mailbox_Sync__c"

    def switch_to_lightning(self):
        logger.info("Attempting to switch to Lightning...")
        try:
            link = self.page.locator(self.switch_to_lightning_link).first
            link.wait_for(state="visible", timeout=5000)
            with self.page.expect_navigation():
                link.click()
        except PWTimeoutError:
            logger.info("Already in Lightning")

    def search_demo_module(self):
        logger.info("Searching for the Demo Module")
        self.page.get_by_label("Search apps and items...").fill("Demo Module")
        self.page.wait_for_selector(self.demo_module)

    def search_and_select_mailbox_app(self):
        logger.info("Searching the Demo Mailbox App via app launcher")
        self.page.get_by_label("Search apps and items...").fill("Demo Mailbox App")
        self.page.wait_for_selector(self.mailbox_app)
        self.click_and_wait_navi(self.mailbox_app)
        from pages.mailbox_app_page import MailboxApp

        return MailboxApp(self.page)

    def click_demo_module(self):
        logger.info("Selecting the Demo Module")
        self.click_element(self.demo_module)
        self.page.wait_for_load_state("domcontentloaded")
        return RecordHomePage(self.page)

    def assert_on_home(self):
        expect(self.page.locator(self.home_tab)).to_be_visible()

    def go_to_admin_page(self):
        self.click_element(self.gear_icon)
        with self.page.context.expect_page() as new_page_info:
            self.click_element(self.setup_option)
        setup_page = new_page_info.value
        return SalesforceAdminPage(setup_page)

    def click_mailbox_sync_tab(self):
        logger.info("Navigating to the Demo Mailbox Sync tab via app launcher")
        self.page.get_by_label("Search apps and items...").fill("Demo Mailbox Sync")
        self.page.wait_for_selector(self.mailbox_sync_tab)
        self.page.locator(self.mailbox_sync_tab).click()
        self.page.wait_for_load_state("networkidle")
        return MailboxSyncHomePage(self.page)
