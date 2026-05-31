"""多市场新闻源爬虫 — 基于 Scrapling"""
import logging
import re
from scrapling import Selector

from .fetcher import SmartFetcher

logger = logging.getLogger(__name__)


class NewsItem:
    """单条新闻"""
    __slots__ = ("title", "content", "url", "source", "sectors")

    def __init__(self, title: str = "", content: str = "", url: str = "",
                 source: str = "", sectors: list[str] = None):
        self.title = title
        self.content = content
        self.url = url
        self.source = source
        self.sectors = sectors or []

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content or self.title,
            "url": self.url,
            "source": self.source,
        }


class NewsSource:
    """新闻源基类"""
    name = "base"
    market = "all"  # "hk", "us", "cn", "all"

    def __init__(self):
        self.fetcher = SmartFetcher()

    def fetch(self) -> list[NewsItem]:
        raise NotImplementedError

    @staticmethod
    def _text(el) -> str:
        """安全提取元素文本"""
        if el is None:
            return ""
        return (el.text or "").strip()

    @staticmethod
    def _attr(el, key: str) -> str:
        """安全提取元素属性"""
        if el is None:
            return ""
        return (el.attrib or {}).get(key, "")

    @staticmethod
    def _abs_url(base: str, path: str) -> str:
        """拼接绝对 URL"""
        if not path:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = base.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"


# ── 美股源 ────────────────────────────────────────────

class YahooFinanceNews(NewsSource):
    """Yahoo Finance 新闻"""
    name = "yahoo_finance"
    market = "all"

    def fetch(self) -> list[NewsItem]:
        items = []
        for url in [
            "https://finance.yahoo.com/news/",
            "https://finance.yahoo.com/topic/stock-market-news/",
        ]:
            try:
                html = self.fetcher.fetch(url)
                if not html:
                    continue
                sel = Selector(html)
                for article in sel.css("li.stream-item, div.js-stream-content"):
                    title_el = article.css("h3").first
                    link_el = article.css("a").first
                    if not title_el:
                        continue
                    items.append(NewsItem(
                        title=self._text(title_el),
                        url=self._abs_url("https://finance.yahoo.com", self._attr(link_el, "href")),
                        source="yahoo_finance",
                    ))
                if items:
                    break
            except Exception as e:
                logger.debug("YahooFinance error: %s", e)
        return items[:15]


class CNBCNews(NewsSource):
    """CNBC 市场新闻"""
    name = "cnbc"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://www.cnbc.com/markets/")
            if not html:
                return []
            sel = Selector(html)
            items = []
            for article in sel.css("div.Card-titleContainer, a.Card"):
                title_el = article.css("h3, span.Card-eyebrow, div.Card-title").first
                link = article if article.tag == "a" else article.css("a").first
                if title_el:
                    items.append(NewsItem(
                        title=self._text(title_el),
                        url=self._abs_url("https://www.cnbc.com", self._attr(link, "href")),
                        source="cnbc",
                    ))
            return items[:10]
        except Exception as e:
            logger.debug("CNBC error: %s", e)
            return []


class ReutersNews(NewsSource):
    """Reuters 市场新闻"""
    name = "reuters"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://www.reuters.com/markets/")
            if not html:
                return []
            sel = Selector(html)
            items = []
            for article in sel.css("a[data-testid='Heading'], div[data-testid='Story']"):
                title_el = article.css("span, h2, h3").first
                if title_el:
                    items.append(NewsItem(
                        title=self._text(title_el),
                        url=self._abs_url("https://www.reuters.com", self._attr(article, "href")),
                        source="reuters",
                    ))
            return items[:10]
        except Exception as e:
            logger.debug("Reuters error: %s", e)
            return []


class FinvizNews(NewsSource):
    """Finviz 新闻聚合"""
    name = "finviz"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://finviz.com/news.ashx")
            if not html:
                return []
            sel = Selector(html)
            items = []
            for row in sel.css("table[bgcolor='#d9e0e8'] tr, table.ttable tr"):
                cells = row.css("td")
                if cells.length < 2:
                    continue
                link = cells.first.css("a").first
                if link:
                    items.append(NewsItem(
                        title=self._text(link),
                        url=self._attr(link, "href"),
                        source="finviz",
                    ))
            return items[:15]
        except Exception as e:
            logger.debug("Finviz error: %s", e)
            return []


