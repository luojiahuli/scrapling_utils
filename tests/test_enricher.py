"""测试 enricher.py"""
from scrapling_utils import (
    classify_by_keywords,
    classify_sectors,
    get_keywords,
)


class TestEnricher:
    def test_get_keywords_cn(self):
        kws = get_keywords("cn")
        assert "人工智能" in kws
        assert "半导体" in kws

    def test_get_keywords_us(self):
        kws = get_keywords("us")
        assert "科技" in kws
        assert "医疗保健" in kws

    def test_get_keywords_hk(self):
        kws = get_keywords("hk")
        assert "科技" in kws
        assert "金融" in kws

    def test_classify_by_keywords_cn(self):
        texts = [
            "AI大模型推动科技发展，算力需求爆发",
            "半导体芯片行业迎来新一轮增长周期",
            "新能源车销量创历史新高",
        ]
        result = classify_by_keywords(texts, market="cn")
        assert len(result) > 0
        sectors = [r["sector"] for r in result]
        assert "人工智能" in sectors or "新能源" in sectors or "半导体" in sectors
        for r in result:
            assert "heat_score" in r
            assert 0 <= r["heat_score"] <= 100

    def test_classify_by_keywords_us(self):
        texts = [
            "Technology stocks rally on AI optimism",
            "Fed keeps rates steady at March meeting",
        ]
        result = classify_by_keywords(texts, market="us")
        assert len(result) > 0
        for r in result:
            assert "heat_score" in r

    def test_classify_by_keywords_hk(self):
        texts = [
            "科技股反弹，腾讯美团领涨",
            "新能源汽车销量持续攀升",
        ]
        result = classify_by_keywords(texts, market="hk")
        assert len(result) > 0
        for r in result:
            assert "heat_score" in r

    def test_classify_by_keywords_empty(self):
        result = classify_by_keywords([], market="cn")
        assert result == []

    def test_classify_by_keywords_no_match(self):
        result = classify_by_keywords(["zzzzyyyyxxxwwww"], market="cn")
        assert result == []

    def test_classify_sectors_keyword_only(self):
        texts = ["人工智能快速发展，芯片需求旺盛"]
        result = classify_sectors(texts, market="cn", use_llm=False)
        assert len(result) > 0
        for r in result:
            assert r.get("source") in ("keyword",)

    def test_classify_sectors_no_llm_fallback(self):
        """无 API key 时自动 fallback 到纯关键词"""
        texts = ["AI推动科技发展"]
        result = classify_sectors(texts, market="cn", api_key="", use_llm=True)
        assert len(result) > 0
        # without valid key, LLM path silently returns keyword-only

    def test_sectors_sort_by_heat(self):
        texts = [
            "人工智能大模型爆发，算力需求旺盛",
            "半导体芯片供不应求",
            "新能源车出口创新高",
        ]
        result = classify_by_keywords(texts, market="cn")
        scores = [r["heat_score"] for r in result]
        assert scores == sorted(scores, reverse=True)
