from __future__ import annotations

import httpx
from bs4 import BeautifulSoup


def run(params: dict) -> dict:
    url = params["url"]
    response = httpx.get(url, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")
    return {"url": url, "title": soup.title.string if soup.title else "", "links": [a.get("href") for a in soup.select("a[href]")[:20]]}