class MarketWatchNews(NewsSource):
    """MarketWatch 最新新闻"""
    name = "marketwatch"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://www.marketwatch.com/latest-news")
            if not html:
                return []
            sel = Selector(html)
            items = []
            for article in sel.css("div.article__content"):
                title_el = article.css("h3.article__title a, a.article__title").first
                if title_el:
                    items.append(NewsItem(
                        title=self._text(title_el),
                        url=self._abs_url("https://www.marketwatch.com", self._attr(title_el, "href")),
                        source="marketwatch",
                    ))
            return items[:10]
        except Exception as e:
            logger.debug("MarketWatch error: %s", e)
            return []


# ── 港股源 ────────────────────────────────────────────

class AASTOCKSNews(NewsSource):
    """AASTOCKS 港股新闻"""
    name = "aastocks"
    market = "hk"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://www.aastocks.com/en/stocks/news/all-stock-news")
            if not html:
                return []
            sel = Selector(html)
            items = []
            for article in sel.css("div.news-item, div.news_list a, a[href*='news']"):
                title_el = article.css("span, div.title, div.news-title").first or article
                if self._text(title_el) and len(self._text(title_el)) > 5:
                    items.append(NewsItem(
                        title=self._text(title_el),
                        url=self._abs_url("https://www.aastocks.com", self._attr(article, "href")),
                        source="aastocks",
                    ))
            return items[:10]
        except Exception as e:
            logger.debug("AASTOCKS error: %s", e)
            return []


class SinaFinanceNews(NewsSource):
    """新浪财经港股新闻"""
    name = "sina_finance"
    market = "hk"

    def fetch(self) -> list[NewsItem]:
        try:
            data = self.fetcher.fetch_json(
                "https://feed.mix.sina.com.cn/api/roll/get"
                "?pageid=163&lid=0&num=10&versionNumber=1.2.4"
            )
            if not data:
                return []
            items = []
            entries = []
            if isinstance(data, dict):
                entries = (data.get("result", {}) or {}).get("data", []) or []
            for entry in entries:
                if isinstance(entry, dict):
                    items.append(NewsItem(
                        title=entry.get("title", ""),
                        content=entry.get("intro", ""),
                        url=entry.get("url", ""),
                        source="sina_finance",
                    ))
            return items
        except Exception as e:
            logger.debug("SinaFinance error: %s", e)
            return []


# ── 通用中文源 ────────────────────────────────────────

class CailiansheNews(NewsSource):
    """财联社电报"""
    name = "cailianshe"
    market = "all"

    def fetch(self) -> list[NewsItem]:
        try:
            data = self.fetcher.fetch_json("https://www.cls.cn/api/telegraph?category=all&limit=10")
            if not data:
                return []
            items = []
            entries = []
            if isinstance(data, dict):
                entries = data.get("data", []) or []
            for entry in entries:
                if isinstance(entry, dict):
                    items.append(NewsItem(
                        title=entry.get("title", "") or entry.get("content", ""),
                        content=entry.get("content", ""),
                        url=f"https://www.cls.cn/detail/{entry.get('id', '')}",
                        source="cailianshe",
                    ))
            return items
        except Exception as e:
            logger.debug("Cailianshe error: %s", e)
            return []


# ── 工厂函数 ──────────────────────────────────────────

_MARKET_SOURCES: dict[str, list[type[NewsSource]]] = {
    "us": [YahooFinanceNews, CNBCNews, ReutersNews, FinvizNews, MarketWatchNews, CailiansheNews],
    "hk": [YahooFinanceNews, AASTOCKSNews, SinaFinanceNews, CailiansheNews],
    "cn": [YahooFinanceNews, CailiansheNews, SinaFinanceNews],
}


def get_news_sources_for_market(market: str) -> list[NewsSource]:
    """获取指定市场的所有新闻源实例"""
    classes = _MARKET_SOURCES.get(market, [])
    return [cls() for cls in classes]


def fetch_all_news(market: str = "us") -> list[NewsItem]:
    """从指定市场的所有新闻源获取新闻"""
    all_items: list[NewsItem] = []
    seen_titles: set[str] = set()

    for source in get_news_sources_for_market(market):
        try:
            items = source.fetch()
            for item in items:
                key = item.title.strip().lower()[:40]
                if key and key not in seen_titles:
                    seen_titles.add(key)
                    all_items.append(item)
        except Exception as e:
            logger.warning("Source %s failed: %s", source.name, e)

    return all_items
