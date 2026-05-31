"""多市场新闻源爬虫 — Scrapling 引擎 + 正则回溯"""
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
        self.content = content or title
        self.url = url
        self.source = source
        self.sectors = sectors or []

    def to_dict(self) -> dict:
        return {"title": self.title, "content": self.content, "url": self.url, "source": self.source}


class NewsSource:
    """新闻源基类"""
    name = "base"
    market = "all"

    def __init__(self):
        self.fetcher = SmartFetcher()

    def fetch(self) -> list[NewsItem]:
        raise NotImplementedError

    @staticmethod
    def _extract_regex(html: str, pattern: str, min_len: int = 1) -> list[str]:
        """正则提取 + 清理 HTML 标签"""
        matches = re.findall(pattern, html, re.DOTALL)
        results = []
        for m in matches:
            clean = re.sub(r'<.*?>', '', m).strip()
            if clean and len(clean) >= min_len:
                results.append(clean)
        return results

    @staticmethod
    def _text(el) -> str:
        if el is None:
            return ""
        return (el.text or "").strip()

    @staticmethod
    def _attr(el, key: str) -> str:
        if el is None:
            return ""
        return (el.attrib or {}).get(key, "") or ""

    @staticmethod
    def _abs_url(base: str, path: str) -> str:
        if not path:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = base.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"


# ── 美股源 ────────────────────────────────────────────

class YahooFinanceNews(NewsSource):
    """Yahoo Finance 新闻（CSS + 正则 fallback）"""
    name = "yahoo_finance"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        for url in [
            "https://finance.yahoo.com/news/",
            "https://finance.yahoo.com/topic/stock-market-news/",
        ]:
            try:
                html = self.fetcher.fetch(url)
                if not html:
                    continue
                sel = Selector(html)
                items = []
                # CSS 提取
                for h3 in sel.css("h3"):
                    title = self._text(h3)
                    if title and len(title) > 10:
                        items.append(NewsItem(title=title, source=self.name))
                if items:
                    return items[:15]
                # Fallback: 正则
                titles = self._extract_regex(html, r'<h3[^>]*>(.*?)</h3>', 10)
                for t in titles[:15]:
                    items.append(NewsItem(title=t, source=self.name))
                if items:
                    return items
            except Exception as e:
                logger.debug("YahooFinance error: %s", e)
        return []


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
            # CSS: card titles
            for el in sel.css("a.Card-title, div.Card-titleContainer a"):
                title = self._text(el)
                if title and len(title) > 10:
                    items.append(NewsItem(title=title, url=self._abs_url("https://www.cnbc.com", self._attr(el, "href")), source=self.name))
            if items:
                return items[:10]
            # Regex fallback
            titles = self._extract_regex(html, r'<a[^>]*class="Card-title"[^>]*>(.*?)</a>', 10)
            for t in titles[:10]:
                items.append(NewsItem(title=t, source=self.name))
            return items
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
            for el in sel.css("h2, h3, h4"):
                title = self._text(el)
                if title and len(title) > 20:
                    link = el.css("a").first
                    items.append(NewsItem(title=title, url=self._abs_url("https://www.reuters.com", self._attr(link, "href")), source=self.name))
            if items:
                return items[:10]
            # Regex fallback
            titles = self._extract_regex(html, r'<h[2-4][^>]*>(.*?)</h[2-4]>', 20)
            for t in titles[:10]:
                items.append(NewsItem(title=t, source=self.name))
            return items
        except Exception as e:
            logger.debug("Reuters error: %s", e)
            return []


class FinvizNews(NewsSource):
    """Finviz 新闻聚合"""
    name = "finviz"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://finviz.com/news.ashx",
                                      headers={"Referer": "https://finviz.com/"})
            if not html:
                return []
            # Regex only (Finviz uses complex nested tables)
            titles = self._extract_regex(html, r'<a[^>]*class="nn-tab-link"[^>]*>(.*?)</a>', 5)
            items = [NewsItem(title=t, source=self.name) for t in titles[:15]]
            return items
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
            for el in sel.css("h3.article__title a, a.article__title"):
                title = self._text(el)
                if title and len(title) > 10:
                    items.append(NewsItem(title=title, url=self._abs_url("https://www.marketwatch.com", self._attr(el, "href")), source=self.name))
            if items:
                return items[:10]
            # Regex fallbacks
            titles = self._extract_regex(html, r'<h[2-4][^>]*class="article__headline"[^>]*>(.*?)</h[2-4]>', 10)
            if not titles:
                titles = self._extract_regex(html, r'<a[^>]*class="link"[^>]*>(.*?)</a>', 10)
            for t in titles[:10]:
                items.append(NewsItem(title=t, source=self.name))
            return items
        except Exception as e:
            logger.debug("MarketWatch error: %s", e)
            return []


class BarchartNews(NewsSource):
    """Barchart 市场新闻（备用）"""
    name = "barchart"
    market = "us"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://www.barchart.com/news")
            if not html:
                return []
            titles = self._extract_regex(html, r'<a[^>]*class="article-title"[^>]*>(.*?)</a>', 10)
            return [NewsItem(title=t, source=self.name) for t in titles[:10]]
        except Exception:
            return []


