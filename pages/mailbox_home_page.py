from playwright.sync_api import Page, expect
from base.base_page import BasePage
from pages.mailbox_sync_record_page import MailboxSyncRecordPage


class MailboxSyncHomePage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.global_search_button = "button[aria-label='Search']"
        self.global_search_input = (
            "input.slds-input[placeholder='Search...'][type='search']"
        )
        self.list_search = "input.slds-input[placeholder='Search...'][type='search']"
        # Sanitized: removed 'Immigration' → just generic Mailbox Sync
        self.picklist_icon = "button[title ='Select a List View: Mailbox Sync']"
        self.search_box = "input[role ='combobox']"

    def select_record(self, inquiry_number: str):
        """
        Selects a record from the Mailbox Sync list by inquiry number.
        """
        record = self.page.locator(f"a[title='{inquiry_number}']")
        with self.page.expect_navigation():
            self.click_element(record)
        return MailboxSyncRecordPage(self.page)

    def go_to_list_view(self, list_view_name: str):
        """
        Switch to a given list view.
        """
        self.click_element(self.picklist_icon)
        self.click_element(self.search_box)
        self.type(self.search_box, list_view_name)
        list_view = self.page.locator(
            f"div.slds-listbox lightning-base-combobox-formatted-text:has-text('{list_view_name}')"
        )
        self.click_element(list_view)

    def assert_list_view_loaded(self, list_view_name: str, timeout: int = 10_000):
        """
        Assert that the given list view is loaded.
        """
        header = self.page.locator(
            f"span.slds-page-header__title:has-text('{list_view_name}')"
        )
        expect(header).to_be_visible(timeout=timeout)

    def open_record_business(self, record_id: str, timeout: int = 30_000):
        """
        Open a record by searching for record_id in the global search.
        """
        # 1) Open global search
        btn = self.page.locator(self.global_search_button)
        expect(btn).to_be_visible()
        btn.click()

        # 2) Focus the global search input
        box = self.page.locator(self.global_search_input).first
        expect(box).to_be_visible()
        box.click()
        box.fill("")  # clear any residue
        box.type(record_id, delay=60)

        with self.page.expect_navigation():
            self.page.locator(
                f"mark[class='data-match']:has-text('{record_id}')"
            ).click()
        self.page.wait_for_timeout(5000)
        return MailboxSyncRecordPage(self.page)
