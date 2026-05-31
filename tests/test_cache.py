"""测试 cache.py"""
import tempfile
from pathlib import Path

from scrapling_utils import ContentHashCache


class TestContentHashCache:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.cache = ContentHashCache(cache_dir=self.tmp, ttl_minutes=60)

    def test_set_and_get(self):
        self.cache.set("test_key", {"hello": "world"})
        result = self.cache.get("test_key")
        assert result == {"hello": "world"}

    def test_missing_key(self):
        assert self.cache.get("nonexistent") is None

    def test_cache_expiry(self):
        short_cache = ContentHashCache(cache_dir=self.tmp, ttl_minutes=0)
        short_cache.set("expire_soon", "data")
        result = short_cache.get("expire_soon")
        assert result is None  # TTL=0 → expired immediately

    def test_url_key(self):
        k1 = self.cache.url_key("https://example.com/news/1")
        k2 = self.cache.url_key("https://example.com/news/2")
        assert k1 != k2
        assert len(k1) == 64  # SHA-256 hexdigest

    def test_content_key(self):
        k1 = self.cache.content_key("some news content")
        k2 = self.cache.content_key("different content")
        assert k1 != k2

    def test_clear_expired(self):
        self.cache.set("keep", "data")
        # create a file with an old timestamp manually
        import time, json
        old_file = Path(self.tmp) / "old_entry.json"
        old_file.write_text(json.dumps({"ts": time.time() - 7200, "data": "old"}), encoding="utf-8")
        count = self.cache.clear_expired()
        assert count >= 1
        assert not old_file.exists()
        assert self.cache.get("keep") == "data"  # still valid

    def test_clear_all(self):
        self.cache.set("a", 1)
        self.cache.set("b", 2)
        assert self.cache.clear_all() == 2
        assert self.cache.get("a") is None
