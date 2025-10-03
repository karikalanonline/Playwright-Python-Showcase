import json, re
from playwright.sync_api import Locator, TimeoutError, expect
import logging, allure
from base.base_page import BasePage

# if TYPE_CHECKING:
from pages.custom_email_page import CustomEmailPage  # sanitized file/class name

logger = logging.getLogger(__name__)


class MailboxSyncRecordPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self._by_label = (
            "div.slds-form-element:has(span.test-id__field-label:has-text('{label}'))"
        )
        self.email_link = "h3.slds-tile__title >> a"

    def _value_node(self, label: str) -> Locator:
        selector = self._by_label.format(label=label)

        try:
            self.page.wait_for_selector(selector, timeout=8000)
        except TimeoutError:
            logger.error(
                "Timeout waiting for label container '%s' at URL %s",
                label,
                self.page.url,
            )
            try:
                sample = self.page.locator("div.slds-form-element").first.inner_html()[
                    :2000
                ]
            except Exception:
                sample = "<could-not-read-sample>"
            raise RuntimeError(
                f"Could not find label container for '{label}'. URL: {self.page.url}\n"
                f"Sample nearby HTML: {sample}"
            )

        container = self.page.locator(selector)
        if container.count() == 0:
            found_labels = self.page.locator(
                "span.test-id__field-label"
            ).all_inner_texts()
            raise RuntimeError(
                f"Label container matched zero nodes for selector {selector!r}.\n"
                f"Labels found on page: {found_labels}\n"
                f"URL: {self.page.url}"
            )

        candidates = [
            "slot >> span",
            "span.owner-name",
            ".slds-form-element__control span.test-id__field-value",
            ".slds-form-element__control lightning-formatted-text",
            ".slds-form-element__control .slds-form-element__static",
        ]

        for sel in candidates:
            loc = container.locator(sel)
            count = loc.count()
            if count == 0:
                continue

            for i in range(count):
                node = loc.nth(i)
                try:
                    text = node.inner_text(timeout=500).strip()
                except Exception:
                    text = ""

                if not text:
                    continue
                if text.lower().startswith("change"):
                    continue
                return node

        raise RuntimeError(
            f"Could not find value node for field label '{label}'. Container HTML: {container.first.inner_html()[:2000]}"
        )

    def assert_case_details(self, expected: dict):
        actual = {}

        for field in expected:
            try:
                node = self._value_node(field)
                actual_value = node.inner_text().strip()
            except Exception as e:
                actual_value = f"<not-found: {e}>"
            actual[field] = actual_value

        try:
            payload = json.dumps(
                {"expected": expected, "actual": actual}, indent=2, ensure_ascii=False
            )
            allure.attach(
                payload,
                name="case details - expected vs actual",
                attachment_type=allure.attachment_type.JSON,
            )
        except Exception:
            pass

        for field, expected_value in expected.items():
            node = self._value_node(field)
            expect(node).to_have_text(expected_value)

    def click_email_link(self, timeout: int = 20_000) -> CustomEmailPage:
        self.page.locator(self.email_link, has_text="EMAIL").click()

        # Sanitize: generic object name instead of Custom_Email_2__c
        pattern = re.compile(r".*/lightning/r/Email__c/.*")
        try:
            self.page.wait_for_url(pattern, timeout=8_000)
        except Exception:
            pass

        unique_selectors = [
            "span.test-id__field-label:has-text('Email Number')",  # sanitized
            "span.test-id__field-label:has-text('Email Status')",
            "h1:has-text('Email'), h1:has-text('Custom Email')",
        ]

        for sel in unique_selectors:
            try:
                self.page.locator(sel).first.wait_for(state="attached", timeout=4000)
                break
            except Exception:
                continue

        try:
            self.page.wait_for_load_state("networkidle", timeout=3_000)
        except Exception:
            pass

        return CustomEmailPage(self.page)
