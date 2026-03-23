"""
aespa 情報系統 - 資料模型
統一定義搜集、分析各階段的資料結構。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class CollectedItem:
    """搜集階段的單筆資料"""
    title: str
    snippet: str
    url: str
    source: str                          # 來源平台（e.g. "Dcard", "Google News"）
    language: str                        # "zh" 或 "en"
    keyword: str                         # 觸發搜尋的關鍵字
    date: Optional[str] = None           # 原始發佈日期（若可取得）
    full_text: Optional[str] = None      # 爬取的完整內文
    collected_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class SentimentResult:
    """情緒分析結果"""
    sentiment: str          # "positive", "negative", "neutral"
    confidence: float       # 0.0 ~ 1.0
    reason: str             # LLM 給出的判斷理由
    source_url: str         # 對應的原始 URL

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EventResult:
    """活動萃取結果"""
    has_event: bool
    event_type: Optional[str] = None    # "new_product", "promotion", "pop_up", "other"
    event_detail: Optional[str] = None  # 活動描述
    event_date: Optional[str] = None    # 活動日期
    source_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalyzedItem:
    """單筆完整分析結果（搜集 + 情緒 + 活動）"""
    collected: CollectedItem
    sentiment: SentimentResult
    event: EventResult
    analyzed_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "collected": self.collected.to_dict(),
            "sentiment": self.sentiment.to_dict(),
            "event": self.event.to_dict(),
            "analyzed_at": self.analyzed_at,
        }


@dataclass
class DailyReport:
    """每日報告摘要"""
    date: str
    total_items: int
    positive_count: int
    negative_count: int
    neutral_count: int
    top_products: list          # [{"keyword": "...", "count": N}, ...]
    events: list                # [EventResult.to_dict(), ...]
    items: list                 # [AnalyzedItem.to_dict(), ...]

    @property
    def positive_ratio(self) -> float:
        return self.positive_count / max(self.total_items, 1)

    @property
    def negative_ratio(self) -> float:
        return self.negative_count / max(self.total_items, 1)

    @property
    def neutral_ratio(self) -> float:
        return self.neutral_count / max(self.total_items, 1)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["positive_ratio"] = round(self.positive_ratio, 3)
        d["negative_ratio"] = round(self.negative_ratio, 3)
        d["neutral_ratio"] = round(self.neutral_ratio, 3)
        return d
