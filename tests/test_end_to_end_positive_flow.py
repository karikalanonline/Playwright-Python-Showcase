import pytest
from playwright.sync_api import expect, Page

from utils import config, report_helper
from data import test_data
from pages.record_home_page import RecordHomePage


# @pytest.mark.e2e
def test_e2e_flow(record_home: RecordHomePage, record_data):
    """
    End-to-end flow:
    1. Navigate to a record from the home page
    2. Get the nominee value from the record page
    3. Assert it matches the expected value from test data
    """
    with record_home.page.expect_navigation():
        record_page = record_home.click_record()
        actual_nominee_value = record_page.get_nominee_value()
        expected_nominee_value = record_data["nominee_value"]
        assert (
            actual_nominee_value.lower() == expected_nominee_value.lower()
        ), f"Expected {expected_nominee_value}, got {actual_nominee_value}"
