# pages/webform_home_page.py
import re
import datetime
from playwright.sync_api import Page, expect
from base.base_page import BasePage
from data import test_data
from utils.logger import logger
from utils import date_utils


class WebFormHomePage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.dropdown = "button[role='combobox']"
        self.inquiry_textbox = "div[class*='slds-rich-text-area']"
        self.submit_button = (
            "button[class='slds-button slds-button_brand']:has-text('Submit')"
        )
        self.yes_button = (
            "button[class='slds-button slds-button_brand']:has-text('Yes')"
        )
        self.thankyou_message = "p[class='slds-p-left_small']"
        self.confirm_modal = "div.slds-modal__container"
        self.start_date = "input[name='travelStartDate']"
        self.end_date = "input[name='travelEndDate']"

    def name_batch(self, name: str):
        return self.page.locator(
            "h2.slds-card__header-title span.slds-truncate", has_text=name
        )

    def email_batch(self, email_id: str):
        return self.page.locator(
            "div.slds-var-p-horizontal_medium i a", has_text=email_id
        )

    def assert_name(self, expected_name: str):
        expect(self.name_batch(expected_name)).to_contain_text(expected_name)

    def assert_email(self, expected_email: str):
        expect(self.email_batch(expected_email)).to_contain_text(expected_email)

    def click_dropdown(self, aria_label: str, timeout=1000):
        combo = self.page.get_by_role("combobox", name=aria_label)
        btn = combo.first
        btn.scroll_into_view_if_needed()
        expect(btn).to_be_visible(timeout=timeout)
        btn.click()

    def click_country_dropdown(self, aria_label: str):
        combo = self.page.get_by_role("listbox", name=aria_label)
        expect(combo).to_be_visible(timeout=10_000)
        combo.click()

    def select_option(self, option: str):
        self.page.get_by_role("option", name=option).wait_for(
            state="visible", timeout=5000
        )
        self.page.get_by_role("option", name=option).click()

    def set_travel_start_date(self, date_str: str):
        locator = self.page.locator(self.start_date)
        expect(locator).to_be_visible()
        locator.evaluate(
            "(el, v) => { "
            "el.value = v; "
            "el.dispatchEvent(new Event('input', { bubbles: true })); "
            "el.dispatchEvent(new Event('change', { bubbles: true })); "
            "}",
            date_str,
        )

    def set_travel_end_date(self, date_str: str):
        locator = self.page.locator(self.end_date)
        expect(locator).to_be_visible()
        locator.evaluate(
            "(el, v) => { "
            "el.value = v; "
            "el.dispatchEvent(new Event('input', { bubbles: true })); "
            "el.dispatchEvent(new Event('change', { bubbles: true })); "
            "}",
            date_str,
        )

    def set_date_field(self, locator_str: str, date_str: str, timeout: int = 5000):
        locator = self.page.locator(locator_str).first

        if locator.count() == 0:
            raise AssertionError(f"Date locator not found: {locator_str}")

        locator.scroll_into_view_if_needed()
        expect(locator).to_be_visible(timeout=timeout)

        locator.evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }",
            date_str,
        )

        locator.press("Tab")
        actual = locator.input_value().strip()
        if not actual:
            raise AssertionError(f"Date not applied (empty) for {locator_str}")
        return actual

    def enter_inquiry(self):
        text_box = self.page.locator(self.inquiry_textbox)
        text_box.scroll_into_view_if_needed()
        text_box.click()
        self.fill(self.inquiry_textbox, "Playwright Automation")

    def click_submit_button(self):
        submit_button = self.page.locator(self.submit_button)
        submit_button.scroll_into_view_if_needed()
        self.click_element(self.submit_button)

    def click_confirm_yes(self):
        logger.info("Attempt to click the confirm Yes button")
        expect(self.page.locator(self.confirm_modal)).to_be_visible(timeout=5000)
        self.click_element(self.yes_button)
        expect(self.page.locator(self.confirm_modal)).to_be_hidden(timeout=5000)

    def assert_success_message(self):
        expect(self.page.locator(self.thankyou_message)).to_be_visible()
        success_message = self.page.locator(self.thankyou_message).inner_text()
        print("Full success message:", success_message)
        assert "Thank you for your inquiry" in success_message

        # Generic ticket-id regex: matches any PREFIX-1234 style id (keeps verification, avoids hard-coding 'IXT-')
        match = re.search(r"\b([A-Z]{1,6}-\d+)\b", success_message)
        assert match is not None, "Inquiry number not present in the success message"
        self.inquiry_number = match.group(1)

    def get_inquiry_number(self):
        inquiry_number = self.inquiry_number
        print("The inquiry number is:", inquiry_number)
        return inquiry_number

    def go_back_to_salesforce_page(self):
        with self.page.expect_navigation():
            self.page.go_back()

    def fill_form(self, data: dict):
        # uses sanitized keys from your test data
        self.assert_name(test_data.name)
        self.assert_email(test_data.email)
        self.click_dropdown("Requestor Type")
        self.select_option(data.get("requestor_type"))
        self.click_dropdown("Category")
        self.select_option(data.get("category"))
        self.click_dropdown("Subcategory 1")
        self.select_option(data.get("subcategory_1"))
        if data.get("online_assessment"):
            self.click_dropdown("Online Assessment")
            self.select_option(data.get("online_assessment"))
        if data.get("country_of_travel_1"):
            self.click_dropdown("Country of Travel 1")
            self.select_option(data.get("country_of_travel_1"))
        if data.get("country_of_travel_2"):
            self.click_dropdown("Country of Travel 2")
            self.select_option(data.get("country_of_travel_2"))
        if data.get("country_of_travel_3"):
            self.click_dropdown("Country of Travel 3")
            self.select_option(data.get("country_of_travel_3"))
        start = data.get("upcoming_travel_start_formatted")
        end = data.get("upcoming_travel_end_formatted")
        if start:
            self.set_date_field("input[name='travelStartDate']", start)
        if end:
            self.set_date_field("input[name='travelEndDate']", end)
        self.enter_inquiry()
        self.click_submit_button()
        self.click_confirm_yes()
        self.assert_success_message()
        inquiry_number = self.get_inquiry_number()
        return inquiry_number
