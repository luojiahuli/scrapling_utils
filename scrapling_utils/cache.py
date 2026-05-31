"""内容哈希缓存 — SHA-256 + TTL，自动失效"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

_HASH_CHUNK_SIZE = 65536


def _content_hash(data: str | bytes) -> str:
    """计算内容 SHA-256"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _default_cache_dir() -> Path:
    base = Path(os.getenv("SCRAPLING_CACHE_DIR", Path.home() / ".cache" / "scrapling_utils"))
    base.mkdir(parents=True, exist_ok=True)
    return base


class ContentHashCache:
    """内容哈希缓存 — 用于新闻去重和避免重复处理"""

    def __init__(self, cache_dir: str | Path | None = None, ttl_minutes: int = 30):
        self._dir = Path(cache_dir) if cache_dir else _default_cache_dir()
        self._ttl = ttl_minutes * 60
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> Any | None:
        """获取缓存，过期返回 None"""
        p = self._path(key)
        if not p.is_file():
            return None
        try:
            entry = json.loads(p.read_text(encoding="utf-8"))
            if time.time() - entry.get("ts", 0) > self._ttl:
                p.unlink(missing_ok=True)
                return None
            return entry.get("data")
        except Exception:
            return None

    def set(self, key: str, data: Any) -> None:
        """写入缓存"""
        entry = {"ts": time.time(), "data": data}
        self._path(key).write_text(json.dumps(entry, ensure_ascii=False, default=str), encoding="utf-8")

    def url_key(self, url: str) -> str:
        """用 URL 生成缓存 key"""
        return _content_hash(url)

    def content_key(self, content: str) -> str:
        """用内容生成缓存 key"""
        return _content_hash(content)

    def clear_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        now = time.time()
        count = 0
        for f in self._dir.glob("*.json"):
            try:
                entry = json.loads(f.read_text(encoding="utf-8"))
                if now - entry.get("ts", 0) > self._ttl:
                    f.unlink()
                    count += 1
            except Exception:
                f.unlink()
                count += 1
        return count

    def clear_all(self) -> int:
        """清空所有缓存"""
        count = 0
        for f in self._dir.glob("*.json"):
            f.unlink()
            count += 1
        return count
