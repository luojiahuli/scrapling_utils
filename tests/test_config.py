"""测试 config.py"""
from scrapling_utils.config import get_resolved_config, load_config, DEFAULT_CONFIG


class TestConfig:
    def test_default_config(self):
        cfg = load_config("/nonexistent/path/config.yaml")
        assert "global" in cfg
        assert "markets" in cfg
        assert "ai" in cfg
        assert "cache" in cfg
        assert cfg["global"]["request_timeout"] == 15
        assert cfg["global"]["cache_ttl_minutes"] == 30

    def test_default_markets(self):
        cfg = load_config("/nonexistent/path/config.yaml")
        markets = cfg["markets"]
        assert "us" in markets
        assert "hk" in markets
        assert "cn" in markets
        assert "yahoo_finance" in markets["us"]["sources"]

    def test_resolved_config_defaults(self):
        cfg = get_resolved_config("/nonexistent/path/config.yaml")
        assert cfg["ai"]["enabled"] is False

    def test_default_contains_all_sections(self):
        assert "global" in DEFAULT_CONFIG
        assert "markets" in DEFAULT_CONFIG
        assert "ai" in DEFAULT_CONFIG
        assert "cache" in DEFAULT_CONFIG

    def test_global_defaults(self):
        g = DEFAULT_CONFIG["global"]
        assert g["request_timeout"] == 15
        assert g["retries"] == 2
        assert g["cache_ttl_minutes"] == 30
        assert g["parallel"] is True
        assert g["max_workers"] == 5
