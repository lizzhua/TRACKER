"""
aespa 情報系統 - Tavily 搜尋模組
透過 Tavily AI API 進行精準網路搜尋，獲取相關新聞與輿情。
"""

import logging
from typing import List

from tavily import TavilyClient

import config
from collector.models import CollectedItem

logger = logging.getLogger(__name__)


def search_tavily(keyword: str, max_results: int = 5) -> List[CollectedItem]:
    """
    使用 Tavily API 搜尋指定關鍵字。

    Args:
        keyword: 搜尋關鍵字
        max_results: 最大回傳筆數

    Returns:
        CollectedItem 列表
    """
    if not config.TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY 未設定，將跳過 Tavily 搜尋")
        return []

    client = TavilyClient(api_key=config.TAVILY_API_KEY)
    items: List[CollectedItem] = []

    try:
        logger.info(f"正在透過 Tavily 搜尋: {keyword} ...")
        
        # 使用 advanced 會提供更好的總結內容，但若想省額度可改用 basic
        response = client.search(
            query=keyword,
            search_depth="advanced",
            max_results=max_results,
            days=1,  # 限制搜尋過去 24 小時的資訊
            include_images=False,
            include_raw_content=False,
        )
        
        results = response.get("results", [])
        
        for r in results:
            item = CollectedItem(
                title=r.get("title", ""),
                snippet=r.get("content", ""),
                url=r.get("url", ""),
                source="Tavily Search",
                language="zh",  # Tavily 回應大部分已自動判斷為所詢問的語言
                keyword=keyword,
            )
            items.append(item)
            logger.debug(f"Tavily 發現: {item.title} ({item.url})")

    except Exception as e:
        logger.error(f"Tavily 搜尋失敗 [{keyword}]: {e}")

    return items


def collect_tavily() -> List[CollectedItem]:
    """
    對所有 config 設定的 Tavily 關鍵字進行搜尋，回傳彙整結果。
    同時自動去除重複 URL。
    """
    if not config.TAVILY_API_KEY:
        logger.warning("未偵測到 TAVILY_API_KEY，略過此階段。")
        return []

    all_items: List[CollectedItem] = []
    seen_urls: set = set()

    # 減少額度消耗：1個中文關鍵字 + 1個英文關鍵字，每個只抓前 2 筆
    target_keywords = [config.KEYWORDS_TAVILY[0]]
    if config.KEYWORDS_EN:
        target_keywords.append(config.KEYWORDS_EN[0])

    for kw in target_keywords:
        results = search_tavily(kw, max_results=2)
        for item in results:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                all_items.append(item)

    logger.info(f"Tavily 搜尋完成，共取得 {len(all_items)} 筆不重複結果")
    return all_items


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    res = collect_tavily()
    print(f"取得 {len(res)} 筆")
