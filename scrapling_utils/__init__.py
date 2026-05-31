"""Scrapling 爬虫工具包 — 跨项目复用"""

from .cache import ContentHashCache
from .config import get_resolved_config, load_config
from .enricher import (
    classify_by_keywords,
    classify_by_llm,
    classify_sectors,
    get_keywords,
)
from .fetcher import SmartFetcher
from .news_sources import (
    AASTOCKSNews,
    BarchartNews,
    CNBCNews,
    CailiansheNews,
    EastMoneySectorNews,
    FinvizNews,
    MarketWatchNews,
    NewsItem,
    NewsSource,
    ReutersNews,
    SinaFinanceNews,
    YahooFinanceNews,
    fetch_all_news,
    get_news_sources_for_market,
)
from .parallel import fetch_all_parallel, fetch_single_source

__all__ = [
    # fetcher
    "SmartFetcher",
    # news sources
    "NewsItem",
    "NewsSource",
    "YahooFinanceNews",
    "CNBCNews",
    "ReutersNews",
    "FinvizNews",
    "MarketWatchNews",
    "BarchartNews",
    "AASTOCKSNews",
    "CailiansheNews",
    "SinaFinanceNews",
    "EastMoneySectorNews",
    "get_news_sources_for_market",
    "fetch_all_news",
    # parallel
    "fetch_all_parallel",
    "fetch_single_source",
    # cache
    "ContentHashCache",
    # config
    "load_config",
    "get_resolved_config",
    # enricher
    "classify_by_keywords",
    "classify_by_llm",
    "classify_sectors",
    "get_keywords",
]
