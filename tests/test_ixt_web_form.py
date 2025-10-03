import json
import pytest
from pages.mailbox_sync_record_page import MailboxSyncRecordPage


# Load sanitized test data
with open("data/case_details.json") as f:
    case_details = json.load(f)


@pytest.mark.dependency(name="submit form")
def test_submit_webform(get_inquiry_number):
    """
    Verify that submitting a webform returns a valid inquiry number.
    """
    assert get_inquiry_number is not None


@pytest.mark.dependency(depends=["submit form"])
@pytest.mark.parametrize("expected", [case_details["TC-00001"]])
def test_verify_case_details(mailbox_record_page: MailboxSyncRecordPage, expected):
    """
    Verify case details and email status for a submitted record.
    """
    mailbox_record_page.assert_case_details(expected)
    custom_email_page = mailbox_record_page.click_email_link()
    custom_email_page.assert_email_status(expected="Sent")
