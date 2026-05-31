"""基于 Scrapling 的智能爬虫封装"""
import logging
from scrapling import Fetcher

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class SmartFetcher:
    """智能爬虫封装，带重试、超时、反检测"""

    def __init__(self, timeout: int = 15, retries: int = 2):
        self.timeout = timeout
        self.retries = retries
        self._fetcher = Fetcher()

    def fetch(self, url: str, headers: dict = None) -> str | None:
        """获取页面 HTML，失败返回 None"""
        all_headers = {**_DEFAULT_HEADERS, **(headers or {})}
        last_error = None

        for attempt in range(self.retries + 1):
            try:
                resp = self._fetcher.get(
                    url,
                    headers=all_headers,
                    timeout=self.timeout,
                )
                if resp and resp.status == 200:
                    return resp.body if hasattr(resp, 'body') else str(resp)
                elif resp:
                    logger.warning(
                        "HTTP %d fetching %s (attempt %d/%d)",
                        resp.status, url, attempt + 1, self.retries + 1,
                    )
                else:
                    logger.warning(
                        "Empty response fetching %s (attempt %d/%d)",
                        url, attempt + 1, self.retries + 1,
                    )
            except Exception as e:
                last_error = e
                logger.debug(
                    "Attempt %d/%d failed for %s: %s",
                    attempt + 1, self.retries + 1, url, e,
                )

        logger.error("Failed to fetch %s after %d attempts: %s", url, self.retries + 1, last_error)
        return None

    def fetch_json(self, url: str, headers: dict = None) -> dict | list | None:
        """获取 JSON 响应"""
        all_headers = {**_DEFAULT_HEADERS, **(headers or {})}
        all_headers["Accept"] = "application/json, text/plain, */*"

        for attempt in range(self.retries + 1):
            try:
                resp = self._fetcher.get(url, headers=all_headers, timeout=self.timeout)
                if resp and resp.status == 200:
                    return resp.json
            except Exception as e:
                logger.debug("JSON fetch attempt %d/%d failed: %s", attempt + 1, self.retries + 1, e)

        return None
