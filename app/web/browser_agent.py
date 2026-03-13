from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.async_api import async_playwright


@dataclass
class BrowserAgent:
    headless: bool = True

    async def create_account(self, url: str, fields: dict[str, Any]) -> dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            for selector, value in fields.items():
                await page.fill(selector, str(value))
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1500)
            snapshot = await page.content()
            await browser.close()
            return {"status": "submitted", "action": "create_account", "url": url, "html": snapshot[:500]}

    async def navigate(self, url: str) -> dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            response = await page.goto(url, wait_until="domcontentloaded")
            title = await page.title()
            await browser.close()
            return {"status": "ok", "action": "navigate", "url": url, "http_status": response.status if response else None, "title": title}

    async def fill_form(self, form_selector: str, fields: dict[str, Any], url: str | None = None) -> dict[str, Any]:
        if not url:
            raise ValueError("url is required for fill_form")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            for selector, value in fields.items():
                await page.locator(form_selector).locator(selector).fill(str(value))
            await page.locator(form_selector).evaluate("form => form.submit()")
            await page.wait_for_timeout(1000)
            await browser.close()
            return {"status": "submitted", "action": "fill_form", "form_selector": form_selector}

    async def post_content(self, url: str, content: str, input_selector: str = "textarea") -> dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            await page.fill(input_selector, content)
            await page.keyboard.press("Control+Enter")
            await page.wait_for_timeout(1200)
            await browser.close()
            return {"status": "posted", "action": "post_content", "url": url}

    async def gather_data(self, url: str, schema: dict[str, Any]) -> dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            rows = []
            for field, selector in schema.items():
                values = await page.locator(str(selector)).all_text_contents()
                rows.append({"field": field, "values": values})
            await browser.close()
            return {"status": "ok", "action": "gather_data", "url": url, "rows": rows}
