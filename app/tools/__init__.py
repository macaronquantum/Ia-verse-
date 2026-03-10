from app.tools import code_generator, crypto_trader, market_analysis, social_media_poster, web_scraper

TOOL_REGISTRY = {
    "market_analysis": market_analysis.run,
    "web_scraper": web_scraper.run,
    "crypto_trader": crypto_trader.run,
    "social_media_poster": social_media_poster.run,
    "code_generator": code_generator.run,
}
