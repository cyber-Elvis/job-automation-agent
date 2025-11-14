import os
from playwright.sync_api import sync_playwright


def prefill_and_pause(apply_url: str, ua: str, fields: dict):
    """
    Prefill fields on an application page and optionally pause.

    In container environments we default to headless mode. Set
    PREFILL_HEADLESS=0 in the environment to run headed (if you have GUI).
    """
    # Default to headless in Docker; you can override by setting PREFILL_HEADLESS=0
    headless = os.getenv("PREFILL_HEADLESS", "1") == "1"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(user_agent=ua)
        page = ctx.new_page()
        page.goto(apply_url, wait_until="domcontentloaded")

        # Generic best-effort fills — selectors are intentionally permissive.
        if fields.get("name"):
            try:
                page.fill('input[name*="name" i]', fields["name"])
            except Exception:
                pass
        if fields.get("email"):
            try:
                page.fill('input[type="email"]', fields["email"])
            except Exception:
                pass
        if fields.get("phone"):
            try:
                page.fill('input[type="tel"]', fields["phone"])
            except Exception:
                pass
        if fields.get("resume_path"):
            try:
                page.set_input_files('input[type="file"]', fields["resume_path"])
            except Exception:
                pass
        if fields.get("cover_letter"):
            try:
                page.fill('textarea[name*="cover" i]', fields["cover_letter"])
            except Exception:
                pass

        # In headless mode we cannot interactively pause; allow a short delay
        # so any async JS runs and uploads settle.
        page.wait_for_timeout(2000)

        browser.close()
