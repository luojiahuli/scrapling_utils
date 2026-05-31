"""板块富化器 — 关键词 + LLM 双通道"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── 板块关键词映射（中文/英文） ────────────────────────

SECTOR_KEYWORDS_CN: dict[str, list[str]] = {
    "人工智能": ["人工智能", "AI", "大模型", "机器学习", "深度学习", "智能体", "算力", "AIGC", "多模态"],
    "半导体": ["半导体", "芯片", "集成电路", "光刻", "封测", "晶圆", "EDA", "先进封装"],
    "新能源": ["新能源", "锂电池", "光伏", "风电", "氢能", "储能", "电池", "固态电池"],
    "新能源汽车": ["新能源汽车", "电动汽车", "充电桩", "锂电", "比亚迪", "特斯拉", "锂矿"],
    "数字经济": ["数字经济", "数据要素", "数据资产", "数字化转型", "云计算", "大数据", "数据安全"],
    "国产软件": ["国产软件", "信创", "操作系统", "数据库", "工业软件", "鸿蒙", "ERP", "自主可控"],
    "军工": ["军工", "国防", "航天", "航空", "舰船", "导弹", "卫星", "船舶"],
    "医药": ["医药", "医疗", "创新药", "CXO", "生物医药", "医疗器械", "中药", "集采"],
    "消费电子": ["消费电子", "智能手机", "可穿戴", "MR", "VR", "AR", "折叠屏", "智能穿戴"],
    "机器人": ["机器人", "人形机器人", "工业机器人", "伺服", "减速器", "机器视觉"],
    "通信": ["通信", "5G", "6G", "光通信", "卫星互联网", "星链"],
    "光伏": ["光伏", "太阳能", "硅料", "硅片", "组件", "逆变器", "异质结"],
    "储能": ["储能", "抽水蓄能", "电化学储能", "钠离子", "钒电池", "压缩空气"],
    "低空经济": ["低空经济", "无人机", "eVTOL", "飞行汽车", "空管", "低空"],
    "消费": ["消费", "食品饮料", "白酒", "家电", "旅游", "免税", "预制菜"],
    "教育": ["教育", "职业教育", "AI教育", "在线教育", "高教"],
    "农业": ["农业", "种业", "粮食", "农机", "猪周期", "乡村振兴"],
    "环保": ["环保", "碳中和", "碳交易", "节能减排", "污水处理", "垃圾发电"],
    "基建": ["基建", "水利", "轨道交通", "公路", "工程机械", "建筑"],
    "金融地产": ["银行", "保险", "证券", "信托", "金融", "券商", "房地产", "地产"],
}

SECTOR_KEYWORDS_US: dict[str, list[str]] = {
    "科技": ["Technology", "Software", "Semiconductor", "AI", "Cloud", "Chip", "Internet", "SaaS", "Cybersecurity", "Data Center", "半导体", "芯片", "人工智能"],
    "医疗保健": ["Healthcare", "Biotech", "Pharma", "Medical Device", "Therapy", "Drug", "医疗", "医药", "创新药"],
    "金融": ["Finance", "Bank", "Investment", "Insurance", "FinTech", "Payment", "金融", "银行"],
    "非必需消费": ["Consumer", "Retail", "E-Commerce", "Automotive", "Luxury", "Restaurant", "消费"],
    "必需消费": ["Consumer Staples", "Food", "Beverage", "Household", "Grocery"],
    "能源": ["Energy", "Oil", "Gas", "Petroleum", "Renewable Energy", "能源", "石油"],
    "工业": ["Industrial", "Manufacturing", "Aerospace", "Defense", "Logistics"],
    "公用事业": ["Utilities", "Electric", "Power", "Water", "Clean Energy"],
    "通信服务": ["Telecom", "Media", "Entertainment", "Streaming", "Social Media"],
    "房地产": ["Real Estate", "REIT", "Property"],
}

SECTOR_KEYWORDS_HK: dict[str, list[str]] = {
    "科技": ["Technology", "Internet", "Software", "AI", "Cloud", "Semiconductor", "科技", "互联网", "软件"],
    "金融": ["Finance", "Bank", "Insurance", "Investment", "金融", "银行", "保险", "证券"],
    "医疗保健": ["Healthcare", "Biotech", "Pharma", "医疗", "医药", "生物医药"],
    "消费": ["Consumer", "Retail", "E-Commerce", "消费", "零售"],
    "能源": ["Energy", "Oil", "Gas", "能源", "石油", "煤炭"],
    "地产": ["Real Estate", "Property", "房地产", "地产", "物业"],
    "电讯": ["Telecom", "Telecommunication", "电讯", "通信"],
    "公用事业": ["Utilities", "Power", "Water", "公用事业", "电力", "水务"],
    "工业": ["Industrial", "Manufacturing", "工业", "制造"],
    "汽车": ["Automotive", "Electric Vehicle", "汽车", "新能源汽车"],
}


def get_keywords(market: str) -> dict[str, list[str]]:
    """获取指定市场的关键词映射表"""
    if market == "us":
        return SECTOR_KEYWORDS_US
    elif market == "hk":
        return SECTOR_KEYWORDS_HK
    else:
        return SECTOR_KEYWORDS_CN


# ── 关键词分类（快速通道） ─────────────────────────────

def classify_by_keywords(
    texts: list[str],
    market: str = "cn",
    excluded: list[str] | None = None,
) -> list[dict[str, Any]]:
    """关键词板块分类，返回 [{"sector": str, "heat_score": float, "matched_count": int}, ...]"""
    keywords = get_keywords(market)
    excluded = excluded or ["金融地产"] if market == "cn" else (excluded or [])

    all_text = " ".join(texts).lower()
    all_text_lower = all_text

    # 提取词集：优先 jieba 分词，fallback 到正则
    try:
        import jieba
        words = jieba.lcut(all_text)
        word_set = set(w for w in words if len(w) > 1)
    except ImportError:
        word_set = set(re.findall(r"[a-zA-Z]{3,}|[一-鿿]{2,}", all_text))

    # 补充英文正则（跨市场兼容）
    eng_words = set(re.findall(r"[a-zA-Z]{3,}", all_text))
    word_set.update(eng_words)

    results = []
    for sector, kw_list in keywords.items():
        if sector in excluded:
            continue
        count = 0
        for kw in kw_list:
            kw_lower = kw.lower()
            # 英文关键词：精确匹配（word_set）
            # 中文关键词：子串匹配（更鲁棒，如"科技"匹配"科技股反弹"）
            if re.search(r"[一-鿿]", kw_lower):
                if kw_lower in all_text_lower:
                    count += 1
            else:
                if kw_lower in word_set:
                    count += 1
        if count > 0:
            results.append({
                "sector": sector,
                "heat_score": round(min(count / max(len(kw_list), 1) * 100, 100), 1),
                "matched_count": count,
            })

    results.sort(key=lambda x: -x["heat_score"])
    return results


# ── LLM 分类（增强通道） ────────────────────────────────

_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
_GEMINI_MODEL_FALLBACK = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]
_last_call = 0.0


def _gemini_call(prompt: str, api_key: str, rate_limit: float = 7.0) -> dict | None:
    """调用 Gemini API 并返回 JSON 结果"""
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < rate_limit:
        time.sleep(rate_limit - elapsed)

    import requests

    models = _GEMINI_MODEL_FALLBACK
    for model in models:
        url = f"{_GEMINI_ENDPOINT}/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }
        try:
            _last_call = time.time()
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                return _parse_gemini_response(resp.json())
            if resp.status_code in (429, 404):
                time.sleep(1)
                continue
            logger.warning("Gemini %s: HTTP %d", model, resp.status_code)
            return None
        except Exception as e:
            logger.debug("Gemini %s failed: %s", model, e)
    return None


def _parse_gemini_response(data: dict) -> dict | None:
    """解析 Gemini API 响应中的 JSON"""
    try:
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )
        if not text:
            return None
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(text)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.debug("Gemini response parse error: %s", e)
        return None


def _build_llm_prompt(texts: list[str], market: str, sectors: list[str]) -> str:
    """构建 LLM 分类 prompt"""
    sector_list = "\n".join(f"- {s}" for s in sectors)
    items = "\n---\n".join(t[:500] for t in texts[:10])

    return f"""You are a sector classification AI for {market.upper()} stock market news.
