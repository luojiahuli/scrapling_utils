# Scrapling Utils — 跨项目共享爬虫工具包

基于 **ECC 架构（COLLECT → ENRICH → STORE）** 的多市场新闻爬虫与板块分类引擎。

## 架构

```
COLLECT          →   ENRICH            →   STORE
并行抓取所有源      关键词 + LLM 分类      热点头条输出
```

## 核心模块

| 模块 | ECC 模式 | 功能 |
|------|----------|------|
| `SmartFetcher` | 基础爬虫 | 自动代理检测 + 重试 + 反检测头 |
| `fetch_all_parallel()` | **Parallel Execution** | `ThreadPoolExecutor` 并行抓取所有新闻源，合并去重 |
| `ContentHashCache` | **Content Hash Cache** | SHA-256 内容哈希缓存 + TTL 自动过期 |
| `classify_sectors()` | **AI Enrichment** | 关键词 + Gemini LLM 双通道板块分类 |
| `load_config()` | **Config-Driven** | YAML 配置 + 环境变量覆盖 |

## 支持的新闻源

### 美股 (US)
- Yahoo Finance, CNBC, Reuters, Finviz, MarketWatch, Barchart, 财联社

### 港股 (HK)
- Yahoo Finance, AASTOCKS, 新浪财经, 财联社

### A 股 (CN)
- 新浪财经, 财联社, 东方财富板块热度

## 板块分类

支持三市场（CN/US/HK）关键词映射 + 可选 Gemini LLM 增强：
- **快速通道**：20+ 板块关键词映射，毫秒级响应
- **增强通道**：Gemini Flash 批量分析，理解语义上下文

## 安装

```bash
pip install -e /path/to/scrapling_utils
```

## 测试

```bash
python -m pytest tests/ -v  # 23 tests, all pass
```

## 配置

支持 YAML 文件或环境变量：

```bash
export GEMINI_API_KEY=your_key    # 启用 LLM 增强分类
export SCRAPLING_TIMEOUT=30       # 全局超时
export SCRAPLING_CACHE_TTL=60     # 缓存 TTL（分钟）
```

## GitHub Actions

- CI：多 Python 版本（3.9/3.11/3.12）自动测试
- 定时：工作日早 6 点运行
