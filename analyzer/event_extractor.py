"""
AVEDA 品牌情報系統 - 活動萃取模組
使用 Gemini LLM 辨識文中的活動資訊（新品上市、促銷、快閃店等）。
"""

import logging
from typing import List

from collector.models import CollectedItem, EventResult
from analyzer.llm_client import call_llm_json

logger = logging.getLogger(__name__)

EVENT_PROMPT_TEMPLATE = """你是一位品牌活動情報分析專家。請分析以下關於 AVEDA（肯夢）品牌的內容，判斷是否包含品牌活動或重要事件。

## 分析對象
- 標題: {title}
- 來源: {source}
- 摘要: {snippet}
- 內文: {full_text}

## 需要辨識的活動類型
1. **new_product** — 新品上市、產品升級
2. **promotion** — 促銷、折扣、優惠活動、週年慶
3. **pop_up** — 快閃店、線下體驗活動
4. **collaboration** — 品牌聯名、跨界合作
5. **other** — 其他值得注意的品牌事件（例如品牌公關危機、重大人事異動等）

## 分析要求
1. 判斷是否包含上述任何類型的活動。
2. 若有，萃取活動細節與日期（若文中有提及）。
3. 若無任何活動資訊，has_event 設為 false。

## 回應格式（必須回傳純 JSON）
{{"has_event": true, "event_type": "promotion", "event_detail": "AVEDA 母親節全館 85 折", "event_date": "2025-05-01"}}

若無活動：
{{"has_event": false, "event_type": null, "event_detail": null, "event_date": null}}
"""


def extract_event(item: CollectedItem) -> EventResult:
    """
    對單筆 CollectedItem 進行活動萃取。

    Args:
        item: 搜集到的內容項目

    Returns:
        EventResult 萃取結果
    """
    prompt = EVENT_PROMPT_TEMPLATE.format(
        title=item.title,
        source=item.source,
        snippet=item.snippet,
        full_text=(item.full_text or item.snippet)[:3000],
    )

    result = call_llm_json(prompt)

    if result and "has_event" in result:
        return EventResult(
            has_event=bool(result["has_event"]),
            event_type=result.get("event_type"),
            event_detail=result.get("event_detail"),
            event_date=result.get("event_date"),
            source_url=item.url,
        )

    # 預設無活動（LLM 解析失敗時）
    logger.warning(f"活動萃取失敗，預設為無活動: {item.url}")
    return EventResult(
        has_event=False,
        source_url=item.url,
    )


def extract_events(items: List[CollectedItem]) -> List[EventResult]:
    """
    批次活動萃取。

    Args:
        items: CollectedItem 列表

    Returns:
        EventResult 列表（與 items 一一對應）
    """
    logger.info(f"開始活動萃取，共 {len(items)} 筆...")
    results = []

    for i, item in enumerate(items, 1):
        logger.info(f"活動萃取 [{i}/{len(items)}]: {item.title[:40]}...")
        er = extract_event(item)
        results.append(er)
        if er.has_event:
            logger.info(f"  → 🎉 發現活動: [{er.event_type}] {er.event_detail}")

    event_count = sum(1 for r in results if r.has_event)
    logger.info(f"活動萃取完成：發現 {event_count}/{len(results)} 筆包含活動")

    return results


# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    test_item = CollectedItem(
        title="AVEDA 母親節限定組合 全館滿額贈好禮",
        snippet="AVEDA 為慶祝母親節推出限定優惠組合，全館消費滿 3000 元贈蘊活旅行組。",
        url="https://example.com/aveda-mothers-day",
        source="Fashion Press",
        language="zh",
        keyword="AVEDA 促銷",
    )

    result = extract_event(test_item)
    print(f"\n有活動: {result.has_event}")
    print(f"類型: {result.event_type}")
    print(f"細節: {result.event_detail}")
    print(f"日期: {result.event_date}")