# ── 港股源 ────────────────────────────────────────────

class AASTOCKSNews(NewsSource):
    """AASTOCKS 港股新闻"""
    name = "aastocks"
    market = "hk"

    def fetch(self) -> list[NewsItem]:
        try:
            html = self.fetcher.fetch("https://www.aastocks.com/en/stocks/market/news.aspx",
                                      headers={"Referer": "https://www.aastocks.com/"})
            if not html:
                return []
            # Regex: AASTOCKS uses class="news" links
            titles = self._extract_regex(html, r'<a[^>]*class="news"[^>]*>(.*?)</a>', 5)
            return [NewsItem(title=t, source=self.name) for t in titles[:10]]
        except Exception as e:
            logger.debug("AASTOCKS error: %s", e)
            return []


class SinaFinanceNews(NewsSource):
    """新浪财经新闻（JSON API）"""
    name = "sina_finance"
    market = "cn"

    def fetch(self, lid: str = "2516") -> list[NewsItem]:
        """lid: 2516=A股, 2515=港股"""
        try:
            data = self.fetcher.fetch_json(
                "https://feed.mix.sina.com.cn/api/roll/get",
                params={"pageid": "153", "lid": lid, "k": "", "num": "10", "page": "1"},
            )
            if not data:
                return []
            items = []
            for entry in (data.get("result", {}) or {}).get("data", []) or []:
                title = (entry.get("title") or "").strip()
                if title:
                    items.append(NewsItem(
                        title=title,
                        content=(entry.get("intro") or title)[:200],
                        url=entry.get("url", ""),
                        source=self.name,
                    ))
            return items
        except Exception as e:
            logger.debug("SinaFinance error: %s", e)
            return []


# ── 通用中文源 ────────────────────────────────────────

class CailiansheNews(NewsSource):
    """财联社电报"""
    name = "cailianshe"
    market = "cn"

    def fetch(self) -> list[NewsItem]:
        try:
            data = self.fetcher.fetch_json(
                "https://www.cls.cn/api/telegraph",
                params={"category": "1", "limit": "10"},
                headers={"Referer": "https://www.cls.cn/"},
            )
            if not data:
                return []
            items = []
            for roll in (data.get("data", {}) or {}).get("roll_data", []) or []:
                title = (roll.get("title") or roll.get("content") or "").strip()
                if title:
                    items.append(NewsItem(
                        title=title,
                        content=(roll.get("content") or title)[:200],
                        url=f"https://www.cls.cn/detail/{roll.get('id', '')}",
                        source=self.name,
                    ))
            return items
        except Exception as e:
            logger.debug("Cailianshe error: %s", e)
            return []


class EastMoneySectorNews(NewsSource):
    """东方财富概念板块热度"""
    name = "eastmoney_sector"
    market = "cn"

    def fetch(self) -> list[dict]:
        """返回板块热度（非新闻，直接返回 sector dict）"""
        try:
            data = self.fetcher.fetch_json(
                "https://push2.eastmoney.com/api/qt/clist/get",
                params={
                    "pn": "1", "pz": "20", "po": "1", "np": "1",
                    "fltt": "2", "invt": "2", "fid": "f3",
                    "fs": "m:90+t:2",
                    "fields": "f12,f14,f3",
                },
            )
            if not data:
                return []
            sectors = []
            for item in (data.get("data", {}) or {}).get("diff", []) or []:
                name = item.get("f14", "")
                change = item.get("f3", 0)
                if name and change is not None:
                    sectors.append({
                        "sector": name,
                        "heat_score": round(float(change) * 10 + 60, 1),
                        "summary": f"涨幅{change}%",
                        "stocks": [],
                    })
            sectors.sort(key=lambda x: -x["heat_score"])
            return sectors[:10]
        except Exception as e:
            logger.debug("EastMoneySector error: %s", e)
            return []


# ── 工厂函数 ──────────────────────────────────────────

_MARKET_SOURCES: dict[str, list[type[NewsSource]]] = {
    "us": [YahooFinanceNews, CNBCNews, ReutersNews, FinvizNews, MarketWatchNews, BarchartNews, CailiansheNews],
    "hk": [YahooFinanceNews, AASTOCKSNews, SinaFinanceNews, CailiansheNews],
    "cn": [SinaFinanceNews, CailiansheNews, EastMoneySectorNews],
}


def get_news_sources_for_market(market: str) -> list[NewsSource]:
    """获取指定市场的所有新闻源实例"""
    classes = _MARKET_SOURCES.get(market, [])
    return [cls() for cls in classes]


def fetch_all_news(market: str = "us") -> list[NewsItem]:
    """从指定市场的所有新闻源获取新闻（自动去重）"""
    all_items: list[NewsItem] = []
    seen_titles: set[str] = set()

    for source in get_news_sources_for_market(market):
        try:
            items = source.fetch()
            for item in items:
                if isinstance(item, NewsItem):
                    key = item.title.strip().lower()[:50]
                    if key and key not in seen_titles:
                        seen_titles.add(key)
                        all_items.append(item)
        except Exception as e:
            logger.warning("Source %s failed: %s", source.name, e)

    return all_items
