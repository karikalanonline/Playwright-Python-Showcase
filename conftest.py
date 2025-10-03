import pytest, re, os, allure, json, time
from pathlib import Path
from playwright.sync_api import Playwright, Page, expect
from playwright.sync_api import TimeoutError as PWTimeoutError
from utils import config
from utils.date_utils import date_from_value
from data import test_data

# Page imports (all sanitized to generic names)
from pages.login_page import LoginPage
from pages.salesforce_home_page import SalesforceHomePage
from pages.mailbox_home_page import MailboxApp
from pages.mailbox_home_page import MailboxSyncHomePage
from pages.webform_home_page import WebFormHomePage
from pages.salesforce_admin_page import SalesforceAdminPage
from pages.mailbox_sync_record_page import MailboxSyncRecordPage
from pages.custom_email_page import CustomEmailPage
from pages.record_home_page import RecordHomePage


INQUIRY_FILE = Path(__file__).parent / "data" / "inquiry.json"
BASE = Path(__file__).parent.parent
COMMON_PATH = BASE / "data" / "common_data.json"
TESTDATA_PATH = Path(__file__).resolve().parent / "data" / "web_form_values.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pytest_addoption(parser):
    parser.addoption(
        "--tc",
        action="store",
        default="",
        help="Run only the test data record(s) matching the TC id(s), comma separated.",
    )


def _normalize_key(k: str) -> str:
    s = k.strip()
    s = s.replace("-", " ").replace("/", " ")
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^0-9a-zA-Z_]", "", s)
    return s.lower()


def pytest_generate_tests(metafunc):
    if "data" not in metafunc.fixturenames:
        return

    common = load_json(COMMON_PATH) if COMMON_PATH.exists() else {}
    all_data = load_json(TESTDATA_PATH)

    tc_option = metafunc.config.option.tc.strip()
    if tc_option:
        wanted = {s.strip() for s in tc_option.split(",") if s.strip()}
        filtered = [d for d in all_data if d.get("tc_id") in wanted]
        if not filtered:
            raise pytest.UsageError(
                f"No test data found for tc id(s): {', '.join(wanted)}"
            )
        param_list = filtered
    else:
        param_list = all_data

    prepared, ids = [], []
    for d in param_list:
        merged = dict(common)
        merged.update(d)
        if merged.get("upcoming_travel_start"):
            merged["upcoming_travel_start_formatted"] = date_from_value(
                merged["upcoming_travel_start"], "%m/%d/%Y"
            )
        if merged.get("upcoming_travel_end"):
            merged["upcoming_travel_end_formatted"] = date_from_value(
                merged["upcoming_travel_end"], "%m/%d/%Y"
            )
        prepared.append(merged)
        ids.append(merged.get("tc_id", "no-id"))

    metafunc.parametrize("data", prepared, ids=ids)


