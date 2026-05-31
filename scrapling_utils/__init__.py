"""Scrapling 爬虫工具包 — 跨项目复用"""

from .fetcher import SmartFetcher
from .news_sources import (
    NewsItem,
    NewsSource,
    YahooFinanceNews,
    CNBCNews,
    ReutersNews,
    FinvizNews,
    MarketWatchNews,
    AASTOCKSNews,
    CailiansheNews,
    SinaFinanceNews,
    get_news_sources_for_market,
    fetch_all_news,
)

__all__ = [
    "SmartFetcher",
    "NewsItem",
    "NewsSource",
    "YahooFinanceNews",
    "CNBCNews",
    "ReutersNews",
    "FinvizNews",
    "MarketWatchNews",
    "AASTOCKSNews",
    "CailiansheNews",
    "SinaFinanceNews",
    "get_news_sources_for_market",
    "fetch_all_news",
]
