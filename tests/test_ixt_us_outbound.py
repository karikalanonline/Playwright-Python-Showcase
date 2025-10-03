import json
import pytest
from pages.mailbox_sync_record_page import MailboxSyncRecordPage
from pages.custom_email_page import CustomEmailPage

with open("data/web_form_values.json") as f:
    case_details = json.load(f)


# Example of webform submission test
# @pytest.mark.dependency(name="submit form")
# def test_submit_webform(get_inquiry_number):
#     assert get_inquiry_number is not None


# Example of verifying case details with dependency
# @pytest.mark.dependency(depends=["submit form"])
# @pytest.mark.parametrize("expected", [case_details["TC-00001"]])
# def test_verify_case_details(
#     mailbox_record_page: MailboxSyncRecordPage, expected
# ):
#     mailbox_record_page.assert_case_details(expected)
#     custom_email_page = mailbox_record_page.click_email_link()
#     custom_email_page.assert_email_status(expected="Sent")


def test_default_user_login(proxy_user_login):
    """
    Verify that the default user can log in and see the App Launcher.
    """
    proxy_user_login.click_app_launcher()


###################################
@pytest.mark.parametrize(
    ("proxy_user_login", "select_list_view"),
    [("Demo Test User", "Master Case List")],
    indirect=["proxy_user_login", "select_list_view"],
)
def test_tc06_us1(select_list_view):
    """
    Example test for a specific list view.
    """
    print("Test")


###################################################
@pytest.mark.parametrize(
    ("proxy_user_login", "select_list_view"),
    [("Business Test User 1", "General Inquiries")],
    indirect=["proxy_user_login", "select_list_view"],
)
def test_tc01_us4(select_list_view):
    """
    Example test with another test user and list view.
    """
    print("Test")
