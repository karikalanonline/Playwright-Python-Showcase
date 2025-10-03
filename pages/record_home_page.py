import allure
from playwright.sync_api import expect, Page
from utils.logger import logger
from base.base_page import BasePage
from data import test_data


class RecordHomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Generic field selectors (renamed, but logic same)
        self.generic_field_1 = (
            "div div div span[class='test-id__field-label']:has-text('Nominee Field')"
        )
        self.generic_field_2 = "div[class='test-id__field-label-container slds-form-element__label']:has-text('Initiation Period')"

    @allure.step("Getting the nominee value")
    def get_nominee_value(self, timeout: int = 30_000) -> str:
        container = self.page.locator(
            "[data-target-selection-name='sfdc:RecordField.DemoObject__c.Nominee__c']"
        ).first
        expect(container).to_be_visible(timeout=timeout)

        value = container.locator(
            "lightning-formatted-text, .test-id__field-value, .slds-form-element__static"
        ).first
        return value.inner_text().strip()

    # @allure.step("Verify the nominee equals: `{expected_value}`")
    # def verify_nominee_field(
    #     self, expected_value: str = test_data.nominee_value
    # ):
    #     logger.info("Verify the value present on the nominee field")
    #     actual_value = self.get_nominee_value()
    #     assert (
    #         actual_value.lower() == expected_value.lower()
    #     ), f"Expected {expected_value!r}, got {actual_value!r}"
