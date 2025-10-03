from playwright.sync_api import expect, Page
from utils.logger import logger
from base.base_page import BasePage
from pages.record_home_page import RecordHomePage


class ImmigrationHomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Kept generic name, safe for public repo
        self.immigration_name = "th[data-label='Record Name']"

    # def click_immigration_record(
    #     self, record_id: str = "I-10001", timeout: int = 30_000
    # ):
    #     link = self.page.locator(f"role=link[name='{record_id}']").first
    #     expect(link).to_be_visible(timeout=timeout)
    #     with self.page.expect_navigation():
    #         link.click()
    #     return ImmigrationRecordPage(self.page)

    def click_immigration_record(self):
        single = self.page.locator(self.immigration_name).first
        expect(single).to_be_visible(timeout=5000)
        single.click()
        return RecordHomePage(self.page)
