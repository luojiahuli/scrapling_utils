"""YAML 配置驱动 — 市场、新闻源、AI 参数"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# ── 默认配置 ──────────────────────────────────────────

DEFAULT_CONFIG: dict[str, Any] = {
    "global": {
        "request_timeout": 15,
        "retries": 2,
        "cache_ttl_minutes": 30,
        "parallel": True,
        "max_workers": 5,
    },
    "markets": {
        "us": {
            "sources": [
                "yahoo_finance", "cnbc", "reuters",
                "finviz", "marketwatch", "barchart", "cailianshe",
            ],
            "max_news_per_source": 10,
        },
        "hk": {
            "sources": ["yahoo_finance", "aastocks", "sina_finance", "cailianshe"],
            "max_news_per_source": 10,
        },
        "cn": {
            "sources": ["sina_finance", "cailianshe", "eastmoney_sector"],
            "max_news_per_source": 10,
        },
    },
    "ai": {
        "enabled": False,
        "provider": "gemini",
        "model": "gemini-2.0-flash-lite",
        "api_key_env": "GEMINI_API_KEY",
        "batch_size": 5,
        "rate_limit_seconds": 7.0,
        "min_score": 0,
    },
    "cache": {
        "backend": "disk",
        "dir": "~/.cache/scrapling_utils",
        "ttl_minutes": 30,
    },
}


def find_config(path: str | Path | None = None) -> Path | None:
    """从指定路径或 CWD 向上查找 config.yaml / config.yml"""
    search = [Path(path)] if path else []
    search.extend([
        Path.cwd() / "config.yaml",
        Path.cwd() / "config.yml",
        Path.cwd() / "scrapling_config.yaml",
        Path.home() / ".config" / "scrapling_utils" / "config.yaml",
    ])
    for p in search:
        if p.is_file():
            return p
    return None


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """加载配置，未找到或解析失败时返回默认值"""
    if yaml is None:
        return DEFAULT_CONFIG

    cfg_path = find_config(path)
    if not cfg_path:
        return DEFAULT_CONFIG

    try:
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return DEFAULT_CONFIG
        return _deep_merge(DEFAULT_CONFIG, raw)
    except Exception:
        return DEFAULT_CONFIG


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并字典"""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def get_env_config() -> dict[str, Any]:
    """环境变量覆盖（最高优先级）"""
    overrides: dict[str, Any] = {}
    if os.getenv("SCRAPLING_TIMEOUT"):
        overrides.setdefault("global", {})["request_timeout"] = int(os.environ["SCRAPLING_TIMEOUT"])
    if os.getenv("SCRAPLING_CACHE_TTL"):
        overrides.setdefault("global", {})["cache_ttl_minutes"] = int(os.environ["SCRAPLING_CACHE_TTL"])
    if os.getenv("GEMINI_API_KEY"):
        overrides.setdefault("ai", {})["enabled"] = True
    return overrides


def get_resolved_config(path: str | Path | None = None) -> dict[str, Any]:
    """合并默认 → 文件 → 环境变量"""
    cfg = load_config(path)
    env_cfg = get_env_config()
    if env_cfg:
        cfg = _deep_merge(cfg, env_cfg)
    cfg["ai"]["api_key"] = os.getenv("GEMINI_API_KEY", "")
    return cfg
