"""Fetch rendered HTML from a URL using Playwright and print it."""
import sys
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

url = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Usage: python fetch.py <url>")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="pt-PT",
        viewport={"width": 1280, "height": 800},
    )
    page = ctx.new_page()
    Stealth().apply_stealth_sync(page)
    page.goto(url, wait_until="load", timeout=30_000)
    page.wait_for_timeout(5_000)
    try:
        page.wait_for_selector("text=Detalhes de voo", timeout=30_000)
    except Exception as e:
        print(f"WARNING: {e}", file=__import__('sys').stderr)
    print(page.content())
    browser.close()