# Screenshot on failure
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed and report.when in ("setup", "call", "teardown"):
        try:
            page = item.funcargs["page"]
            screenshot = page.screenshot()
            allure.attach(
                screenshot,
                name="Failure Screenshot",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                page.url,
                name="URL at failure",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception as e:
            print(f"Could not take screenshot: {e}")


@pytest.fixture
def context(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    yield context
    context.close()
    browser.close()


@pytest.fixture
def page(context):
    page = context.new_page()
    yield page
    page.close()


# Video recording
@pytest.fixture(scope="session")
def brower_context_args(browser_context_args):
    os.makedirs("Videos", exist_ok=True)
    return {
        **browser_context_args,
        "record_video_dir": "videos",
        "record_video_size": {"width": 1280, "height": 720},
    }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    outcome = yield
    item.rep_call = outcome.get_result()


# Trace & video on failure
@pytest.fixture(autouse=True)
def _video_trace(page: Page, request):
    page.context.tracing.start(
        title=request.node.name, screenshots=True, snapshots=True, sources=True
    )
    yield
    failed = (
        request.node.rep_call.failed if hasattr(request.node, "rep_call") else False
    )
    if failed:
        os.makedirs("reports", exist_ok=True)
        trace_path = f"reports/trace-{request.node}.zip"
        page.context.tracing.stop(path=trace_path)
        allure.attach.file(
            trace_path,
            name="Playwright Trace",
            attachment_type=allure.attachment_type.ZIP,
        )
        try:
            page.close()
        except Exception:
            pass
        for v in page.video.values():
            try:
                p = v.path()
                allure.attach.file(
                    p,
                    name="Video (failure)",
                    attachment_type=allure.attachment_type.MP4,
                )
            except Exception:
                pass
    else:
        page.context.tracing.stop()


def get_sf_credentials_from_env():
    return [
        {
            "user": os.getenv("sf1_user", config.USERNAME),
            "password": os.getenv("sf1_password", config.PASSWORD),
        },
        {
            "user": os.getenv("sf2_user", config.USERNAME),
            "password": os.getenv("sf2_password", config.PASSWORD),
        },
    ]


# Fixtures for test data
@pytest.fixture(scope="session")
def common_data():
    file = os.path.join("data", "common_data.json")
    with open(file) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def users():
    file = os.path.join("data", "users.json")
    with open(file) as f:
        return json.load(f)


# Core Salesforce login fixture
@pytest.fixture
def sf_home_page(request, page: Page) -> SalesforceHomePage:
    if hasattr(request, "param") and isinstance(request.param, dict):
        creds = request.param
    else:
        creds = {
            "user": os.getenv("sf_user", getattr(config, "USERNAME")),
            "password": os.getenv("sf_password", getattr(config, "PASSWORD")),
        }
    with allure.step(f"Login as {creds['user']} and switch to lightning"):
        login_page = LoginPage(page)
        login_page.navigate_to(config.BASE_URL)
        sf_home = login_page.login(creds["user"], creds["password"])
        sf_home.switch_to_lightning()
        expect(page.locator(sf_home.home_tab)).to_be_visible()
        return sf_home


@pytest.fixture
def webform_page(sf_home_page: SalesforceHomePage) -> WebFormHomePage:
    sf_home_page.click_app_launcher()
    mailbox_app = sf_home_page.search_and_select_mailbox_app()
    return mailbox_app.search_and_select_webform()


@pytest.fixture
def custom_email_page(mailbox_record_page: MailboxSyncRecordPage) -> CustomEmailPage:
    return mailbox_record_page.click_email_link()


@pytest.fixture()
def sf_admin_page(sf_home_page: SalesforceHomePage) -> SalesforceAdminPage:
    with allure.step("Goto the admin page to do a proxy login"):
        return sf_home_page.go_to_admin_page()


@pytest.fixture
def proxy_user_login(sf_admin_page: SalesforceAdminPage, users, request):
    mapping = users.get("users", {})
    key_or_value = getattr(request, "param", None)
    user_name = mapping.get("Test_User_1")  # sanitized
    if key_or_value:
        user_name = mapping.get(key_or_value, key_or_value)
    if not user_name:
        raise ValueError(f"Proxy user not found for key/value: {key_or_value}")
    return sf_admin_page.proxy_login(user_name)


@pytest.fixture
def mailbox_record_page(proxy_user_login: SalesforceHomePage) -> MailboxSyncRecordPage:
    file = os.path.join("data", "inquiry.json")
    inquiry_id = None
    if os.path.exists(file) and os.path.getsize(file) > 0:
        try:
            with open(file, "r", encoding="utf-8") as f:
                inquiry_id = json.load(f).get("inquiry")
        except Exception:
            pass
    if not inquiry_id:
        raise RuntimeError("No inquiry id found in data/inquiry.json")
    proxy_user_login.switch_to_lightning()
    proxy_user_login.click_app_launcher()
    mailbox_sync_home = proxy_user_login.click_mailbox_sync_tab()
    return mailbox_sync_home.open_record(inquiry_id)


@pytest.fixture
def select_list_view(proxy_mailbox_sync_home_page, common_data, request):
    mapping = common_data.get("list_view_name", {})
    key = getattr(request, "param", None) or "All"
    list_view_name = mapping.get(key, key)
    if not list_view_name:
        raise ValueError(f"List view not found for {key!r}")
    proxy_mailbox_sync_home_page.go_to_list_view(list_view_name)
    return proxy_mailbox_sync_home_page


@pytest.fixture
def record_home(sf_home_page: SalesforceHomePage) -> RecordHomePage:
    with allure.step("Precondition: Open Record module"):
        sf_home_page.click_app_launcher()
        record_home_page = sf_home_page.click_record_module()
        expect(record_home_page.page).to_have_url(
            re.compile(rf"^{re.escape(test_data.record_home_url)}")
        )
    return record_home_page


@pytest.fixture(scope="session")
def record_data():
    with open("data/record_data.json") as f:
        return json.load(f)


@pytest.fixture
def mailbox_app_home_page(sf_home_page: SalesforceHomePage) -> MailboxApp:
    sf_home_page.switch_to_lightning()
    sf_home_page.click_app_launcher()
    return sf_home_page.search_and_select_mailbox_app()


@pytest.fixture
def mailbox_sync_home_page(mailbox_app_home_page: MailboxApp) -> MailboxSyncHomePage:
    return mailbox_app_home_page.click_mailbox_sync_tab()


@pytest.fixture
def proxy_mailbox_sync_home_page(
    proxy_user_login: SalesforceHomePage,
) -> MailboxSyncHomePage:
    proxy_user_login.switch_to_lightning()
    proxy_user_login.click_app_launcher()
    return proxy_user_login.click_mailbox_sync_tab()


@pytest.fixture(scope="function")
def clear_inquiry_key():
    file = Path(__file__).parent / "data" / "inquiry.json"
    if file.exists() and file.stat().st_size > 0:
        try:
            data = json.loads(file.read_text(encoding="utf-8")) or {}
            removed = False
            for k in ("inquiry", "_latest"):
                if k in data:
                    data.pop(k, None)
                    removed = True
            if removed:
                file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print("DEBUG: removed 'inquiry'/_latest from inquiry.json")
        except Exception as e:
            print("DEBUG: clear_inquiry_key fallback:", e)
            try:
                file.unlink()
            except Exception:
                pass
    yield


@pytest.fixture(scope="function")
def get_inquiry_number(request, data) -> str:
    file = os.path.join("data", "inquiry.json")
    if os.path.exists(file) and os.path.getsize(file) > 0:
        try:
            with open(file, "r", encoding="utf-8") as f:
                val = json.load(f).get("inquiry")
                if val:
                    return val
        except json.JSONDecodeError:
            pass

    webform_page = request.getfixturevalue("webform_page")
    inquiry = webform_page.fill_form(data)

    with open(file, "w", encoding="utf-8") as f:
        json.dump({"inquiry": inquiry}, f)
    return inquiry
