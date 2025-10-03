import json
import pytest
from pages.mailbox_home_page import MailboxSyncHomePage

# Load sanitized common data
with open("data/common_data.json") as f:
    common_data = json.load(f)


@pytest.mark.parametrize("select_list_view", ["Open Cases"], indirect=True)
def test_select_open_cases(select_list_view):
    """
    Verify that the 'Open Cases' list view can be selected.
    """
    mailbox_sync_home_page = select_list_view
    assert mailbox_sync_home_page is not None


def test_select_open_cases_from_common(select_list_view, common_data):
    """
    Verify that the list view loaded matches the expected value from common data.
    """
    page = select_list_view("Open Cases")
    page.assert_list_view_loaded(common_data["list_view_name"]["Open Cases"])


# Example of parametrizing across multiple list views
@pytest.mark.parametrize("list_view", ["All", "Open Cases"])
def test_list_view_variants(select_list_view_factory, list_view):
    select_list_view_factory(list_view)
