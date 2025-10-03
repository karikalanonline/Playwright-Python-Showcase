from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from base.base_page import BasePage
import time, allure


class CustomEmailPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.page = page

    def _debug_nodes(self, selector):
        """Print some debug info for nodes matching selector."""
        nodes = self.page.locator(selector)
        count = nodes.count()
        print(f"DEBUG: selector={selector!r} count={count}")
        for i in range(count):
            n = nodes.nth(i)
            try:
                vis = n.is_visible()
            except Exception:
                vis = "<is_visible-error>"
            try:
                text = n.inner_text(timeout=300).strip()
            except Exception:
                text = "<inner_text-error>"
            print(f"  [{i}] visible={vis} text={repr(text)}")
        return count

    def get_status_value(self, timeout: int = 10_000) -> str:
        """
        Return the 'Email Status' (preferred) or the 'Status' inside the Custom Email area.
        Picks the first *visible* and non-empty node.
        """
        # 1) ensure the view switched to the Custom Email record (URL and anchor label)
        # Wait for the URL or the unique 'Custom Email Number' label to appear.
        try:
            # Wait for the URL pattern -- your click_email_link already calls wait_for_url.
            # Additionally wait for 'Custom Email Number' label to be visible so we know the
            # custom email record is actually displayed.
            self.page.wait_for_selector(
                "span.test-id__field-label:has-text('Custom Email Number')",
                timeout=timeout,
            )
        except PlaywrightTimeoutError:
            # fallback small sleep+debug so tests don't immediately fail intermittently
            time.sleep(1)
            # continue to try; we'll dump nodes if we fail later

        # candidate selectors (most specific first)
        candidates = [
            # explicit Email Status label (preferred)
            "div.slds-form-element:has(span.test-id__field-label:has-text('Email Status')) span.test-id__field-value",
            # explicit Email Status but look inside lightning-formatted-text slot (sometimes used)
            "div.slds-form-element:has(span.test-id__field-label:has-text('Email Status')) slot[name='outputField'] lightning-formatted-text",
            # fallback: within the Custom Email block look for 'Status' value
            "xpath=//span[text()='Custom Email Number']/ancestor::div[contains(@class,'records-record-layout-row') or contains(@class,'slds-grid')][1]//div[contains(@class,'slds-form-element') and .//span[contains(@class,'test-id__field-label') and normalize-space(text())='Status']]//span[contains(@class,'test-id__field-value')]",
            # generic Status (last resort) - but we will only take visible nodes
            "div.slds-form-element:has(span.test-id__field-label:has-text('Status')) span.test-id__field-value",
            # generic value inside slot
            "div.slds-form-element:has(span.test-id__field-label:has-text('Status')) slot[name='outputField'] lightning-formatted-text",
        ]

        # try each candidate selector and return the first visible non-empty inner_text()
        for sel in candidates:
            try:
                nodes = self.page.locator(sel)
                count = nodes.count()
            except Exception:
                count = 0

            if count == 0:
                continue

            for i in range(count):
                node = nodes.nth(i)
                try:
                    if not node.is_visible():
                        # skip hidden nodes (they may be from the earlier page)
                        continue
                except Exception:
                    # if `is_visible` errors, still try to read inner_text but prefer visible
                    pass

                # use inner_text() to get what user sees
                try:
                    txt = node.inner_text(timeout=500).strip()
                except Exception:
                    try:
                        txt = node.text_content(timeout=500) or ""
                        txt = txt.strip()
                    except Exception:
                        txt = ""

                if txt and not txt.lower().startswith("change"):  # skip edit hints
                    return txt

        # nothing found: dump debug info so you can see what's on the page
        print(
            "--- get_status_value: couldn't find visible Status; dumping candidates ---"
        )
        for sel in candidates:
            self._debug_nodes(sel)
        raise AssertionError(
            f"Row for 'Status' not visible within {timeout}ms (url={self.page.url})"
        )

    def assert_email_status(self, expected: str = "Sent"):
        actual = self.get_status_value()
        allure.attach(
            f"Expected: {expected}\nActual: {actual}",
            name="Email Status Verification",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert (
            actual == expected
        ), f"Email status expected '{expected}' but got '{actual}'"
