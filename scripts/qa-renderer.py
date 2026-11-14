"""Run against `python -m http.server 5173 --directory electron/dist`.

Uses a fake preload bridge, never the user's actual accounts or Codex process.
Requires Python Playwright and an installed Chromium browser.
"""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:5173")
parser.add_argument("--browser", required=True)
parser.add_argument("--output", default="/tmp/cam-qa")
args = parser.parse_args()
output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parent.parent

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, executable_path=args.browser)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(path=str(root / "electron/tests/fixtures/desktop-bridge.js"))
    page.goto(args.url)
    page.wait_for_load_state("networkidle")
    expect(page.get_by_test_id("profiles-view")).to_be_visible()
    search = page.get_by_role("searchbox", name="Search accounts")
    search.fill("BACKUP@")
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(page.locator("tbody tr")).to_contain_text("backup")
    search.fill("missing-account")
    expect(page.get_by_role("heading", name="No matching accounts")).to_be_visible()
    page.get_by_role("button", name="Clear filters").click()
    expect(page.locator("tbody tr")).to_have_count(2)
    page.get_by_role("button", name="Needs attention", exact=False).click()
    expect(page.get_by_role("heading", name="No matching accounts")).to_be_visible()
    page.get_by_role("button", name="Clear filters").click()
    header = page.locator('th[data-col="profile"]')
    header.focus()
    page.keyboard.press("Enter")
    expect(header).to_have_attribute("aria-sort", "descending")
    page.keyboard.press("Enter")
    expect(header).to_have_attribute("aria-sort", "ascending")
    manage = page.locator(".account-management summary")
    manage.click()
    expect(page.get_by_role("button", name="Import accounts")).to_be_visible()
    page.keyboard.press("Escape")
    expect(manage).to_be_focused()
    expect(page.get_by_role("button", name="Import accounts")).to_be_hidden()
    # Discover the actual rendered controls before operating them.
    (output / "initial-dom.html").write_text(page.content())
    page.screenshot(path=str(output / "profiles-before.png"), full_page=True)
    backup = page.locator("tbody tr").filter(has_text="backup@example.test")
    backup.get_by_role("button", name="Switch to backup", exact=True).click()
    expect(page.locator(".switch-status")).to_be_visible()
    expect(backup.locator(".switch-loading-btn")).to_be_disabled()
    expect(page.get_by_text("Account switched", exact=True)).to_be_visible()
    assert len(page.evaluate("fixture.switchCalls")) == 1
    assert page.evaluate("fixture.switchCalls[0].options.continueWork") is True
    expect(page.locator(".switch-status")).to_have_count(0)
    # Saving a purchase date updates visible rows without a manual refresh.
    backup.locator("[data-row-actions=backup]").click()
    page.get_by_role("button", name="Purchase date / Plus period").click()
    date_input = page.get_by_label("Purchase date", exact=True)
    expect(date_input).to_be_focused()
    page.get_by_role("button", name="Close dialog").focus()
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("button", name="Save", exact=True)).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_have_count(0)
    expect(backup.locator("[data-row-actions=backup]")).to_be_focused()
    backup.locator("[data-row-actions=backup]").click()
    page.get_by_role("button", name="Purchase date / Plus period").click()
    page.get_by_label("Purchase date", exact=True).fill("2026-10-25")
    page.get_by_role("button", name="Save", exact=True).click()
    expect(page.get_by_text("Purchase date saved", exact=True)).to_be_visible()
    expect(backup.locator('[title="2026-11-24"]')).to_be_visible()
    page.screenshot(path=str(output / "purchase-date.png"), full_page=True)
    backup.locator("[data-row-actions=backup]").click()
    page.get_by_role("button", name="Purchase date / Plus period").click()
    expect(date_input).to_have_value("2026-10-25")
    page.keyboard.press("Escape")
    # Optional update/chain failures must not remove usable account controls.
    page.evaluate("fixture.failOptional = true")
    page.get_by_role("button", name="Refresh", exact=True).click()
    expect(backup.locator("[data-row-actions=backup]")).to_be_visible()
    expect(page.locator(".workspace-error")).to_have_count(0)
    # A failed stop is persistent, actionable, and does not claim success.
    page.evaluate("fixture.failSwitch = true")
    work = page.locator("tbody tr").filter(has_text="work@example.test")
    work.get_by_role("button", name="Switch to work", exact=True).click()
    expect(page.locator(".workspace-error")).to_contain_text("Codex is still running")
    expect(work.get_by_role("button", name="Switch to work", exact=True)).to_be_enabled()
    assert page.evaluate("fixture.state.usage.current_profile") == "backup"
    page.screenshot(path=str(output / "switch-error.png"), full_page=True)
    page.get_by_role("button", name="Close error", exact=True).click()
    expect(page.locator(".workspace-error")).to_have_count(0)
    page.set_viewport_size({"width": 940, "height": 640})
    expect(page.locator(".profiles-data-table")).to_be_visible()
    assert page.locator(".profiles-table-wrap").evaluate("el => el.scrollWidth <= el.clientWidth + 2")
    page.screenshot(path=str(output / "compact.png"), full_page=True)
    for width in [600, 400]:
        page.set_viewport_size({"width": width, "height": 760})
        expect(page.get_by_test_id("profiles-mobile-list")).to_be_visible()
        expect(page.locator(".profiles-data-table")).to_be_hidden()
        assert page.locator(".desktop-shell").evaluate("el => el.scrollWidth <= el.clientWidth + 2")
        expect(page.get_by_role("button", name="Switch to work", exact=True)).to_be_visible()
    page.screenshot(path=str(output / "narrow.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.get_by_test_id("topbar-theme-button").click()
    page.get_by_test_id("topbar-theme-button").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    page.screenshot(path=str(output / "light.png"), full_page=True)
    assert not errors, errors
    browser.close()
print("PASS: account search and filters, keyboard sorting, dialog focus, purchase dates, switch feedback, error recovery, and responsive light/dark layouts.")
