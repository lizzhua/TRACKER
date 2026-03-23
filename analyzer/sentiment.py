"""
aespa 情報系統 - 情緒分析模組
使用 Gemini LLM 對搜集到的內容進行正/負/中立情緒判斷。
"""

import logging
from typing import List

from collector.models import CollectedItem, SentimentResult
from analyzer.llm_client import call_llm_json

logger = logging.getLogger(__name__)

SENTIMENT_PROMPT_TEMPLATE = """你是一位品牌輿情分析專家。請分析以下關於 aespa品牌的內容，判斷其情緒傾向。

## 分析對象
- 標題: {title}
- 來源: {source}
- 摘要: {snippet}
- 內文: {full_text}

## 分析要求
1. 判斷這段內容對 aespa 品牌的情緒是「正面 (positive)」、「負面 (negative)」或「中立 (neutral)」。
2. 若是單純轉載官方消息或事實描述，判定為中立。
3. 給出 0.0 到 1.0 之間的信心分數。
4. 簡短說明判斷理由（20 字以內）。

## 回應格式（必須回傳純 JSON）
{{"sentiment": "positive|negative|neutral", "confidence": 0.95, "reason": "判斷理由"}}
"""


def analyze_sentiment(item: CollectedItem) -> SentimentResult:
    """
    對單筆 CollectedItem 進行情緒分析。

    Args:
        item: 搜集到的內容項目

    Returns:
        SentimentResult 分析結果
    """
    prompt = SENTIMENT_PROMPT_TEMPLATE.format(
        title=item.title,
        source=item.source,
        snippet=item.snippet,
        full_text=(item.full_text or item.snippet)[:3000],  # 限制長度
    )

    result = call_llm_json(prompt)

    if result and "sentiment" in result:
        return SentimentResult(
            sentiment=result["sentiment"],
            confidence=float(result.get("confidence", 0.5)),
            reason=result.get("reason", ""),
            source_url=item.url,
        )

    # 預設回傳中立（LLM 解析失敗時）
    logger.warning(f"情緒分析失敗，預設為中立: {item.url}")
    return SentimentResult(
        sentiment="neutral",
        confidence=0.0,
        reason="LLM 分析失敗，預設中立",
        source_url=item.url,
    )


def analyze_sentiments(items: List[CollectedItem]) -> List[SentimentResult]:
    """
    批次情緒分析。

    Args:
        items: CollectedItem 列表

    Returns:
        SentimentResult 列表（與 items 一一對應）
    """
    logger.info(f"開始情緒分析，共 {len(items)} 筆...")
    results = []

    for i, item in enumerate(items, 1):
        logger.info(f"情緒分析 [{i}/{len(items)}]: {item.title[:40]}...")
        sr = analyze_sentiment(item)
        results.append(sr)
        logger.info(f"  → {sr.sentiment} (信心: {sr.confidence:.2f}) - {sr.reason}")

    pos = sum(1 for r in results if r.sentiment == "positive")
    neg = sum(1 for r in results if r.sentiment == "negative")
    neu = sum(1 for r in results if r.sentiment == "neutral")
    logger.info(f"情緒分析完成：正面 {pos} / 負面 {neg} / 中立 {neu}")

    return results


# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # 模擬測試資料
    test_item = CollectedItem(
        title="Gemini 1.5 Pro升級版上市",
        snippet="Google 推出全新 Invati 蘊活菁華，添加更多植物萃取成分，有效減少掉髮。",
        url="https://example.com/aespa-supernova",
        language="zh",
        source="dcard",
        keyword="aespa",
    )

    result = analyze_sentiment(test_item)
    print(f"\n情緒: {result.sentiment}")
    print(f"信心: {result.confidence}")
    print(f"理由: {result.reason}")
