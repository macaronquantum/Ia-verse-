import asyncio

import pytest

from app.web.browser_agent import BrowserAgent


def test_browser_fill_form_requires_url():
    agent = BrowserAgent()

    async def run():
        with pytest.raises(ValueError):
            await agent.fill_form("form", {"input": "x"})

    asyncio.run(run())