Classify each news item into the most relevant sector(s) and assign a relevance score.

Available sectors:
{sector_list}

News items:
{items}

Return JSON: {{"items": [{{"index": 0, "sectors": [{{"sector": "name", "score": 0-100}}], "sentiment": "positive/negative/neutral"}}, ...]}}
Score = relevance & heat combined (0=none, 100=extremely relevant hot topic).
Return max 2 sectors per item, only include sectors with score >= 20."""


def classify_by_llm(
    texts: list[str],
    market: str,
    api_key: str = "",
    sector_list: list[str] | None = None,
) -> list[dict[str, Any]] | None:
    """LLM 板块分类（可选），批量返回"""
    if not api_key:
        logger.info("LLM classification skipped: no API key")
        return None

    sectors = sector_list or list(get_keywords(market).keys())
    batches = [texts[i:i + 5] for i in range(0, len(texts), 5)]
    all_results: list[dict[str, Any]] = []

    for batch in batches:
        prompt = _build_llm_prompt(batch, market, sectors)
        result = _gemini_call(prompt, api_key)
        if result and "items" in result:
            for item in result["items"]:
                for sec in item.get("sectors", []):
                    all_results.append({
                        "sector": sec["sector"],
                        "heat_score": float(sec["score"]),
                        "sentiment": item.get("sentiment", "neutral"),
                    })

    if not all_results:
        return None

    # 合并统计
    merged: dict[str, dict[str, Any]] = {}
    for r in all_results:
        s = r["sector"]
        if s not in merged:
            merged[s] = {"sector": s, "heat_score": 0, "mention_count": 0}
        merged[s]["heat_score"] = max(merged[s]["heat_score"], r["heat_score"])
        merged[s]["mention_count"] = merged[s].get("mention_count", 0) + 1

    results = list(merged.values())
    results.sort(key=lambda x: -x["heat_score"])
    return results


# ── 统一分类器 ─────────────────────────────────────────

def classify_sectors(
    texts: list[str],
    market: str = "cn",
    api_key: str = "",
    use_llm: bool = False,
) -> list[dict[str, Any]]:
    """统一入口：关键词 + 可选 LLM，结果融合

    返回 [{"sector": str, "heat_score": float, "source": str}, ...]
    """
    # 1. 关键词快速通道
    kw_results = classify_by_keywords(texts, market=market)

    # 2. LLM 增强
    llm_results = None
    if use_llm and api_key:
        try:
            llm_results = classify_by_llm(texts, market, api_key)
        except Exception as e:
            logger.warning("LLM classification failed: %s", e)

    # 3. 融合（有 LLM 时用 LLM 分数调整关键词分数）
    if llm_results:
        llm_map = {r["sector"]: r["heat_score"] for r in llm_results}
        for r in kw_results:
            if r["sector"] in llm_map:
                r["heat_score"] = max(r["heat_score"], llm_map[r["sector"]])
                r["source"] = "keyword+llm"
            else:
                r["source"] = "keyword"
        # 补入 LLM 特有的板块
        existing = {r["sector"] for r in kw_results}
        for r in llm_results:
            if r["sector"] not in existing:
                kw_results.append({**r, "source": "llm"})
    else:
        for r in kw_results:
            r["source"] = "keyword"

    kw_results.sort(key=lambda x: -x["heat_score"])
    return kw_results
