from app.sensing.web_crawler import CrawlPolicy, WebCrawler
from app.sensing.web_trends import SensingBus


def test_web_crawler_extracts_trends() -> None:
    bus = SensingBus()
    crawler = WebCrawler(bus, CrawlPolicy(per_domain_limit=3, allowed_domains=["local.dev"]))
    events = crawler.crawl([
        {"url": "https://local.dev/a", "html": "new launch trend"},
        {"url": "https://local.dev/b", "html": "developer repo trend"},
    ])
    assert len(events) == 2
    assert events[0]["source"] == "web_crawler"
