"""
AVEDA 品牌情報系統 - 報告生成模組
將分析結果注入 Jinja2 HTML 模板，生成靜態 Dashboard 報告。
"""

import logging
import os
from collections import Counter
from datetime import datetime
from typing import List

from jinja2 import Environment, FileSystemLoader

import config
from collector.models import (
    AnalyzedItem,
    CollectedItem,
    DailyReport,
    EventResult,
    SentimentResult,
)

logger = logging.getLogger(__name__)


def build_daily_report(
    items: List[CollectedItem],
    sentiments: List[SentimentResult],
    events: List[EventResult],
) -> DailyReport:
    """
    從分析結果建構 DailyReport 物件。

    Args:
        items: 搜集到的項目
        sentiments: 情緒分析結果（與 items 一一對應）
        events: 活動萃取結果（與 items 一一對應）

    Returns:
        DailyReport 物件
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # 計算情緒統計
    pos = sum(1 for s in sentiments if s.sentiment == "positive")
    neg = sum(1 for s in sentiments if s.sentiment == "negative")
    neu = sum(1 for s in sentiments if s.sentiment == "neutral")

    # Top 關鍵字統計
    keyword_counter = Counter(item.keyword for item in items)
    top_products = [
        {"keyword": kw, "count": count}
        for kw, count in keyword_counter.most_common(8)
    ]

    # 有效活動列表（過濾重複內容）
    raw_events = [e.to_dict() for e in events if e.has_event]
    active_events = []
    seen_events = set()
    for e_dict in raw_events:
        # 以文字作為去重金鑰（相容 event_detail 或 event_title）
        key = str(e_dict.get("event_detail") or e_dict.get("event_title") or e_dict.get("event_type", "未命名"))
        if key not in seen_events:
            seen_events.add(key)
            active_events.append(e_dict)

    # 完整分析項目
    analyzed_items = []
    for item, sent, evt in zip(items, sentiments, events):
        analyzed = AnalyzedItem(collected=item, sentiment=sent, event=evt)
        analyzed_items.append(analyzed.to_dict())

    return DailyReport(
        date=today,
        total_items=len(items),
        positive_count=pos,
        negative_count=neg,
        neutral_count=neu,
        top_products=top_products,
        events=active_events,
        items=analyzed_items,
    )


def generate_html(report: DailyReport) -> str:
    """
    將 DailyReport 注入 HTML 模板，生成完整的 Dashboard HTML。

    Args:
        report: DailyReport 物件

    Returns:
        生成的 HTML 檔案路徑
    """
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATES_DIR),
        autoescape=True,
    )
    template = env.get_template("dashboard.html")

    total = max(report.total_items, 1)
    html = template.render(
        date=report.date,
        total_items=report.total_items,
        positive_count=report.positive_count,
        negative_count=report.negative_count,
        neutral_count=report.neutral_count,
        positive_pct=round(report.positive_count / total * 100, 1),
        negative_pct=round(report.negative_count / total * 100, 1),
        neutral_pct=round(report.neutral_count / total * 100, 1),
        top_products=report.top_products,
        events=report.events,
        items=report.items,
    )

    # 寫入檔案
    filename = f"report_{report.date}.html"
    filepath = os.path.join(config.REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"報告已生成: {filepath}")
    return filepath


# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # 模擬測試資料
    test_items = [
        CollectedItem(
            title="AVEDA 蘊活菁華超好用",
            snippet="用了三個月掉髮減少好多",
            url="https://example.com/1",
            source="Dcard",
            language="zh",
            keyword="AVEDA 蘊活菁華",
        ),
        CollectedItem(
            title="AVEDA shampoo review",
            snippet="Great scent and effective",
            url="https://example.com/2",
            source="Reddit",
            language="en",
            keyword="AVEDA",
        ),
    ]
    test_sentiments = [
        SentimentResult("positive", 0.92, "表達好用、改善掉髮", "https://example.com/1"),
        SentimentResult("positive", 0.88, "Positive review", "https://example.com/2"),
    ]
    test_events = [
        EventResult(has_event=False, source_url="https://example.com/1"),
        EventResult(has_event=False, source_url="https://example.com/2"),
    ]

    report = build_daily_report(test_items, test_sentiments, test_events)
    path = generate_html(report)
    print(f"\n報告已生成: {path}")
    print(f"請在瀏覽器開啟查看")
