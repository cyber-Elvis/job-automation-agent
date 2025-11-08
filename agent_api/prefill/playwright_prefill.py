from playwright.sync_api import sync_playwright

def prefill_and_pause(apply_url: str, ua: str, fields: dict):
    """
    Opens a headed Chromium browser, pre-fills available fields, then pauses.
    You review and submit manually (human-in-the-loop).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(user_agent=ua)
        page = ctx.new_page()
        page.goto(apply_url, wait_until="domcontentloaded")

        # Example selectors (customize per site)
        # if fields.get("name"): page.fill('input[name="name"]', fields["name"])
        # if fields.get("email"): page.fill('input[name="email"]', fields["email"])
        # if fields.get("phone"): page.fill('input[name="phone"]', fields["phone"])
        # if fields.get("resume_path"): page.set_input_files('input[type="file"]', fields["resume_path"])
        # if fields.get("cover_letter"): page.fill('textarea[name="cover_letter"]', fields["cover_letter"])

        page.pause()  # pause for manual review/submit
        browser.close()
