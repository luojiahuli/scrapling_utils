"""并行抓取调度器 — ThreadPoolExecutor + 合并去重"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .news_sources import NewsItem, get_news_sources_for_market

logger = logging.getLogger(__name__)


def _identity(x): return x


def fetch_all_parallel(
    market: str = "us",
    max_workers: int = 5,
    source_filter: Callable[[str], bool] | None = None,
    max_per_source: int = 10,
) -> list[NewsItem]:
    """并行抓取指定市场的所有新闻源，合并去重"""
    sources = get_news_sources_for_market(market)
    if source_filter:
        sources = [s for s in sources if source_filter(s.name)]

    if not sources:
        logger.warning("No news sources for market=%s after filter", market)
        return []

    all_items: list[NewsItem] = []
    seen_titles: set[str] = set()

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        fut_map = {pool.submit(s.fetch): s for s in sources}

        for fut in as_completed(fut_map):
            src = fut_map[fut]
            try:
                items = fut.result()
                if not items:
                    continue
                count = 0
                for item in items:
                    if not isinstance(item, NewsItem):
                        continue
                    key = item.title.strip().lower()[:50]
                    if key and key not in seen_titles:
                        seen_titles.add(key)
                        all_items.append(item)
                        count += 1
                        if max_per_source and count >= max_per_source:
                            break
                logger.info("[%s] %d items (+%d new)", src.name, len(items), count)
            except Exception as e:
                logger.warning("[%s] fetch failed: %s", src.name, e)

    logger.info("Total unique items for market=%s: %d", market, len(all_items))
    return all_items


def fetch_single_source(source_name: str) -> list[NewsItem]:
    """仅测试用：抓取单个新闻源"""
    for market in ("us", "hk", "cn"):
        for src in get_news_sources_for_market(market):
            if src.name == source_name:
                return src.fetch()
    return []
